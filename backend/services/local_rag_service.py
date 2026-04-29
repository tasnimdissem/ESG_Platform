from __future__ import annotations

from typing import Any


def _fallback_chat_response(message: str) -> str:
    normalized = (message or '').strip().lower()

    if not normalized:
        return 'Please type a question about ESG, reporting, or the dashboard.'

    if 'esg' in normalized and any(keyword in normalized for keyword in ['meaning', 'definition', 'what is', 'quoi', 'signifie']):
        return 'ESG means Environmental, Social, and Governance. It is a framework used to assess sustainability and responsible business practices.'

    if any(keyword in normalized for keyword in ['hello', 'hi', 'hey']):
        return 'Hello. I can help with ESG KPIs, reports, and dashboard navigation.'

    if 'report' in normalized:
        return 'Use the export report action to generate a PDF summary of the current ESG snapshot.'

    if 'power bi' in normalized or 'powerbi' in normalized:
        return 'The dashboard includes an iframe area reserved for your Power BI embed link.'

    if 'predict' in normalized or 'recommend' in normalized:
        return 'The ML routes are ready for future model integration and currently return structured dummy responses.'

    if 'dashboard' in normalized:
        return 'Open the dashboard to see ESG KPIs, risk level, and Power BI integration.'

    return 'I am a local ESG assistant. Ask me about ESG meaning, dashboards, reports, recommendations, or authentication.'


def _source_to_text(source: Any, index: int) -> str:
    if isinstance(source, str):
        cleaned = source.strip()
        return cleaned or f'Source {index}'

    if isinstance(source, dict):
        preferred_keys = [
            'title',
            'document',
            'source',
            'file_name',
            'filename',
            'id',
            'chunk_id',
            'url',
        ]
        for key in preferred_keys:
            value = source.get(key)
            if value:
                return str(value)
        return f'Source {index}'

    return f'Source {index}'


def extract_sources(raw_sources: Any) -> list[str]:
    if not isinstance(raw_sources, list):
        return []

    labels: list[str] = []
    for idx, source in enumerate(raw_sources, start=1):
        labels.append(_source_to_text(source, idx))
    return labels


def generate_local_chat_answer(message: str, top_k: int = 3) -> tuple[str, list[str]]:
    answer = _fallback_chat_response(message)
    sources = [
        'ESG dashboard overview',
        'Reporting workflow',
        'Recommendations playbook',
    ][: max(1, top_k)]
    return answer, sources


def generate_local_recommendations(payload: dict[str, Any] | None = None, top_k: int = 3) -> tuple[list[dict[str, Any]], list[str]]:
    score = None
    risk_level = 'Medium'
    focus_area = 'overall'

    if isinstance(payload, dict):
        score = payload.get('score')
        risk_level = str(payload.get('risk_level', risk_level))
        focus_area = str(payload.get('focus_area', focus_area))

    if isinstance(score, (int, float)) and score < 50:
        base_priority = 'high'
    elif risk_level.lower() == 'high':
        base_priority = 'high'
    else:
        base_priority = 'medium'

    recommendations = [
        {
            'id': '1',
            'title': 'Review ESG policies quarterly',
            'category': 'Governance',
            'priority': base_priority,
            'impact': 10,
            'effort': 'medium',
            'timeline': '3 months',
            'currentScore': 74,
            'targetScore': 86,
            'description': 'Align policy reviews with reporting cycles and governance checks.',
            'actions': [
                'Assign an owner for quarterly policy review',
                'Track action items in the ESG dashboard',
                'Close the loop with executive reporting',
            ],
            'status': 'in-progress',
        },
        {
            'id': '2',
            'title': 'Automate carbon data collection',
            'category': 'Environmental',
            'priority': 'high',
            'impact': 12,
            'effort': 'high',
            'timeline': '6 months',
            'currentScore': 76,
            'targetScore': 90,
            'description': 'Reduce manual entry and improve traceability across Scope 1, 2, and 3.',
            'actions': [
                'Connect utility and logistics sources to a single pipeline',
                'Validate emissions data at ingestion',
                'Create audit logs for compliance review',
            ],
            'status': 'not-started',
        },
        {
            'id': '3',
            'title': 'Prepare stakeholder summary packs',
            'category': 'Social',
            'priority': 'medium',
            'impact': 8,
            'effort': 'low',
            'timeline': '2 months',
            'currentScore': 78,
            'targetScore': 88,
            'description': 'Package the most important ESG outcomes for leadership and investors.',
            'actions': [
                'Summarize top risks and mitigations',
                'Highlight KPIs that moved this quarter',
                'Reuse the same narrative across reporting channels',
            ],
            'status': 'not-started',
        },
    ][: max(1, top_k)]

    if focus_area.lower() != 'overall':
        recommendations[0]['description'] = f'Prioritize {focus_area} actions in the next reporting cycle.'

    return recommendations, ['ESG playbook', 'Reporting guidelines', 'RAG fallback context']
