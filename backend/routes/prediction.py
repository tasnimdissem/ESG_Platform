from flask import Blueprint, request, jsonify
import logging
from pydantic import ValidationError

from backend.extensions import limiter, db
from backend.services.ml_service import predict_esg
from backend.schemas import PredictRequest
from backend.models.prediction import PredictionHistory
from backend.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity

logger = logging.getLogger(__name__)

_FR_LABELS: dict[str, str] = {
    'primary_industry': "Secteur d'activité",
    'log_market_cap': "Valeur boursière de l'entreprise",
    'log_employees': "Nombre total d'employés",
    'log_revenue_wins': "Chiffre d'affaires annuel",
    'log_scope_1': "Émissions CO₂ directes (usines, véhicules)",
    'log_scope_2': "Émissions CO₂ de l'électricité achetée",
    'log_scope_3': "Émissions CO₂ chaîne d'approvisionnement",
    'log_energy_consumption': "Consommation d'énergie totale",
    'log_waste_production': "Déchets produits",
    'log_water_consumption': "Eau consommée",
    'log_hours_of_training_wins': "Heures de formation des employés",
    'log_ceo_compensation': "Rémunération annuelle du PDG",
    'independent_board_members_percentage': "% d'administrateurs indépendants",
    'log_legal_costs_paid_for_controversies': "Montant des litiges et amendes",
    'intensity_scope_1': "Ratio CO₂ direct / chiffre d'affaires",
    'intensity_scope_2': "Ratio CO₂ électricité / chiffre d'affaires",
    'intensity_scope_3': "Ratio CO₂ chaîne / chiffre d'affaires",
    'intensity_energy': "Ratio énergie / chiffre d'affaires",
    'intensity_waste': "Ratio déchets / chiffre d'affaires",
    'intensity_water': "Ratio eau / chiffre d'affaires",
    'intensity_training': "Heures de formation par employé",
    'intensity_productivity': "Chiffre d'affaires par employé",
    'revenue_negative_flag': "Revenus en baisse cette année",
}

def _translate_error(err: dict) -> str:
    """Traduit un objet erreur Pydantic v2 en message français lisible.
    Utilise le champ `type` (fiable) plutôt que le texte anglais."""
    error_type = err.get("type", "")
    ctx = err.get("ctx", {}) or {}

    if error_type == "greater_than_equal":
        limit = ctx.get("ge", ctx.get("limit_value", 0))
        return f"La valeur doit être supérieure ou égale à {limit}"
    if error_type == "less_than_equal":
        limit = ctx.get("le", ctx.get("limit_value", 100))
        return f"La valeur doit être inférieure ou égale à {limit}"
    if error_type == "greater_than":
        limit = ctx.get("gt", ctx.get("limit_value", 0))
        return f"La valeur doit être strictement supérieure à {limit}"
    if error_type == "less_than":
        limit = ctx.get("lt", ctx.get("limit_value", 100))
        return f"La valeur doit être strictement inférieure à {limit}"
    if error_type in ("float_parsing", "int_parsing", "float_type", "int_type"):
        return "Veuillez saisir un nombre valide"
    if error_type == "missing":
        return "Ce champ est obligatoire"
    if error_type == "value_error":
        raw = err.get("msg", "")
        if "At least one prediction feature" in raw:
            return "Veuillez renseigner au moins une variable de prédiction"
        return raw
    # Fallback : retourner le message brut sans le préfixe anglais "Value error, "
    return err.get("msg", "Erreur de validation")


