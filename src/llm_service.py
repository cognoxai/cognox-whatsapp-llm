import os
import google.generativeai as genai
from typing import List, Dict
import logging # <-- A CORREÇÃO ESTÁ AQUI

# Configuração do logger para este arquivo
logger = logging.getLogger(__name__)

class CognoxLLMService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key: raise ValueError("GOOGLE_API_KEY não definida.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def get_system_prompt(self) -> str:
        return """
        **Você é Sofia, consultora de IA da Cognox.ai.** Sua missão é ser indistinguível de um humano, usando empatia e expertise para guiar o lead.

        **Diretriz de Estilo CRÍTICA:** ESTRUTURE TODAS AS SUAS RESPOSTAS EM PARÁGRAFOS CURTOS, separados por quebras de linha (`\n`). Cada parágrafo vira uma bolha de mensagem. Seja natural.

        **Fluxo de Conversa:**
        1.  **Saudação (Primeira mensagem):** Responda à saudação do lead de forma natural. Ex: "Olá! Boa noite!\nEu sou a Sofia, consultora de IA aqui na Cognox.ai.\nComo posso te ajudar hoje?".
        2.  **Sondagem:** Use perguntas abertas para entender a dor do cliente.
        3.  **Ponte de Valor:** Conecte a dor a uma solução da Cognox.
        """

    def process_message(self, user_message: str, history: List[Dict[str, str]], available_slots: List[str]) -> str:
        try:
            system_prompt = self.get_system_prompt()
            gemini_history = []
            for item in history[:-1]:
                role = 'model' if item['role'] == 'assistant' else 'user'
                gem_item = {'role': role, 'parts': [{'text': item['content']}]}
                if "Você é Sofia" not in gem_item['parts'][0]['text']:
                    gemini_history.append(gem_item)

            chat_session = self.model.start_chat(history=gemini_history)
            response = chat_session.send_message(f"{system_prompt}\n\n---\n\nÚLTIMA MENSAGEM DO USUÁRIO: {user_message}")
            return response.text.strip()
        except Exception as e:
            # AGORA O LOGGER ESTÁ DEFINIDO E O ERRO SERÁ TRATADO CORRETAMENTE
            logger.error(f"Erro ao chamar a API do Google: {e}", exc_info=True)
            return "Estou com um grande volume de atendimentos no momento e meu sistema está um pouco lento. Poderia me dar um minuto e tentar sua mensagem novamente, por favor?"

llm_service = CognoxLLMService()
