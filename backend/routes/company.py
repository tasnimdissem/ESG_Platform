from flask import Blueprint, jsonify
from backend.models.company import Company
from backend.models.prediction import PredictionHistory
from flask_jwt_extended import jwt_required, get_jwt_identity

company_bp = Blueprint('company', __name__)

@company_bp.get('/companies')
@jwt_required(optional=True)
def get_companies():
    """
    Endpoint: GET /api/companies
    Returns all companies that have at least one prediction.
    """
    companies = Company.query.all()
    result = []
    for company in companies:
        # Get the latest prediction for this company
        latest_prediction = PredictionHistory.query.filter_by(company_id=company.id).order_by(PredictionHistory.created_at.desc()).first()
        if latest_prediction:
            company_data = company.to_dict()
            company_data['latest_score'] = latest_prediction.score
            company_data['latest_prediction_date'] = latest_prediction.created_at.isoformat() + 'Z'
            result.append(company_data)
            
    return jsonify(result), 200

@company_bp.get('/companies/<int:company_id>/history')
@jwt_required(optional=True)
def get_company_history(company_id):
    """
    Endpoint: GET /api/companies/:id/history
    Returns the prediction history for a specific company.
    """
    company = Company.query.get_or_404(company_id)
    history = PredictionHistory.query.filter_by(company_id=company.id).order_by(PredictionHistory.created_at.asc()).all()
    
    return jsonify({
        "company": company.to_dict(),
        "history": [h.to_dict() for h in history]
    }), 200
