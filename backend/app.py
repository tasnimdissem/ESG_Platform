from __future__ import annotations

import logging
import os
import time
import traceback

from flask import Flask, jsonify
from flask_limiter.errors import RateLimitExceeded
from flask_jwt_extended.exceptions import JWTExtendedException, NoAuthorizationError
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from werkzeug.exceptions import HTTPException

from backend.config import Config
from backend.extensions import bcrypt, db, jwt, limiter
from backend.routes.api import api_bp
from backend.routes.companies import companies_bp
from backend.routes.analytics import analytics_bp
from backend.routes.auth import auth_bp
from backend.routes.prediction import prediction_bp
from backend.routes.admin import admin_bp
from backend.routes.voice import voice_bp
from backend.routes.chat import chat_bp
from flask_cors import CORS  # FIXED: Importer CORS

try:
    from flask_migrate import Migrate
except ModuleNotFoundError:
    Migrate = None

# Configure logging for debugging errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith('postgres://'):
        return database_url.replace('postgres://', 'postgresql://', 1)
    return database_url


# SQLite helper removed; PostgreSQL is required


# Demo user seeding removed; manage users via PostgreSQL migrations or admin tools


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config.get('SECRET_KEY'))

    db.init_app(app)
    if Migrate is not None:
        Migrate(app, db)
    else:
        logging.getLogger(__name__).warning('Flask-Migrate is not installed; starting without migration integration')
    bcrypt.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    
    # Security: do not allow wildcard origins when credentials are enabled.
    allowed_origins = [origin.strip() for origin in os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(',') if origin.strip()]
    allowed_origins = [origin for origin in allowed_origins if origin != '*']
    if not allowed_origins:
        allowed_origins = ['http://localhost:5173']
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(companies_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(prediction_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(voice_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    @app.get('/api/health')
    def health() -> object:
        return jsonify({'status': 'ok'})

    @app.get('/')
    def root() -> object:
        return jsonify({'name': 'ESG Platform API', 'status': 'ok'})

    with app.app_context():
        from backend.models.user import PasswordResetToken, User  # noqa: F401
        from backend.models.prediction import PredictionHistory  # noqa: F401
        from backend.models.company import Company  # noqa: F401
        from backend.models.chat import ChatConversation, ChatMessage  # noqa: F401
        from backend.routes.companies import ensure_company_schema
        from backend.routes.auth import ensure_user_schema

        # Create the local schema automatically, but don't crash if DB is unavailable.
        # Retry a few times to tolerate the DB still initializing (useful in Docker)
        logger = logging.getLogger(__name__)
        for attempt in range(5):
            try:
                db.create_all()
                ensure_company_schema()
                ensure_user_schema()
                logger.info('Database schema initialized successfully')
                # Seed initial admin user from ADMIN_EMAIL / ADMIN_PASSWORD env vars
                admin_email = os.getenv('ADMIN_EMAIL', '').strip().lower()
                admin_password = os.getenv('ADMIN_PASSWORD', '').strip()
                admin_name = os.getenv('ADMIN_NAME', 'Administrateur').strip()
                if admin_email and admin_password:
                    existing = User.query.filter_by(email=admin_email).first()
                    if existing is None:
                        admin_user = User(
                            name=admin_name,
                            email=admin_email,
                            role='admin',
                            is_approved=True,
                            is_verified=True,
                        )
                        admin_user.set_password(admin_password)
                        db.session.add(admin_user)
                        db.session.commit()
                        logger.info(f'Admin user created: {admin_email}')
                    else:
                        existing.is_approved = True
                        existing.is_verified = True
                        existing.role = 'admin'
                        existing.set_password(admin_password)
                        db.session.commit()
                        logger.info(f'Existing user promoted to admin: {admin_email}')
                break
            except OperationalError as oe:
                logger.warning(f'Database not ready (attempt {attempt+1}/5): {oe}')
                time.sleep(2)
            except Exception as e:
                logger.warning(f'Could not initialize database schema on startup: {str(e)}. Will retry on first request.')
                break

    # Global error handlers for debugging
    logger = logging.getLogger(__name__)

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error: SQLAlchemyError) -> tuple:
        """Catch database errors and log them for debugging."""
        logger.error(f"Database error: {str(error)}\n{traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'error': 'Erreur de connexion à la base de données. Veuillez réessayer.'}), 500

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_error(error: RateLimitExceeded) -> tuple:
        """Return a proper 429 response for rate-limited requests."""
        logger.warning(f"Rate limit exceeded: {str(error)}")
        return jsonify({'error': 'Trop de requêtes. Veuillez réessayer plus tard.'}), 429

    @app.errorhandler(JWTExtendedException)
    def handle_jwt_error(error: JWTExtendedException) -> tuple:
        """Return 401 for ALL JWT errors: missing token, expired, malformed, wrong type."""
        logger.warning(f"JWT error ({type(error).__name__}): {str(error)}")
        return jsonify({'error': 'Session expirée ou invalide. Veuillez vous reconnecter.'}), 401

    # Flask-JWT-Extended calls abort() internally rather than raising JWTExtendedException,
    # so the errorhandler above is never reached. These callbacks intercept at the right level.
    @jwt.unauthorized_loader
    def missing_token_callback(reason: str) -> tuple:
        logger.warning(f"JWT missing token: {reason}")
        return jsonify({'error': 'Session expirée ou invalide. Veuillez vous reconnecter.'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason: str) -> tuple:
        logger.warning(f"JWT invalid token: {reason}")
        return jsonify({'error': 'Session expirée ou invalide. Veuillez vous reconnecter.'}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header: dict, jwt_payload: dict) -> tuple:
        logger.warning(f"JWT expired for sub={jwt_payload.get('sub')}")
        return jsonify({'error': 'Session expirée. Veuillez vous reconnecter.'}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header: dict, jwt_payload: dict) -> tuple:
        logger.warning(f"JWT revoked for sub={jwt_payload.get('sub')}")
        return jsonify({'error': 'Session révoquée. Veuillez vous reconnecter.'}), 401

    @jwt.needs_fresh_token_loader
    def fresh_token_required_callback(jwt_header: dict, jwt_payload: dict) -> tuple:
        return jsonify({'error': 'Authentification fraîche requise.'}), 401

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> tuple:
        """Preserve Flask/HTTP errors instead of converting them to 500s."""
        logger.warning(f"HTTP error: {error.code} {error.description}")
        return jsonify({'error': error.description}), error.code

    @app.errorhandler(Exception)
    def handle_generic_error(error: Exception) -> tuple:
        """Catch all unhandled exceptions and log them for debugging."""
        logger.error(f"Unhandled exception: {str(error)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Erreur interne du serveur. Consultez les journaux pour plus de détails.'}), 500

    return app


app = create_app()


if __name__ == '__main__':
    # FIXED: debug actif uniquement en développement
    is_dev = os.getenv('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=5001, debug=is_dev)
