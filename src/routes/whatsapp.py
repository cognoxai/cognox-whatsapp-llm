import os
import logging
import json
from flask import Blueprint, request, jsonify
from src.database import db
from src.models.conversation import Conversation, Message
# from src.whatsapp_api import whatsapp_api  # Descomente quando a API estiver pronta
# from src.llm_service import llm_service    # Descomente quando o serviço LLM estiver pronto

logger = logging.getLogger(__name__)
whatsapp_bp = Blueprint('whatsapp_bp', __name__)
# ... (o resto do arquivo permanece o mesmo)
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
        pass
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")

    return "OK", 200

@whatsapp_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200
