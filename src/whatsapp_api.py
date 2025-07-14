import os
import requests
import logging
import hmac
import hashlib
import json

logger = logging.getLogger(__name__)

class WhatsAppAPI:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.api_url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
        self.app_secret = os.getenv("WHATSAPP_APP_SECRET" )

    def send_text_message(self, to_number: str, message_body: str) -> bool:
        """
        Envia uma mensagem de texto para um número de telefone via API do WhatsApp.
        """
        if not self.access_token or not self.phone_number_id:
            logger.error("Variáveis de ambiente do WhatsApp (ACCESS_TOKEN, PHONE_NUMBER_ID) não configuradas.")
            return False

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # --- JSON CORRIGIDO E MAIS ROBUSTO ---
        # Adicionado 'preview_url' para evitar problemas com links.
        # A estrutura está 100% alinhada com a documentação da Meta para mensagens de texto.
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_body
            }
        }

        try:
            logger.info(f"Attempting to send message to {to_number} with payload: {json.dumps(payload)}")
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            # Levanta um erro para status de resposta ruins (4xx ou 5xx)
            response.raise_for_status()
            
            logger.info(f"Message sent successfully to {to_number}. Response: {response.json()}")
            return True
            
        except requests.exceptions.RequestException as e:
            # Log detalhado do erro, incluindo a resposta da API se disponível
            error_response = e.response.text if e.response else "N/A"
            logger.error(f"Erro ao enviar mensagem para {to_number}: {e}. Resposta da API: {error_response}")
            return False

    def mark_message_as_read(self, message_id: str, phone_number_id: str) -> bool:
        """
        Marca uma mensagem como lida.
        """
        if not self.access_token:
            logger.warning("ACCESS_TOKEN não configurado. Pulando 'marcar como lida'.")
            return False
            
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
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Mensagem {message_id} marcada como lida com sucesso.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao marcar mensagem {message_id} como lida: {e}")
            return False

# Instância global da API
whatsapp_api = WhatsAppAPI()
