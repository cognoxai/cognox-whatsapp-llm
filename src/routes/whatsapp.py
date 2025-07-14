import os
import logging
import json
from flask import Blueprint, request, jsonify
from ..database import db # Importa 'db' do novo arquivo database.py
from ..models.conversation import Conversation, Message
from ..whatsapp_api import whatsapp_api
from ..llm_service import llm_service

logger = logging.getLogger(__name__)
whatsapp_bp = Blueprint('whatsapp_bp', __name__)

@whatsapp_bp.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == os.getenv("WHATSAPP_VERIFY_TOKEN"):
        logger.info("Webhook verified successfully")
        return challenge, 200
    else:
        logger.warning("Webhook verification failed")
        return "Forbidden", 403

@whatsapp_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    logger.info(f"Webhook received: {json.dumps(data, indent=2)}")
    
    try:
        # Lógica para processar a mensagem
        # (Esta parte pode ser expandida conforme a necessidade)
        pass # Adicione a lógica de processamento aqui
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")

    return "OK", 200

@whatsapp_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200
