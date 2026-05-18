from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from backend.extensions import db


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    sector = db.Column(db.String(255), nullable=True)
    country = db.Column(db.String(255), nullable=True)
    historique = db.Column(db.JSON, nullable=False, default=list)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def entreprise_id(self) -> str:
        return str(self.id)

    @property
    def nom(self) -> str:
        return self.name

    @nom.setter
    def nom(self, value: str) -> None:
        self.name = value

    def add_history_entry(self, entry: dict[str, Any]) -> None:
        history = self.historique if isinstance(self.historique, list) else []
        history.insert(0, entry)
        self.historique = history

    def to_dict(self) -> dict[str, Any]:
        return {
            'entreprise_id': self.entreprise_id,
            'nom': self.name,
            'name': self.name,
            'sector': self.sector,
            'country': self.country,
            'historique': self.historique if isinstance(self.historique, list) else [],
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
