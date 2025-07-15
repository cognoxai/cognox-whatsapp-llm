import os
import requests
import logging
from typing import List, Dict
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

# O ID do modelo que vamos usar. É um modelo brasileiro, treinado para conversação.
MODEL_ID = "microsoft/DialogRPT-updown"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

class CognoxLLMService:
    def __init__(self ):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY não definida.")
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def get_greeting(self) -> str:
        try:
            tz = pytz.timezone('America/Sao_Paulo')
            now = datetime.now(tz)
            hour = now.hour
            if 5 <= hour < 12: return "Bom dia"
            elif 12 <= hour < 18: return "Boa tarde"
            else: return "Boa noite"
        except Exception as e:
            logger.error(f"Erro ao obter fuso horário: {e}")
            return "Olá"

    def query_huggingface(self, payload):
        """Função para fazer a requisição à API do Hugging Face."""
        response = requests.post(API_URL, headers=self.headers, json=payload)
        return response.json()

    def process_message(self, user_message: str, history: List[Dict[str, str]]) -> str:
        """
        Processa a mensagem do usuário usando um modelo de código aberto do Hugging Face.
        """
        try:
            is_first_message = len(history) <= 1
            if is_first_message:
                greeting = self.get_greeting()
                return f"{greeting}! Eu sou a Sofia, consultora de IA aqui na Cognox.ai.\nComo posso te ajudar hoje?"

            # Prepara o histórico para o modelo.
            # Este modelo específico funciona melhor com o histórico recente.
            past_user_inputs = [h['content'] for h in history if h['role'] == 'user']
            generated_responses = [h['content'] for h in history if h['role'] == 'assistant']

            # A API espera um formato específico.
            payload = {
                "inputs": {
                    "past_user_inputs": past_user_inputs,
                    "generated_responses": generated_responses,
                    "text": user_message
                },
                "parameters": {
                    "repetition_penalty": 1.03,
                    "temperature": 0.9
                }
            }
            
            output = self.query_huggingface(payload)
            
            if 'generated_text' in output:
                return output['generated_text'].strip()
            elif 'error' in output:
                logger.error(f"Erro da API do Hugging Face: {output['error']}")
                return "Desculpe, estou com uma pequena instabilidade. Poderia repetir sua mensagem?"
            else:
                return "Compreendo. Poderia me dar mais detalhes?"

        except Exception as e:
            logger.error(f"Erro ao processar mensagem com Hugging Face: {e}", exc_info=True)
            return "Desculpe, estou com uma instabilidade no meu sistema. Poderia repetir, por favor?"

llm_service = CognoxLLMService()
