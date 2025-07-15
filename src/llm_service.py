import os
import requests
import logging
import time
from typing import List, Dict
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

# MUDANÇA PARA UM MODELO MAIS ROBUSTO E DE PROPÓSITO GERAL
MODEL_ID = "distilbert-base-uncased-finetuned-sst-2-english"
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

    def query_huggingface_with_retry(self, payload, retries=3, delay=10):
        """
        Tenta fazer a requisição à API, com novas tentativas se o modelo estiver carregando.
        ESTA É A MUDANÇA CRÍTICA.
        """
        for i in range(retries):
            try:
                response = requests.post(API_URL, headers=self.headers, json=payload)
                # Se a resposta estiver vazia, o modelo ainda está carregando.
                if not response.content:
                    raise ValueError("Resposta vazia da API, modelo provavelmente carregando.")
                
                # Se a resposta for um erro 503, o modelo está carregando.
                if response.status_code == 503:
                    estimated_time = response.json().get("estimated_time", delay)
                    logger.info(f"Modelo está carregando. Tentando novamente em {estimated_time} segundos...")
                    time.sleep(estimated_time)
                    continue

                response.raise_for_status() # Levanta um erro para outros status HTTP ruins.
                return response.json()

            except (requests.exceptions.RequestException, ValueError, requests.exceptions.JSONDecodeError) as e:
                logger.warning(f"Tentativa {i+1}/{retries} falhou: {e}. Tentando novamente em {delay} segundos...")
                time.sleep(delay)
        
        logger.error("Todas as tentativas de contatar a API do Hugging Face falharam.")
        return {"error": "Falha ao contatar a API após múltiplas tentativas."}


    def process_message(self, user_message: str, history: List[Dict[str, str]]) -> str:
        """
        Processa a mensagem do usuário usando um modelo de código aberto do Hugging Face.
        """
        try:
            is_first_message = len(history) <= 1
            if is_first_message:
                greeting = self.get_greeting()
                return f"{greeting}! Eu sou a Sofia, consultora de IA aqui na Cognox.ai.\nComo posso te ajudar hoje?"

            # Este modelo é mais simples e funciona bem com a última mensagem.
            payload = {"inputs": user_message}
            
            output = self.query_huggingface_with_retry(payload)
            
            # A resposta deste modelo é diferente, precisamos adaptá-la.
            # É uma resposta de análise de sentimento, vamos usá-la para criar uma resposta de chatbot.
            if isinstance(output, list) and output:
                # Exemplo de como interpretar a resposta de análise de sentimento
                sentiment = output[0][0]['label']
                if sentiment == 'POSITIVE':
                    return "Entendido! Fico feliz em ouvir isso. Como posso te ajudar a ir além?"
                elif sentiment == 'NEGATIVE':
                    return "Compreendo sua preocupação. Poderia me detalhar um pouco mais o problema para que eu possa ajudar?"
                else:
                    return "Certo. Para que eu possa te ajudar melhor, qual o seu principal desafio no momento?"
            elif 'error' in output:
                logger.error(f"Erro da API do Hugging Face: {output['error']}")
                return "Desculpe, estou com uma pequena instabilidade. Poderia repetir sua mensagem?"
            else:
                return "Compreendo. Poderia me dar mais detalhes?"

        except Exception as e:
            logger.error(f"Erro ao processar mensagem com Hugging Face: {e}", exc_info=True)
            return "Desculpe, estou com uma instabilidade no meu sistema. Poderia repetir, por favor?"

llm_service = CognoxLLMService()
