from flask import Blueprint, request, jsonify
from src.models.conversation import db, Conversation, Message, SchedulingInfo
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
        if mode == "subscribe" and token == whatsapp_api.verify_token:
            logger.info("Webhook verificado com sucesso")
            return challenge, 200
        else:
            logger.warning("Token de verificação inválido")
            return "Forbidden", 403
    
    return "Bad Request", 400

@whatsapp_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    """
    Processa mensagens recebidas do WhatsApp
    """
    try:
        # Validação de assinatura (se configurada)
        signature = request.headers.get("X-Hub-Signature-256", "")
        if signature and not whatsapp_api.validate_webhook_signature(request.get_data(as_text=True), signature):
            logger.warning("Assinatura do webhook inválida")
            return "Forbidden", 403
        
        data = request.get_json()
        logger.info(f"Webhook recebido: {json.dumps(data, indent=2)}")
        
        # Verifica se há mensagens na requisição
        if "entry" in data:
            for entry in data["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages":
                            process_message(change["value"])
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def process_message(message_data):
    """
    Processa uma mensagem individual do WhatsApp
    """
    try:
        # Extrai informações da mensagem
        if "messages" not in message_data:
            return
        
        for message in message_data["messages"]:
            phone_number = message["from"]
            message_id = message["id"]
            message_type = message.get("type", "text")
            
            # Processa diferentes tipos de mensagem
            if message_type == "text":
                message_text = message.get("text", {}).get("body", "")
            elif message_type == "image":
                message_text = f"[Imagem recebida] {message.get("image", {}).get("caption", "")}"
            elif message_type == "document":
                message_text = f"[Documento recebido] {message.get("document", {}).get("caption", "")}"
            elif message_type == "audio":
                message_text = "[Áudio recebido]"
            elif message_type == "video":
                message_text = f"[Vídeo recebido] {message.get("video", {}).get("caption", "")}"
            else:
                message_text = f"[Mensagem do tipo {message_type} recebida]"
            
            logger.info(f"Processando mensagem de {phone_number}: {message_text}")
            
            # Marca mensagem como lida
            whatsapp_api.mark_message_as_read(message_id)
            
            # Busca ou cria conversa
            conversation = get_or_create_conversation(phone_number)
            
            # Salva mensagem do usuário
            user_message = Message(
                conversation_id=conversation.id,
                message_type="user",
                content=message_text
            )
            db.session.add(user_message)
            
            # Para mensagens não-texto, envia resposta padrão
            if message_type != "text":
                ai_response = "Obrigado pela mensagem! No momento, posso responder apenas a mensagens de texto. Como posso ajudar você com informações sobre a Cognox.ai?"
                has_scheduling_intent = False
            else:
                # Obtém histórico da conversa
                conversation_history = get_conversation_history(conversation.id)
                
                # Processa com LLM
                ai_response, has_scheduling_intent = llm_service.process_message(
                    message_text, 
                    conversation_history
                )
            
            # Salva resposta da IA
            ai_message = Message(
                conversation_id=conversation.id,
                message_type="assistant",
                content=ai_response,
                has_scheduling_intent=has_scheduling_intent
            )
            db.session.add(ai_message)
            
            # Se há intenção de agendamento, extrai informações
            if has_scheduling_intent:
                handle_scheduling_intent(conversation, get_conversation_history(conversation.id) + [
                    {"role": "user", "content": message_text},
                    {"role": "assistant", "content": ai_response}
                ])
            
            db.session.commit()
            
            # Envia resposta via WhatsApp
            success = whatsapp_api.send_text_message(phone_number, ai_response)
            if not success:
                logger.error(f"Falha ao enviar mensagem para {phone_number}")

    except Exception as e:
        logger.error(f"Erro ao processar mensagem do WhatsApp: {str(e)}")

def get_or_create_conversation(phone_number):
    """
    Busca uma conversa existente ou cria uma nova
    """
    conversation = Conversation.query.filter_by(phone_number=phone_number).first()
    if not conversation:
        conversation = Conversation(phone_number=phone_number)
        db.session.add(conversation)
        db.session.commit()
        logger.info(f"Nova conversa criada para {phone_number}")
    return conversation

def get_conversation_history(conversation_id):
    """
    Obtém o histórico de mensagens de uma conversa
    """
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
    history = []
    for msg in messages:
        history.append({"role": msg.message_type, "content": msg.content})
    return history

def handle_scheduling_intent(conversation, full_conversation_history):
    """
    Lida com a intenção de agendamento, extraindo informações e salvando
    """
    extracted_info = llm_service.extract_scheduling_info(full_conversation_history)
    
    scheduling_info = SchedulingInfo.query.filter_by(conversation_id=conversation.id).first()
    if not scheduling_info:
        scheduling_info = SchedulingInfo(conversation_id=conversation.id)
        db.session.add(scheduling_info)
    
    scheduling_info.name = extracted_info.get("nome", scheduling_info.name)
    scheduling_info.company = extracted_info.get("empresa", scheduling_info.company)
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
