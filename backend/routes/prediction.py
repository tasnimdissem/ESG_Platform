from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from pydantic import ValidationError

from backend.extensions import limiter, db
from backend.services.ml_service import predict_esg
from backend.schemas import PredictRequest
from backend.models.prediction import PredictionHistory
from backend.models.company import Company
from flask_jwt_extended import jwt_required, get_jwt_identity

logger = logging.getLogger(__name__)

# Create a Blueprint for the prediction routes
prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.post('/predict')
@limiter.limit("20 per minute")  # FIXED: Rate limiting a 20 requetes / minute par IP
@jwt_required(optional=True)
def predict():
    """
    Endpoint: POST /predict
    Receives validated JSON input and returns the predicted ESG score.
    """
    try:
        # 1. Get JSON data from the incoming request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON payload provided in the request"}), 400
        
        # 2. Validate input against Pydantic schema (bounds checking, type validation)
        try:
            validated_data = PredictRequest(**data)
        except ValidationError as ve:
            logger.warning(f"Validation error in predict: {ve}")
            errors = [{"field": err["loc"][0], "message": err["msg"]} for err in ve.errors()]
            return jsonify({"error": "Invalid input data", "details": errors}), 400
        
        logger.info(f"Predict request validated successfully")
        logger.debug(f"Predict request data: {validated_data.dict()}")
            
        # 3. Call the ml_service prediction function with validated data
        score = predict_esg(validated_data.dict())
        
        logger.info(f"Prediction successful: score={score}")
        
        # --- Sauvegarde dans l'historique ---
        user_id = get_jwt_identity() # Retourne None si pas authentifié
        try:
            # Récupérer ou créer l'entreprise
            company_name = validated_data.company_name
            company = Company.query.filter_by(name=company_name).first()
            if not company:
                company = Company(name=company_name, sector=validated_data.primary_industry)
                db.session.add(company)
                db.session.commit() # Commit to get company.id
            
            history_entry = PredictionHistory(
                user_id=user_id,
                company_id=company.id,
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
            "score": score,
            "company_name": company_name,
            "date": datetime.utcnow().isoformat() + 'Z' if 'datetime' in globals() else None
        }), 200
        
    except ValueError as ve:
        logger.error(f"ValueError in predict: {str(ve)}")
        # Handle data validation or processing errors
        return jsonify({"error": f"Invalid input data: {str(ve)}"}), 400
    except RuntimeError as re:
        logger.error(f"RuntimeError in predict: {str(re)}")
        # Handle model loading or internal errors
        return jsonify({"error": f"Internal model error: {str(re)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in predict: {str(e)}", exc_info=True)
        # Catch-all for any other unexpected errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@prediction_bp.get('/history')
@jwt_required()
def get_history():
    """
    Endpoint: GET /history
    Returns the prediction history for the authenticated user.
    """
    user_id = get_jwt_identity()
    history = PredictionHistory.query.filter_by(user_id=user_id).order_by(PredictionHistory.created_at.desc()).all()
    return jsonify([h.to_dict() for h in history]), 200
