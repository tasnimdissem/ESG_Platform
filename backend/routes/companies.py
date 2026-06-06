from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models.company import Company
from backend.models.user import User


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


def _is_admin() -> bool:
    identity = get_jwt_identity()
    if identity in (None, ''):
        return False
    try:
        user = db.session.get(User, int(identity))
        return user is not None and user.role == 'admin'
    except (TypeError, ValueError):
        return False


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
    uid = _current_user_id()
    if uid is None:
        return jsonify({'error': 'Identité du jeton invalide'}), 401
    user = db.session.get(User, uid)
    if user is None:
        return jsonify({'error': 'Utilisateur introuvable'}), 401

    if user.role == 'admin':
        companies = Company.query.order_by(Company.updated_at.desc(), Company.created_at.desc()).all()
        return jsonify([c.to_dict() for c in companies]), 200

    if user.role == 'metier':
        if not user.company_id:
            return jsonify({'error': 'Aucune entreprise assignée à votre compte. Contactez un administrateur.'}), 403
        company = db.session.get(Company, user.company_id)
        if company is None:
            return jsonify({'error': 'Entreprise introuvable'}), 404
        return jsonify([company.to_dict()]), 200

    return jsonify({'error': 'Accès refusé. Permissions insuffisantes.'}), 403


@companies_bp.post('/companies')
@jwt_required()
def create_company() -> object:
    if not _is_admin():
        return jsonify({'error': 'Accès refusé. Réservé aux administrateurs.'}), 403
    ensure_company_schema()
    payload, error = _get_json_payload()
    if error is not None:
        return error

    name = str(payload.get('name') or payload.get('nom') or '').strip()
    if not name:
        return jsonify({'error': 'Company name is required'}), 400

    # Allow creation with or without history entry (indicators + score)
    history_entry = None
    has_indicators = 'indicators' in payload or 'indicateurs' in payload
    has_score = 'score' in payload
    
    if has_indicators or has_score:
        history_entry, error = _build_history_entry(payload)
        if error is not None:
            return error
    
    # Extract sector and country if provided
    sector = payload.get('sector')
    sector = str(sector).strip() if sector is not None and str(sector).strip() else None
    country = payload.get('country')
    country = str(country).strip() if country is not None and str(country).strip() else None

    # If a company with the same name already exists, append a history entry
    # instead of raising an unhandled unique-constraint database error.
    existing_company = Company.query.filter_by(name=name).first()
    if existing_company is not None:
        if history_entry is not None:
            existing_company.add_history_entry(history_entry)
        if sector:
            existing_company.sector = sector
        if country:
            existing_company.country = country
        existing_company.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify(existing_company.to_dict()), 200

    company = Company(
        name=name,
        historique=[history_entry] if history_entry else [],
        sector=sector,
        country=country,
        created_by_user_id=_current_user_id(),
    )

    try:
        db.session.add(company)
        db.session.commit()
        return jsonify(company.to_dict()), 201
    except IntegrityError:
        # Race condition safety: if another request created the same name first,
        # rollback and append history on the existing row.
        db.session.rollback()
        existing_company = Company.query.filter_by(name=name).first()
        if existing_company is None:
            return jsonify({'error': 'Une erreur de concurrence est survenue. Veuillez réessayer.'}), 409
        existing_company.add_history_entry(history_entry)
        existing_company.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify(existing_company.to_dict()), 200


@companies_bp.get('/companies/<string:company_id>')
@jwt_required()
def get_company(company_id: str) -> object:
    ensure_company_schema()
    uid = _current_user_id()
    if uid is None:
        return jsonify({'error': 'Identité du jeton invalide'}), 401
    user = db.session.get(User, uid)
    if user is None:
        return jsonify({'error': 'Utilisateur introuvable'}), 401

    try:
        cid = int(company_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Company not found'}), 404

    if user.role == 'admin':
        company = db.session.get(Company, cid)
        if company is None:
            return jsonify({'error': 'Company not found'}), 404
        return jsonify(company.to_dict()), 200

    if user.role == 'metier':
        if not user.company_id or user.company_id != cid:
            return jsonify({'error': 'Accès refusé. Vous n\'avez pas accès à cette entreprise.'}), 403
        company = db.session.get(Company, cid)
        if company is None:
            return jsonify({'error': 'Company not found'}), 404
        return jsonify(company.to_dict()), 200

    return jsonify({'error': 'Accès refusé. Permissions insuffisantes.'}), 403


@companies_bp.post('/companies/<string:company_id>/history')
@jwt_required()
def add_company_history(company_id: str) -> object:
    uid = _current_user_id()
    if uid is None:
        return jsonify({'error': 'Identité du jeton invalide'}), 401
    user = db.session.get(User, uid)
    if user is None:
        return jsonify({'error': 'Utilisateur introuvable'}), 401

    try:
        cid = int(company_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Company not found'}), 404

    if user.role == 'metier':
        if not user.company_id or user.company_id != cid:
            return jsonify({'error': 'Accès refusé. Vous ne pouvez sauvegarder que pour votre entreprise assignée.'}), 403
    elif user.role != 'admin':
        return jsonify({'error': 'Accès refusé. Permissions insuffisantes.'}), 403
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
    if not _is_admin():
        return jsonify({'error': 'Accès refusé. Les informations des entreprises sont réservées aux administrateurs.'}), 403
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
    if not _is_admin():
        return jsonify({'error': 'Accès refusé. Les informations des entreprises sont réservées aux administrateurs.'}), 403
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
