from flask import Blueprint, request, jsonify
from src.main import db # Importar db do main.py
from src.models.conversation import Conversation, Message, SchedulingInfo
from src.llm_service import CognoxLLMService
from src.whatsapp_api import whatsapp_api
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint("whatsapp", __name__)
llm_service = CognoxLLMService()

@whatsapp_bp.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Verificação do webhook do WhatsApp Business API
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == os.getenv("WHATSAPP_VERIFY_TOKEN"):
            logger.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            logger.warning("Token de verificação inválido")
            return jsonify({"status": "error", "message": "Token de verificação inválido"}), 403
    return jsonify({"status": "error", "message": "Parâmetros ausentes"}), 400

@whatsapp_bp.route("/webhook", methods=["POST"])
def webhook_post():
    """
    Recebe e processa mensagens do WhatsApp
    """
    data = request.get_json()
    logger.info(f"Webhook recebido: {json.dumps(data, indent=2)}")

    try:
        if "object" in data and "entry" in data:
            for entry in data["entry"]:
                for change in entry["changes"]:
                    if "value" in change and "messages" in change["value"]:
                        for message in change["value"]["messages"]:
                            phone_number_id = change["value"]["metadata"]["phone_number_id"]
                            from_number = message["from"]
                            msg_body = message["text"]["body"]
                            wamid = message["id"]

                            logger.info(f"Processando mensagem de {from_number}: {msg_body}")

                            # Marcar mensagem como lida
                            whatsapp_api.mark_message_as_read(wamid, phone_number_id)

                            # Encontrar ou criar conversa
                            conversation = Conversation.query.filter_by(phone_number=from_number).first()
                            if not conversation:
                                conversation = Conversation(phone_number=from_number)
                                db.session.add(conversation)
                                db.session.commit()
                                logger.info(f"Nova conversa criada para {from_number}")

                            # Salvar mensagem do usuário
                            new_message = Message(conversation_id=conversation.id, sender='user', content=msg_body)
                            db.session.add(new_message)
                            db.session.commit()

                            # Obter resposta do LLM
                            llm_response = llm_service.get_llm_response(conversation, msg_body)

                            # Salvar resposta do bot
                            bot_message = Message(conversation_id=conversation.id, sender='bot', content=llm_response)
                            db.session.add(bot_message)
                            db.session.commit()

                            # Enviar resposta via WhatsApp API
                            whatsapp_api.send_text_message(from_number, llm_response)

                            # Atualizar informações de agendamento se aplicável
                            if "agendamento" in llm_response.lower(): # Exemplo simples de gatilho
                                update_scheduling_info(conversation, llm_response)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem do WhatsApp: {str(e)}")
        # Retornar 200 OK mesmo em caso de erro para evitar reenvios do Meta
        return jsonify({"status": "error", "message": str(e)}), 200

def update_scheduling_info(conversation, llm_response):
    # Lógica para extrair e salvar informações de agendamento
    # Isso é um placeholder e precisaria de lógica de NLP mais avançada
    scheduling_info = SchedulingInfo.query.filter_by(conversation_id=conversation.id).first()
    if not scheduling_info:
        scheduling_info = SchedulingInfo(conversation_id=conversation.id)
        db.session.add(scheduling_info)
    
    # Exemplo: extrair nome e empresa (simplificado)
    # if "nome" in llm_response.lower():
    #     scheduling_info.name = "Nome Extraído"
    # if "empresa" in llm_response.lower():
    #     scheduling_info.company = "Empresa Extraída"
    
    # Adicione mais campos conforme necessário
    
    db.session.commit()
    logger.info(f"Informações de agendamento salvas/atualizadas para conversa {conversation.id}")

@whatsapp_bp.route("/conversations", methods=["GET"])
def get_conversations():
    conversations = Conversation.query.all()
    return jsonify([conv.to_dict() for conv in conversations])

@whatsapp_bp.route("/scheduling", methods=["GET"])
def get_scheduling_info():
    scheduling_records = SchedulingInfo.query.all()
    return jsonify([rec.to_dict() for rec in scheduling_records])

@whatsapp_bp.route("/health", methods=["GET"])
def health_check():
    """
    Endpoint para verificar a saúde da aplicação e configuração do WhatsApp
    """
    try:
        # Verifica se as variáveis de ambiente do WhatsApp estão configuradas
        whatsapp_configured = all([
            os.getenv("WHATSAPP_ACCESS_TOKEN"),
            os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
            os.getenv("WHATSAPP_VERIFY_TOKEN"),
            os.getenv("WHATSAPP_APP_SECRET")
        ])
        
        return jsonify({"status": "healthy", "whatsapp_configured": whatsapp_configured}), 200
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
