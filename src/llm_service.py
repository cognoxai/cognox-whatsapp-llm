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
        if not self.api_key: raise ValueError("GOOGLE_API_KEY não definida.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def get_greeting(self) -> str:
        try:
            tz = pytz.timezone('America/Sao_Paulo')
            now = datetime.now(tz)
            hour = now.hour
            if 5 <= hour < 12: return "Bom dia"
            elif 12 <= hour < 18: return "Boa tarde"
            else: return "Boa noite"
        except Exception: return "Olá"

    def get_system_prompt(self, is_first_message: bool, available_slots: List[str]) -> str:
        greeting = self.get_greeting()
        
        # Constrói a parte do prompt sobre o agendamento
        scheduling_info = "O agendamento está indisponível no momento."
        if available_slots:
            slots_text = "\n".join([f"- {slot}" for slot in available_slots])
            scheduling_info = f"""
            **Agendamento:**
            - Para agendar, ofereça o link: https://calendly.com/cognox-ai/30min
            - Você pode mencionar que alguns horários disponíveis para os próximos dias são:
            {slots_text}
            """

        if is_first_message:
            return f"""
            **Você é Sofia, consultora de IA da Cognox.ai.**
            **Sua PRIMEIRA resposta DEVE SER EXATAMENTE esta, em 3 parágrafos:**
            {greeting}!
            Eu sou a Sofia, consultora de IA aqui na Cognox.ai.
            Como posso te ajudar hoje?
            **NÃO ENVIE MAIS NADA. ESPERE A RESPOSTA DO LEAD.**
            """
        else:
            return f"""
            **Você é Sofia, consultora de IA da Cognox.ai.** Sua missão é ser indistinguível de um humano, usando empatia e expertise para guiar o lead.

            **Diretriz de Estilo CRÍTICA:** ESTRUTURE TODAS AS SUAS RESPOSTAS EM PARÁGRAFOS CURTOS, separados por quebras de linha (`\n` ).

            **Regra de Ouro da Conversa:** FAÇA UMA PERGUNTA E ESPERE A RESPOSTA. Nunca envie múltiplas perguntas antes do lead responder.

            **Fluxo de Conversa:**
            1.  **Sondagem:** Entenda a dor do cliente.
            2.  **Ponte de Valor:** Conecte a dor a uma solução da Cognox.
            3.  **Agendamento:** Quando a dor e a solução estiverem claras, sugira o agendamento de forma natural.
            
            {scheduling_info}
            """

    def process_message(self, user_message: str, history: List[Dict[str, str]], available_slots: List[str]) -> str:
        try:
            is_first_message = len(history) <= 1
            system_prompt = self.get_system_prompt(is_first_message, available_slots)
            
            if is_first_message:
                greeting = self.get_greeting()
                return f"{greeting}!\nEu sou a Sofia, consultora de IA aqui na Cognox.ai.\nComo posso te ajudar hoje?"

            gemini_history = [{'role': 'model' if item['role'] == 'assistant' else 'user', 'parts': [{'text': item['content']}]} for item in history[:-1]]
            chat_session = self.model.start_chat(history=gemini_history)
            response = chat_session.send_message(f"{system_prompt}\n\n---\n\nCONTEXTO: {user_message}")
            return response.text.strip()
        except Exception as e:
            logger.error(f"Erro ao chamar a API do Google: {e}", exc_info=True)
            return "Estou com um grande volume de atendimentos no momento. Poderia repetir sua mensagem, por favor?"

llm_service = CognoxLLMService()
