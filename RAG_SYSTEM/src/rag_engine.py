from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import faiss
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from . import config

_EMBEDDER = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Squared L2 distance threshold (IndexFlatL2 returns squared distances).
# For normalized vectors: cosine_similarity = 1 - distance/2.
# Threshold of 0.7 → cosine ≥ 0.65 (rejects off-topic chunks more aggressively).
_SIMILARITY_THRESHOLD = 0.7

# Keywords used ONLY to detect sector intent in a user query (French + English).
_SECTOR_DETECT_KEYWORDS: Dict[str, List[str]] = {
    "energy": [
        "energy", "energi", "énergi", "énergéti", "énergétique",
        "oil", "gas", "gaz", "petroleum", "petrole", "pétrol",
        "renewable", "renouvelable", "solar", "wind", "coal", "charbon",
        "nuclear", "nucléaire", "electricity", "électricité", "électrique",
        "fossil", "lng", "refinery", "raffin", "upstream", "downstream",
        "utility", "utilities", "totalenergies",
    ],
    "technology": ["tech", "technology", "software", "digital", "semiconductor",
                   "internet", "cloud", "cybersecurity", "technologi", "informatique"],
    "finance": ["bank", "banking", "finance", "insurance", "financial", "assurance",
                "banque", "fintech", "investment"],
    "healthcare": ["health", "healthcare", "pharma", "pharmaceutical", "medical",
                   "biotech", "hospital", "santé", "médicament"],
    "manufacturing": ["manufacturing", "industrial", "automobile", "automotive",
                      "steel", "chemical", "fabrication"],
    "retail": ["retail", "consumer", "food", "beverage", "distribution", "commerce"],
}

# Keywords used to match CHUNKS to a sector.
# For dataset chunks these match against the "Sector: ..." GICS field only.
# For PDF chunks these match against source filename + text.
# IMPORTANT: do NOT use "energy" or "energi" here — they appear in
# "Energy Consumption (log)" metrics of EVERY company, causing false positives.
# For dataset chunks: matched against the extracted "Sector: ..." GICS field only.
# For PDF filename: matched against source_name (short keywords allowed).
# For PDF text: matched against first 1000 chars — multi-word terms only to avoid
#   false positives like "palm oil" (Nestlé) or "oil pressure" (unrelated).
_SECTOR_CHUNK_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "energy": {
        # Used on dataset "Sector: ..." field — safe against false positives
        "dataset_sector": [
            "oil and gas", "oil & gas", "electric utilities", "gas utilities",
            "renewable electricity", "coal and consumable", "multi-utilities",
            "independent power", "integrated oil", "oil and gas drilling",
            "oil and gas refining", "oil and gas storage", "oil and gas equipment",
            "oil",  # safe here: sector names like "Oil and Gas" not "Energy Consumption"
        ],
        # Used on PDF/article source FILENAME (short terms safe — filename is specific)
        "pdf_filename": [
            "totalenergies", "total energies", "shell", "exxon", "chevron",
            "petroleum", "oil-and-gas", "bp-", "energy-report",
        ],
        # Used on PDF/article TEXT — multi-word energy-specific terms only.
        # Do NOT use "scope 1/2" — those appear in all sustainability reports.
        "pdf_text": [
            "oil and gas", "upstream oil", "lng terminal", "petroleum refin",
            "fossil fuel", "oil field", "gas exploration", "oil production",
            "oil reserve", "natural gas field", "offshore platform",
            "totalenergies", "total energies",
        ],
    },
    "technology": {
        "dataset_sector": ["application software", "semiconductor", "it consulting",
                           "tech hardware", "electronic equipment", "internet services"],
        "pdf_filename": ["microsoft", "google", "apple", "tech"],
        "pdf_text": ["software development", "cloud computing", "semiconductor"],
    },
    "finance": {
        "dataset_sector": ["diversified bank", "regional bank", "asset management",
                           "investment bank", "insurance"],
        "pdf_filename": ["bank", "finance", "insurance"],
        "pdf_text": ["banking sector", "financial institution", "insurance premium"],
    },
    "healthcare": {
        "dataset_sector": ["pharmaceutical", "biotech", "medical device", "hospital",
                           "managed health", "health care equipment", "health care facilities"],
        "pdf_filename": ["pharma", "health", "medical", "biotech"],
        "pdf_text": ["pharmaceutical drug", "clinical trial", "patient care"],
    },
    "manufacturing": {
        "dataset_sector": ["industrial machinery", "auto part", "auto equipment",
                           "steel", "commodity chemical", "specialty chemical"],
        "pdf_filename": ["manufacturing", "industrial", "automotive"],
        "pdf_text": ["manufacturing process", "industrial production"],
    },
    "retail": {
        "dataset_sector": ["packaged food", "food and staple", "retail", "beverage"],
        "pdf_filename": ["retail", "consumer", "food"],
        "pdf_text": ["retail store", "consumer goods", "food product"],
    },
}

