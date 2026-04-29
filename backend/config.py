from __future__ import annotations

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


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv('DATABASE_URL', 'sqlite:///esg_pfe.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RAG_API_BASE_URL = os.getenv('RAG_API_BASE_URL', 'http://localhost:8000')
    RAG_INTEGRATION_PATH = os.getenv('RAG_INTEGRATION_PATH', '/api/v1/query')
    RAG_API_URL = os.getenv('RAG_API_URL', '')
    RAG_API_TOKEN = os.getenv('RAG_API_TOKEN', '')
    RAG_TOP_K = int(os.getenv('RAG_TOP_K', '3'))
    RAG_TIMEOUT_SECONDS = int(os.getenv('RAG_TIMEOUT_SECONDS', '90'))
    RAG_ALLOW_LOCAL_FALLBACK = os.getenv('RAG_ALLOW_LOCAL_FALLBACK', 'true').lower() in {'1', 'true', 'yes'}
    INTEGRATION_AUTH_ENABLED = os.getenv('INTEGRATION_AUTH_ENABLED', 'false').lower() in {'1', 'true', 'yes'}
    INTEGRATION_BEARER_TOKEN = os.getenv('INTEGRATION_BEARER_TOKEN', '')
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() in {'1', 'true', 'yes'}
    SMTP_USE_SSL = os.getenv('SMTP_USE_SSL', 'false').lower() in {'1', 'true', 'yes'}
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'no-reply@esg-platform.local')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'ESG Platform')
    EMAIL_RESET_LINK_BASE_URL = os.getenv('EMAIL_RESET_LINK_BASE_URL', 'http://localhost:5173/reset-password')
    POWER_BI_IFRAME_URL = os.getenv(
        'POWER_BI_IFRAME_URL',
        'https://app.powerbi.com/reportEmbed?reportId=YOUR_REPORT_ID&groupId=YOUR_GROUP_ID&autoAuth=true&ctid=YOUR_TENANT_ID',
    )
