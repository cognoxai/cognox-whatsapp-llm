import os
import requests
import logging
import time
import random

logger = logging.getLogger(__name__)

class WhatsAppAPI:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.base_url = "https://graph.facebook.com/v19.0"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _send_request(self, payload: dict, phone_number_id: str ) -> bool:
        url = f"{self.base_url}/{phone_number_id}/messages"
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}. Resposta: {e.response.text if e.response else 'N/A'}")
            return False

    def _toggle_typing_indicator(self, to_number: str, phone_number_id: str, is_typing: bool):
        payload = {"messaging_product": "whatsapp", "to": to_number, "action": "typing_on" if is_typing else "typing_off"}
        self._send_request(payload, phone_number_id)

    def send_humanized_text_message(self, to_number: str, full_message: str, phone_number_id: str):
        message_bubbles = [p.strip() for p in full_message.split('\n') if p.strip()]
        if not message_bubbles: return

        self._toggle_typing_indicator(to_number, phone_number_id, is_typing=True)
        initial_wait = min(1.5 + len(message_bubbles) * 1.0, 6.0)
        time.sleep(random.uniform(initial_wait * 0.8, initial_wait * 1.2))

        for bubble in message_bubbles:
            payload = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": bubble}}
            self._send_request(payload, phone_number_id)
            time.sleep(random.uniform(1.5, 3.0))
        
        self._toggle_typing_indicator(to_number, phone_number_id, is_typing=False)

    def mark_message_as_read(self, message_id: str, phone_number_id: str):
        payload = {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}
        self._send_request(payload, phone_number_id)

whatsapp_api = WhatsAppAPI()
