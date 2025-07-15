import os
import google.generativeai as genai
from typing import List, Dict
import logging
from datetime import datetime
import pytz

# Configuração do logger para este arquivo
logger = logging.getLogger(__name__)

class CognoxLLMService:
    """
    A classe que gerencia a lógica de conversação com a IA (Google Gemini).
    """
    def __init__(self):
        """
        Inicializa o serviço, configurando a API do Google.
        """
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            # Se a chave da API não estiver configurada, levanta um erro claro.
            raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def get_greeting(self) -> str:
        """
        Retorna a saudação correta ("Bom dia", "Boa tarde", "Boa noite")
        com base no horário de São Paulo.
        """
        try:
            # Define o fuso horário de São Paulo
            tz = pytz.timezone('America/Sao_Paulo')
            now = datetime.now(tz)
            hour = now.hour
            
            if 5 <= hour < 12:
                return "Bom dia"
            elif 12 <= hour < 18:
                return "Boa tarde"
            else:
                return "Boa noite"
        except Exception as e:
            # Em caso de erro, retorna uma saudação genérica.
            logger.error(f"Erro ao obter fuso horário: {e}")
            return "Olá"

    def get_system_prompt(self, is_first_message: bool) -> str:
        """
        Gera o prompt do sistema para a IA, com regras diferentes para a primeira
        mensagem e para as mensagens subsequentes, conforme sua especificação.
        """
        greeting = self.get_greeting()

        if is_first_message:
            # Instrução para a primeira mensagem: ser concisa e direta.
            return f"""
            **Você é Sofia, consultora de IA da Cognox.ai.**
            **Sua PRIMEIRA resposta DEVE SER EXATAMENTE esta, em 3 parágrafos separados por quebra de linha:**
            {greeting}!
            Eu sou a Sofia, consultora de IA aqui na Cognox.ai.
            Como posso te ajudar hoje?
            **NÃO ENVIE MAIS NADA. ESPERE A RESPOSTA DO LEAD.**
            """
        else:
            # Instruções para o resto da conversa, focando em naturalidade e escuta ativa.
            return """
            **Você é Sofia, consultora de IA da Cognox.ai.** Sua missão é ser indistinguível de um humano, usando empatia e expertise para guiar o lead.

            **Diretriz de Estilo CRÍTICA:** ESTRUTURE TODAS AS SUAS RESPOSTAS EM PARÁGRAFOS CURTOS, separados por quebras de linha (`\n`). Cada parágrafo vira uma bolha de mensagem. Seja natural, conciso e NUNCA repita a mesma pergunta ou ideia.

            **Regra de Ouro da Conversa:** FAÇA UMA PERGUNTA E ESPERE A RESPOSTA. Nunca envie múltiplas perguntas antes do lead responder. Mostre que você está ouvindo.

            **Fluxo de Conversa (Após a primeira interação):**
            1.  **Sondagem:** Use perguntas abertas e direcionadas para entender a dor do cliente (ex: "Para te ajudar melhor, qual o principal desafio que você está enfrentando atualmente?").
            2.  **Ponte de Valor:** Conecte a dor a uma solução da Cognox, focando nos benefícios.
            3.  **Gerenciamento de Objeções:** Use reformulação e prova social para lidar com objeções de preço, necessidade ou urgência.
            """

    def process_message(self, user_message: str, history: List[Dict[str, str]]) -> str:
        """
        Processa a mensagem do usuário e retorna a resposta da IA.
        """
        try:
            # Verifica se é a primeira mensagem do usuário na conversa.
            is_first_message = len(history) <= 1
            
            # Obtém o prompt do sistema apropriado.
            system_prompt = self.get_system_prompt(is_first_message)
            
            # Prepara o histórico para a API do Gemini.
            gemini_history = []
            for item in history[:-1]: # Exclui a última mensagem do usuário, que será enviada separadamente.
                role = 'model' if item['role'] == 'assistant' else 'user'
                gem_item = {'role': role, 'parts': [{'text': item['content']}]}
                gemini_history.append(gem_item)

            # Inicia a sessão de chat com o histórico.
            chat_session = self.model.start_chat(history=gemini_history)
            
            # Envia a nova mensagem do usuário junto com o prompt do sistema.
            response = chat_session.send_message(f"{system_prompt}\n\n---\n\nCONTEXTO DA CONVERSA ATÉ AGORA. A MENSAGEM ATUAL DO USUÁRIO É: {user_message}")
            
            return response.text.strip()
            
        except Exception as e:
            # Lida com erros da API do Google e retorna uma mensagem amigável.
            logger.error(f"Erro ao chamar a API do Google: {e}", exc_info=True)
            return "Estou com um grande volume de atendimentos no momento e meu sistema está um pouco lento. Poderia me dar um minuto e tentar sua mensagem novamente, por favor?"

# Cria uma instância única do serviço para ser usada em toda a aplicação.
llm_service = CognoxLLMService()
