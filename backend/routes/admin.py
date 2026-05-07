from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from backend.extensions import db
from backend.models.user import User

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

@admin_bp.get('/users')
@admin_required
def get_users():
    """Returns all users."""
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

@admin_bp.delete('/users/<int:user_id>')
@admin_required
def delete_user(user_id):
    """Deletes a user."""
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
    current_admin_id = get_jwt_identity()
    if int(current_admin_id) == user_id:
        return jsonify({'error': 'Vous ne pouvez pas modifier votre propre rôle.'}), 400
        
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Utilisateur introuvable.'}), 404
        
    data = request.get_json()
    new_role = data.get('role')
    if new_role not in ['user', 'admin']:
        return jsonify({'error': 'Rôle invalide.'}), 400
        
    user.role = new_role
    db.session.commit()
    return jsonify({'message': f'Rôle mis à jour vers {new_role}.', 'user': user.to_dict()}), 200
