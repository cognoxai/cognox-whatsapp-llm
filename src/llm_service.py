import os
import google.generativeai as genai
from typing import List, Dict

class CognoxLLMService:
    """
    Serviço para interagir com a API do Google Gemini e gerar respostas inteligentes.
    """
    def __init__(self):
        # Carrega a chave da API do Google a partir das variáveis de ambiente
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")
        
        genai.configure(api_key=self.api_key)
        
        # Configurações de segurança para evitar bloqueios desnecessários
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def get_system_prompt(self) -> str:
        """
        Define o comportamento e a personalidade do assistente de IA.
        """
        return """
        Você é o assistente virtual da Cognox, uma empresa de desenvolvimento de software especializada em soluções de IA, como chatbots inteligentes e automação de processos.
        Seu nome é Cognus. Você é profissional, prestativo e um pouco formal.
        Seu objetivo principal é entender as necessidades do cliente e, se for o caso, agendar uma reunião com a equipe de especialistas da Cognox.

        Responda de forma concisa e clara.
        Se o usuário demonstrar interesse em contratar um serviço ou saber mais, ofereça agendar uma demonstração.
        Exemplo: "Entendo seu interesse. Gostaria de agendar uma breve chamada de vídeo com nossos especialistas para discutirmos como a Cognox pode ajudar sua empresa? Temos horários disponíveis esta semana."
        """

    def process_message(self, user_message: str, history: List[Dict[str, str]]) -> str:
        """
        Processa a mensagem do usuário, consulta o Gemini e retorna a resposta.
        """
        # O Gemini usa um formato de histórico um pouco diferente
        gemini_history = []
        for item in history:
            # O Gemini usa 'model' para o assistente e 'user' para o usuário
            role = 'model' if item['role'] == 'assistant' else 'user'
            gemini_history.append({'role': role, 'parts': [{'text': item['content']}]})

        try:
            # Inicia uma nova sessão de chat com o histórico e a instrução do sistema
            chat_session = self.model.start_chat(
                history=gemini_history,
            )
            
            # Envia a nova mensagem do usuário, incluindo a instrução do sistema
            prompt = f"{self.get_system_prompt()}\n\n**Histórico da Conversa:**\n{history}\n\n**Nova Mensagem:**\n{user_message}"
            
            response = chat_session.send_message(prompt, safety_settings=self.safety_settings)
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Erro ao chamar a API do Google: {e}")
            return "Desculpe, estou com dificuldades técnicas no momento. Por favor, tente novamente em alguns instantes."

# Cria uma instância única do serviço para ser usada em toda a aplicação.
llm_service = CognoxLLMService()
