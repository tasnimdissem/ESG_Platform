from __future__ import annotations

import json
from urllib import error, request
from typing import Dict, List, Tuple

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
        self.index_path = self.faiss_dir / "index.faiss"
        self.meta_path = self.faiss_dir / "metadata.json"

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

        faiss.write_index(index, str(self.index_path))
        self.meta_path.write_text(json.dumps(chunks, ensure_ascii=True, indent=2), encoding="utf-8")

        return {"chunks": len(chunks), "dimension": int(vectors.shape[1])}

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, str]]:
        if not self.index_path.exists() or not self.meta_path.exists():
            raise FileNotFoundError("Index not found. Call /ingest first.")

        index = faiss.read_index(str(self.index_path))
        metadata: List[Dict[str, str]] = json.loads(self.meta_path.read_text(encoding="utf-8"))

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
