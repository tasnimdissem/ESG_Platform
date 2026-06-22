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
        "greenhouse",
        "deforestation",
        "net zero",
    ],
    # GRI 400 series: Social indicators (401-419)
    # GRI 405 Diversity belongs HERE — not in Governance
    "Social": [
        "employee",
        "employees",
        # GRI 405 — Diversity and Equal Opportunity (SOCIAL, not Governance)
        "diversity",
        "equal opportunity",
        "gri 405",
        "gri405",
        "inclusion",
        "health",
        "safety",
        "occupational",
        "community",
        "labor",
        "labour",
        "training",
        "human rights",
        "wellbeing",
        "welfare",
        "gender",
        "turnover",
        "child labor",
        "forced labor",
        "local community",
        "customer privacy",
        "gri 401",
        "gri 402",
        "gri 403",
        "gri 404",
        "gri 406",
        "gri 407",
        "gri 408",
        "gri 409",
        "gri 410",
        "gri 411",
        "gri 413",
        "gri 416",
        "gri 417",
        "gri 418",
        "gri 419",
    ],
    # GRI 2 (2021) + GRI 205/206/207/415: Governance indicators
    # Board diversity is GRI 2-9 (Governance), distinct from GRI 405 (Social)
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
        "executive",
        "oversight",
        "transparency",
        "remuneration",
        "independent director",
        "whistleblowing",
        "conflict of interest",
        "tax transparency",
        "lobbying",
        "political contribution",
        # GRI 2021 governance disclosures
        "gri 2-9",
        "gri 2-10",
        "gri 2-11",
        "gri 2-12",
        "gri 2-13",
        "gri 2-14",
        "gri 2-15",
        "gri 2-16",
        "gri 2-17",
        "gri 2-18",
        "gri 2-19",
        "gri 2-20",
        "gri 2-21",
        "gri 205",
        "gri 206",
        "gri 207",
        "gri 415",
    ],
}

# Explicit GRI indicator → pillar mapping used by _infer_category
# to prevent misclassification when a GRI number appears in the text.
_GRI_PILLAR_OVERRIDES: dict[str, str] = {
    # Social series (400)
    **{f"gri 4{i:02d}": "Social" for i in range(1, 20)},
    # Governance: GRI 2 disclosures
    **{f"gri 2-{i}": "Governance" for i in range(9, 30)},
    # Governance topic standards
    "gri 205": "Governance",
    "gri 206": "Governance",
    "gri 207": "Governance",
    "gri 415": "Governance",
    # Environmental series (300)
    **{f"gri 3{i:02d}": "Environmental" for i in range(1, 9)},
}

_NUMBER_PATTERN = re.compile(
    r"(?:\b\d{1,3}(?:[\s,]\d{3})*(?:[\.,]\d+)?%?\b|\b\d+(?:[\.,]\d+)?%?\b|\b(?:USD|EUR|GBP|€|\$)\s?\d+(?:[\.,]\d+)?\b)",
    re.IGNORECASE,
)


def _infer_category(text: str) -> str:
    lowered = text.lower()

    # GRI indicator overrides take priority over keyword scoring
    for gri_ref, pillar in _GRI_PILLAR_OVERRIDES.items():
        if gri_ref in lowered:
            return pillar

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
            "Tu es un expert ESG qui transforme des textes sources en lignes de dataset structurées. "
            "Réponds uniquement avec du JSON valide avec exactement ces clés : category, key_insights, numerical_indicators, rewritten_text.\n"
            "category doit être l'une de ces valeurs : Environmental, Social, Governance.\n\n"
            "RÈGLES DE CLASSIFICATION STRICTES (GRI 2021) :\n"
            "- Governance : GRI 2 (2-9 à 2-29), GRI 205, GRI 206, GRI 207, GRI 415. "
            "Inclut : conseil d'administration, anti-corruption, fiscalité, lobbying, conformité.\n"
            "- Social : GRI 401-419. GRI 405 Diversité et égalité des chances = SOCIAL (pas Governance). "
            "Inclut : employés, santé-sécurité, droits humains, formation, communautés.\n"
            "- Environmental : GRI 301-308. Inclut : émissions, énergie, eau, déchets, biodiversité.\n"
            "- Ne cite jamais GRI 101, GRI 102, GRI 103 — remplacés par GRI 1, GRI 2, GRI 3 (2021).\n\n"
            "Conserve les valeurs numériques exactement telles qu'elles apparaissent. "
            "Réécris le texte clairement et de façon concise en français. "
            "En cas de doute sur la catégorie, utilise la catégorie fournie.\n\n"
            f"Catégorie fournie : {category}\n"
            f"Nombres détectés : {numbers}\n"
            f"Texte : {text}"
        )
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        content = (response.choices[0].message.content or "").strip()
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
