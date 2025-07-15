import os
import requests
import logging
import time
from typing import List, Dict
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

# MUDANÇA PARA O MODELO QUE VOCÊ ESCOLHEU: GPT2
MODEL_ID = "gpt2"
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

    def query_huggingface_with_retry(self, payload, retries=3, delay=15):
        """
        Tenta fazer a requisição à API, com novas tentativas se o modelo estiver carregando.
        """
        for i in range(retries):
            try:
                response = requests.post(API_URL, headers=self.headers, json=payload)
                
                if response.status_code == 503:
                    estimated_time = response.json().get("estimated_time", delay)
                    logger.info(f"Modelo BlenderBot está carregando. Tentando novamente em {estimated_time} segundos...")
                    time.sleep(estimated_time)
                    continue

                response.raise_for_status()
                return response.json()

            except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as e:
                logger.warning(f"Tentativa {i+1}/{retries} falhou: {e}. Tentando novamente em {delay} segundos...")
                time.sleep(delay)
        
        logger.error("Todas as tentativas de contatar a API do Hugging Face falharam.")
        return {"error": "Falha ao contatar a API após múltiplas tentativas."}

    def process_message(self, user_message: str, history: List[Dict[str, str]]) -> str:
        """
        Processa a mensagem do usuário usando o BlenderBot.
        """
        try:
            is_first_message = len(history) <= 1
            if is_first_message:
                greeting = self.get_greeting()
                return f"{greeting}! Eu sou a Sofia, consultora de IA aqui na Cognox.ai.\nComo posso te ajudar hoje?"

            # Prepara o histórico para o BlenderBot
            past_user_inputs = [h['content'] for h in history if h['role'] == 'user']
            generated_responses = [h['content'] for h in history if h['role'] == 'assistant']

            payload = {
                "inputs": {
                    "past_user_inputs": past_user_inputs,
                    "generated_responses": generated_responses,
                    "text": user_message,
                },
                "parameters": {
                    "repetition_penalty": 1.3,
                    "temperature": 0.85,
                    "min_length": 8, 
                    "max_length": 60,
                },
                "options": {
                    "wait_for_model": True # Pede para a API esperar o modelo carregar
                }
            }
            
            output = self.query_huggingface_with_retry(payload)
            
            if 'generated_text' in output:
                return output['generated_text'].strip()
            elif 'error' in output:
                logger.error(f"Erro da API do Hugging Face: {output['error']}")
                return "Desculpe, estou com uma pequena instabilidade. Poderia repetir sua mensagem?"
            else:
                logger.warning(f"Resposta inesperada da API: {output}")
                return "Compreendo. Poderia me dar mais detalhes?"

        except Exception as e:
            logger.error(f"Erro ao processar mensagem com Hugging Face: {e}", exc_info=True)
            return "Desculpe, estou com uma instabilidade no meu sistema. Poderia repetir, por favor?"

llm_service = CognoxLLMService()
