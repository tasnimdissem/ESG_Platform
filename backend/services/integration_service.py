from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import requests
from flask import current_app

from services.local_rag_service import generate_local_chat_answer, generate_local_recommendations


def _safe_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {'true', '1', 'yes', 'y'}:
            return True
        if lowered in {'false', '0', 'no', 'n'}:
            return False
    return default


def _safe_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
        return max(0.0, min(parsed, 1.0))
    except (TypeError, ValueError):
        return default


def _normalize_request_payload(payload: dict[str, Any]) -> dict[str, Any]:
    message = str(payload.get('message', '')).strip()
    if not message:
        raise ValueError('Missing mandatory field: message')

    normalized: dict[str, Any] = {
        'client_request_id': str(payload.get('client_request_id', '')).strip() or None,
        'message': message,
        'top_k': _safe_int(payload.get('top_k', current_app.config.get('RAG_TOP_K', 3)), 3),
        'include_recommendations': _safe_bool(payload.get('include_recommendations', False), False),
        'signals': payload.get('signals', {}) if isinstance(payload.get('signals'), dict) else {},
        'filters': payload.get('filters', {}) if isinstance(payload.get('filters'), dict) else {},
    }
    return normalized


def _integration_endpoint_url() -> str:
    explicit_url = str(current_app.config.get('RAG_API_URL', '')).strip()
    if explicit_url:
        return explicit_url

    base_url = str(current_app.config.get('RAG_API_BASE_URL', 'http://localhost:8000')).strip().rstrip('/') + '/'
    path = str(current_app.config.get('RAG_INTEGRATION_PATH', '/api/v1/integration')).strip()
    if not path.startswith('/'):
        path = '/' + path
    return urljoin(base_url, path.lstrip('/'))


def _build_remote_headers() -> dict[str, str]:
    headers = {'Content-Type': 'application/json'}
    token = str(current_app.config.get('RAG_API_TOKEN', '')).strip()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers


