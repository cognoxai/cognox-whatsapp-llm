import os
import requests
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)

class WhatsAppAPI:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
        self.app_secret = os.getenv("WHATSAPP_APP_SECRET")
        self.api_url = "https://graph.facebook.com/v19.0/"

    def send_text_message(self, to_number, message_body ):
        if not self.access_token or not self.phone_number_id:
            logger.warning("Variáveis de ambiente do WhatsApp não configuradas. Simulação de envio de mensagem.")
            logger.info(f"[SIMULAÇÃO] Enviando para {to_number}: {message_body}")
            return True

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message_body}
        }
        url = f"{self.api_url}{self.phone_number_id}/messages"

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Levanta um erro para status de resposta ruins (4xx ou 5xx)
            logger.info(f"Mensagem enviada com sucesso para {to_number}. Resposta: {response.json()}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem para {to_number}: {e}. Resposta: {response.text if response else 'N/A'}")
            return False

    def mark_message_as_read(self, message_id):
        if not self.access_token or not self.phone_number_id:
            logger.warning("Variáveis de ambiente do WhatsApp não configuradas. Simulação de marcar como lida.")
            logger.info(f"[SIMULAÇÃO] Marcando mensagem {message_id} como lida.")
            return True

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        url = f"{self.api_url}{self.phone_number_id}/messages"

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(f"Mensagem {message_id} marcada como lida. Resposta: {response.json()}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao marcar mensagem {message_id} como lida: {e}. Resposta: {response.text if response else 'N/A'}")
            return False

    def validate_webhook_signature(self, payload, signature):
        if not self.app_secret:
            logger.warning("WHATSAPP_APP_SECRET não configurado. Pulando validação de assinatura do webhook.")
            return True

        try:
            expected_signature = "sha256=" + hmac.new(
                self.app_secret.encode("utf-8"),
                payload.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Erro ao validar assinatura do webhook: {str(e)}")
            return False

    def download_media(self, media_url, save_path):
        if not self.access_token:
            logger.info(f"[SIMULAÇÃO] Baixando mídia de {media_url} para {save_path}")
            return True
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.get(media_url, headers=headers)
            response.raise_for_status()
            
            with open(save_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Mídia baixada com sucesso: {save_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao baixar mídia: {str(e)}")
            return False
        except IOError as e:
            logger.error(f"Erro ao salvar arquivo: {str(e)}")
            return False

# Instância global da API
whatsapp_api = WhatsAppAPI()
