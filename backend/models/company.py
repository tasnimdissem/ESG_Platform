from backend.extensions import db

class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    sector = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)

    # Relationships
    predictions = db.relationship('PredictionHistory', backref='company', lazy=True, cascade='all, delete-drop')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sector': self.sector,
            'country': self.country
        }
