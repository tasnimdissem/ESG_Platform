from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
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
# Threshold of 1.6 → cosine ≥ 0.2  (permissif — accepte les chunks faiblement liés
# pour éviter les réponses vides ; le LLM filtre la non-pertinence via le system prompt).
_SIMILARITY_THRESHOLD = 1.6

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
    "manufacturing": [
        "manufacturing", "industrial", "automobile", "automotive",
        "steel", "chemical", "fabrication",
        # French terms
        "manufacturier", "industriel", "usine", "acier", "sidérurgie",
        "métallurgie", "chimique", "plasturgie", "agroalimentaire",
        "équipement industriel", "mécanique", "assemblage", "production",
        # Additional English
        "machinery", "cement", "textile", "paper", "packaging", "foundry",
        "aerospace", "defense", "mining", "construction material",
    ],
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
        # Used on PDF/article TEXT — terms specific enough to energy sector reports.
        # Single-word terms are safe here because this path is only reached for PDFs/articles,
        # never for dataset rows (which use dataset_sector keywords instead).
        "pdf_text": [
            "oil and gas", "upstream oil", "lng terminal", "petroleum refin",
            "fossil fuel", "oil field", "gas exploration", "oil production",
            "oil reserve", "natural gas field", "offshore platform",
            "totalenergies", "total energies",
            "renewable energy", "energy transition", "decarbonisation", "decarbonization",
            "hydrocarbon", "refinery", "offshore wind", "net zero", "net-zero",
            "carbon neutrality", "greenhouse gas", "carbon footprint",
            "scope 1 emission", "scope 2 emission", "scope 3 emission",
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
        "dataset_sector": [
            "industrial machinery", "auto part", "auto equipment",
            "steel", "commodity chemical", "specialty chemical",
            "aerospace", "defense", "paper", "packaging", "textile",
            "cement", "mining", "construction material", "foundry",
        ],
        "pdf_filename": [
            "manufacturing", "industrial", "automotive", "automobile",
            "steel", "chemical", "aerospace", "cement", "textile",
            "machinery", "gri-manufacturing",
        ],
        "pdf_text": [
            "manufacturing process", "industrial production",
            "manufacturing sector", "industrial sector",
            "assembly line", "production facility", "factory",
            "supply chain manufacturing", "industrial waste",
            "metal production", "chemical plant", "automotive production",
            "manufacturing company", "industrial company",
        ],
    },
    "retail": {
        "dataset_sector": ["packaged food", "food and staple", "retail", "beverage"],
        "pdf_filename": ["retail", "consumer", "food"],
        "pdf_text": ["retail store", "consumer goods", "food product"],
    },
}

# Keep backward-compatible alias used by _detect_sector
_SECTOR_KEYWORDS = _SECTOR_DETECT_KEYWORDS

# ── Small-talk routing ────────────────────────────────────────────────────────
# Exact normalized queries that should never hit the FAISS index.
_SMALL_TALK_EXACT: frozenset = frozenset([
    "hello", "hi", "hey", "yo", "sup", "howdy",
    "how are you", "how are you doing", "how are you today",
    "how's it going", "how is it going", "what's up", "whats up",
    "how do you do", "how r u", "how r you",
    "good morning", "good evening", "good afternoon", "good night", "good day",
    "thank you", "thanks", "thx", "ty", "merci", "merci beaucoup",
    "bonjour", "salut", "bonsoir", "bonne journée", "bonne nuit",
    "bye", "goodbye", "see you", "see ya", "ciao", "au revoir", "à bientôt",
    "ok", "okay", "alright", "sure", "no problem", "np",
    "who are you", "what are you", "what can you do",
    "nice", "great", "awesome", "perfect", "cool",
    "yes", "no", "oui", "non",
])

# If the query starts with one of these prefixes AND is short (< 80 chars)
# AND contains no ESG signal, it's treated as small talk.
_SMALL_TALK_PREFIXES: tuple = (
    "hello", "hi ", "hi!", "hi,",
    "hey ", "hey!", "hey,",
    "bonjour", "salut", "bonsoir",
)

