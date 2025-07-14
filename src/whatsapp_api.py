import os
import requests
import logging
import json
import time
import random
import re

logger = logging.getLogger(__name__)

class WhatsAppAPI:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.base_url = "https://graph.facebook.com/v19.0"

    def _send_single_message(self, to_number: str, message_body: str, phone_number_id: str ) -> bool:
        """Função interna para enviar uma única bolha de mensagem."""
        if not self.access_token:
            logger.error("WHATSAPP_ACCESS_TOKEN não configurado.")
            return False

        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": message_body}}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem para {to_number}: {e}. Resposta: {e.response.text if e.response else 'N/A'}")
            return False

    def send_humanized_text_message(self, to_number: str, full_message: str, phone_number_id: str) -> bool:
        """
        Envia uma mensagem de texto de forma humanizada:
        1. Quebra a mensagem em parágrafos/frases.
        2. Envia cada parte em uma bolha separada.
        3. Adiciona pausas aleatórias entre as mensagens.
        """
        # Divide a mensagem por quebras de linha. Respeita os parágrafos.
        # Também divide por frases que terminam com . ? ! para maior naturalidade.
        message_bubbles = [p.strip() for p in re.split(r'\n|(?<=[.?!])\s+', full_message) if p.strip()]

        if not message_bubbles:
            logger.warning("Tentativa de enviar mensagem vazia.")
            return False

        total_success = True
        for i, bubble in enumerate(message_bubbles):
            # Simula o tempo de digitação antes de enviar a bolha.
            # Pausas mais curtas para as primeiras bolhas, um pouco mais longas depois.
            typing_delay = random.uniform(1.5, 3.0) if i > 0 else random.uniform(1.0, 2.0)
            time.sleep(typing_delay)

            success = self._send_single_message(to_number, bubble, phone_number_id)
            if not success:
                total_success = False
                # Se uma bolha falhar, paramos para não inundar o usuário.
                break
        
        logger.info(f"Envio humanizado para {to_number} concluído.")
        return total_success

    def mark_message_as_read(self, message_id: str, phone_number_id: str) -> bool:
        """Marca uma mensagem como lida."""
        # (Esta função permanece a mesma)
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

whatsapp_api = WhatsAppAPI()
