import logging
import json
from flask import Blueprint, request, jsonify, current_app
from src.database import db
from src.models.conversation import Conversation, Message
from src.whatsapp_api import whatsapp_api
from src.llm_service import llm_service

logger = logging.getLogger(__name__)
whatsapp_bp = Blueprint('whatsapp_bp', __name__)

def process_message_in_context(data):
    app = current_app._get_current_object()
    with app.app_context():
        try:
            value = data["entry"][0]["changes"][0]["value"]
            message_data = value["messages"][0]
            
            phone_number_id = value["metadata"]["phone_number_id"]
            from_number = message_data["from"]
            msg_body = message_data["text"]["body"]
            wamid = message_data["id"]

            whatsapp_api.mark_message_as_read(wamid, phone_number_id)

            # --- A CORREÇÃO PREMIADA ---
            # 1. Encontra ou cria a conversa.
            conversation = Conversation.query.filter_by(phone_number=from_number).first()
            if not conversation:
                conversation = Conversation(phone_number=from_number)
                db.session.add(conversation)
                # 2. SALVA IMEDIATAMENTE a conversa no banco de dados.
                # Isso garante que `conversation.id` tenha um valor para o próximo passo.
                db.session.commit()
            
            # 3. Agora, com um `conversation.id` garantido, cria e salva a mensagem do usuário.
            user_message = Message(conversation_id=conversation.id, message_type="user", content=msg_body)
            db.session.add(user_message)
            db.session.commit() # Commit da mensagem do usuário.

            # 4. Busca o histórico completo para a IA.
            history = [{"role": msg.message_type, "content": msg.content} for msg in conversation.messages]
            
            # 5. Processa a mensagem com a IA.
            ai_response = llm_service.process_message(msg_body, history)
            
            # 6. Salva a resposta da IA.
            ai_message = Message(conversation_id=conversation.id, message_type="assistant", content=ai_response)
            db.session.add(ai_message)
            db.session.commit() # Commit da mensagem da IA.
            
            # 7. Envia a resposta para o usuário.
            whatsapp_api.send_humanized_text_message(from_number, ai_response, phone_number_id)

        except Exception as e:
            logger.critical(f"ERRO CRÍTICO NO PROCESSAMENTO: {e}", exc_info=True)

@whatsapp_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    if (data.get("object") == "whatsapp_business_account" and
            data.get("entry") and data["entry"][0].get("changes") and
            data["entry"][0]["changes"][0].get("value") and
            data["entry"][0]["changes"][0]["value"]["messages") and
            data["entry"][0]["changes"][0]["value"]["messages"][0].get("type") == "text"):
        
        process_message_in_context(data)

    return jsonify(status="ok"), 200
