from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from backend.services.esg_service import compute_esg_score, get_recommendations, validate_predict_payload
from backend.services.integration_service import build_integration_response
from backend.services.news_service import fetch_esg_news


api_bp = Blueprint('api', __name__)


def _auth_enabled() -> bool:
    return bool(current_app.config.get('INTEGRATION_AUTH_ENABLED', False))


def _is_authorized() -> bool:
    expected_token = str(current_app.config.get('INTEGRATION_BEARER_TOKEN', '')).strip()
    if not expected_token:
        return False

    authorization = request.headers.get('Authorization', '')
    if not authorization.startswith('Bearer '):
        return False

    provided_token = authorization.removeprefix('Bearer ').strip()
    return provided_token == expected_token


@api_bp.route('/v1/integration', methods=['POST'])
def integration() -> object:
    if _auth_enabled() and not _is_authorized():
        return jsonify({'error': 'Unauthorized'}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'error': 'Bad request payload or missing mandatory field'}), 400

    try:
        result = build_integration_response(payload)
        return jsonify(result)
    except ValueError:
        return jsonify({'error': 'Bad request payload or missing mandatory field'}), 400
    except PermissionError:
        return jsonify({'error': 'Unauthorized (invalid/missing bearer token when auth is enabled)'}), 401
    except RuntimeError as exc:
        return jsonify({'error': str(exc)}), 502
    except Exception:
        current_app.logger.exception('Unexpected integration error')
        return jsonify({'error': 'Unexpected internal error'}), 500




@api_bp.route('/recommend', methods=['POST'])
def recommend() -> object:
    payload = request.get_json(silent=True) or {}
    recommendations = get_recommendations(payload)
    return jsonify(
        {
            'status': 'success',
            **recommendations,
            'message': 'Recommendations returned successfully.',
        }
    )


@api_bp.route('/news', methods=['GET'])
def news() -> object:
    raw_limit = request.args.get('limit', '8')
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        limit = 8

    items = fetch_esg_news(limit=limit)
    return jsonify(
        {
            'status': 'success',
            'items': items,
            'count': len(items),
        }
    )
