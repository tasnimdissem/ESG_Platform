from datetime import datetime
from backend.extensions import db

class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Peut être null si pas connecté
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    primary_industry = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # On stocke les métriques saisies sous forme de JSON pour pouvoir les réutiliser
    features_data = db.Column(db.JSON, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'primary_industry': self.primary_industry,
            'score': self.score,
            'created_at': self.created_at.isoformat() + 'Z',
            'features_data': self.features_data
        }
