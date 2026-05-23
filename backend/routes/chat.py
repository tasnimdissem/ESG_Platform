from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.extensions import db
from backend.models.chat import ChatConversation, ChatMessage

chat_bp = Blueprint('chat', __name__)


def _current_user_id() -> int | None:
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


@chat_bp.get('/conversations')
@jwt_required(optional=True)
def list_conversations() -> object:
    user_id = _current_user_id()
    if user_id is None:
        return jsonify([])

    conversations = (
        ChatConversation.query.filter_by(user_id=user_id)
        .order_by(ChatConversation.created_at.desc())
        .all()
    )
    return jsonify([c.to_dict() for c in conversations])


@chat_bp.post('/conversations')
@jwt_required()
def create_conversation() -> object:
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({'error': 'Identité du jeton invalide'}), 401

    payload = request.get_json(silent=True) or {}
    title = str(payload.get('title', 'Nouvelle conversation'))[:255]
    session_id = str(payload.get('session_id', ''))[:64] or None

    conv = ChatConversation(user_id=user_id, title=title, session_id=session_id)
    db.session.add(conv)
    db.session.commit()
    return jsonify(conv.to_dict()), 201


@chat_bp.get('/conversations/<int:conv_id>')
@jwt_required()
def get_conversation(conv_id: int) -> object:
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({'error': 'Identité du jeton invalide'}), 401

    conv = ChatConversation.query.filter_by(id=conv_id, user_id=user_id).first_or_404()
    messages = [m.to_dict() for m in conv.messages]
    return jsonify({'conversation': conv.to_dict(), 'messages': messages})


@chat_bp.post('/conversations/<int:conv_id>/messages')
@jwt_required()
def add_message(conv_id: int) -> object:
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({'error': 'Identité du jeton invalide'}), 401

    conv = ChatConversation.query.filter_by(id=conv_id, user_id=user_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    sender = str(payload.get('sender', 'user'))
    if sender not in ('user', 'bot'):
        return jsonify({'error': 'sender doit être "user" ou "bot"'}), 400

    text = str(payload.get('text', '')).strip()
    if not text:
        return jsonify({'error': 'text est requis'}), 400

    sources = payload.get('sources', [])
    if not isinstance(sources, list):
        sources = []

    # Auto-title from first user message
    if sender == 'user' and conv.title == 'Nouvelle conversation':
        conv.title = text[:60] + ('…' if len(text) > 60 else '')

    msg = ChatMessage(conversation_id=conv_id, sender=sender, text=text, sources=sources)
    db.session.add(msg)
    db.session.commit()
    return jsonify(msg.to_dict()), 201


@chat_bp.delete('/conversations/<int:conv_id>')
@jwt_required()
def delete_conversation(conv_id: int) -> object:
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({'error': 'Identité du jeton invalide'}), 401

    conv = ChatConversation.query.filter_by(id=conv_id, user_id=user_id).first_or_404()
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'deleted': True})