# Keep backward-compatible alias used by _detect_sector
_SECTOR_KEYWORDS = _SECTOR_DETECT_KEYWORDS


class RagEngine:
    def __init__(self) -> None:
        self.faiss_dir = config.FAISS_DIR
        self.faiss_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir = config.FAISS_VERSIONS_DIR
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.current_file = config.FAISS_CURRENT_FILE

    def _version_dir(self, version: str) -> Path:
        return self.versions_dir / version

    def _write_current_version(self, version: str) -> None:
        payload = {
            "active_version": version,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        temp_path = self.current_file.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        temp_path.replace(self.current_file)

    def _read_current_version(self) -> Dict[str, Any]:
        if not self.current_file.exists():
            raise FileNotFoundError("Active index pointer not found. Call /ingest first.")

        return json.loads(self.current_file.read_text(encoding="utf-8"))

    def _active_paths(self) -> Tuple[str, Path, Path]:
        current = self._read_current_version()
        version = str(current.get("active_version", "")).strip()
        if not version:
            raise FileNotFoundError("Active index version is missing. Call /ingest first.")

        version_dir = self._version_dir(version)
        index_path = version_dir / "index.faiss"
        meta_path = version_dir / "metadata.json"

        if not index_path.exists() or not meta_path.exists():
            raise FileNotFoundError("Active index files are missing. Call /ingest first.")

        return version, index_path, meta_path

    def _index_status(self) -> Dict[str, Any]:
        try:
            version, index_path, meta_path = self._active_paths()
        except FileNotFoundError:
            return {
                "available": False,
                "active_version": None,
                "index_path": None,
                "metadata_path": None,
                "chunks": 0,
                "dimension": 0,
            }

        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        try:
            index = faiss.read_index(str(index_path))
            dimension = int(index.d)
        except Exception:
            dimension = 0

        return {
            "available": True,
            "active_version": version,
            "index_path": str(index_path),
            "metadata_path": str(meta_path),
            "chunks": len(metadata),
            "dimension": dimension,
        }

    def build_index(self, chunks: List[Dict[str, str]]) -> Dict[str, int]:
        if not chunks:
            raise ValueError("No chunks found. Add files into data/raw folders first.")

        texts = [item["text"] for item in chunks]
        vectors = _EMBEDDER.encode(texts, convert_to_numpy=True)
        vectors = vectors.astype("float32")

        # INFO FOR DEFENSE: 'IndexFlatL2' is exhaustive and exact, perfect for your current scale.
        # For scaling to millions of documents, you would replace it with 'IndexIVFFlat' (Inverted File)
        # or 'IndexHNSWFlat' (Hierarchical Navigable Small World) to maintain real-time API performance.
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)

        version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + f"-{uuid4().hex[:8]}"
        version_dir = self._version_dir(version)
        version_dir.mkdir(parents=True, exist_ok=True)

        index_path = version_dir / "index.faiss"
        meta_path = version_dir / "metadata.json"

        faiss.write_index(index, str(index_path))
        meta_path.write_text(json.dumps(chunks, ensure_ascii=True, indent=2), encoding="utf-8")
        self._write_current_version(version)

        return {
            "chunks": len(chunks),
            "dimension": int(vectors.shape[1]),
            "version": version,
        }

    def _chunk_in_sector(self, item: Dict[str, Any], sector_kw_groups: Dict[str, List[str]]) -> bool:
        """Return True if this chunk belongs to the target sector.

        Uses different keyword sets depending on chunk type to avoid false positives:
        - Dataset: only the 'Sector: ...' GICS field (never full text)
        - PDF/article filename: short keywords allowed
        - PDF/article text: multi-word keywords only (prevents 'palm oil' type matches)
        """
        # Structured metadata field takes priority (populated after re-ingestion)
        sector_meta = (item.get("sector", "") or "").lower()
        if sector_meta:
            kws = sector_kw_groups.get("dataset_sector", [])
            return any(kw in sector_meta for kw in kws)

        source_type = item.get("source_type", "")

        if source_type == "dataset":
            # Extract only the "Sector: ..." GICS label — never the full text.
            # This prevents "Energy Consumption (log)" from matching energy filter.
            sector_value = ""
            for part in (item.get("text", "") or "").split("|"):
                stripped = part.strip()
                if stripped.lower().startswith("sector:"):
                    sector_value = stripped[7:].strip().lower()
                    break
            kws = sector_kw_groups.get("dataset_sector", [])
            return any(kw in sector_value for kw in kws)

        # PDFs and articles
        source_name = (item.get("source_name", "") or "").lower()
        text_head = (item.get("text", "") or "").lower()[:1000]

        filename_kws = sector_kw_groups.get("pdf_filename", [])
        if any(kw in source_name for kw in filename_kws):
            return True

        text_kws = sector_kw_groups.get("pdf_text", [])
        return any(kw in text_head for kw in text_kws)

    def _detect_sector(self, query: str) -> Optional[str]:
        normalized = query.lower()
        for sector, keywords in _SECTOR_KEYWORDS.items():
            if any(kw in normalized for kw in keywords):
                return sector
        return None

    def search(
        self,
        query: str,
        top_k: int = 5,
        sector_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        _, index_path, meta_path = self._active_paths()

        index = faiss.read_index(str(index_path))
        metadata: List[Dict[str, str]] = json.loads(meta_path.read_text(encoding="utf-8"))

        q_vec = _EMBEDDER.encode([query], convert_to_numpy=True).astype("float32")
        # Fetch more candidates when sector filtering is requested
        fetch_k = min(top_k * 4, index.ntotal) if sector_filter else min(top_k, index.ntotal)
        distances, indices = index.search(q_vec, fetch_k)

        results: List[Dict[str, Any]] = []
        for rank, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(metadata):
                continue
            item = dict(metadata[idx])
            distance = float(distances[0][rank])
            item["rank"] = rank + 1
            item["distance"] = distance
            # For normalized vectors (all-MiniLM-L6-v2), IndexFlatL2 returns
            # squared L2 distance d where cosine_similarity = 1 - d/2.
            item["similarity"] = round(max(0.0, 1.0 - distance / 2.0), 4)
            results.append(item)

        if sector_filter:
            chunk_kw_groups = _SECTOR_CHUNK_KEYWORDS.get(
                sector_filter,
                {"dataset_sector": [sector_filter], "pdf_filename": [sector_filter], "pdf_text": []},
            )
            sector_matched = [
                r for r in results
                if self._chunk_in_sector(r, chunk_kw_groups)
            ]
            # CRITICAL: if sector was explicitly requested but no chunk belongs to it,
            # return empty → triggers the "no relevant documents" fallback.
            # Do NOT fall back to off-topic chunks — that causes hallucination.
            results = sector_matched

        return results[:top_k]

    def health(self) -> Dict[str, Any]:
        status = self._index_status()
        status["service"] = "rag-esg"
        status["timestamp"] = datetime.now(timezone.utc).isoformat()
        status["embedder"] = "sentence-transformers/all-MiniLM-L6-v2"
        status["index_strategy"] = "versioned-faiss"
        return status

    def _prefers_pdf_context(self, query: str) -> bool:
        normalized = query.lower()
        pdf_signals = (
            "pdf",
            "report",
            "sustainability",
            "climate",
            "energy",
            "emission",
            "emissions",
            "renewable",
            "carbon",
            "oil",
            "gas",
            "totalenergies",
            "microsoft",
        )
        return any(signal in normalized for signal in pdf_signals)

    def _should_use_exact_dataset(self, query: str) -> bool:
        normalized = query.lower()
        if self._prefers_pdf_context(query):
            return False

        dataset_signals = (
            "score",
            "ranking",
            "compare",
            "company",
            "companies",
            "year",
            "sector",
            "country",
        )
        return any(signal in normalized for signal in dataset_signals)

    def answer(self, query: str, top_k: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
        # Detect sector hint from query for targeted retrieval
        sector_hint = self._detect_sector(query)
        retrieved = self.search(query=query, top_k=top_k, sector_filter=sector_hint)

        # ── Similarity gate ────────────────────────────────────────────────────
        # Reject chunks that are too dissimilar to avoid hallucination on
        # off-topic context (e.g., energy query returning insurance documents).
        relevant = [r for r in retrieved if r.get("distance", 999.0) <= _SIMILARITY_THRESHOLD]

        if not relevant:
            return (
                "Je ne dispose pas de documents suffisamment pertinents sur ce sujet "
                "dans ma base de connaissances. "
                "Essayez de préciser le nom d'une entreprise, un secteur ou une année.",
                [],
            )

        if self._prefers_pdf_context(query):
            relevant = sorted(
                relevant,
                key=lambda item: 0 if item.get("source_type") == "pdf" else 1,
            )

        from .dataset_query import lookup_exact

        max_context_chars = 16000
        current_chars = 0
        context_lines: List[str] = []

        # Prepend exact database rows first so the LLM can cite verbatim numbers.
        exact_data = lookup_exact(query, top_k=top_k) if self._should_use_exact_dataset(query) else ""
        if exact_data:
            exact_block = "=== EXACT DATA FROM DATABASE ===\n" + exact_data
            context_lines.append(exact_block)
            current_chars += len(exact_block)

        for item in relevant:
            line = f"[{item['source_type']}::{item['source_name']}::{item['chunk_id']}] {item['text']}"
            if current_chars + len(line) > max_context_chars and context_lines:
                break
            context_lines.append(line)
            current_chars += len(line)

        has_exact = bool(exact_data)
        if has_exact:
            system_prompt = (
                "You are a precise ESG data analyst. "
                "The context includes exact data rows extracted from the database. "
                "You MUST cite those numerical values verbatim — never round, never estimate. "
                "Always include the company name, year, and all relevant scores exactly as shown. "
                "When asked to rank or compare companies, use the exact values to do so. "
                "Answer ONLY from the provided context. "
                "If data for a specific request is absent, clearly state it is not available — "
                "do NOT generate speculative or approximate answers."
            )
        else:
            system_prompt = (
                "You are a precise ESG data analyst. "
                "Answer ONLY using information explicitly present in the provided context. "
                "CRITICAL RULES:\n"
                "1. If the context does not contain relevant information, respond: "
                "'La base de connaissances ne contient pas de données pertinentes sur ce sujet.'\n"
                "2. Do NOT speculate, infer, or generate information not present in the context.\n"
                "3. Do NOT answer with data from a different sector or company than what was asked.\n"
                "4. Do NOT reference internal markers, formats, or data structures.\n"
                "5. If you cannot answer confidently from the context, say so clearly."
            )

        prompt = (
            f"{system_prompt}\n\n"
            f"Question: {query}\n\n"
            "Context:\n"
            + "\n\n".join(context_lines)
        )

        groq_answer = self._generate_with_groq(prompt=prompt)
        if groq_answer:
            return groq_answer, relevant

        if config.OPENAI_API_KEY:
            try:
                openai_answer = self._generate_with_openai(prompt=prompt)
                if openai_answer:
                    return openai_answer, relevant
            except Exception:
                pass

        ollama_answer = self._generate_with_ollama(prompt=prompt)
        if ollama_answer:
            return ollama_answer, relevant

        return self._fallback_answer(query=query, retrieved=relevant), relevant

    def _generate_with_groq(self, prompt: str) -> str:
        if not config.GROQ_API_KEY or not config.GROQ_MODEL:
            return ""

        try:
            client = OpenAI(
                api_key=config.GROQ_API_KEY,
                base_url=config.GROQ_BASE_URL,
                timeout=config.GROQ_TIMEOUT_SECONDS,
            )
            response = client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise ESG data analyst. "
                            "Answer ONLY from the context provided in the user message. "
                            "Never speculate or use knowledge outside the context. "
                            "If the context is insufficient, say so explicitly."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            content = response.choices[0].message.content
            return (content or "").strip()
        except Exception:
            return ""

    def _generate_with_openai(self, prompt: str) -> str:
        if not config.OPENAI_API_KEY or not config.OPENAI_MODEL:
            return ""

        try:
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise ESG data analyst. "
                            "Answer ONLY from the context provided in the user message. "
                            "Never speculate or use knowledge outside the context. "
                            "If the context is insufficient, say so explicitly."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            content = response.choices[0].message.content
            return (content or "").strip()
        except Exception:
            return ""

    def _generate_with_ollama(self, prompt: str) -> str:
        if not config.OLLAMA_MODEL:
            return ""

        payload = {
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }

        req = request.Request(
            url=f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=config.OLLAMA_TIMEOUT_SECONDS) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            parsed = json.loads(raw)
            return (parsed.get("response") or "").strip()
        except (error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return ""

    def _fallback_answer(self, query: str, retrieved: List[Dict[str, str]]) -> str:
        from .dataset_query import lookup_exact

        # Try to answer directly from exact database data even without an LLM.
        exact_data = lookup_exact(query, top_k=10) if self._should_use_exact_dataset(query) else ""
        if exact_data:
            lines = [
                "⚠️ LLM unavailable — showing exact database results directly:",
                "",
                exact_data,
            ]
            return "\n".join(lines)

        if not retrieved:
            return "No relevant context was found in the index for this question."

        lines = [
            "Groq and OpenAI generation are currently unavailable (missing key, quota, or API error).",
            "Below is a context-based fallback answer from retrieved chunks:",
            f"Question: {query}",
            "",
        ]

        for item in retrieved[:3]:
            snippet = (item.get("text") or "").strip()
            if len(snippet) > 400:
                snippet = snippet[:400].rstrip() + "..."
            lines.append(
                f"- Source {item.get('source_name', 'unknown')} ({item.get('source_type', 'unknown')}): {snippet}"
            )

        lines.append("")
        lines.append(
            "Set GROQ_API_KEY and GROQ_MODEL, or configure OLLAMA_MODEL in .env to get synthesized answers."
        )
        return "\n".join(lines)
