import hashlib
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from backend.extensions import db
from backend.models.user import EmailVerificationToken, User
from backend.routes.auth import ensure_user_schema
from backend.services.email_service import send_account_activation_email

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

def admin_required(fn):
    """Decorator to require admin role."""
    from functools import wraps
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Accès refusé. Réservé aux administrateurs.'}), 403
        return fn(*args, **kwargs)
    return wrapper


def _issue_activation_email(user: User) -> bool:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.session.add(verification_token)
    db.session.commit()
    return send_account_activation_email(user.email, user.name, raw_token)

@admin_bp.get('/users')
@admin_required
def get_users():
    """Returns all users."""
    ensure_user_schema()
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

@admin_bp.delete('/users/<int:user_id>')
@admin_required
def delete_user(user_id):
    """Deletes a user."""
    ensure_user_schema()
    current_admin_id = get_jwt_identity()
    if int(current_admin_id) == user_id:
        return jsonify({'error': 'Vous ne pouvez pas supprimer votre propre compte.'}), 400
        
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Utilisateur introuvable.'}), 404
        
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Utilisateur supprimé avec succès.'}), 200

@admin_bp.put('/users/<int:user_id>/role')
@admin_required
def update_user_role(user_id):
    """Updates user role (user/admin)."""
    ensure_user_schema()
    current_admin_id = get_jwt_identity()
    if int(current_admin_id) == user_id:
        return jsonify({'error': 'Vous ne pouvez pas modifier votre propre rôle.'}), 400
        
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Utilisateur introuvable.'}), 404
        
    data = request.get_json()
    new_role = data.get('role')
    if new_role not in ['user', 'metier', 'decideur', 'admin']:
        return jsonify({'error': 'Rôle invalide.'}), 400
        
    user.role = new_role
    db.session.commit()
    return jsonify({'message': f'Rôle mis à jour vers {new_role}.', 'user': user.to_dict()}), 200


@admin_bp.put('/users/<int:user_id>/approve')
@admin_required
def approve_user(user_id):
    """Approuve un utilisateur et lui envoie l'e-mail d'activation."""
    ensure_user_schema()

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Utilisateur introuvable.'}), 404

    if user.is_blocked:
        return jsonify({'error': 'Impossible d’approuver un compte bloqué.'}), 400

    if user.is_approved and user.is_verified:
        return jsonify({'message': 'Le compte est déjà approuvé et activé.', 'user': user.to_dict()}), 200

    user.is_approved = True
    email_sent = False

    smtp_configured = bool(current_app.config.get('SMTP_HOST'))
    if smtp_configured:
        user.is_verified = False
        db.session.commit()
        try:
            email_sent = _issue_activation_email(user)
        except Exception:
            db.session.rollback()
            user.is_approved = True
            db.session.commit()
            current_app.logger.exception('Échec de l’envoi de l’e-mail d’activation pour %s', user.email)
            return jsonify({
                'message': 'Compte approuvé, mais l’e-mail d’activation n’a pas pu être envoyé.',
                'email_sent': False,
                'user': user.to_dict(),
            }), 500
    else:
        user.is_verified = True
        db.session.commit()

    return jsonify({
        'message': 'Compte approuvé avec succès.',
        'email_sent': email_sent,
        'user': user.to_dict(),
    }), 200


@admin_bp.put('/users/<int:user_id>/block')
@admin_required
def toggle_block_user(user_id):
    """Bloque ou débloque un utilisateur."""
    current_admin_id = get_jwt_identity()
    if int(current_admin_id) == user_id:
        return jsonify({'error': 'Vous ne pouvez pas bloquer votre propre compte.'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Utilisateur introuvable.'}), 404

    user.is_blocked = not user.is_blocked
    db.session.commit()

    action = 'bloqué' if user.is_blocked else 'débloqué'
    return jsonify({'message': f'Utilisateur {action} avec succès.', 'user': user.to_dict()}), 200
