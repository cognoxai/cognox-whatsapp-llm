import os
import logging
import json
from flask import Blueprint, request, jsonify
from threading import Thread
from src.database import db
from src.models.conversation import Conversation, Message
from src.whatsapp_api import whatsapp_api
from src.llm_service import llm_service
from src.calendly_service import calendly_service # Importamos o serviço do Calendly

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint('whatsapp_bp', __name__)

def process_whatsapp_message(data):
    """
    Função que contém toda a lógica de processamento e será executada em background.
    """
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
        
        # --- NOVA LÓGICA DE INTEGRAÇÃO ---
        # Verificamos se a IA deve agendar uma reunião
        should_schedule = "agendar" in msg_body.lower() or "reunião" in msg_body.lower()
        available_slots = []
        if should_schedule:
            logger.info("Tentando buscar horários no Calendly...")
            available_slots = calendly_service.get_available_slots("https://calendly.com/cognox-ai/30min" )
            logger.info(f"Horários encontrados: {available_slots}")

        # Passamos os horários disponíveis para a IA
        ai_response = llm_service.process_message(msg_body, history, available_slots)
        
        ai_message = Message(conversation_id=conversation.id, message_type="assistant", content=ai_response)
        db.session.add(ai_message)
        db.session.commit()
        
        whatsapp_api.send_humanized_text_message(from_number, ai_response, phone_number_id)

    except Exception as e:
        logger.critical(f"ERRO CRÍTICO NO PROCESSAMENTO EM BACKGROUND: {e}", exc_info=True)

@whatsapp_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    # ... (esta função permanece a mesma da versão anterior)
    data = request.get_json()
    logger.info(f"Webhook recebido: {json.dumps(data, indent=2)}")

    if (data.get("object") == "whatsapp_business_account" and
            data.get("entry") and data["entry"][0].get("changes") and
            data["entry"][0]["changes"][0].get("value") and
            data["entry"][0]["changes"][0]["value"].get("messages") and
            data["entry"][0]["changes"][0]["value"]["messages"][0].get("type") == "text"):
        
        thread = Thread(target=process_whatsapp_message, args=(data,))
        thread.start()

    return jsonify(status="accepted"), 200
