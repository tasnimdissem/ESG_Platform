from __future__ import annotations

from typing import Any


def _fallback_chat_response(message: str) -> str:
    normalized = (message or '').strip().lower()

    if not normalized:
        return 'Veuillez saisir une question sur l’ESG, le reporting ou le tableau de bord.'

    if 'esg' in normalized and any(keyword in normalized for keyword in ['meaning', 'definition', 'what is', 'quoi', 'signifie']):
        return 'ESG signifie Environmental, Social et Governance. C’est un cadre utilisé pour évaluer la durabilité et les pratiques responsables des entreprises.'

    if any(keyword in normalized for keyword in ['hello', 'hi', 'hey']):
        return 'Bonjour. Je peux vous aider sur les KPI ESG, les rapports et la navigation du tableau de bord.'

    if 'report' in normalized:
        return 'Utilisez l’action d’export de rapport pour générer un résumé PDF de l’état ESG actuel.'

    if 'power bi' in normalized or 'powerbi' in normalized:
        return 'Le tableau de bord inclut une zone iframe réservée à votre lien Power BI.'

    if 'predict' in normalized or 'recommend' in normalized:
        return 'Les routes ML sont prêtes pour une future intégration de modèle et renvoient actuellement des réponses factices structurées.'

    if 'dashboard' in normalized:
        return 'Ouvrez le tableau de bord pour voir les KPI ESG, le niveau de risque et l’intégration Power BI.'

    return 'Je suis un assistant ESG local. Posez-moi des questions sur la signification de l’ESG, les tableaux de bord, les rapports, les recommandations ou l’authentification.'


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
