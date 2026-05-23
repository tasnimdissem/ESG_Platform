from __future__ import annotations

import hashlib
import logging
import secrets
import os
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from pydantic import ValidationError
from sqlalchemy import inspect, text

from backend.extensions import db, limiter
from backend.models.user import PasswordResetToken, User
from backend.services.avatar_service import delete_user_avatar, upload_user_avatar
from backend.services.email_service import send_password_reset_email
from backend.schemas import LoginRequest, RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest, UpdateProfileRequest

logger = logging.getLogger(__name__)



auth_bp = Blueprint('auth', __name__)


def ensure_user_schema() -> None:
    inspector = inspect(db.engine)
    if 'users' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('users')}
    statements: list[str] = []

    if 'avatar_url' not in columns:
        statements.append('ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512)')
    if 'avatar_s3_key' not in columns:
        statements.append('ALTER TABLE users ADD COLUMN avatar_s3_key VARCHAR(255)')

    for statement in statements:
        db.session.execute(text(statement))

    if statements:
        db.session.commit()


def _get_json_payload() -> tuple[dict | None, tuple[object, int] | None]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, (jsonify({'error': 'Charge utile JSON invalide'}), 400)
    return payload, None


@auth_bp.post('/register')
@limiter.limit("3 per minute")  # FIXED: Prevent registration spam (3 attempts per minute per IP)
def register() -> object:
    payload, error = _get_json_payload()
    if error is not None:
        return error

    # Validate input against Pydantic schema
    try:
        validated_data = RegisterRequest(**payload)
    except ValidationError as ve:
        logger.warning(f"Erreur de validation lors de l'inscription : {ve}")
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in ve.errors()]
        return jsonify({"error": "Données d'entrée invalides", "details": errors}), 400

    name = validated_data.name.strip()
    email = validated_data.email.strip().lower()
    password = validated_data.password
    # Security: never trust client-provided role during self-registration.
    role = 'user'

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': 'Cet e-mail existe déjà'}), 409

    user = User(name=name, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    
    # Return only user info; token is set in secure HttpOnly cookie
    response = jsonify({'message': 'Inscription réussie', 'user': user.to_dict()})
    set_access_cookies(response, access_token)
    return response, 201


@auth_bp.post('/login')
@limiter.limit("5 per minute")  # FIXED: Prevent brute-force attacks (5 attempts per minute per IP)
def login() -> object:
    try:
        # Ensure tables exist (in case DB became available after startup)
        try:
            db.create_all()
        except Exception:
            pass  # Log will happen at startup; don't fail the request
        
        payload, error = _get_json_payload()
        if error is not None:
            return error

        # Validate input against Pydantic schema
        try:
            validated_data = LoginRequest(**payload)
        except ValidationError as ve:
            logger.warning(f"Erreur de validation lors de la connexion : {ve}")
            errors = [{"field": err["loc"][0], "message": err["msg"]} for err in ve.errors()]
            return jsonify({"error": "Données d'entrée invalides", "details": errors}), 400

        email = validated_data.email.strip().lower()
        password = validated_data.password

        logger.info(f"Tentative de connexion pour l'e-mail : {email}")
        user = User.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            logger.warning(f"Connexion échouée : identifiants invalides pour {email}")
            return jsonify({'error': 'Identifiants invalides'}), 401

        access_token = create_access_token(identity=str(user.id))
        logger.info(f"Connexion réussie pour l'utilisateur : {user.id} ({email})")
        
        # Return only user info; token is set in secure HttpOnly cookie
        response = jsonify({'message': 'Connexion réussie', 'user': user.to_dict()})
        set_access_cookies(response, access_token)
        return response
    
    except Exception as e:
        logger.error(f"Exception lors de la connexion : {str(e)}", exc_info=True)
        raise


@auth_bp.get('/me')
@jwt_required(optional=True)
def me() -> object:
    identity = get_jwt_identity()
    if identity is None:
        return jsonify({'user': None})

    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Identité du jeton invalide'}), 401

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({'error': 'Utilisateur introuvable'}), 404

    return jsonify({'user': user.to_dict()})


@auth_bp.put('/me')
@jwt_required()
@limiter.limit('5 per minute')
def update_me() -> object:
    ensure_user_schema()

    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Identité du jeton invalide'}), 401

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({'error': 'Utilisateur introuvable'}), 404

    payload = request.form.to_dict()
    try:
        validated_data = UpdateProfileRequest(**payload)
    except ValidationError as ve:
        logger.warning(f"Erreur de validation lors de la mise à jour du profil : {ve}")
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in ve.errors()]
        return jsonify({"error": "Données d'entrée invalides", "details": errors}), 400

    current_password = validated_data.current_password
    new_password = validated_data.new_password
    if bool(current_password) ^ bool(new_password):
        return jsonify({'error': 'Veuillez fournir le mot de passe actuel et le nouveau mot de passe'}), 400

    if current_password and new_password and not user.check_password(current_password):
        return jsonify({'error': 'Mot de passe actuel invalide'}), 401

    name = validated_data.name.strip() if validated_data.name else user.name
    email = validated_data.email.strip().lower() if validated_data.email else user.email

    if email != user.email and User.query.filter(User.email == email, User.id != user.id).first() is not None:
        return jsonify({'error': 'Cet e-mail existe déjà'}), 409

    avatar_file = request.files.get('avatar')
    new_avatar_key = None
    new_avatar_url = None
    if avatar_file and avatar_file.filename:
        new_avatar_key, new_avatar_url = upload_user_avatar(user_id=user.id, upload=avatar_file)

    old_avatar_key = user.avatar_s3_key

    user.name = name
    user.email = email
    if new_password:
        user.set_password(new_password)
    if new_avatar_key and new_avatar_url:
        user.avatar_s3_key = new_avatar_key
        user.avatar_url = new_avatar_url

    db.session.commit()

    if new_avatar_key and old_avatar_key and old_avatar_key != new_avatar_key:
        delete_user_avatar(old_avatar_key)

    return jsonify({'message': 'Profil mis à jour avec succès', 'user': user.to_dict()})


