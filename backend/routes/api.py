from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from backend.services.esg_service import compute_esg_score, get_recommendations, validate_predict_payload
from backend.services.integration_service import build_integration_response
from backend.services.news_service import fetch_esg_news
from backend.services.conversation_service import add_turn, build_history_block


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
        return jsonify({'error': 'Non autorisé'}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'error': 'Charge utile invalide ou champ obligatoire manquant'}), 400

    # Conversation history: prepend previous turns to the message when session_id is present
    session_id = str(payload.get('session_id') or '').strip() or None
    if session_id:
        history_block = build_history_block(session_id)
        if history_block:
            original_message = str(payload.get('message', '')).strip()
            payload = {**payload, 'message': f"{history_block}\n\n{original_message}"}

    try:
        result = build_integration_response(payload)
        # Store this turn in history so future requests have context
        if session_id:
            answer = result.get('response', {}).get('answer', '')
            question = str(payload.get('message', '')).split('\n\n')[-1].strip()
            if answer:
                add_turn(session_id, question, answer)
        return jsonify(result)
    except ValueError:
        return jsonify({'error': 'Charge utile invalide ou champ obligatoire manquant'}), 400
    except PermissionError:
        return jsonify({'error': "Non autorisé (jeton bearer invalide ou manquant lorsque l'authentification est activée)"}), 401
    except RuntimeError as exc:
        return jsonify({'error': str(exc)}), 502
    except Exception:
        current_app.logger.exception('Erreur d’intégration inattendue')
        return jsonify({'error': 'Erreur interne inattendue'}), 500




@api_bp.route('/recommend', methods=['POST'])
def recommend() -> object:
    payload = request.get_json(silent=True) or {}
    recommendations = get_recommendations(payload)
    return jsonify(
        {
            'status': 'success',
            **recommendations,
            'message': 'Recommandations renvoyées avec succès.',
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


@api_bp.route('/powerbi-url', methods=['GET'])
def powerbi_url() -> object:
    return jsonify({'url': current_app.config.get('POWER_BI_IFRAME_URL', '')})
