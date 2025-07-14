from flask import Blueprint, request, jsonify
from src.models.conversation import db, Conversation, Message, SchedulingInfo
from src.scheduling_service import scheduling_service
from src.whatsapp_api import whatsapp_api
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

scheduling_bp = Blueprint('scheduling', __name__)

@scheduling_bp.route('/available-slots', methods=['GET'])
def get_available_slots():
    """
    Endpoint para obter horários disponíveis
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        duration = int(request.args.get('duration', 60))
        
        if not start_date or not end_date:
            # Define datas padrão (próximos 7 dias)
            today = datetime.now()
            start_date = today.strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        
        slots = scheduling_service.get_available_slots(start_date, end_date, duration)
        
        return jsonify({
            'status': 'success',
            'available_slots': slots,
            'total_slots': len(slots)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar horários disponíveis: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@scheduling_bp.route('/schedule', methods=['POST'])
def schedule_meeting():
    """
    Endpoint para agendar uma reunião
    """
    try:
        data = request.get_json()
        
        # Validação dos dados obrigatórios
        required_fields = ['name', 'phone_number']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Busca conversa existente
        conversation = Conversation.query.filter_by(
            phone_number=data['phone_number']
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversa não encontrada'}), 404
        
        # Busca ou cria informações de agendamento
        scheduling_info = SchedulingInfo.query.filter_by(
            conversation_id=conversation.id
        ).first()
        
        if not scheduling_info:
            scheduling_info = SchedulingInfo(conversation_id=conversation.id)
            db.session.add(scheduling_info)
        
        # Atualiza informações
        scheduling_info.name = data['name']
        scheduling_info.company = data.get('company', '')
        scheduling_info.preferred_time = data.get('preferred_time', '')
        scheduling_info.service_interest = data.get('service_interest', '')
        scheduling_info.additional_info = data.get('additional_info', '')
        
        # Tenta agendar
        success, result = scheduling_service.schedule_meeting({
            'name': data['name'],
            'company': data.get('company', ''),
            'preferred_time': data.get('preferred_time', ''),
            'service_interest': data.get('service_interest', ''),
            'phone_number': data['phone_number']
        })
        
        if success:
            scheduling_info.status = 'confirmed'
            
            # Envia confirmação via WhatsApp
            confirmation_message = f"""✅ Reunião agendada com sucesso!

📝 Nome: {data['name']}
🏢 Empresa: {data.get('company', 'Não informado')}
🎯 Interesse: {data.get('service_interest', 'Não especificado')}

🔗 Link para agendamento: {result}

Em breve você receberá uma confirmação por email com todos os detalhes da reunião.

Obrigado por escolher a Cognox.ai! 🚀"""
            
            whatsapp_api.send_text_message(data['phone_number'], confirmation_message)
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Reunião agendada com sucesso',
                'scheduling_link': result,
                'scheduling_id': scheduling_info.id
            }), 200
        else:
            scheduling_info.status = 'failed'
            db.session.commit()
            
            return jsonify({
                'status': 'error',
                'message': f'Erro ao agendar: {result}'
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao agendar reunião: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@scheduling_bp.route('/parse-time', methods=['POST'])
def parse_time_preference():
    """
    Endpoint para analisar preferência de horário em texto natural
    """
    try:
        data = request.get_json()
        time_text = data.get('time_text', '')
        
        if not time_text:
            return jsonify({'error': 'time_text é obrigatório'}), 400
        
        parsed_time = scheduling_service.parse_time_preference(time_text)
        
        return jsonify({
            'status': 'success',
            'original_text': time_text,
            'parsed_time': parsed_time
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao analisar horário: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@scheduling_bp.route('/confirm/<int:scheduling_id>', methods=['POST'])
def confirm_scheduling(scheduling_id):
    """
    Endpoint para confirmar um agendamento
    """
    try:
        scheduling_info = SchedulingInfo.query.get(scheduling_id)
        
        if not scheduling_info:
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        
        scheduling_info.status = 'confirmed'
        db.session.commit()
        
        # Envia confirmação via WhatsApp
        conversation = scheduling_info.conversation
        if conversation:
            confirmation_message = f"""✅ Agendamento confirmado!

Olá {scheduling_info.name}! Sua reunião foi confirmada com sucesso.

📅 Em breve você receberá os detalhes finais por email.

Estamos ansiosos para conversar com você sobre como a Cognox.ai pode transformar seu negócio! 🚀"""
            
            whatsapp_api.send_text_message(conversation.phone_number, confirmation_message)
        
        return jsonify({
            'status': 'success',
            'message': 'Agendamento confirmado'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao confirmar agendamento: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@scheduling_bp.route('/cancel/<int:scheduling_id>', methods=['POST'])
def cancel_scheduling(scheduling_id):
    """
    Endpoint para cancelar um agendamento
    """
    try:
        scheduling_info = SchedulingInfo.query.get(scheduling_id)
        
        if not scheduling_info:
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        
        scheduling_info.status = 'cancelled'
        db.session.commit()
        
        # Envia notificação via WhatsApp
        conversation = scheduling_info.conversation
        if conversation:
            cancellation_message = f"""❌ Agendamento cancelado

Olá {scheduling_info.name}, seu agendamento foi cancelado conforme solicitado.

Se desejar reagendar, é só me enviar uma mensagem! Estou aqui para ajudar.

Obrigado pela compreensão! 😊"""
            
            whatsapp_api.send_text_message(conversation.phone_number, cancellation_message)
        
        return jsonify({
            'status': 'success',
            'message': 'Agendamento cancelado'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao cancelar agendamento: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@scheduling_bp.route('/reminders', methods=['POST'])
def send_reminders():
    """
    Endpoint para enviar lembretes de reuniões
    """
    try:
        # Busca agendamentos confirmados para os próximos dias
        from datetime import datetime, timedelta
        
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        # Busca agendamentos que precisam de lembrete
        # (implementação simplificada - em produção seria mais sofisticada)
        confirmed_schedulings = SchedulingInfo.query.filter_by(status='confirmed').all()
        
        reminders_sent = 0
        
        for scheduling in confirmed_schedulings:
            conversation = scheduling.conversation
            if conversation and scheduling.preferred_time:
                # Verifica se precisa enviar lembrete (lógica simplificada)
                reminder_message = f"""🔔 Lembrete de Reunião

Olá {scheduling.name}! Este é um lembrete sobre nossa reunião agendada.

📅 Horário preferido: {scheduling.preferred_time}
🎯 Assunto: {scheduling.service_interest or 'Soluções de IA'}

Estamos ansiosos para nossa conversa! Se precisar reagendar, é só me avisar.

Até breve! 🚀"""
                
                success = whatsapp_api.send_text_message(conversation.phone_number, reminder_message)
                if success:
                    reminders_sent += 1
        
        return jsonify({
            'status': 'success',
            'reminders_sent': reminders_sent
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao enviar lembretes: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@scheduling_bp.route('/stats', methods=['GET'])
def get_scheduling_stats():
    """
    Endpoint para obter estatísticas de agendamento
    """
    try:
        total_schedulings = SchedulingInfo.query.count()
        confirmed_schedulings = SchedulingInfo.query.filter_by(status='confirmed').count()
        pending_schedulings = SchedulingInfo.query.filter_by(status='pending').count()
        cancelled_schedulings = SchedulingInfo.query.filter_by(status='cancelled').count()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total': total_schedulings,
                'confirmed': confirmed_schedulings,
                'pending': pending_schedulings,
                'cancelled': cancelled_schedulings,
                'conversion_rate': (confirmed_schedulings / total_schedulings * 100) if total_schedulings > 0 else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
