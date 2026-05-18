from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import inspect, text

from backend.extensions import db
from backend.models.company import Company


logger = logging.getLogger(__name__)
companies_bp = Blueprint('companies', __name__)


def ensure_company_schema() -> None:
    inspector = inspect(db.engine)
    if 'companies' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('companies')}
    statements: list[str] = []

    if 'historique' not in columns:
        statements.append("ALTER TABLE companies ADD COLUMN historique JSONB NOT NULL DEFAULT '[]'::jsonb")
    if 'created_by_user_id' not in columns:
        statements.append('ALTER TABLE companies ADD COLUMN created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL')
    if 'created_at' not in columns:
        statements.append('ALTER TABLE companies ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP')
    if 'updated_at' not in columns:
        statements.append('ALTER TABLE companies ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP')

    for statement in statements:
        db.session.execute(text(statement))
    if statements:
        db.session.commit()


def _current_user_id() -> int | None:
    identity = get_jwt_identity()
    if identity in (None, ''):
        return None
    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


def _get_json_payload() -> tuple[dict[str, Any] | None, tuple[object, int] | None]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, (jsonify({'error': 'Invalid JSON payload'}), 400)
    return payload, None


def _build_history_entry(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, tuple[object, int] | None]:
    indicators = payload.get('indicators')
    if not isinstance(indicators, dict):
        indicators = payload.get('indicateurs')
    if not isinstance(indicators, dict):
        return None, (jsonify({'error': 'Missing indicators payload'}), 400)

    score = payload.get('score')
    if score is None:
        return None, (jsonify({'error': 'Missing score payload'}), 400)

    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return None, (jsonify({'error': 'Invalid score payload'}), 400)

    return {
        'date': str(payload.get('date') or datetime.utcnow().date().isoformat()),
        'indicateurs': indicators,
        'scores': {
            'E': numeric_score,
            'S': numeric_score,
            'G': numeric_score,
            'global': numeric_score,
        },
    }, None


@companies_bp.get('/companies')
@jwt_required()
def list_companies() -> object:
    ensure_company_schema()
    companies = Company.query.order_by(Company.updated_at.desc(), Company.created_at.desc()).all()
    return jsonify([company.to_dict() for company in companies]), 200


@companies_bp.post('/companies')
@jwt_required()
def create_company() -> object:
    ensure_company_schema()
    payload, error = _get_json_payload()
    if error is not None:
        return error

    name = str(payload.get('name') or payload.get('nom') or '').strip()
    if not name:
        return jsonify({'error': 'Company name is required'}), 400

    history_entry, error = _build_history_entry(payload)
    if error is not None:
        return error

    company = Company(
        name=name,
        historique=[history_entry],
        created_by_user_id=_current_user_id(),
    )

    db.session.add(company)
    db.session.commit()
    return jsonify(company.to_dict()), 201


@companies_bp.get('/companies/<string:company_id>')
@jwt_required()
def get_company(company_id: str) -> object:
    ensure_company_schema()
    try:
        company = db.session.get(Company, int(company_id))
    except (TypeError, ValueError):
        return jsonify({'error': 'Company not found'}), 404
    if company is None:
        return jsonify({'error': 'Company not found'}), 404
    return jsonify(company.to_dict()), 200


@companies_bp.post('/companies/<string:company_id>/history')
@jwt_required()
def add_company_history(company_id: str) -> object:
    ensure_company_schema()
    payload, error = _get_json_payload()
    if error is not None:
        return error

    try:
        company = db.session.get(Company, int(company_id))
    except (TypeError, ValueError):
        return jsonify({'error': 'Company not found'}), 404
    if company is None:
        return jsonify({'error': 'Company not found'}), 404

    history_entry, error = _build_history_entry(payload)
    if error is not None:
        return error

    company.add_history_entry(history_entry)
    db.session.commit()
    return jsonify(company.to_dict()), 200


@companies_bp.put('/companies/<string:company_id>')
@jwt_required()
def update_company(company_id: str) -> object:
    ensure_company_schema()
    payload, error = _get_json_payload()
    if error is not None:
        return error

    try:
        company = db.session.get(Company, int(company_id))
    except (TypeError, ValueError):
        return jsonify({'error': 'Company not found'}), 404

    if company is None:
        return jsonify({'error': 'Company not found'}), 404

    if 'name' in payload or 'nom' in payload:
        name = str(payload.get('name') or payload.get('nom') or '').strip()
        if not name:
            return jsonify({'error': 'Company name is required'}), 400
        company.name = name

    if 'sector' in payload:
        sector = payload.get('sector')
        company.sector = str(sector).strip() if sector is not None and str(sector).strip() else None

    if 'country' in payload:
        country = payload.get('country')
        company.country = str(country).strip() if country is not None and str(country).strip() else None

    db.session.commit()
    return jsonify(company.to_dict()), 200


@companies_bp.delete('/companies/<string:company_id>')
@jwt_required()
def delete_company(company_id: str) -> object:
    ensure_company_schema()
    try:
        company = db.session.get(Company, int(company_id))
    except (TypeError, ValueError):
        return jsonify({'error': 'Company not found'}), 404

    if company is None:
        return jsonify({'error': 'Company not found'}), 404

    db.session.delete(company)
    db.session.commit()
    return jsonify({'message': 'Company deleted successfully'}), 200
