from flask import Blueprint, request, jsonify
import logging
from pydantic import ValidationError

from backend.extensions import limiter
from backend.services.ml_service import predict_esg
from backend.schemas import PredictRequest

logger = logging.getLogger(__name__)

# Create a Blueprint for the prediction routes
prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.post('/predict')
@limiter.limit("30 per hour")  # Prevent ML model abuse - 30 predictions per hour per IP
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
        # 4. Return the result in the requested format
        return jsonify({
            "score": score
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
