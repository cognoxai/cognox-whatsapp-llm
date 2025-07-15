import logging
import json
from flask import Blueprint, request, jsonify, current_app
from threading import Thread
from src.database import db
from src.models.conversation import Conversation, Message
from src.whatsapp_api import whatsapp_api
from src.llm_service import llm_service

logger = logging.getLogger(__name__)
whatsapp_bp = Blueprint('whatsapp_bp', __name__)

def process_message_background(app, data):
    with app.app_context():
        try:
            value = data["entry"][0]["changes"][0]["value"]
            message_data = value["messages"][0]
            phone_number_id = value["metadata"]["phone_number_id"]
            from_number = message_data["from"]
            msg_body = message_data["text"]["body"]
            wamid = message_data["id"]

            whatsapp_api.mark_message_as_read(wamid, phone_number_id)

            conversation = Conversation.query.filter_by(phone_number=from_number).first()
            if not conversation:
                conversation = Conversation(phone_number=from_number)
                db.session.add(conversation)
                db.session.commit()
            
            user_message = Message(conversation_id=conversation.id, message_type="user", content=msg_body)
            db.session.add(user_message)
            db.session.commit()

            history = [{"role": msg.message_type, "content": msg.content} for msg in conversation.messages]
            
            ai_response = llm_service.process_message(msg_body, history)
            
            ai_message = Message(conversation_id=conversation.id, message_type="assistant", content=ai_response)
            db.session.add(ai_message)
            db.session.commit()
            
            whatsapp_api.send_humanized_text_message(from_number, ai_response, phone_number_id)

        except Exception as e:
            logger.critical(f"ERRO CRÍTICO NO PROCESSAMENTO EM BACKGROUND: {e}", exc_info=True)

@whatsapp_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    try:
        if (data and data.get("object") == "whatsapp_business_account" and
                data["entry"][0]["changes"][0]["value"]["messages"][0].get("type") == "text"):
            
            app = current_app._get_current_object()
            thread = Thread(target=process_message_background, args=(app, data))
            thread.start()
            
            logger.info("Webhook válido recebido, processamento iniciado.")
    except (KeyError, IndexError):
        logger.info(f"Webhook recebido, mas não é uma mensagem de texto do usuário: {json.dumps(data)}")

    return jsonify(status="ok"), 200
