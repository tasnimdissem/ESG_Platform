from flask import Blueprint, request, jsonify
from backend.services.ml_service import predict_esg

# Create a Blueprint for the prediction routes
prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.post('/predict')
def predict():
    """
    Endpoint: POST /predict
    Receives JSON input and returns the predicted ESG score.
    """
    try:
        # 1. Get JSON data from the incoming request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON payload provided in the request"}), 400
            
        # 2. Call the ml_service prediction function
        score = predict_esg(data)
        
        # 3. Return the result in the requested format
        return jsonify({
            "score": score
        }), 200
        
    except ValueError as ve:
        # Handle data validation or processing errors
        return jsonify({"error": f"Invalid input data: {str(ve)}"}), 400
    except RuntimeError as re:
        # Handle model loading or internal errors
        return jsonify({"error": f"Internal model error: {str(re)}"}), 500
    except Exception as e:
        # Catch-all for any other unexpected errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
