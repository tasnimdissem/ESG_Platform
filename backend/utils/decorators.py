from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from backend.models.user import User
from backend.extensions import db

def require_role(role: str):
    """
    Decorator to protect routes based on user role.
    Requires a valid JWT token in the request.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # FIXED: Vérification des rôles sur les routes sensibles
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            try:
                user = db.session.get(User, int(user_id))
                if not user or user.role != role:
                    return jsonify({"error": f"Forbidden: Requires {role} role"}), 403
            except (TypeError, ValueError):
                return jsonify({"error": "Invalid token identity"}), 401
                
            return fn(*args, **kwargs)
        return wrapper
    return decorator
