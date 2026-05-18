from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

# Load backend configuration from .env files when present.
load_dotenv(ROOT_DIR / '.env')
load_dotenv(BACKEND_DIR / '.env')


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith('postgres://'):
        return database_url.replace('postgres://', 'postgresql://', 1)
    return database_url


def _first_non_empty_env(*names: str, default: str = '') -> str:
    for name in names:
        value = os.getenv(name, '').strip()
        if value:
            return value
    return default


def _validate_required_secrets(is_production: bool) -> None:
    """Validate that production secrets are properly configured."""
    if not is_production:
        return
    
    secret_key = os.getenv('SECRET_KEY', '').strip()
    if not secret_key or secret_key == 'dev-secret-key-change-me':
        raise ValueError(
            "CRITICAL: SECRET_KEY is not configured or uses default value in production. "
            "Set a strong SECRET_KEY in your .env file."
        )
    
    # Validate JWT is not empty in production
    if len(secret_key) < 32:
        raise ValueError(
            "CRITICAL: SECRET_KEY is too weak (<32 chars). Use a strong, randomly-generated secret."
        )


class Config:
    # Auto-detect environment
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    IS_PRODUCTION = FLASK_ENV in ('production', 'prod')
    
    # Get SECRET_KEY - required for JWT, CSRF, session protection
    _secret_key = os.getenv('SECRET_KEY', '').strip()
    if IS_PRODUCTION and not _secret_key:
        raise ValueError(
            "CRITICAL: SECRET_KEY must be set in production. "
            "Generate a strong key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    SECRET_KEY = _secret_key or 'dev-insecure-key-only-for-dev'
    
    # Validate secrets
    _validate_required_secrets(IS_PRODUCTION)
    # Database configuration: Prefer DATABASE_URL if provided; otherwise fall back to SQLite for local dev.
    _db_url = os.getenv('DATABASE_URL')
    if _db_url:
        SQLALCHEMY_DATABASE_URI = _normalize_database_url(_db_url)
    else:
        # No DATABASE_URL set – use SQLite for quick local development.
        SQLALCHEMY_DATABASE_URI = 'sqlite:///esg_pfe.db'
        logging.getLogger(__name__).warning('DATABASE_URL not set; using SQLite fallback for development')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration - Secure token handling
    JWT_SECRET_KEY = SECRET_KEY  # Use the validated SECRET_KEY for JWT
    JWT_ALGORITHM = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours in seconds
    
    # Cookie Configuration - HttpOnly; Secure; SameSite
    JWT_TOKEN_LOCATION = ['cookies']  # Only use cookies, not headers
    JWT_COOKIE_SECURE = IS_PRODUCTION  # HTTPS only in production
    JWT_COOKIE_HTTPONLY = True  # Cannot be accessed by JavaScript
    JWT_COOKIE_SAMESITE = 'Strict'  # Prevent CSRF
    JWT_COOKIE_NAME = 'access_token_cookie'
    JWT_COOKIE_CSRF_PROTECT = IS_PRODUCTION  # Enable CSRF protection in prod
    RAG_API_BASE_URL = os.getenv('RAG_API_BASE_URL', 'http://localhost:8000')
    RAG_INTEGRATION_PATH = os.getenv('RAG_INTEGRATION_PATH', '/api/v1/query')
    RAG_API_URL = os.getenv('RAG_API_URL', '')
    RAG_API_TOKEN = os.getenv('RAG_API_TOKEN', '')
    RAG_TOP_K = int(os.getenv('RAG_TOP_K', '3'))
    RAG_TIMEOUT_SECONDS = int(os.getenv('RAG_TIMEOUT_SECONDS', '90'))
    RAG_ALLOW_LOCAL_FALLBACK = os.getenv('RAG_ALLOW_LOCAL_FALLBACK', 'true').lower() in {'1', 'true', 'yes'}
    INTEGRATION_AUTH_ENABLED = os.getenv('INTEGRATION_AUTH_ENABLED', 'false').lower() in {'1', 'true', 'yes'}
    INTEGRATION_BEARER_TOKEN = os.getenv('INTEGRATION_BEARER_TOKEN', '')
    SMTP_HOST = _first_non_empty_env('SMTP_HOST', 'MAIL_SERVER')
    SMTP_PORT = int(_first_non_empty_env('SMTP_PORT', 'MAIL_PORT', default='587'))
    SMTP_USERNAME = _first_non_empty_env('SMTP_USERNAME', 'MAIL_USERNAME')
    SMTP_PASSWORD = _first_non_empty_env('SMTP_PASSWORD', 'MAIL_PASSWORD')
    SMTP_USE_TLS = _first_non_empty_env('SMTP_USE_TLS', 'MAIL_USE_TLS', default='true').lower() in {'1', 'true', 'yes'}
    SMTP_USE_SSL = _first_non_empty_env('SMTP_USE_SSL', 'MAIL_USE_SSL', default='false').lower() in {'1', 'true', 'yes'}
    MAIL_SERVER = SMTP_HOST
    MAIL_PORT = SMTP_PORT
    MAIL_USERNAME = SMTP_USERNAME
    MAIL_PASSWORD = SMTP_PASSWORD
    MAIL_USE_TLS = SMTP_USE_TLS
    MAIL_USE_SSL = SMTP_USE_SSL
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'no-reply@esg-platform.local')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'ESG Platform')
    EMAIL_RESET_LINK_BASE_URL = os.getenv('EMAIL_RESET_LINK_BASE_URL', 'http://localhost:5173/reset-password')
    RESET_PASSWORD_TOKEN_EXPIRES_MINUTES = int(os.getenv('RESET_PASSWORD_TOKEN_EXPIRES_MINUTES', '15'))
    AWS_REGION = os.getenv('AWS_REGION', os.getenv('AWS_S3_REGION', ''))
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', '')
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', '')
    AWS_S3_PUBLIC_BASE_URL = os.getenv('AWS_S3_PUBLIC_BASE_URL', '')
    AVATAR_MAX_UPLOAD_BYTES = int(os.getenv('AVATAR_MAX_UPLOAD_BYTES', str(5 * 1024 * 1024)))
    AVATAR_IMAGE_MAX_SIZE = int(os.getenv('AVATAR_IMAGE_MAX_SIZE', '512'))
    
    # Security: Password reset token exposure
    # Default: never return raw tokens in API responses. To enable (dev only),
    # set RETURN_RESET_TOKEN_IN_RESPONSE=true in your .env (not recommended in prod).
    RETURN_RESET_TOKEN_IN_RESPONSE = os.getenv('RETURN_RESET_TOKEN_IN_RESPONSE', 'false').lower() in {'1', 'true', 'yes'}
    POWER_BI_IFRAME_URL = os.getenv(
        'POWER_BI_IFRAME_URL',
        'https://app.powerbi.com/reportEmbed?reportId=YOUR_REPORT_ID&groupId=YOUR_GROUP_ID&autoAuth=true&ctid=YOUR_TENANT_ID',
    )
