# Analytics summary endpoint: aggregates CatBoost prediction history so the frontend can render live ESG trends instead of static demo data.
from __future__ import annotations

from typing import Any

import pandas as pd
from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.extensions import db
from backend.models.prediction import PredictionHistory
from backend.models.user import User
from backend.services.ml_service import ml_service_instance


analytics_bp = Blueprint('analytics', __name__)


def _to_numeric_features(features_data: Any) -> dict[str, float]:
    if not isinstance(features_data, dict):
        return {}

    numeric_features: dict[str, float] = {}
    for key, value in features_data.items():
        if isinstance(value, bool):
            continue
        try:
            numeric_features[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return numeric_features


def _empty_summary() -> dict[str, Any]:
    return {
        'score_moyen': None,
        'score_min': None,
        'score_max': None,
        'nb_predictions': 0,
        'evolution_mensuelle': [],
        'top_variables': [],
        'correlation_matrix': [],
    }


@analytics_bp.get('/summary')
@jwt_required()
def analytics_summary() -> object:
    user_id = get_jwt_identity()
    try:
        current_user = db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return jsonify({'error': 'Identité du jeton invalide'}), 401

    if current_user is None:
        return jsonify({'error': 'Utilisateur introuvable'}), 401

    if current_user.role not in ('admin', 'decideur', 'metier'):
        return jsonify({'error': 'Accès refusé. Réservé aux décideurs, utilisateurs métier et administrateurs.'}), 403

    if current_user.role == 'admin':
        history = (
            PredictionHistory.query
            .order_by(PredictionHistory.created_at.asc())
            .all()
        )
    else:
        # decideur/metier : prédictions de leur entreprise + prédictions des admins (plateforme-wide)
        admin_ids = [u.id for u in User.query.filter_by(role='admin').all()]
        if current_user.company_id:
            company_user_ids = [
                u.id for u in User.query.filter_by(company_id=current_user.company_id).all()
            ]
            relevant_ids = list(set(company_user_ids + admin_ids))
            history = (
                PredictionHistory.query
                .filter(PredictionHistory.user_id.in_(relevant_ids))
                .order_by(PredictionHistory.created_at.asc())
                .all()
            )
        else:
            relevant_ids = list(set([int(user_id)] + admin_ids))
            history = (
                PredictionHistory.query
                .filter(PredictionHistory.user_id.in_(relevant_ids))
                .order_by(PredictionHistory.created_at.asc())
                .all()
            )

    if len(history) == 0:
        return jsonify(_empty_summary()), 200

    rows: list[dict[str, Any]] = []
    for item in history:
        row = _to_numeric_features(item.features_data)
        row['score'] = float(item.score)
        row['created_at'] = item.created_at
        row['month_key'] = item.created_at.strftime('%Y-%m') if item.created_at else None
        rows.append(row)

    df = pd.DataFrame(rows)

    score_series = df['score'].dropna()
    if score_series.empty:
        return jsonify(_empty_summary()), 200

    end_month = pd.Timestamp.utcnow().to_period('M').to_timestamp()
    month_starts = pd.date_range(end=end_month, periods=12, freq='MS')
    grouped_scores = df.groupby('month_key')['score'].mean().to_dict() if 'month_key' in df.columns else {}

    evolution_mensuelle = []
    for month_start in month_starts:
        month_key = month_start.strftime('%Y-%m')
        evolution_mensuelle.append(
            {
                'mois': month_start.strftime('%b %Y'),
                'score': round(float(grouped_scores[month_key]), 2) if month_key in grouped_scores and pd.notna(grouped_scores[month_key]) else None,
            }
        )

    top_variables: list[dict[str, Any]] = []
    try:
        ml_service_instance.load_resources()
        feature_names = list(getattr(ml_service_instance, 'feature_names', []))
        if feature_names and getattr(ml_service_instance, 'model', None) is not None:
            raw_importances = ml_service_instance.model.get_feature_importance()
            paired = [
                {'feature': feature, 'importance': float(importance)}
                for feature, importance in zip(feature_names, raw_importances, strict=False)
            ]
            total_importance = sum(item['importance'] for item in paired) or 1.0
            top_variables = [
                {
                    'feature': item['feature'],
                    'importance': round(item['importance'] / total_importance, 4),
                }
                for item in sorted(paired, key=lambda item: item['importance'], reverse=True)[:8]
            ]
    except Exception as exc:
        current_app.logger.warning('Unable to compute feature importances for analytics: %s', exc)

    numeric_columns = [
        column
        for column in df.columns
        if column not in {'created_at', 'month_key'} and pd.api.types.is_numeric_dtype(df[column])
    ]
    numeric_columns = sorted(
        numeric_columns,
        key=lambda column: (int(df[column].notna().sum()), float(df[column].std(ddof=0) or 0.0)),
        reverse=True,
    )[:8]

    correlation_matrix: list[dict[str, Any]] = []
    if len(numeric_columns) >= 2:
        corr_df = df[numeric_columns].corr().fillna(0.0)
        for x in corr_df.columns:
            for y in corr_df.index:
                correlation_matrix.append(
                    {
                        'x': x,
                        'y': y,
                        'value': round(float(corr_df.loc[y, x]), 4),
                    }
                )

    return jsonify(
        {
            'score_moyen': round(float(score_series.mean()), 2),
            'score_min': round(float(score_series.min()), 2),
            'score_max': round(float(score_series.max()), 2),
            'nb_predictions': len(history),
            'evolution_mensuelle': evolution_mensuelle,
            'top_variables': top_variables,
            'correlation_matrix': correlation_matrix,
        }
    ), 200