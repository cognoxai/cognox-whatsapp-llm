import os
import calendly
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CalendlyService:
    def __init__(self):
        self.api_key = os.getenv("CALENDLY_API_KEY")
        if not self.api_key:
            logger.warning("A variável de ambiente CALENDLY_API_KEY não foi definida. O serviço de agendamento estará inativo.")
            self.client = None
        else:
            # A FORMA CORRETA DE INICIAR O CLIENTE
            self.client = calendly.Calendly(self.api_key)

    def get_available_slots(self, event_type_link: str, days_in_future: int = 7) -> list:
        """
        Busca os próximos horários disponíveis para um tipo de evento específico.
        """
        if not self.client:
            return []

        try:
            # 1. Obter o URI do usuário logado
            user_profile = self.client.get_current_user()
            user_uri = user_profile['resource']['uri']

            # 2. Obter todos os tipos de evento do usuário
            # A CHAMADA CORRETA DA API
            event_types_data = self.client.get_event_types(user=user_uri)
            event_types = event_types_data.get('collection', [])

            # 3. Encontrar o URI do evento específico pelo link amigável
            target_event_uri = None
            for event in event_types:
                if event_type_link.endswith(event.get('slug', '')):
                    target_event_uri = event.get('uri')
                    break
            
            if not target_event_uri:
                logger.error(f"Não foi possível encontrar o tipo de evento para o link: {event_type_link}")
                return []

            # 4. Buscar os horários disponíveis (availability)
            now = datetime.utcnow()
            end_time = now + timedelta(days=days_in_future)
            
            # A CHAMADA CORRETA DA API
            availability_data = self.client.get_event_type_availability(
                target_event_uri,
                start_time=now.isoformat() + "Z",
                end_time=end_time.isoformat() + "Z"
            )
            availability_slots = availability_data.get('collection', [])

            # 5. Formatar os horários para serem amigáveis para o usuário
            formatted_slots = []
            for slot in availability_slots[:3]: # Pega apenas os 3 primeiros horários
                start_time_str = slot.get('start_time')
                if not start_time_str:
                    continue
                
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                # Converte para o fuso horário local do servidor (Render usa UTC, o que é bom)
                local_time = start_time.astimezone(tz=None) 
                
                if local_time.date() == now.date():
                    day_str = "Hoje"
                elif local_time.date() == (now + timedelta(days=1)).date():
                    day_str = "Amanhã"
                else:
                    # Formato para outros dias da semana
                    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                    day_str = dias[local_time.weekday()]
                
                time_str = local_time.strftime('%H:%M')
                formatted_slots.append(f"{day_str}, às {time_str}")

            return formatted_slots

        except Exception as e:
            logger.error(f"Erro ao buscar horários no Calendly: {e}", exc_info=True)
            return []

# Instância única do serviço
calendly_service = CalendlyService()