# Create a Blueprint for the prediction routes
prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.post('/predict')
@limiter.limit("20 per minute")
@jwt_required()
def predict():
    """
    Endpoint: POST /predict
    Receives validated JSON input and returns the predicted ESG score.
    """
    user_id = get_jwt_identity()
    try:
        current_user = db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return jsonify({'error': 'Identité du jeton invalide'}), 401
    if current_user is None or current_user.role not in ('admin', 'metier'):
        return jsonify({'error': 'Accès refusé. Réservé aux experts métier et administrateurs.'}), 403

    try:
        # 1. Get JSON data from the incoming request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Aucune charge JSON n'a été fournie dans la requête"}), 400
        
        # 2. Validate input against Pydantic schema (bounds checking, type validation)
        try:
            validated_data = PredictRequest(**data)
        except ValidationError as ve:
            logger.warning(f"Validation error in predict: {ve}")
            errors = [{"field": _FR_LABELS.get(str(err["loc"][0]), str(err["loc"][0])), "message": _translate_error(err)} for err in ve.errors()]
            return jsonify({"error": "Données d'entrée invalides", "details": errors}), 400
        
        logger.info(f"Predict request validated successfully")
        logger.debug(f"Predict request data: {validated_data.dict()}")
            
        # 3. Call the ml_service prediction function with validated data
        score = predict_esg(validated_data.dict())
        
        logger.info(f"Prediction successful: score={score}")
        
        # --- Sauvegarde dans l'historique ---
        try:
            history_entry = PredictionHistory(
                user_id=user_id,
                primary_industry=validated_data.primary_industry,
                score=score,
                features_data=validated_data.dict()
            )
            db.session.add(history_entry)
            db.session.commit()
            logger.info("Historique de prédiction sauvegardé avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'historique: {e}")
            db.session.rollback()
            
        # 4. Return the result in the requested format
        return jsonify({
            "score": score
        }), 200
        
    except ValueError as ve:
        logger.error(f"ValueError in predict: {str(ve)}")
        # Handle data validation or processing errors
        return jsonify({"error": f"Données d'entrée invalides : {str(ve)}"}), 400
    except RuntimeError as re:
        logger.error(f"RuntimeError in predict: {str(re)}")
        # Handle model loading or internal errors
        return jsonify({"error": f"Erreur interne du modèle : {str(re)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in predict: {str(e)}", exc_info=True)
        # Catch-all for any other unexpected errors
        return jsonify({"error": f"Une erreur inattendue s'est produite : {str(e)}"}), 500

@prediction_bp.get('/company-latest-prediction')
@jwt_required()
def company_latest_prediction():
    """Returns the most recent prediction for the current user's company.
    Accessible to admin, metier and decideur roles."""
    user_id = get_jwt_identity()
    try:
        current_user = db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return jsonify({'error': 'Identité du jeton invalide'}), 401

    if current_user is None or current_user.role not in ('admin', 'metier', 'decideur'):
        return jsonify({'error': 'Accès refusé.'}), 403

    if current_user.role == 'admin':
        entry = PredictionHistory.query.order_by(PredictionHistory.created_at.desc()).first()
        if entry is None:
            return jsonify({'found': False}), 200
        return jsonify({
            'found': True,
            'is_admin_view': True,
            'score': entry.score,
            'company_name': entry.company_name,
            'primary_industry': entry.primary_industry,
            'created_at': entry.created_at.isoformat() + 'Z',
            'features_data': entry.features_data,
        }), 200
    admin_ids = [u.id for u in User.query.filter_by(role='admin').all()]

    if current_user.company_id:
        company_user_ids = [
            u.id for u in User.query.filter_by(company_id=current_user.company_id).all()
        ]
        relevant_ids = list(set(company_user_ids + admin_ids))
        entry = (
            PredictionHistory.query
            .filter(PredictionHistory.user_id.in_(relevant_ids))
            .order_by(PredictionHistory.created_at.desc())
            .first()
        )
    else:
        relevant_ids = list(set([int(user_id)] + admin_ids))
        entry = (
            PredictionHistory.query
            .filter(PredictionHistory.user_id.in_(relevant_ids))
            .order_by(PredictionHistory.created_at.desc())
            .first()
        )

    if entry is None:
        return jsonify({'found': False}), 200

    return jsonify({
        'found': True,
        'score': entry.score,
        'primary_industry': entry.primary_industry,
        'created_at': entry.created_at.isoformat() + 'Z',
        'features_data': entry.features_data,
    }), 200


@prediction_bp.get('/history')
@jwt_required()
def get_history():
    """Returns the prediction history scoped to the user's company."""
    user_id = get_jwt_identity()
    try:
        current_user = db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return jsonify({'error': 'Identité du jeton invalide'}), 401
    if current_user is None or current_user.role not in ('admin', 'metier'):
        return jsonify({'error': 'Accès refusé. Réservé aux experts métier et administrateurs.'}), 403

    if current_user.role == 'admin':
        history = PredictionHistory.query.order_by(PredictionHistory.created_at.desc()).all()
    elif current_user.company_id:
        company_user_ids = [
            u.id for u in User.query.filter_by(company_id=current_user.company_id).all()
        ]
        history = (
            PredictionHistory.query
            .filter(PredictionHistory.user_id.in_(company_user_ids))
            .order_by(PredictionHistory.created_at.desc())
            .all()
        )
    else:
        history = PredictionHistory.query.filter_by(user_id=user_id).order_by(PredictionHistory.created_at.desc()).all()

    return jsonify([h.to_dict() for h in history]), 200
