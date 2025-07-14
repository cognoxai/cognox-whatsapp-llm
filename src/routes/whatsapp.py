import os
import logging
import json
from flask import Blueprint, request, jsonify
from src.database import db
from src.models.conversation import Conversation, Message
from src.whatsapp_api import whatsapp_api
from src.llm_service import llm_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint('whatsapp_bp', __name__)

@whatsapp_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    logger.info(f"Webhook recebido: {json.dumps(data, indent=2)}")

    try:
        # Validação robusta para garantir que é uma mensagem de texto do usuário
        if (data.get("object") == "whatsapp_business_account" and
                data.get("entry") and data["entry"][0].get("changes") and
                data["entry"][0]["changes"][0].get("value") and
                data["entry"][0]["changes"][0]["value"].get("messages")):
            
            value = data["entry"][0]["changes"][0]["value"]
            message_data = value["messages"][0]
            
            if message_data.get("type") != "text":
                logger.info("Ignorando notificação que não é mensagem de texto.")
                return jsonify(status="ignored_non_text_message"), 200

            # Extração de dados essenciais
            phone_number_id = value["metadata"]["phone_number_id"]
            from_number = message_data["from"]
            msg_body = message_data["text"]["body"]
            wamid = message_data["id"]

            # --- CHAMADAS CORRIGIDAS ---
            whatsapp_api.mark_message_as_read(wamid, phone_number_id)

            # Lógica de banco de dados
            conversation = Conversation.query.filter_by(phone_number=from_number).first()
            if not conversation:
                conversation = Conversation(phone_number=from_number)
                db.session.add(conversation)
                db.session.commit()
            
            user_message = Message(conversation_id=conversation.id, message_type="user", content=msg_body)
            db.session.add(user_message)
            db.session.commit()

            # Lógica da IA
            history = [{"role": msg.message_type, "content": msg.content} for msg in conversation.messages]
            ai_response = llm_service.process_message(msg_body, history)
            
            ai_message = Message(conversation_id=conversation.id, message_type="assistant", content=ai_response)
            db.session.add(ai_message)
            db.session.commit()
            
            # --- CHAMADA CORRIGIDA ---
            whatsapp_api.send_text_message(from_number, ai_response, phone_number_id)

    except Exception as e:
        logger.critical(f"ERRO CRÍTICO NO WEBHOOK: {e}", exc_info=True)
    
    # Retorna 200 OK em todos os casos para o WhatsApp não reenviar a notificação.
    return jsonify(status="processed"), 200
