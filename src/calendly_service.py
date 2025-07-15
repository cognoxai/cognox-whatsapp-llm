import os
import logging
from calendly import Calendly
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CalendlyService:
    def __init__(self):
        self.api_key = os.getenv("CALENDLY_API_KEY")
        self.user_uri = os.getenv("CALENDLY_USER_URI")
        if not self.api_key or not self.user_uri:
            logger.warning("CALENDLY_API_KEY ou CALENDLY_USER_URI não definidas. O serviço de agendamento estará inativo.")
            self.client = None
        else:
            self.client = Calendly(self.api_key)

    def get_available_slots(self) -> List[str]:
        if not self.client:
            return []
        try:
            user = self.client.get_user(self.user_uri)
            event_types = self.client.get_event_types(user_uri=user['resource']['uri'])
            
            if not event_types:
                return []

            # Pega o primeiro tipo de evento ativo
            event_type_uri = next((et['uri'] for et in event_types if et.get('active')), None)
            if not event_type_uri:
                return []

            now = datetime.utcnow()
            start_time = now.isoformat() + "Z"
            end_time = (now + timedelta(days=7)).isoformat() + "Z"

            availability = self.client.get_event_type_availability(
                event_type_uri, start_time=start_time, end_time=end_time
            )
            
            slots = [slot['start_time'] for slot in availability]
            return slots[:5] # Retorna apenas os 5 primeiros horários
        except Exception as e:
            logger.error(f"Erro ao buscar horários no Calendly: {e}", exc_info=True)
            return []

calendly_service = CalendlyService()
