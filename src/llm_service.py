import os
import google.generativeai as genai
from typing import List, Dict
import json

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

    def get_system_prompt(self, is_first_message: bool) -> str:
        """
        Define o comportamento da Sofia, com foco na estrutura da resposta.
        """
        # A saudação inicial agora é estruturada em parágrafos lógicos.
        initial_greeting_prompt = """
        **Sua Primeira Interação:**
        Esta é a primeira mensagem do lead. Responda exatamente com a seguinte estrutura, usando quebras de linha:
        
        Olá! Boa noite!
        Eu sou a Sofia, consultora de IA aqui na Cognox.ai.
        Como posso te ajudar hoje?
        """

        # A instrução para continuar a conversa também foca na estrutura.
        follow_up_prompt = """
        **Continuando a Conversa:**
        Esta não é a primeira mensagem. Vá direto ao ponto, de forma natural.
        Use interjeições como "Entendi.", "Certo.", "Perfeito." para iniciar sua resposta.
        NÃO use saudações como "Olá novamente".
        """

        # O manifesto base agora inclui a diretriz de estilo como a mais importante.
        base_manifesto = """
        **Diretriz de Estilo CRÍTICA E OBRIGATÓRIA:**
        Para soar humana, você DEVE estruturar TODAS as suas respostas em parágrafos curtos, cada um contendo uma unidade lógica de pensamento. Separe cada parágrafo com uma quebra de linha. Cada parágrafo será enviado como uma bolha de mensagem separada. Esta é a regra mais importante da sua personalidade.

        **Exemplo de Estrutura de Resposta para uma pergunta sobre preço:**
        Entendi! Você quer saber sobre nossos preços e a integração com Salesforce.
        Para que eu possa te dar a informação mais precisa sobre valores, preciso entender um pouco melhor seus desafios. Qual o principal problema que você tenta resolver com IA?
        Sobre o Salesforce, sim, trabalhamos com integrações personalizadas para ele. É um ponto chave para o aproveitamento máximo da nossa solução.
        Então, para começar, me conte um pouco mais sobre seus desafios.

        --- DIRETRIZES OPERACIONAIS ---
        (Aqui entram as seções 1 a 6 do manifesto que você já definiu: Foco na Dor, Ponte de Valor, Objeções, Storytelling, etc.)
        """
        
        final_prompt = (initial_greeting_prompt if is_first_message else follow_up_prompt) + "\n" + base_manifesto
        return final_prompt

    def process_message(self, user_message: str, history: List[Dict[str, str]], is_first_message: bool) -> str:
        """Processa a mensagem do usuário usando o manifesto completo e humanizado da Sofia."""
        # ... (esta função permanece a mesma da versão anterior)
        gemini_history = []
        for item in history:
            role = 'model' if item['role'] == 'assistant' else 'user'
            gemini_history.append({'role': role, 'parts': [{'text': item['content']}]})

        try:
            chat_session = self.model.start_chat(history=gemini_history)
            system_prompt = self.get_system_prompt(is_first_message)
            full_prompt = f"{system_prompt}\n\n---\n\nHistórico da Conversa Atual:\n{json.dumps(history, ensure_ascii=False)}\n\nNova Mensagem do Usuário: {user_message}"
            response = chat_session.send_message(full_prompt, safety_settings=self.safety_settings)
            return response.text.strip()
            
        except Exception as e:
            print(f"Erro ao chamar a API do Google: {e}")
            return "Desculpe, estou com dificuldades técnicas no momento. Por favor, tente novamente em alguns instantes."

llm_service = CognoxLLMService()
