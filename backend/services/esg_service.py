from __future__ import annotations

import re
from typing import Any

import requests
from flask import current_app

from backend.services.local_rag_service import generate_local_recommendations


REQUIRED_FIELDS = [
    'co2_emissions',
    'revenue',
    'governance_score',
    'social_score',
    'environment_score',
]


def validate_predict_payload(payload: Any) -> tuple[bool, dict[str, float], str | None]:
    if not isinstance(payload, dict):
        return False, {}, 'Payload must be a JSON object.'

    missing_fields = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing_fields:
        return False, {}, f"Missing required fields: {', '.join(missing_fields)}"

    numeric_features: dict[str, float] = {}
    try:
        for field in REQUIRED_FIELDS:
            numeric_features[field] = float(payload[field])
    except (TypeError, ValueError):
        return False, {}, 'All required fields must be numeric values.'

    for score_field in ['governance_score', 'social_score', 'environment_score']:
        value = numeric_features[score_field]
        if value < 0 or value > 100:
            return False, {}, f'{score_field} must be between 0 and 100.'

    if numeric_features['co2_emissions'] < 0:
        return False, {}, 'co2_emissions must be greater than or equal to 0.'

    if numeric_features['revenue'] < 0:
        return False, {}, 'revenue must be greater than or equal to 0.'

    return True, numeric_features, None


def compute_esg_score(features: dict[str, float]) -> dict[str, Any]:
    governance = features['governance_score']
    social = features['social_score']
    environment = features['environment_score']
    co2_emissions = features['co2_emissions']

    co2_component = max(0.0, 100.0 - min(co2_emissions / 10.0, 100.0))

    raw_score = (
        0.35 * environment
        + 0.30 * governance
        + 0.25 * social
        + 0.10 * co2_component
    )
    score = round(max(0.0, min(raw_score, 100.0)), 2)

    if score < 40:
        risk = 'High'
    elif score < 70:
        risk = 'Medium'
    else:
        risk = 'Low'

    return {
        'score': score,
        'risk': risk,
        'confidence': 0.78,
    }


def get_dashboard_kpis(user: Any | None = None) -> dict[str, Any]:
    role = getattr(user, 'role', 'user')

    base_metrics = {
        'esg_score': 76,
        'risk_level': 'Medium',
        'environment_score': 81,
        'social_score': 73,
        'governance_score': 78,
        'carbon_footprint': '1,240 tCO2e',
        'compliance_rate': 92,
        'open_actions': 5,
    }

    if role == 'admin':
        base_metrics['open_actions'] = 8

    return base_metrics


def _safe_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def _parse_recommendation_lines(answer: str) -> list[str]:
    parsed_lines: list[str] = []
    for line in answer.splitlines():
        cleaned = line.strip().lstrip('-•*').strip()
        if not cleaned:
            continue
        cleaned = re.sub(r'^\d+[\.)]\s*', '', cleaned)
        parsed_lines.append(cleaned)
    return parsed_lines


def _ask_rag_recommendations(prompt: str, rag_url: str, top_k: int, timeout_seconds: int) -> tuple[list[dict[str, Any]], list[str]]:
    rag_payload = {'message': prompt, 'top_k': top_k}
    response = requests.post(rag_url, json=rag_payload, timeout=timeout_seconds)
    response.raise_for_status()
    data = response.json()

    output = data.get('output', {}) if isinstance(data, dict) else {}
    answer = str(output.get('answer', '')).strip() if isinstance(output, dict) else ''

    recommendations: list[dict[str, Any]] = []
    if answer:
        parsed_lines = _parse_recommendation_lines(answer)
        for index, line in enumerate(parsed_lines[:5], start=1):
            recommendations.append(
                {
                    'id': str(index),
                    'title': line,
                    'category': 'Governance',
                    'priority': 'medium',
                    'impact': 8 + index,
                    'effort': 'medium',
                    'timeline': '3 months',
                    'currentScore': 74,
                    'targetScore': 86,
                    'description': line,
                    'actions': [line],
                    'status': 'not-started',
                }
            )

    raw_sources = output.get('sources', []) if isinstance(output, dict) else []
    rag_sources: list[str] = []
    if isinstance(raw_sources, list):
        for source in raw_sources:
            if isinstance(source, str):
                cleaned = source.strip()
                if cleaned:
                    rag_sources.append(cleaned)
            elif isinstance(source, dict):
                label = (
                    source.get('title')
                    or source.get('document')
                    or source.get('source')
                    or source.get('file_name')
                    or source.get('filename')
                    or source.get('id')
                    or source.get('chunk_id')
                    or source.get('url')
                )
                if label:
                    rag_sources.append(str(label))

    return recommendations, rag_sources


