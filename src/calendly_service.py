import os
from calendly.api import API
from datetime import datetime, timedelta

class CalendlyService:
    def __init__(self ):
        self.api_key = os.getenv("CALENDLY_API_KEY")
        if not self.api_key:
            raise ValueError("A variável de ambiente CALENDLY_API_KEY não foi definida.")
        self.client = API(self.api_key)

    def get_event_type_uri(self, event_link: str) -> str:
        """Obtém o URI do tipo de evento a partir do link amigável."""
        try:
            # O SDK não busca por link, então extraímos o UUID da página do evento.
            # Esta é uma simplificação; uma implementação robusta pode precisar de web scraping
            # ou de uma busca mais complexa. Por agora, vamos assumir que o URI é conhecido.
            # Para obter o URI: use a API para listar seus event_types e copie o URI do evento desejado.
            # Ex: 'https://api.calendly.com/event_types/ABCDEFGHIJKLMNOP'
            # Esta parte precisará ser preenchida com o URI real.
            
            # Placeholder - esta URI precisa ser a URI real do seu evento.
            # Você pode encontrá-la fazendo uma chamada à API para listar seus tipos de evento.
            user_profile = self.client.get_current_user( )
            user_uri = user_profile['resource']['uri']
            event_types = self.client.get_event_types(user=user_uri)
            
            for event in event_types:
                if event_link.endswith(event['resource']['slug']):
                    return event['resource']['uri']
            
            return None

        except Exception as e:
            print(f"Erro ao buscar tipo de evento no Calendly: {e}")
            return None

# Instância única do serviço
calendly_service = CalendlyService()
