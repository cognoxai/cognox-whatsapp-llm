from flask import Blueprint, request, jsonify
from src.models.conversation import db, Conversation, Message, SchedulingInfo
from src.llm_service import CognoxLLMService
from src.whatsapp_api import whatsapp_api
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint('whatsapp', __name__)
llm_service = CognoxLLMService()

@whatsapp_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Verificação do webhook do WhatsApp Business API
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == whatsapp_api.verify_token:
            logger.info("Webhook verificado com sucesso")
            return challenge, 200
        else:
            logger.warning("Token de verificação inválido")
            return "Forbidden", 403
    
    return "Bad Request", 400

@whatsapp_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    """
    Processa mensagens recebidas do WhatsApp
    """
    try:
        # Validação de assinatura (se configurada)
        signature = request.headers.get('X-Hub-Signature-256', '')
        if signature and not whatsapp_api.validate_webhook_signature(request.get_data(as_text=True), signature):
            logger.warning("Assinatura do webhook inválida")
            return "Forbidden", 403
        
        data = request.get_json()
        logger.info(f"Webhook recebido: {json.dumps(data, indent=2)}")
        
        # Verifica se há mensagens na requisição
        if 'entry' in data:
            for entry in data['entry']:
                if 'changes' in entry:
                    for change in entry['changes']:
                        if change.get('field') == 'messages':
                            process_message(change['value'])
        
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
        if 'messages' not in message_data:
            return
        
        for message in message_data['messages']:
            phone_number = message['from']
            message_id = message['id']
            message_type = message.get('type', 'text')
            
            # Processa diferentes tipos de mensagem
            if message_type == 'text':
                message_text = message.get('text', {}).get('body', '')
            elif message_type == 'image':
                message_text = f"[Imagem recebida] {message.get('image', {}).get('caption', '')}"
            elif message_type == 'document':
                message_text = f"[Documento recebido] {message.get('document', {}).get('caption', '')}"
            elif message_type == 'audio':
                message_text = "[Áudio recebido]"
            elif message_type == 'video':
                message_text = f"[Vídeo recebido] {message.get('video', {}).get('caption', '')}"
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
                message_type='user',
                content=message_text
            )
            db.session.add(user_message)
            
            # Para mensagens não-texto, envia resposta padrão
            if message_type != 'text':
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
                message_type='assistant',
                content=ai_response,
                has_scheduling_intent=has_scheduling_intent
            )
            db.session.add(ai_message)
            
            # Se há intenção de agendamento, extrai informações
            if has_scheduling_intent:
                handle_scheduling_intent(conversation, get_conversation_history(conversation.id) + [
                    {'role': 'user', 'content': message_text},
                    {'role': 'assistant', 'content': ai_response}
                ])
            
            db.session.commit()
            
            # Envia resposta via WhatsApp
            success = whatsapp_api.send_text_message(phone_number, ai_response)
            if not success:
                logger.error(f"Falha ao enviar mensagem para {phone_number}")
            
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        db.session.rollback()

def get_or_create_conversation(phone_number):
    """
    Busca conversa existente ou cria uma nova
    """
    conversation = Conversation.query.filter_by(
        phone_number=phone_number,
        status='active'
    ).first()
    
    if not conversation:
        conversation = Conversation(phone_number=phone_number)
        db.session.add(conversation)
        db.session.flush()  # Para obter o ID
    
    return conversation

def get_conversation_history(conversation_id, limit=10):
    """
    Obtém histórico recente da conversa
    """
    messages = Message.query.filter_by(
        conversation_id=conversation_id
    ).order_by(Message.timestamp.desc()).limit(limit).all()
    
    history = []
    for message in reversed(messages):  # Ordem cronológica
        role = 'user' if message.message_type == 'user' else 'assistant'
        history.append({
            'role': role,
            'content': message.content
        })
    
    return history

def handle_scheduling_intent(conversation, conversation_history):
    """
    Processa intenção de agendamento
    """
    try:
        # Extrai informações de agendamento
        extracted_info = llm_service.extract_scheduling_info(conversation_history)
        
        # Busca ou cria registro de agendamento
        scheduling_info = SchedulingInfo.query.filter_by(
            conversation_id=conversation.id
        ).first()
        
        if not scheduling_info:
            scheduling_info = SchedulingInfo(conversation_id=conversation.id)
            db.session.add(scheduling_info)
        
        # Atualiza informações extraídas
        if 'nome' in extracted_info:
            scheduling_info.name = extracted_info['nome']
            conversation.user_name = extracted_info['nome']
        
        if 'empresa' in extracted_info:
            scheduling_info.company = extracted_info['empresa']
            conversation.company = extracted_info['empresa']
        
        if 'horario' in extracted_info:
            scheduling_info.preferred_time = extracted_info['horario']
        
        if 'necessidade' in extracted_info:
            scheduling_info.service_interest = extracted_info['necessidade']
        
        logger.info(f"Informações de agendamento atualizadas para conversa {conversation.id}")
        
    except Exception as e:
        logger.error(f"Erro ao processar agendamento: {str(e)}")

@whatsapp_bp.route('/send-message', methods=['POST'])
def send_message():
    """
    Endpoint para enviar mensagens manualmente (para testes ou administração)
    """
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        message = data.get('message')
        
        if not phone_number or not message:
            return jsonify({"error": "phone_number e message são obrigatórios"}), 400
        
        success = whatsapp_api.send_text_message(phone_number, message)
        
        if success:
            return jsonify({"status": "success", "message": "Mensagem enviada"}), 200
        else:
            return jsonify({"error": "Falha ao enviar mensagem"}), 500
            
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem manual: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@whatsapp_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """
    Endpoint para listar conversas (para administração)
    """
    try:
        conversations = Conversation.query.order_by(Conversation.updated_at.desc()).all()
        return jsonify([conv.to_dict() for conv in conversations]), 200
    except Exception as e:
        logger.error(f"Erro ao buscar conversas: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@whatsapp_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """
    Endpoint para obter mensagens de uma conversa específica
    """
    try:
        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.timestamp.asc()).all()
        
        return jsonify([msg.to_dict() for msg in messages]), 200
    except Exception as e:
        logger.error(f"Erro ao buscar mensagens: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@whatsapp_bp.route('/scheduling', methods=['GET'])
def get_scheduling_info():
    """
    Endpoint para listar informações de agendamento
    """
    try:
        scheduling_infos = SchedulingInfo.query.order_by(SchedulingInfo.created_at.desc()).all()
        return jsonify([info.to_dict() for info in scheduling_infos]), 200
    except Exception as e:
        logger.error(f"Erro ao buscar agendamentos: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@whatsapp_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint de verificação de saúde do serviço
    """
    return jsonify({
        "status": "healthy",
        "service": "Cognox WhatsApp LLM",
        "whatsapp_configured": bool(whatsapp_api.access_token and whatsapp_api.phone_number_id)
    }), 200
