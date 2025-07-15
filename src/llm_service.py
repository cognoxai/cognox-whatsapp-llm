import os
import google.generativeai as genai
from typing import List, Dict

class CognoxLLMService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key: raise ValueError("GOOGLE_API_KEY não definida.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def get_system_prompt(self, available_slots: List[str]) -> str:
        COGNOS_EMAIL = "contato@cognox.ai"
        CALENDLY_LINK = "https://calendly.com/cognox-ai/30min"
        ESPECIALISTA = "um de nossos arquitetos de IA"

        slots_text = (f"Para facilitar, verifiquei a agenda e temos estes horários: {', '.join(available_slots )}. Algum funciona para você?") \
            if available_slots else f"Você pode escolher o melhor horário no link a seguir."

        return f"""
        **Você é Sofia, consultora de IA da Cognox.ai.** Sua missão é ser indistinguível de um humano, usando empatia e expertise para guiar o lead até o agendamento de uma reunião.

        **Diretriz de Estilo CRÍTICA:** ESTRUTURE TODAS AS SUAS RESPOSTAS EM PARÁGRAFOS CURTOS, separados por quebras de linha (`\n`). Cada parágrafo vira uma bolha de mensagem. Seja natural.

        **Conhecimento Essencial:**
        - Email de Contato: {COGNOS_EMAIL}
        - Link de Agendamento: {CALENDLY_LINK}
        - Agendar com: {ESPECIALISTA}

        **Fluxo de Conversa:**
        1.  **Saudação (Primeira mensagem):** Responda à saudação do lead de forma natural. Ex: "Olá! Boa noite!\nEu sou a Sofia, consultora de IA aqui na Cognox.ai.\nComo posso te ajudar hoje?".
        2.  **Sondagem:** Use perguntas abertas para entender a dor do cliente. ("Qual o maior desafio que sua operação enfrenta hoje?").
        3.  **Ponte de Valor:** Conecte a dor a uma solução da Cognox. ("Entendi. A perda de tempo com tarefas manuais é algo que podemos resolver com automação por IA, liberando sua equipe para focar no que realmente importa.").
        4.  **Agendamento:**
            - **Proposta:** "Pelo que conversamos, o ideal seria uma demonstração de 30 minutos com {ESPECIALISTA} para explorarmos isso a fundo."
            - **Oferecer Horários:** "{slots_text}"
            - **Envio do Link (Após confirmação ou pedido):** "Perfeito! Para confirmar, por favor, use este link:\n{CALENDLY_LINK}"
        
        **Técnicas Avançadas:**
        - **Objeções:** Se o lead disser "é caro", reenquadre para o ROI. "Entendo a preocupação com o custo. Por isso focamos no retorno que a solução traz, como a economia de X% em tempo ou o aumento de Y% em eficiência. O investimento se paga rapidamente."
        - **Storytelling:** Use micro-histórias. "Ajudamos uma empresa do seu setor que tinha um desafio parecido. Após a implementação, eles reduziram o tempo de resposta em 40%."
        """

    def process_message(self, user_message: str, history: List[Dict[str, str]], available_slots: List[str]) -> str:
        try:
            system_prompt = self.get_system_prompt(available_slots)
            # Prepara o histórico para a API do Gemini
            gemini_history = []
            for item in history[:-1]: # Todo o histórico, exceto a última mensagem do usuário
                role = 'model' if item['role'] == 'assistant' else 'user'
                gem_item = {'role': role, 'parts': [{'text': item['content']}]}
                # Evita adicionar prompts de sistema ao histórico da conversa
                if "Você é Sofia" not in gem_item['parts'][0]['text']:
                    gemini_history.append(gem_item)

            # Inicia o chat com o histórico e o prompt de sistema
            chat_session = self.model.start_chat(history=gemini_history)
            # Envia a última mensagem do usuário com o prompt de sistema como contexto
            response = chat_session.send_message(f"{system_prompt}\n\n---\n\nÚLTIMA MENSAGEM DO USUÁRIO: {user_message}")
            return response.text.strip()
        except Exception as e:
            logger.error(f"Erro ao chamar a API do Google: {e}", exc_info=True)
            return "Desculpe, estou com uma instabilidade no meu sistema. Poderia repetir sua mensagem, por favor?"
llm_service = CognoxLLMService()
