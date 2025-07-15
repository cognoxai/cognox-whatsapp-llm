import os
import requests
import logging
import time
import random
from typing import List

logger = logging.getLogger(__name__)

class WhatsAppAPI:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("WHATSAPP_ACCESS_TOKEN não definida.")
        self.base_url = "https://graph.facebook.com/v19.0"

    def send_request(self, method, endpoint, data=None ):
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.request(method, url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}. Resposta: {e.response.text if e.response else 'N/A'}")
            return None

    def mark_message_as_read(self, wamid, phone_number_id):
        data = {"messaging_product": "whatsapp", "status": "read", "message_id": wamid}
        return self.send_request("POST", f"{phone_number_id}/messages", data)

    def send_typing_indicator(self, recipient_id, phone_number_id, stop=False):
        action = "typing_off" if stop else "typing_on"
        data = {"recipient_type": "individual", "to": recipient_id, "messaging_product": "whatsapp", "type": "typing", "action": action}
        # Esta chamada não é oficial e pode não funcionar, mas é a tentativa padrão.
        # A lógica principal de delay funcionará independentemente.
        self.send_request("POST", f"{phone_number_id}/messages", data)

    def send_humanized_text_message(self, recipient_id, text, phone_number_id):
        """
        Envia uma mensagem de texto simulando o comportamento humano.
        A SUA LÓGICA FOI IMPLEMENTADA AQUI.
        """
        messages = text.split('\n')
        
        # Simula o "digitando..." por um tempo proporcional ao tamanho da resposta.
        typing_duration = min(2 + len(messages) * 1.5, 8) # Duração entre 3.5s e 8s
        self.send_typing_indicator(recipient_id, phone_number_id)
        time.sleep(typing_duration)
        self.send_typing_indicator(recipient_id, phone_number_id, stop=True)

        for i, msg in enumerate(messages):
            if not msg.strip(): continue
            
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient_id,
                "type": "text",
                "text": {"preview_url": False, "body": msg.strip()},
            }
            if self.send_request("POST", f"{phone_number_id}/messages", data):
                logger.info(f"Bolha de mensagem enviada com sucesso para {recipient_id}.")
            else:
                logger.error(f"Falha ao enviar bolha de mensagem para {recipient_id}.")
                break 

            # Pausa entre as bolhas, exceto na última.
            if i < len(messages) - 1:
                pause_duration = random.uniform(1.5, 3.0) # Pausa natural entre 1.5s e 3s
                time.sleep(pause_duration)

whatsapp_api = WhatsAppAPI()
