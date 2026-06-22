from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from backend.models.user import User
from backend.extensions import db


def require_role(role: str):
    """Protect a route for a single exact role."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            try:
                user = db.session.get(User, int(user_id))
                if not user or user.role != role:
                    return jsonify({"error": f"Accès refusé. Rôle requis : {role}"}), 403
            except (TypeError, ValueError):
                return jsonify({"error": "Identité du jeton invalide"}), 401
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_roles(*roles: str):
    """Protect a route for any of the listed roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            try:
                user = db.session.get(User, int(user_id))
                if not user or user.role not in roles:
                    return jsonify({"error": "Accès refusé. Permissions insuffisantes."}), 403
            except (TypeError, ValueError):
                return jsonify({"error": "Identité du jeton invalide"}), 401
            return fn(*args, **kwargs)
        return wrapper
    return decorator
