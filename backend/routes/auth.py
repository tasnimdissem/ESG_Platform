from __future__ import annotations

import hashlib
import logging
import secrets
import os
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from pydantic import ValidationError

from backend.extensions import db, limiter
from backend.models.user import PasswordResetToken, User
from backend.services.email_service import send_password_reset_email
from backend.schemas import LoginRequest, RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest

logger = logging.getLogger(__name__)



auth_bp = Blueprint('auth', __name__)


def _get_json_payload() -> tuple[dict | None, tuple[object, int] | None]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, (jsonify({'error': 'Invalid JSON payload'}), 400)
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
        logger.warning(f"Validation error in register: {ve}")
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in ve.errors()]
        return jsonify({"error": "Invalid input data", "details": errors}), 400

    name = validated_data.name.strip()
    email = validated_data.email.strip().lower()
    password = validated_data.password
    # Security: never trust client-provided role during self-registration.
    role = 'user'

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': 'Email already exists'}), 409

    user = User(name=name, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    
    # Return only user info; token is set in secure HttpOnly cookie
    response = jsonify({'message': 'Registration successful', 'user': user.to_dict()})
    response.set_cookie(
        key=current_app.config.get('JWT_COOKIE_NAME', 'access_token_cookie'),
        value=access_token,
        httponly=True,
        secure=current_app.config.get('JWT_COOKIE_SECURE', False),
        samesite=current_app.config.get('JWT_COOKIE_SAMESITE', 'Strict'),
        max_age=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400),
    )
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
            logger.warning(f"Validation error in login: {ve}")
            errors = [{"field": err["loc"][0], "message": err["msg"]} for err in ve.errors()]
            return jsonify({"error": "Invalid input data", "details": errors}), 400

        email = validated_data.email.strip().lower()
        password = validated_data.password

        logger.info(f"Login attempt for email: {email}")
        user = User.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            logger.warning(f"Login failed: invalid credentials for email {email}")
            return jsonify({'error': 'Invalid credentials'}), 401

        access_token = create_access_token(identity=str(user.id))
        logger.info(f"Login successful for user: {user.id} ({email})")
        
        # Return only user info; token is set in secure HttpOnly cookie
        response = jsonify({'message': 'Login successful', 'user': user.to_dict()})
        response.set_cookie(
            key=current_app.config.get('JWT_COOKIE_NAME', 'access_token_cookie'),
            value=access_token,
            httponly=True,
            secure=current_app.config.get('JWT_COOKIE_SECURE', False),
            samesite=current_app.config.get('JWT_COOKIE_SAMESITE', 'Strict'),
            max_age=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400),
        )
        return response
    
    except Exception as e:
        logger.error(f"Login exception: {str(e)}", exc_info=True)
        raise


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


@auth_bp.get('/logout')
def logout() -> object:
    """Clear the authentication cookie."""
    response = jsonify({'message': 'Logout successful'})
    response.set_cookie(
        key=current_app.config.get('JWT_COOKIE_NAME', 'access_token_cookie'),
        value='',
        httponly=True,
        secure=current_app.config.get('JWT_COOKIE_SECURE', False),
        samesite=current_app.config.get('JWT_COOKIE_SAMESITE', 'Strict'),
        max_age=0,  # Delete cookie immediately
    )
    return response


@auth_bp.post('/forgot-password')
@limiter.limit("3 per hour")  # Prevent password reset spam
def forgot_password() -> object:
    payload, error = _get_json_payload()
    if error is not None:
        return error

    # Validate input against Pydantic schema
    try:
        validated_data = ForgotPasswordRequest(**payload)
    except ValidationError as ve:
        logger.warning(f"Validation error in forgot-password: {ve}")
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in ve.errors()]
        return jsonify({"error": "Invalid input data", "details": errors}), 400

    email = validated_data.email.strip().lower()

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

    # SECURITY: Only return reset_token in development mode (never expose secrets in production)
    # FIXED: Token en clair uniquement si FLASK_ENV=development
    is_dev = os.getenv('FLASK_ENV', 'development') == 'development'
    return_token = raw_token if (not email_sent and is_dev) else None

    return jsonify(
        {
            'message': 'Password reset email sent.' if email_sent else 'Reset token generated for development use.',
            'reset_token': return_token,
            'email_sent': email_sent,
        }
    )


@auth_bp.post('/reset-password')
def reset_password() -> object:
    payload, error = _get_json_payload()
    if error is not None:
        return error

    # Validate input against Pydantic schema
    try:
        validated_data = ResetPasswordRequest(**payload)
    except ValidationError as ve:
        logger.warning(f"Validation error in reset-password: {ve}")
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in ve.errors()]
        return jsonify({"error": "Invalid input data", "details": errors}), 400

    token = validated_data.token.strip()
    new_password = validated_data.new_password

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
