import os
import requests
import logging
import json

logger = logging.getLogger(__name__)

class WhatsAppAPI:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.base_url = "https://graph.facebook.com/v19.0"

    def send_text_message(self, to_number: str, message_body: str ) -> bool:
        if not self.access_token or not self.phone_number_id:
            logger.error("Variáveis de ambiente do WhatsApp não configuradas.")
            return False

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message_body}
        }

        try:
            logger.info(f"Attempting to send message to {to_number} via URL: {url}")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Message sent successfully to {to_number}.")
            return True
        except requests.exceptions.RequestException as e:
            error_response = e.response.text if e.response else "N/A"
            logger.error(f"Erro ao enviar mensagem para {to_number}: {e}. Resposta da API: {error_response}")
            return False

    def mark_message_as_read(self, message_id: str) -> bool:
        if not self.access_token:
            logger.warning("ACCESS_TOKEN não configurado. Pulando 'marcar como lida'.")
            return False
            
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            logger.info(f"Attempting to mark message {message_id} as read.")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Mensagem {message_id} marcada como lida com sucesso.")
            return True
        except requests.exceptions.RequestException as e:
            error_response = e.response.text if e.response else "N/A"
            logger.error(f"Erro ao marcar mensagem {message_id} como lida: {e}. Resposta da API: {error_response}")
            return False

# Instância global da API
whatsapp_api = WhatsAppAPI()
