from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from backend.extensions import db
from backend.models.user import PasswordResetToken, User
from backend.services.email_service import send_password_reset_email


auth_bp = Blueprint('auth', __name__)


def _get_json_payload() -> tuple[dict | None, tuple[object, int] | None]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, (jsonify({'error': 'Invalid JSON payload'}), 400)
    return payload, None


@auth_bp.post('/register')
def register() -> object:
    payload, error = _get_json_payload()
    if error is not None:
        return error

    name = str(payload.get('name', '')).strip()
    email = str(payload.get('email', '')).strip().lower()
    password = str(payload.get('password', ''))
    role = str(payload.get('role', 'user')).strip() or 'user'

    if not name or not email or not password:
        return jsonify({'error': 'name, email and password are required'}), 400

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': 'Email already exists'}), 409

    user = User(name=name, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': access_token, 'user': user.to_dict()}), 201


@auth_bp.post('/login')
def login() -> object:
    payload, error = _get_json_payload()
    if error is not None:
        return error

    email = str(payload.get('email', '')).strip().lower()
    password = str(payload.get('password', ''))

    if not email or not password:
        return jsonify({'error': 'email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': access_token, 'user': user.to_dict()})


@auth_bp.get('/me')
@jwt_required()
def me() -> object:
    identity = get_jwt_identity()

    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token identity'}), 401

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user.to_dict()})


@auth_bp.post('/forgot-password')
def forgot_password() -> object:
    payload, error = _get_json_payload()
    if error is not None:
        return error

    email = str(payload.get('email', '')).strip().lower()
    if not email:
        return jsonify({'error': 'email is required'}), 400

    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({'message': 'If the account exists, a reset token has been generated.'})

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.session.add(reset_token)
    db.session.commit()

    email_sent = send_password_reset_email(user.email, raw_token)

    return jsonify(
        {
            'message': 'Password reset email sent.' if email_sent else 'Reset token generated for development use.',
            'reset_token': raw_token if not email_sent else None,
            'email_sent': email_sent,
        }
    )


@auth_bp.post('/reset-password')
def reset_password() -> object:
    payload, error = _get_json_payload()
    if error is not None:
        return error

    token = str(payload.get('token', '')).strip()
    new_password = str(payload.get('new_password', ''))

    if not token or not new_password:
        return jsonify({'error': 'token and new_password are required'}), 400

    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
    if reset_token is None:
        return jsonify({'error': 'Invalid or expired reset token'}), 400

    if reset_token.used_at is not None or reset_token.expires_at < datetime.utcnow():
        return jsonify({'error': 'Invalid or expired reset token'}), 400

    user = db.session.get(User, reset_token.user_id)
    if user is None:
        return jsonify({'error': 'User not found'}), 404

    user.set_password(new_password)
    reset_token.used_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Password reset successfully'})
