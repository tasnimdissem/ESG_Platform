from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import faiss
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from . import config

_EMBEDDER = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


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

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, str]]:
        _, index_path, meta_path = self._active_paths()

        index = faiss.read_index(str(index_path))
        metadata: List[Dict[str, str]] = json.loads(meta_path.read_text(encoding="utf-8"))

        q_vec = _EMBEDDER.encode([query], convert_to_numpy=True).astype("float32")
        distances, indices = index.search(q_vec, top_k)

        results: List[Dict[str, str]] = []
        for rank, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(metadata):
                continue
            item = dict(metadata[idx])
            item["rank"] = rank + 1
            item["distance"] = float(distances[0][rank])
            results.append(item)

        return results

    def health(self) -> Dict[str, Any]:
        status = self._index_status()
        status["service"] = "rag-esg"
        status["timestamp"] = datetime.now(timezone.utc).isoformat()
        status["embedder"] = "sentence-transformers/all-MiniLM-L6-v2"
        status["index_strategy"] = "versioned-faiss"
        return status

    def answer(self, query: str, top_k: int = 5) -> Tuple[str, List[Dict[str, str]]]:
        retrieved = self.search(query=query, top_k=top_k)
        
        # Protection Context Window Overflow: Limit prompt context size 
        # ~16000 chars is roughly 4000 tokens for most LLMs.
        max_context_chars = 16000 
        current_chars = 0
        context_lines = []
        
        for item in retrieved:
            line = f"[{item['source_type']}::{item['source_name']}::{item['chunk_id']}] {item['text']}"
            if current_chars + len(line) > max_context_chars and context_lines:
                # Stop appending if context size exceeds the limit
                break
            context_lines.append(line)
            current_chars += len(line)

        prompt = (
            "You are an ESG assistant. Answer only from the context. "
            "If context is insufficient, say that clearly.\n\n"
            f"Question: {query}\n\n"
            "Context:\n"
            + "\n\n".join(context_lines)
        )

        groq_answer = self._generate_with_groq(prompt=prompt)
        if groq_answer:
            return groq_answer, retrieved

        if config.OPENAI_API_KEY:
            try:
                openai_answer = self._generate_with_openai(prompt=prompt)
                if openai_answer:
                    return openai_answer, retrieved
            except Exception:
                pass

        ollama_answer = self._generate_with_ollama(prompt=prompt)
        if ollama_answer:
            return ollama_answer, retrieved

        return self._fallback_answer(query=query, retrieved=retrieved), retrieved

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
                    {"role": "system", "content": "You are an ESG assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
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
                    {"role": "system", "content": "You are an ESG assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
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
