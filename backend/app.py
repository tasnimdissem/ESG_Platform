from __future__ import annotations

import logging
import os
import time
import traceback

from flask import Flask, jsonify
from flask_limiter.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from backend.config import Config
from backend.extensions import bcrypt, db, jwt, limiter
from backend.routes.api import api_bp
from backend.routes.companies import companies_bp
from backend.routes.analytics import analytics_bp
from backend.routes.auth import auth_bp
from backend.routes.prediction import prediction_bp
from backend.routes.admin import admin_bp
from backend.routes.voice import voice_bp
from flask_cors import CORS  # FIXED: Importer CORS

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
                # Demo user seeding removed; PostgreSQL environment should handle user creation via migrations or admin tools
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
    app.run(host='0.0.0.0', port=5050, debug=is_dev)
