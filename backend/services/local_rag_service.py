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
        'Vue d\'ensemble du tableau de bord ESG',
        'Flux de reporting',
        'Guide des recommandations',
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
            'title': 'Réviser les politiques ESG chaque trimestre',
            'category': 'Governance',
            'priority': base_priority,
            'impact': 10,
            'effort': 'medium',
            'timeline': '3 mois',
            'currentScore': 74,
            'targetScore': 86,
            'description': 'Aligner les révisions de politiques avec les cycles de reporting et les contrôles de gouvernance.',
            'actions': [
                'Désigner un responsable de la révision trimestrielle des politiques',
                'Suivre les actions dans le tableau de bord ESG',
                'Boucler le cycle avec le reporting exécutif',
            ],
            'status': 'in-progress',
        },
        {
            'id': '2',
            'title': 'Automatiser la collecte des données carbone',
            'category': 'Environmental',
            'priority': 'high',
            'impact': 12,
            'effort': 'high',
            'timeline': '6 mois',
            'currentScore': 76,
            'targetScore': 90,
            'description': 'Réduire la saisie manuelle et améliorer la traçabilité sur les Scopes 1, 2 et 3.',
            'actions': [
                'Connecter les sources d\'énergie et de logistique à un pipeline centralisé',
                'Valider les données d\'émissions à l\'ingestion',
                'Créer des journaux d\'audit pour la conformité réglementaire',
            ],
            'status': 'not-started',
        },
        {
            'id': '3',
            'title': 'Préparer des synthèses ESG pour les parties prenantes',
            'category': 'Social',
            'priority': 'medium',
            'impact': 8,
            'effort': 'low',
            'timeline': '2 mois',
            'currentScore': 78,
            'targetScore': 88,
            'description': 'Regrouper les résultats ESG les plus importants pour la direction et les investisseurs.',
            'actions': [
                'Résumer les principaux risques et mesures d\'atténuation',
                'Mettre en avant les KPI ayant évolué ce trimestre',
                'Réutiliser le même message sur tous les canaux de reporting',
            ],
            'status': 'not-started',
        },
    ][: max(1, top_k)]

    if focus_area.lower() != 'overall':
        recommendations[0]['description'] = f'Prioriser les actions {focus_area} lors du prochain cycle de reporting.'

    return recommendations, ['Guide ESG', 'Directives de reporting', 'Contexte RAG local']