@auth_bp.get('/logout')
def logout() -> object:
    """Clear the authentication cookie."""
    response = jsonify({'message': 'Déconnexion réussie'})
    unset_jwt_cookies(response)
    return response


@auth_bp.post('/forgot-password')
@limiter.limit("3 per hour")  # Prevent password reset spam
def forgot_password() -> object:
    try:
        db.create_all()
    except Exception:
        pass

    payload, error = _get_json_payload()
    if error is not None:
        return error

    # Validate input against Pydantic schema
    try:
        validated_data = ForgotPasswordRequest(**payload)
    except ValidationError as ve:
        logger.warning(f"Erreur de validation lors de la réinitialisation du mot de passe : {ve}")
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in ve.errors()]
        return jsonify({"error": "Données d'entrée invalides", "details": errors}), 400

    email = validated_data.email.strip().lower()

    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({'message': 'Si le compte existe, un e-mail de réinitialisation a été envoyé.', 'email_sent': False})

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    expiry_minutes = int(current_app.config.get('RESET_PASSWORD_TOKEN_EXPIRES_MINUTES', 15))
    if expiry_minutes <= 0:
        expiry_minutes = 15

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )
    db.session.add(reset_token)
    db.session.commit()

    try:
        email_sent = send_password_reset_email(user.email, raw_token, expiry_minutes=expiry_minutes)
    except Exception:
        logger.exception("Échec de l'envoi de l'e-mail de réinitialisation pour %s", email)
        email_sent = False

    # SECURITY: Never expose the raw token in the API response.
    # The token is only sent through email and stored hashed in the database.
    return jsonify(
        {
            'message': 'Si le compte existe, un e-mail de réinitialisation a été envoyé.',
            'email_sent': email_sent,
        }
    )


@auth_bp.post('/reset-password')
def reset_password() -> object:
    try:
        db.create_all()
    except Exception:
        pass

    payload, error = _get_json_payload()
    if error is not None:
        return error

    # Validate input against Pydantic schema
    try:
        validated_data = ResetPasswordRequest(**payload)
    except ValidationError as ve:
        logger.warning(f"Erreur de validation lors de la réinitialisation du mot de passe : {ve}")
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in ve.errors()]
        return jsonify({"error": "Données d'entrée invalides", "details": errors}), 400

    token = validated_data.token.strip()
    new_password = validated_data.new_password

    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
    if reset_token is None:
        return jsonify({'error': 'Jeton de réinitialisation invalide ou expiré'}), 400

    if reset_token.used_at is not None or reset_token.expires_at < datetime.utcnow():
        return jsonify({'error': 'Jeton de réinitialisation invalide ou expiré'}), 400

    user = db.session.get(User, reset_token.user_id)
    if user is None:
        return jsonify({'error': 'Utilisateur introuvable'}), 404

    user.set_password(new_password)
    reset_token.used_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Mot de passe réinitialisé avec succès'})


