import openai
import os
from typing import List, Dict

class CognoxLLMService:
    """
    Serviço para interagir com a API da OpenAI e gerar respostas inteligentes.
    """
    def __init__(self):
        # Carrega a chave da API a partir das variáveis de ambiente
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("A variável de ambiente OPENAI_API_KEY não foi definida.")
        openai.api_key = self.api_key

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
        Processa a mensagem do usuário, consulta a IA e retorna a resposta.
        """
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            ai_response = response.choices[0].message.content.strip()
            return ai_response
        except Exception as e:
            print(f"Erro ao chamar a API da OpenAI: {e}")
            return "Desculpe, estou com dificuldades técnicas no momento. Por favor, tente novamente em alguns instantes."

# --- ESTA É A LINHA QUE FALTAVA ---
# Cria uma instância única do serviço para ser usada em toda a aplicação.
llm_service = CognoxLLMService()
