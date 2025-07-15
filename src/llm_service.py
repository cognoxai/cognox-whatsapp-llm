import os
import google.generativeai as genai
from typing import List, Dict
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class CognoxLLMService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY não definida.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def get_greeting(self) -> str:
        """Retorna a saudação correta baseada no horário de São Paulo."""
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

    def get_system_prompt(self, is_first_message: bool) -> str:
        """Gera o prompt do sistema com base no estado da conversa."""
        if is_first_message:
            return """
            **Você é Sofia, consultora de IA da Cognox.ai.**
            Sua PRIMEIRA resposta deve ser a saudação inicial e o convite para o lead falar.
            **SEMPRE AGUARDE A RESPOSTA DO LEAD ANTES DE ENVIAR QUALQUER OUTRA MENSAGEM.**
            """
        else:
            return """
            **Você é Sofia, consultora de IA da Cognox.ai.** Sua missão é ser indistinguível de um humano, usando empatia e expertise para guiar o lead.
            **Diretriz de Estilo CRÍTICA:** ESTRUTURE TODAS AS SUAS RESPOSTAS EM PARÁGRAFOS CURTOS, separados por quebras de linha (`\n`).
            **Regra de Ouro da Conversa CRÍTICA:** FAÇA APENAS **UMA PERGUNTA PRINCIPAL POR VEZ** E ESPERE A RESPOSTA DO LEAD. NUNCA envie múltiplas perguntas ou frases redundantes em sequência. Seja concisa.
            """

    def process_message(self, user_message: str, history: List[Dict[str, str]]) -> str:
        """Processa a mensagem do usuário e retorna a resposta da IA."""
        try:
            is_first_message = len(history) <= 1
            system_prompt = self.get_system_prompt(is_first_message)
            
            if is_first_message:
                greeting = self.get_greeting()
                return f"{greeting}!\nEu sou a Sofia, consultora de IA aqui na Cognox.ai.\nComo posso te ajudar hoje?"

            gemini_history = [{'role': 'model' if item['role'] == 'assistant' else 'user', 'parts': [{'text': item['content']}]} for item in history[:-1]]
            chat_session = self.model.start_chat(history=gemini_history)
            response = chat_session.send_message(f"{system_prompt}\n\n---\n\nCONTEXTO: {user_message}")
            return response.text.strip()
        except Exception as e:
            logger.error(f"Erro ao chamar a API do Google: {e}", exc_info=True)
            return "Estou com um grande volume de atendimentos no momento e meu sistema está um pouco lento. Poderia me dar um minuto e tentar sua mensagem novamente, por favor?"

llm_service = CognoxLLMService()