def _build_local_sources(labels: list[str]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for index, label in enumerate(labels, start=1):
        cleaned_label = str(label).strip() or f'Source {index}'
        sources.append(
            {
                'rank': index,
                'source_type': 'local-fallback',
                'source_name': cleaned_label,
                'chunk_id': f'local-{index}',
                'text': '',
                'distance': 0.0,
                'confidence': 1.0,
            }
        )
    return sources


def _build_local_integration_response(normalized_request: dict[str, Any]) -> dict[str, Any]:
    message = str(normalized_request.get('message', '')).strip()
    top_k = _safe_int(normalized_request.get('top_k', 3), 3)
    include_recommendations = _safe_bool(normalized_request.get('include_recommendations', False), False)
    signals = normalized_request.get('signals', {}) if isinstance(normalized_request.get('signals'), dict) else {}
    filters = normalized_request.get('filters', {}) if isinstance(normalized_request.get('filters'), dict) else {}

    answer, answer_sources = generate_local_chat_answer(message, top_k=top_k)
    recommendations: list[dict[str, Any]] = []
    recommendation_sources: list[str] = []

    if include_recommendations:
        fallback_payload = {
            'score': signals.get('esg_score'),
            'risk_level': signals.get('risk_level', filters.get('risk_level', 'Medium')),
            'focus_area': signals.get('focus_area', filters.get('focus_area', 'overall')),
        }
        recommendations, recommendation_sources = generate_local_recommendations(fallback_payload, top_k=top_k)

    combined_sources = _build_local_sources(answer_sources + recommendation_sources)

    return {
        'request': {
            'request_id': str(normalized_request.get('client_request_id') or ''),
            'question': message,
            'top_k': top_k,
            'include_recommendations': include_recommendations,
            'signals': signals,
            'filters': filters,
        },
        'response': {
            'answer': answer,
            'recommendations': recommendations,
            'sources': combined_sources,
            'confidence': 0.5,
        },
        'meta': {
            'service': 'rag-esg-local',
            'version': 'fallback',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        },
    }


def _normalize_source_for_contract(source: Any, index: int) -> dict[str, Any]:
    if isinstance(source, dict):
        distance = float(source.get('distance', 0.0) or 0.0)
        confidence = source.get('confidence')
        normalized_confidence = _safe_float(confidence, 1.0 / (1.0 + max(distance, 0.0)))
        return {
            'rank': int(source.get('rank', index) or index),
            'source_type': str(source.get('source_type', 'unknown')),
            'source_name': str(source.get('source_name', source.get('source', 'unknown'))),
            'chunk_id': str(source.get('chunk_id', source.get('id', f'chunk-{index}'))),
            'text': str(source.get('text', source.get('snippet', ''))),
            'distance': distance,
            'confidence': normalized_confidence,
        }

    if isinstance(source, str):
        return {
            'rank': index,
            'source_type': 'unknown',
            'source_name': source.strip() or f'source-{index}',
            'chunk_id': f'chunk-{index}',
            'text': '',
            'distance': 0.0,
            'confidence': 1.0,
        }

    return {
        'rank': index,
        'source_type': 'unknown',
        'source_name': f'source-{index}',
        'chunk_id': f'chunk-{index}',
        'text': '',
        'distance': 0.0,
        'confidence': 1.0,
    }


def _normalize_sources_for_contract(raw_sources: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_sources, list):
        return []

    normalized: list[dict[str, Any]] = []
    for idx, source in enumerate(raw_sources, start=1):
        normalized.append(_normalize_source_for_contract(source, idx))
    return normalized


def _call_remote_integration(normalized_request: dict[str, Any]) -> dict[str, Any]:
    endpoint = _integration_endpoint_url()
    timeout_seconds = _safe_int(current_app.config.get('RAG_TIMEOUT_SECONDS', 60), 60)
    headers = _build_remote_headers()

    payload = {
        'client_request_id': normalized_request.get('client_request_id') or '',
        'message': normalized_request.get('message', ''),
        'top_k': normalized_request.get('top_k', 3),
        'include_recommendations': normalized_request.get('include_recommendations', False),
        'signals': normalized_request.get('signals', {}),
        'filters': normalized_request.get('filters', {}),
    }

    response = requests.post(endpoint, json=payload, headers=headers, timeout=timeout_seconds)
    if response.status_code == 401:
        raise PermissionError('Unauthorized (invalid/missing bearer token when auth is enabled)')
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError('RAG integration returned invalid JSON payload')

    request_block = data.get('request', {}) if isinstance(data.get('request'), dict) else {}
    response_block = data.get('response', {}) if isinstance(data.get('response'), dict) else {}
    meta_block = data.get('meta', {}) if isinstance(data.get('meta'), dict) else {}

    request_id = request_block.get('request_id') or request_block.get('client_request_id') or normalized_request.get('client_request_id') or ''
    question = request_block.get('question') or request_block.get('message') or normalized_request.get('message', '')
    top_k = _safe_int(request_block.get('top_k', normalized_request.get('top_k', 3)), normalized_request.get('top_k', 3))
    include_recommendations = _safe_bool(
        request_block.get('include_recommendations', normalized_request.get('include_recommendations', False)),
        bool(normalized_request.get('include_recommendations', False)),
    )

    normalized_sources = _normalize_sources_for_contract(response_block.get('sources', []))
    confidence = _safe_float(response_block.get('confidence', 0.0), 0.0)

    return {
        'request': {
            'request_id': str(request_id),
            'question': str(question),
            'top_k': top_k,
            'include_recommendations': include_recommendations,
            'signals': normalized_request.get('signals', {}),
            'filters': normalized_request.get('filters', {}),
        },
        'response': {
            'answer': str(response_block.get('answer', '')).strip(),
            'recommendations': response_block.get('recommendations', []) if isinstance(response_block.get('recommendations'), list) else [],
            'sources': normalized_sources,
            'confidence': confidence,
        },
        'meta': {
            'service': str(meta_block.get('service', 'rag-esg')),
            'version': str(meta_block.get('version', 'v1')),
            'timestamp': str(meta_block.get('timestamp', datetime.now(timezone.utc).isoformat())),
        },
    }


def build_integration_response(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_request = _normalize_request_payload(payload)
    allow_local_fallback = _safe_bool(current_app.config.get('RAG_ALLOW_LOCAL_FALLBACK', True), True)

    try:
        return _call_remote_integration(normalized_request)
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        if not allow_local_fallback:
            raise RuntimeError(f'Remote RAG integration failed and local fallback is disabled: {exc}') from exc

        current_app.logger.warning('Remote RAG integration unavailable, using local fallback: %s', exc)
        return _build_local_integration_response(normalized_request)