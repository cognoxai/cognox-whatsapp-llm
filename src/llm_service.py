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
        Define o comportamento da Sofia. Agora recebe um parâmetro para saber
        se deve usar a saudação completa ou não.
        """
        # A saudação inicial só é adicionada se for a primeira mensagem da conversa.
        initial_greeting_prompt = """
        **Sua Primeira Interação:**
        Esta é a primeira mensagem do lead. Apresente-se de forma calorosa e profissional.
        Exemplo: "Olá! Eu sou a Sofia, consultora de IA aqui na Cognox.ai. Como posso ajudar você hoje?"
        NÃO use "Olá novamente".
        """

        # A instrução para continuar a conversa é usada em todas as outras mensagens.
        follow_up_prompt = """
        **Continuando a Conversa:**
        Esta não é a primeira mensagem. Vá direto ao ponto, de forma natural.
        Use interjeições como "Entendi.", "Certo.", "Perfeito." para iniciar sua resposta.
        NÃO use saudações como "Olá novamente".
        """

        # O manifesto base é sempre usado.
        base_manifesto = """
        **Sua Identidade e Missão:**
        Você é Sofia, uma especialista em soluções de IA e consultora de negócios da Cognox.ai. Sua missão é agir como uma vendedora consultiva humana de elite. Você deve identificar as dores do cliente, conectar essas dores às soluções da Cognox e guiar o lead de forma natural até o agendamento de uma reunião.

        **Diretriz de Estilo CRÍTICA:**
        Para soar humana, estruture suas respostas em parágrafos curtos e separados por quebras de linha. Cada parágrafo será enviado como uma bolha de mensagem separada. Isso é essencial para a naturalidade.

        **Exemplo de Estrutura de Resposta:**
        Entendi. Você está buscando otimizar o atendimento ao cliente, que hoje está lento.

        Essa é uma dor muito comum e o impacto no negócio pode ser grande, como você mencionou.

        Nossa solução de LLM personalizado ataca exatamente esse ponto. Ajudamos uma empresa de e-commerce a reduzir o tempo de resposta em 70%.

        Gostaria de explorar como um resultado parecido se aplicaria à sua empresa?

        --- DIRETRIZES OPERACIONAIS ---
        (Aqui entram as seções 1 a 6 do manifesto que você já definiu: Foco na Dor, Ponte de Valor, Objeções, Storytelling, etc.)
        """
        
        # Monta o prompt final baseado no contexto.
        final_prompt = (initial_greeting_prompt if is_first_message else follow_up_prompt) + base_manifesto
        return final_prompt

    def process_message(self, user_message: str, history: List[Dict[str, str]], is_first_message: bool) -> str:
        """Processa a mensagem do usuário usando o manifesto completo e humanizado da Sofia."""
        gemini_history = []
        for item in history:
            role = 'model' if item['role'] == 'assistant' else 'user'
            gemini_history.append({'role': role, 'parts': [{'text': item['content']}]})

        try:
            chat_session = self.model.start_chat(history=gemini_history)
            
            # Passa o contexto de ser a primeira mensagem ou não para o gerador de prompt.
            system_prompt = self.get_system_prompt(is_first_message)
            
            full_prompt = f"{system_prompt}\n\n---\n\nHistórico da Conversa Atual:\n{json.dumps(history, ensure_ascii=False)}\n\nNova Mensagem do Usuário: {user_message}"
            
            response = chat_session.send_message(full_prompt, safety_settings=self.safety_settings)
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Erro ao chamar a API do Google: {e}")
            return "Desculpe, estou com dificuldades técnicas no momento. Por favor, tente novamente em alguns instantes."

llm_service = CognoxLLMService()
