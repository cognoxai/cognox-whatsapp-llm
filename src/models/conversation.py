from ..database import db # Importa 'db' do novo arquivo database.py
from datetime import datetime

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False, index=True)
    user_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')
    scheduling_info = db.relationship('SchedulingInfo', backref='conversation', uselist=False, cascade='all, delete-orphan')

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    message_type = db.Column(db.String(10), nullable=False)  # 'user' ou 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SchedulingInfo(db.Model):
    __tablename__ = 'scheduling_info'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, unique=True)
    name = db.Column(db.String(100))
    company = db.Column(db.String(100))
    preferred_time = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