# Terms that indicate a real ESG/data question even inside a greeting.
_ESG_SIGNALS: frozenset = frozenset([
    "esg", "score", "report", "company", "emission", "carbon",
    "sustain", "environment", "social", "governance", "sector",
    "nestl", "total", "energi", "climat", "renewable", "ghg",
    "analysi", "analys", "compar", "rank", "predict", "model",
    "data", "dataset", "pdf", "document", "what is", "qu'est",
])


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
        text_head = (item.get("text", "") or "").lower()[:3000]

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
        prefer_pdf: bool = False,
    ) -> List[Dict[str, Any]]:
        _, index_path, meta_path = self._active_paths()

        index = faiss.read_index(str(index_path))
        metadata: List[Dict[str, str]] = json.loads(meta_path.read_text(encoding="utf-8"))

        q_vec = _EMBEDDER.encode([query], convert_to_numpy=True).astype("float32")
        # Fetch a wider candidate pool to ensure PDFs and niche chunks are represented.
        # Dataset rows are numerous and dominate a narrow pool; PDFs need a bigger sample.
        if sector_filter and prefer_pdf:
            fetch_k = min(top_k * 40, index.ntotal)
        elif sector_filter or prefer_pdf:
            fetch_k = min(top_k * 25, index.ntotal)
        else:
            fetch_k = min(top_k * 8, index.ntotal)
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
            # If sector-matched chunks exist, use them for precision.
            # Otherwise fall back to the similarity-ranked results — a "no relevant documents"
            # failure is worse than a cross-sector answer that the LLM can qualify.
            if sector_matched:
                results = sector_matched
            # else: keep results as-is; the similarity gate in answer() handles quality.

        # When the caller prefers PDF context (sustainability reports, GRI, governance…),
        # guarantee that at least half the returned slots are PDF/article chunks so they
        # are never crowded out by the numerically dominant dataset rows.
        if prefer_pdf:
            pdf_results = [r for r in results if r.get("source_type") in ("pdf", "article")]
            other_results = [r for r in results if r.get("source_type") not in ("pdf", "article")]
            n_pdf = min(len(pdf_results), max(top_k // 2, min(4, len(pdf_results))))
            combined = pdf_results[:n_pdf] + other_results[: top_k - n_pdf]
            combined.sort(key=lambda x: x.get("distance", 999.0))
            return combined[:top_k]

        return results[:top_k]

    def health(self) -> Dict[str, Any]:
        status = self._index_status()
        status["service"] = "rag-esg"
        status["timestamp"] = datetime.now(timezone.utc).isoformat()
        status["embedder"] = "sentence-transformers/all-MiniLM-L6-v2"
        status["index_strategy"] = "versioned-faiss"
        return status

    def _classify_intent(self, query: str) -> str:
        """Ask the LLM to classify query intent. Returns 'SMALLTALK', 'GENERAL', or 'RAG'.

        SMALLTALK — casual chat, emotions, greetings, personal questions with no data need.
        GENERAL   — conceptual/factual questions answerable from general ESG knowledge.
        RAG       — needs specific company reports, scores, or indexed proprietary data.
        """
        classification_prompt = (
            "Classify the user query into exactly one of these three categories:\n\n"
            "SMALLTALK — casual chat, greetings, emotions, personal questions, random phrases "
            "that require no data or expertise to handle "
            "(examples: 'hello', 'thank you i love you', 'do you know my name', 'lol', 'ok bye')\n\n"
            "GENERAL — conceptual or factual question answerable from general knowledge, "
            "no specific company document needed "
            "(examples: 'what is ESG?', 'explain CSRD', 'how is a carbon footprint calculated?', "
            "'what are the main ESG rating agencies?')\n\n"
            "RAG — requires searching specific indexed documents, company reports, or proprietary data "
            "(examples: 'Nestlé ESG score 2022', 'analyse TotalEnergies sustainability report', "
            "'compare Nestlé and Microsoft carbon emissions')\n\n"
            f"User query: {query}\n\n"
            "Reply with ONE word only: SMALLTALK, GENERAL, or RAG"
        )
        raw = self._generate_direct(
            system="You are a query intent classifier. Reply with exactly one word from the given options.",
            user=classification_prompt,
        )
        intent = (raw or "").strip().upper().split()[0] if raw else ""
        if intent in ("SMALLTALK", "GENERAL", "RAG"):
            return intent
        return self._classify_intent_fallback(query)

    def _classify_intent_fallback(self, query: str) -> str:
        """Pattern-based fallback when the LLM classifier is unavailable."""
        normalized = re.sub(r'[^\w\s]', ' ', query.strip().lower()).strip()
        normalized = re.sub(r'\s+', ' ', normalized)

        if normalized in _SMALL_TALK_EXACT:
            return "SMALLTALK"

        has_esg = any(sig in normalized for sig in _ESG_SIGNALS)

        if not has_esg:
            if len(query.strip()) < 80 and any(normalized.startswith(p) for p in _SMALL_TALK_PREFIXES):
                return "SMALLTALK"
            if len(query.strip()) < 60 and normalized.startswith("i "):
                return "SMALLTALK"
            if len(query.strip()) < 50:
                return "SMALLTALK"

        if has_esg:
            return "RAG"
        return "GENERAL"

    def _generate_direct(self, system: str, user: str) -> str:
        if config.GROQ_API_KEY and config.GROQ_MODEL:
            try:
                client = OpenAI(
                    api_key=config.GROQ_API_KEY,
                    base_url=config.GROQ_BASE_URL,
                    timeout=config.GROQ_TIMEOUT_SECONDS,
                )
                response = client.chat.completions.create(
                    model=config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.4,
                )
                content = response.choices[0].message.content
                return (content or "").strip()
            except Exception:
                pass
        return ""

    def _small_talk_response(self, query: str) -> str:
        system = (
            "Tu es un assistant ESG sympathique et professionnel. "
            "Réponds naturellement et brièvement (1-2 phrases) dans la même langue que l'utilisateur. "
            "Mentionne que tu peux aider sur les données ESG, les rapports de durabilité ou les scores d'entreprises. "
            "Ne commence pas par 'Bien sûr' ou 'Certainement' — sois direct et chaleureux."
        )
        direct = self._generate_direct(system=system, user=query)
        if direct:
            return direct

        normalized = query.strip().lower()
        if any(w in normalized for w in ["thank", "merci"]):
            return "You're welcome! Feel free to ask any ESG or sustainability question."
        if any(w in normalized for w in ["bye", "goodbye", "au revoir", "ciao"]):
            return "Goodbye! Come back anytime for ESG data or sustainability insights."
        return (
            "Hello! I'm your ESG data assistant. "
            "Ask me about sustainability reports, ESG scores, company performance, or sector comparisons."
        )

    def _answer_from_general_knowledge(self, query: str) -> str:
        system = (
            "Tu es un expert ESG et développement durable avec une connaissance approfondie "
            "des frameworks de reporting (GRI, SASB, TCFD, CSRD), du reporting carbone, "
            "des marchés financiers ESG et des meilleures pratiques sectorielles.\n\n"
            "RÈGLES :\n"
            "1. Réponds TOUJOURS dans la même langue que la question "
            "(français si la question est en français, anglais si en anglais).\n"
            "2. Commence DIRECTEMENT par la réponse — sans formule introductive artificielle.\n"
            "3. Structure ta réponse avec des exemples concrets d'entreprises ou de secteurs réels.\n"
            "4. Sois pédagogique et synthétique : sous-titres ou listes si plusieurs domaines.\n"
            "5. N'invente jamais de données chiffrées spécifiques non vérifiables.\n\n"
            "NORMES GRI — RÈGLES STRICTES :\n"
            "• Utilise EXCLUSIVEMENT les normes GRI publiées en 2021 ou après.\n"
            "• Ne cite JAMAIS GRI 101, GRI 102 ni GRI 103 — ils sont obsolètes depuis janvier 2023 "
            "et ont été remplacés par GRI 1, GRI 2 et GRI 3 (édition 2021).\n"
            "• Classification officielle des piliers ESG (NE PAS déroger) :\n"
            "  - Gouvernance (G) : GRI 2 (disclosures 2-9 à 2-29), GRI 205 Anti-corruption, "
            "GRI 206 Anti-compétitif, GRI 207 Fiscalité, GRI 415 Politique publique.\n"
            "  - Social (S) : série GRI 400 (GRI 401 à 419). "
            "GRI 405 Diversité et égalité des chances est un indicateur SOCIAL, pas Gouvernance.\n"
            "  - Environnement (E) : série GRI 300 (GRI 301 à 308).\n"
            "• Pour chaque indicateur GRI cité, précise : numéro exact, titre officiel, pilier E/S/G."
        )
        answer = self._generate_direct(system=system, user=query)
        if answer:
            return answer
        return (
            "Je n'ai pas de données spécifiques sur ce sujet dans ma base documentaire. "
            "Reformulez votre question en précisant une entreprise, un secteur ou une année "
            "pour que je puisse mieux vous aider."
        )

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
            # GRI / governance signals → prefer framework documents over dataset rows
            "gri",
            "gouvernance",
            "governance",
            "tcfd",
            "csrd",
            "manufacturing",
            "manufacturier",
            "board",
            "conseil",
            "pilier",
            "indicateur",
            "norme",
            "standard",
            "recommandation",
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

    def answer(self, query: str, top_k: int = 8) -> Tuple[str, List[Dict[str, Any]]]:
        # Classify intent: SMALLTALK → direct reply, GENERAL/RAG → check index first.
        intent = self._classify_intent(query)

        if intent == "SMALLTALK":
            return self._small_talk_response(query), []

        # For both GENERAL and RAG intents: always search the index first.
        # If relevant documents are found, use them (with sources).
        # Only fall back to general-knowledge answer when nothing relevant is indexed.
        sector_hint = self._detect_sector(query)
        prefer_pdf = self._prefers_pdf_context(query)
        retrieved = self.search(query=query, top_k=top_k, sector_filter=sector_hint, prefer_pdf=prefer_pdf)

        # ── Similarity gate ────────────────────────────────────────────────────
        # Reject chunks that are too dissimilar to avoid hallucination on
        # off-topic context (e.g., energy query returning insurance documents).
        relevant = [r for r in retrieved if r.get("distance", 999.0) <= _SIMILARITY_THRESHOLD]

        if not relevant:
            # No indexed document is close enough — answer from LLM general knowledge.
            return self._answer_from_general_knowledge(query), []

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
            exact_block = "=== DONNÉES EXACTES DE LA BASE DE DONNÉES ===\n" + exact_data
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
                "Tu es un analyste de données ESG de précision. "
                "Le contexte contient des lignes de données exactes extraites de la base de données.\n\n"
                "RÈGLES IMPÉRATIVES :\n"
                "1. Réponds toujours dans la même langue que la question "
                "(français si la question est en français, anglais si en anglais).\n"
                "2. Commence directement par la réponse — sans formule introductive.\n"
                "3. Cite les valeurs numériques EXACTEMENT telles qu'elles apparaissent "
                "— sans arrondir, sans estimer. Inclus le nom de l'entreprise, l'année et les scores pertinents.\n"
                "4. Pour classer ou comparer des entreprises, utilise les valeurs exactes du contexte.\n"
                "5. Si une donnée est absente du contexte, dis-le clairement sans inventer.\n\n"
                "NORMES GRI — RÈGLES STRICTES :\n"
                "• Utilise EXCLUSIVEMENT les normes GRI 2021 ou ultérieures.\n"
                "• Ne cite JAMAIS GRI 101, GRI 102, GRI 103 (obsolètes depuis janvier 2023).\n"
                "• Piliers officiels : Gouvernance = GRI 2 + GRI 205/206/207/415 ; "
                "Social = GRI 400 (GRI 405 Diversité = SOCIAL, pas Gouvernance) ; "
                "Environnement = GRI 300."
            )
        else:
            system_prompt = (
                "Tu es un expert ESG (Environnement, Social, Gouvernance) et développement durable. "
                "Tu analyses des rapports de durabilité, des données d'entreprises et des études académiques "
                "pour répondre aux questions des utilisateurs de façon claire, concrète et pédagogique.\n\n"
                "RÈGLES IMPÉRATIVES :\n"
                "1. LANGUE : réponds TOUJOURS dans la même langue que la question. "
                "Si la question est en français → réponse entièrement en français, aucun mot anglais. "
                "Si en anglais → réponse entièrement en anglais.\n"
                "2. STYLE : commence DIRECTEMENT par la réponse. "
                "N'utilise JAMAIS de formules introductives comme 'Selon le contexte fourni', "
                "'D'après les documents', 'According to the documents', 'Based on the context', etc.\n"
                "3. EXEMPLES CONCRETS : si les documents mentionnent une entreprise "
                "(TotalEnergies, Unilever, Michelin, Microsoft…), cite ses initiatives, "
                "indicateurs ou objectifs réels tirés du document.\n"
                "4. STRUCTURE : utilise des sous-titres ou des listes à puces si la question couvre plusieurs domaines.\n"
                "5. COMPLÉTUDE : si le contexte ne couvre pas tout, complète naturellement "
                "avec tes connaissances générales ESG sans le signaler artificiellement.\n"
                "6. PRÉCISION : n'invente jamais de chiffres ou données absents du contexte.\n"
                "7. DISCRÉTION : ne révèle jamais les noms de fichiers internes, chunk IDs ou la structure technique.\n\n"
                "NORMES GRI — RÈGLES STRICTES :\n"
                "• Utilise EXCLUSIVEMENT les normes GRI publiées en 2021 ou après.\n"
                "• Ne cite JAMAIS GRI 101, GRI 102 ni GRI 103 — remplacés par GRI 1, GRI 2, GRI 3 (2021). "
                "Si les sources du contexte les mentionnent, corrige-les silencieusement avec la version 2021.\n"
                "• Classification officielle des piliers ESG (NE PAS déroger) :\n"
                "  - Gouvernance (G) : GRI 2 (2-9 à 2-29), GRI 205, GRI 206, GRI 207, GRI 415.\n"
                "  - Social (S) : série GRI 400 (GRI 401-419). "
                "GRI 405 Diversité est SOCIAL, pas Gouvernance — même si les sources l'associent au CA.\n"
                "  - Environnement (E) : série GRI 300 (GRI 301-308).\n"
                "• Pour chaque indicateur GRI cité, précise : numéro exact, titre officiel, pilier E/S/G."
            )

        user_prompt = (
            f"Question : {query}\n\n"
            "Contexte documentaire :\n"
            + "\n\n".join(context_lines)
        )

        groq_answer = self._generate_with_groq(prompt=user_prompt, system=system_prompt)
        if groq_answer:
            return groq_answer, relevant

        if config.OPENAI_API_KEY:
            try:
                openai_answer = self._generate_with_openai(prompt=user_prompt, system=system_prompt)
                if openai_answer:
                    return openai_answer, relevant
            except Exception:
                pass

        return self._fallback_answer(query=query, retrieved=relevant), relevant

    def _generate_with_groq(self, prompt: str, system: str = "") -> str:
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
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            content = response.choices[0].message.content
            return (content or "").strip()
        except Exception:
            return ""

    def _generate_with_openai(self, prompt: str, system: str = "") -> str:
        if not config.OPENAI_API_KEY or not config.OPENAI_MODEL:
            return ""

        try:
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            content = response.choices[0].message.content
            return (content or "").strip()
        except Exception:
            return ""

    def _fallback_answer(self, query: str, retrieved: List[Dict[str, str]]) -> str:
        from .dataset_query import lookup_exact

        # Try to answer directly from exact database data even without an LLM.
        exact_data = lookup_exact(query, top_k=10) if self._should_use_exact_dataset(query) else ""
        if exact_data:
            lines = [
                "⚠️ LLM indisponible — affichage direct des résultats de la base de données :",
                "",
                exact_data,
            ]
            return "\n".join(lines)

        if not retrieved:
            return "Aucun contexte pertinent n'a été trouvé dans l'index pour cette question."

        lines = [
            "La génération via Groq et OpenAI est actuellement indisponible (clé manquante, quota dépassé ou erreur API).",
            "Voici une réponse de secours basée sur les extraits récupérés :",
            f"Question : {query}",
            "",
        ]

        for item in retrieved[:3]:
            snippet = (item.get("text") or "").strip()
            if len(snippet) > 400:
                snippet = snippet[:400].rstrip() + "..."
            lines.append(
                f"- Source {item.get('source_name', 'unknown')} ({item.get('source_type', 'unknown')}) : {snippet}"
            )

        lines.append("")
        lines.append(
            "Configurez GROQ_API_KEY et GROQ_MODEL, ou OPENAI_API_KEY dans le fichier .env pour obtenir des réponses synthétisées."
        )
        return "\n".join(lines)
