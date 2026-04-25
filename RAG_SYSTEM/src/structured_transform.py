from __future__ import annotations

import json
import re
from typing import Dict, List

from openai import OpenAI

from . import config

_OPENAI_DISABLED = False

_CATEGORY_HINTS = {
    "Environmental": [
        "carbon",
        "co2",
        "emission",
        "emissions",
        "energy",
        "renewable",
        "water",
        "waste",
        "pollution",
        "climate",
        "biodiversity",
        "sustainability",
        "recycling",
        "scope 1",
        "scope 2",
        "scope 3",
    ],
    "Social": [
        "employee",
        "employees",
        "diversity",
        "inclusion",
        "health",
        "safety",
        "community",
        "labor",
        "training",
        "human rights",
        "wellbeing",
        "welfare",
        "gender",
        "turnover",
    ],
    "Governance": [
        "board",
        "audit",
        "compliance",
        "ethics",
        "anti-corruption",
        "corruption",
        "risk management",
        "shareholder",
        "governance",
        "policy",
        "executive",
        "oversight",
        "transparency",
        "remuneration",
        "independent director",
    ],
}

_NUMBER_PATTERN = re.compile(
    r"(?:\b\d{1,3}(?:[\s,]\d{3})*(?:[\.,]\d+)?%?\b|\b\d+(?:[\.,]\d+)?%?\b|\b(?:USD|EUR|GBP|€|\$)\s?\d+(?:[\.,]\d+)?\b)",
    re.IGNORECASE,
)


def _infer_category(text: str) -> str:
    lowered = text.lower()
    scores = {
        category: sum(1 for hint in hints if hint in lowered)
        for category, hints in _CATEGORY_HINTS.items()
    }
    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        return "Environmental"
    return best_category


def _extract_numbers(text: str) -> List[str]:
    seen = []
    for match in _NUMBER_PATTERN.findall(text):
        normalized = match.strip()
        if normalized and normalized not in seen:
            seen.append(normalized)
    return seen


def _rewrite_with_ai(text: str, category: str, numbers: List[str]) -> Dict[str, object]:
    global _OPENAI_DISABLED

    fallback = {
        "category": category,
        "key_insights": _fallback_insights(text),
        "numerical_indicators": numbers,
        "rewritten_text": _rewrite_fallback(text, category),
    }

    if not config.OPENAI_API_KEY or _OPENAI_DISABLED:
        return fallback

    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        prompt = (
            "You are transforming ESG source text into structured dataset rows. "
            "Return only valid JSON with the exact keys: category, key_insights, numerical_indicators, rewritten_text. "
            "category must be one of Environmental, Social, Governance. "
            "Keep numerical values exactly as they appear when relevant. "
            "Rewrite the text clearly and concisely for dataset use. "
            "If the category seems uncertain, use the provided category.\n\n"
            f"Provided category: {category}\n"
            f"Detected numbers: {numbers}\n"
            f"Text: {text}"
        )
        response = client.responses.create(
            model=config.OPENAI_MODEL,
            input=prompt,
            temperature=0.1,
        )
        content = (response.output_text or "").strip()
    except Exception:
        _OPENAI_DISABLED = True
        return fallback

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = fallback

    parsed["category"] = parsed.get("category") or category
    parsed["key_insights"] = parsed.get("key_insights") or _fallback_insights(text)
    parsed["numerical_indicators"] = parsed.get("numerical_indicators") or numbers
    parsed["rewritten_text"] = parsed.get("rewritten_text") or _rewrite_fallback(text, category)
    return parsed


def _fallback_insights(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    insights = []
    for sentence in sentences:
        clean = sentence.strip()
        if clean and clean not in insights:
            insights.append(clean)
        if len(insights) >= 3:
            break
    return insights or [text[:200].strip()]


def _rewrite_fallback(text: str, category: str) -> str:
    cleaned = " ".join(text.split())
    return f"[{category}] {cleaned}"


def transform_chunks(chunks: List[Dict[str, str]]) -> List[Dict[str, object]]:
    transformed: List[Dict[str, object]] = []
    for chunk in chunks:
        text = chunk.get("text", "").strip()
        if not text:
            continue

        category = _infer_category(text)
        numbers = _extract_numbers(text)
        structured = _rewrite_with_ai(text=text, category=category, numbers=numbers)
        transformed.append(
            {
                "category": structured["category"],
                "text": structured["rewritten_text"],
                "key_insights": structured["key_insights"],
                "numerical_indicators": structured["numerical_indicators"],
                "source_type": chunk.get("source_type", "unknown"),
                "source_name": chunk.get("source_name", "unknown"),
                "chunk_id": chunk.get("chunk_id", "unknown"),
                "original_text": text,
            }
        )

    return transformed
