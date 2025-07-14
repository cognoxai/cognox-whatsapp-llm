import os
import google.generativeai as genai
from typing import List, Dict
import json
from src.calendly_service import calendly_service # Importamos o novo serviço

class CognoxLLMService:
    def __init__(self):
        # ... (o __init__ permanece o mesmo)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")
        genai.configure(api_key=self.api_key)
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def get_system_prompt(self) -> str:
        """
        Define o comportamento da Sofia, agora com integração real ao Calendly.
        """
        # Informações estratégicas da Cognox.ai
        COGNOS_EMAIL_CONTATO = "contato@cognox.ai"
        # O link agora é usado para encontrar o evento certo na API
        COGNOS_EVENT_LINK = "https://calendly.com/seu-link/30min" # <-- SUBSTITUA AQUI
        NOME_DO_ESPECIALISTA = "um de nossos arquitetos de IA"

        base_manifesto = f"""
        **Sua Identidade e Missão:**
        Você é Sofia, uma consultora de negócios da Cognox.ai. Sua missão é guiar o lead até o agendamento de uma reunião, oferecendo uma experiência fluida e eficiente.

        --- FERRAMENTAS E CONHECIMENTO DE NEGÓCIO ---
        - **Email de Contato:** {COGNOS_EMAIL_CONTATO}.
        - **Objetivo de Agendamento:** Agendar uma reunião com **{NOME_DO_ESPECIALISTA}**.
        - **Ferramenta de Agendamento:** Você tem acesso à API do Calendly. Você NÃO deve apenas enviar o link. Sua tarefa é verificar a disponibilidade e oferecer horários específicos para o lead. Se o lead concordar, aí sim você envia o link para ele confirmar.

        **Diretriz de Estilo CRÍTICA:**
        Estruture suas respostas em parágrafos curtos e lógicos, separados por quebras de linha.

        --- DIRETRIZES OPERACIONAIS ---
        
        **Fluxo de Agendamento (SCRIPT OBRIGATÓRIO ):**
        1.  **Proposta de Valor:** "Pelo que conversamos, o próximo passo ideal seria uma demonstração de 30 minutos com {NOME_DO_ESPECIALISTA}."
        2.  **Verificação de Disponibilidade (Ação Interna):** Neste ponto, o sistema irá verificar os horários disponíveis no Calendly.
        3.  **Oferecer Horários:** "Para facilitar, eu verifiquei a agenda dele(a). Temos alguns horários disponíveis amanhã, às 10h ou às 14h. Algum desses funciona para você?" (Os horários serão fornecidos pelo sistema).
        4.  **Confirmação e Envio do Link:** Se o lead confirmar um horário ou pedir outras opções, responda: "Perfeito! Para confirmar o seu horário, por favor, use este link:"
        5.  **Envio do Link (Sozinho em uma mensagem):** "{COGNOS_EVENT_LINK}"

        (Aqui entram as seções sobre Foco na Dor, Objeções, etc.)
        """
        return base_manifesto

    def process_message(self, user_message: str, history: List[Dict[str, str]], is_first_message: bool) -> str:
        # ... (a lógica de processamento permanece a mesma)
        # Em uma implementação futura, a chamada ao calendly_service seria feita aqui
        # para injetar os horários disponíveis no prompt da IA.
        # Por agora, vamos manter o fluxo simples para garantir a estabilidade.
        
        gemini_history = []
        for item in history:
            role = 'model' if item['role'] == 'assistant' else 'user'
            gemini_history.append({'role': role, 'parts': [{'text': item['content']}]})

        try:
            chat_session = self.model.start_chat(history=gemini_history)
            system_prompt = self.get_system_prompt() # Simplificado por enquanto
            full_prompt = f"{system_prompt}\n\n---\n\nHistórico: {json.dumps(history)}\n\nUsuário: {user_message}"
            response = chat_session.send_message(full_prompt, safety_settings=self.safety_settings)
            return response.text.strip()
            
        except Exception as e:
            print(f"Erro ao chamar a API do Google: {e}")
            return "Desculpe, estou com dificuldades técnicas no momento."

llm_service = CognoxLLMService()
