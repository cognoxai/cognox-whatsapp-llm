import os
import requests
import logging
import json

logger = logging.getLogger(__name__)

class WhatsAppAPI:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        # A URL base é mais limpa e menos propensa a erros.
        self.base_url = "https://graph.facebook.com/v19.0"

    def send_text_message(self, to_number: str, message_body: str, phone_number_id: str ) -> bool:
        """Envia uma mensagem de texto a partir de um ID de número de telefone específico."""
        if not self.access_token:
            logger.error("WHATSAPP_ACCESS_TOKEN não configurado.")
            return False

        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": message_body}}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Mensagem enviada com sucesso para {to_number}.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem para {to_number}: {e}. Resposta: {e.response.text if e.response else 'N/A'}")
            return False

    def mark_message_as_read(self, message_id: str, phone_number_id: str) -> bool:
        """Marca uma mensagem como lida usando o ID do número de telefone que a recebeu."""
        if not self.access_token:
            logger.error("WHATSAPP_ACCESS_TOKEN não configurado.")
            return False

        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Mensagem {message_id} marcada como lida com sucesso.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao marcar mensagem {message_id} como lida: {e}. Resposta: {e.response.text if e.response else 'N/A'}")
            return False

# Instância única para ser usada em toda a aplicação.
whatsapp_api = WhatsAppAPI()
