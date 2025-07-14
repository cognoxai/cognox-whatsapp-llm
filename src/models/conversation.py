from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Conversation(db.Model):
    """
    Modelo para armazenar conversas do WhatsApp
    """
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False, index=True)
    user_name = db.Column(db.String(100), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default=\'active\')  # active, scheduled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com mensagens
    messages = db.relationship(\'Message\', backref=\'conversation\', lazy=True, cascade=\'all, delete-orphan\')
    
    def to_dict(self):
        return {
            \'id\': self.id,
            \'phone_number\': self.phone_number,
            \'user_name\': self.user_name,
            \'company\': self.company,
            \'status\': self.status,
            \'created_at\': self.created_at.isoformat() if self.created_at else None,
            \'updated_at\': self.updated_at.isoformat() if self.updated_at else None,
            \'messages_count\': len(self.messages)
        }

class Message(db.Model):
    """
    Modelo para armazenar mensagens individuais
    """
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey(\'conversations.id\'), nullable=False)
    message_type = db.Column(db.String(10), nullable=False)  # \'user\' ou \'assistant\'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    has_scheduling_intent = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            \'id\': self.id,
            \'conversation_id\': self.conversation_id,
            \'message_type\': self.message_type,
            \'content\': self.content,
            \'timestamp\': self.timestamp.isoformat() if self.timestamp else None,
            \'has_scheduling_intent\': self.has_scheduling_intent
        }

class SchedulingInfo(db.Model):
    """
    Modelo para armazenar informações de agendamento extraídas
    """
    __tablename__ = 'scheduling_info'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey(\'conversations.id\'), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    preferred_time = db.Column(db.String(200), nullable=True)
    service_interest = db.Column(db.String(200), nullable=True)
    additional_info = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default=\'pending\')  # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    conversation = db.relationship(\'Conversation\', backref=\'scheduling_info\', uselist=False)
    
    def to_dict(self):
        return {
            \'id\': self.id,
            \'conversation_id\': self.conversation_id,
            \'name\': self.name,
            \'company\': self.company,
            \'preferred_time\': self.preferred_time,
            \'service_interest\': self.service_interest,
            \'additional_info\': self.additional_info,
            \'status\': self.status,
            \'created_at\': self.created_at.isoformat() if self.created_at else None,
            \'updated_at\': self.updated_at.isoformat() if self.updated_at else None
        }
