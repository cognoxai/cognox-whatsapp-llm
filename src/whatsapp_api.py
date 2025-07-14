import os
import requests
import logging
import json
import time
import random

logger = logging.getLogger(__name__)

class WhatsAppAPI:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.base_url = "https://graph.facebook.com/v19.0"

    def _send_request(self, method: str, url: str, payload: dict ) -> bool:
        """Função genérica para enviar requisições à API."""
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        try:
            response = requests.request(method, url, headers=headers, json=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}. Resposta: {e.response.text if e.response else 'N/A'}")
            return False

    def _toggle_typing_indicator(self, to_number: str, phone_number_id: str, is_typing: bool):
        """Ativa ou desativa o indicador de 'digitando...'."""
        url = f"{self.base_url}/{phone_number_id}/messages"
        payload = {"messaging_product": "whatsapp", "to": to_number, "action": "typing_on" if is_typing else "typing_off"}
        self._send_request("POST", url, payload)

    def send_humanized_text_message(self, to_number: str, full_message: str, phone_number_id: str) -> bool:
        """
        Orquestra o envio humanizado completo:
        1. Ativa o 'digitando...'.
        2. Simula o tempo de pensamento.
        3. Envia as bolhas de mensagem com pausas.
        4. Desativa o 'digitando...'.
        """
        message_bubbles = [p.strip() for p in full_message.split('\n') if p.strip()]
        if not message_bubbles:
            return False

        # Ativa o 'digitando...'
        self._toggle_typing_indicator(to_number, phone_number_id, is_typing=True)

        # Simula o tempo de pensamento/digitação inicial.
        # Proporcional ao número de bolhas que serão enviadas.
        initial_wait = min(2.0 + len(message_bubbles) * 1.5, 8.0) # Espera no máximo 8 segundos
        time.sleep(random.uniform(initial_wait * 0.8, initial_wait * 1.2))

        total_success = True
        for bubble in message_bubbles:
            success = self._send_request("POST", f"{self.base_url}/{phone_number_id}/messages", {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": bubble}
            })
            if not success:
                total_success = False
                break
            # Pausa entre as bolhas
            time.sleep(random.uniform(1.5, 3.5))
        
        # Desativa o 'digitando...'
        self._toggle_typing_indicator(to_number, phone_number_id, is_typing=False)
        
        logger.info(f"Envio humanizado para {to_number} concluído.")
        return total_success

    def mark_message_as_read(self, message_id: str, phone_number_id: str) -> bool:
        """Marca uma mensagem como lida."""
        url = f"{self.base_url}/{phone_number_id}/messages"
        payload = {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}
        return self._send_request("POST", url, payload)

whatsapp_api = WhatsAppAPI()
