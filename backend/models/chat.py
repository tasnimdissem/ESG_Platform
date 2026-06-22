from __future__ import annotations

from datetime import datetime

from backend.extensions import db


class ChatConversation(db.Model):
    __tablename__ = 'chat_conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False, default='Nouvelle conversation')
    session_id = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    messages = db.relationship(
        'ChatMessage',
        backref='conversation',
        lazy='select',
        cascade='all, delete-orphan',
        order_by='ChatMessage.timestamp',
    )
    user = db.relationship('User', backref=db.backref('conversations', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
        }


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey('chat_conversations.id', ondelete='CASCADE'), nullable=False, index=True
    )
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    text = db.Column(db.Text, nullable=False)
    sources = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'sender': self.sender,
            'text': self.text,
            'sources': self.sources or [],
            'timestamp': self.timestamp.isoformat(),
        }
