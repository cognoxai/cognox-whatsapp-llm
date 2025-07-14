import os
import logging
import json
from flask import Blueprint, request, jsonify
from src.database import db
from src.models.conversation import Conversation, Message
from src.whatsapp_api import whatsapp_api
from src.llm_service import llm_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint('whatsapp_bp', __name__)

@whatsapp_bp.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == os.getenv("WHATSAPP_VERIFY_TOKEN"):
        logger.info("Webhook verified successfully!")
        return challenge, 200
    else:
        logger.warning("Webhook verification failed.")
        return "Forbidden", 403

@whatsapp_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    logger.info(f"Webhook received: {json.dumps(data, indent=2)}")

    try:
        if not (data.get("object") == "whatsapp_business_account" and
                data.get("entry") and data["entry"][0].get("changes") and
                data["entry"][0]["changes"][0].get("value") and
                data["entry"][0]["changes"][0]["value"].get("messages")):
            logger.info("Webhook received but not a message notification.")
            return jsonify({"status": "not a message"}), 200

        value = data["entry"][0]["changes"][0]["value"]
        message_data = value["messages"][0]
        
        if message_data.get("type") != "text":
            logger.info("Ignoring non-text message.")
            return jsonify({"status": "ignored"}), 200

        phone_number_id = value["metadata"]["phone_number_id"]
        phone_number = message_data["from"]
        message_text = message_data["text"]["body"]
        message_id = message_data["id"]

        whatsapp_api.mark_message_as_read(message_id, phone_number_id)

        # --- LÓGICA DE BANCO DE DADOS MAIS ROBUSTA ---
        conversation = Conversation.query.filter_by(phone_number=phone_number).first()
        if not conversation:
            conversation = Conversation(phone_number=phone_number)
            db.session.add(conversation)
            db.session.commit()
            logger.info(f"New conversation created for {phone_number} with ID {conversation.id}.")
        
        user_message = Message(conversation_id=conversation.id, message_type="user", content=message_text)
        db.session.add(user_message)
        db.session.commit()

        history = [{"role": msg.message_type, "content": msg.content} for msg in conversation.messages]
        
        ai_response = llm_service.process_message(message_text, history)
        
        # Salva a resposta da IA ANTES de tentar enviar, garantindo a integridade do DB
        ai_message = Message(conversation_id=conversation.id, message_type="assistant", content=ai_response)
        db.session.add(ai_message)
        db.session.commit()
        
        # Tenta enviar a mensagem, mas não quebra a aplicação se falhar
        success = whatsapp_api.send_text_message(phone_number, ai_response)
        if not success:
            logger.error(f"Failed to send WhatsApp message to {phone_number}, but conversation is saved.")

    except Exception as e:
        logger.error(f"CRITICAL ERROR in webhook processing: {e}", exc_info=True)
        # Retorna 200 para não ser bombardeado pelo WhatsApp, mas loga o erro crítico.
        return jsonify({"status": "error"}), 200

    return jsonify({"status": "ok"}), 200

@whatsapp_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200