def get_recommendations(payload: Any | None = None) -> dict[str, Any]:
    score = None
    risk_level = 'Medium'
    focus_area = 'overall'

    if isinstance(payload, dict):
        score = payload.get('score')
        risk_level = payload.get('risk_level', risk_level)
        focus_area = payload.get('focus_area', focus_area)

    recommendations: list[dict[str, Any]]
    rag_sources: list[str]
    rag_used = False

    rag_url = str(current_app.config.get('RAG_API_URL', '')).strip()
    top_k = _safe_int(current_app.config.get('RAG_TOP_K', 3), 3)

    if rag_url:
        timeout_seconds = _safe_int(current_app.config.get('RAG_TIMEOUT_SECONDS', 60), 60)
        prompt = (
            'You are an ESG recommendation assistant. '
            'Given the company context below, return concise, actionable recommendations as a bullet list. '
            'Each recommendation must be practical and measurable.\n\n'
            f'Context:\n- ESG score: {score}\n- Risk level: {risk_level}\n- Focus area: {focus_area}\n\n'
            'Return 3 to 5 recommendations.'
        )

        try:
            recommendations, rag_sources = _ask_rag_recommendations(prompt, rag_url, top_k, timeout_seconds)
            rag_used = True
        except (requests.RequestException, ValueError) as exc:
            current_app.logger.exception('Remote RAG recommendations failed, switching to local fallback: %s', exc)
            recommendations, rag_sources = generate_local_recommendations(payload, top_k=top_k)
    else:
        recommendations, rag_sources = generate_local_recommendations(payload, top_k=top_k)

    if not recommendations:
        recommendations, rag_sources = generate_local_recommendations(payload, top_k=top_k)

    if isinstance(score, (int, float)) and score < 50:
        recommendations.insert(0, {
            'id': '0',
            'title': 'Prioritize remediation actions',
            'category': 'Governance',
            'priority': 'high',
            'impact': 15,
            'effort': 'medium',
            'timeline': '1 month',
            'currentScore': int(score),
            'targetScore': min(100, int(score) + 15),
            'description': 'Focus on the weakest ESG pillar first to reduce short-term risk.',
            'actions': ['Review the weakest pillar', 'Assign an owner', 'Track weekly progress'],
            'status': 'in-progress',
        })

    if str(risk_level).lower() == 'high':
        recommendations.insert(0, {
            'id': '-1',
            'title': 'Escalate to governance committee',
            'category': 'Governance',
            'priority': 'high',
            'impact': 10,
            'effort': 'low',
            'timeline': '2 weeks',
            'currentScore': int(score) if isinstance(score, (int, float)) else 60,
            'targetScore': 80,
            'description': 'Escalate the issue and define a remediation plan at committee level.',
            'actions': ['Prepare executive briefing', 'Schedule committee review', 'Track mitigation actions'],
            'status': 'in-progress',
        })

    return {
        'focus_area': focus_area,
        'risk_level': risk_level,
        'recommendations': recommendations[:5],
        'sources': rag_sources,
        'rag_used': rag_used,
        'source_count': len(rag_sources),
    }
