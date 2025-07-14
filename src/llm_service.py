import openai
import json
import re
from typing import Dict, List, Tuple, Optional

class CognoxLLMService:
    """
    Serviço LLM personalizado para a Cognox.ai que simula uma conversa humana
    e ajuda com informações sobre a empresa e agendamento de reuniões.
    """
    
    def __init__(self):
        self.company_info = {
            "nome": "Cognox.ai",
            "descricao": "Pioneiros na criação de soluções de Inteligência Artificial personalizadas e sob medida para empresas",
            "objetivo": "Democratizar o acesso à IA, tornando-a uma ferramenta acessível e transformadora para negócios de todos os portes e segmentos",
            "servicos": [
                "Desenvolvimento de LLMs Personalizados",
                "Integração de IA",
                "Consultoria em IA", 
                "Suporte e Manutenção"
            ],
            "diferenciais": [
                "Entender seu Negócio em Profundidade",
                "Automatizar Tarefas Complexas",
                "Gerar Insights Acionáveis",
                "Escalar suas Operações",
                "Melhorar a Experiência do Cliente"
            ]
        }
        
        self.system_prompt = self._create_system_prompt()
        
    def _create_system_prompt(self) -> str:
        """Cria o prompt do sistema personalizado para a Cognox.ai"""
        return f"""Você é um assistente virtual da {self.company_info['nome']}, uma empresa especializada em soluções de Inteligência Artificial para negócios.

INFORMAÇÕES DA EMPRESA:
- Nome: {self.company_info['nome']}
- Descrição: {self.company_info['descricao']}
- Objetivo: {self.company_info['objetivo']}

NOSSOS SERVIÇOS:
{chr(10).join([f"• {servico}" for servico in self.company_info['servicos']])}

NOSSOS DIFERENCIAIS:
{chr(10).join([f"• {diferencial}" for diferencial in self.company_info['diferenciais']])}

INSTRUÇÕES DE COMPORTAMENTO:
1. Seja sempre cordial, profissional e prestativo
2. Responda como se fosse um consultor humano da empresa
3. Use linguagem natural e conversacional em português brasileiro
4. Mantenha as respostas concisas mas informativas
5. Quando detectar interesse em agendamento, colete informações necessárias
6. Se não souber algo específico, seja honesto e ofereça conectar com um especialista
7. Sempre termine oferecendo ajuda adicional

DETECÇÃO DE AGENDAMENTO:
Se o usuário demonstrar interesse em:
- Agendar reunião/call/conversa
- Falar com especialista
- Conhecer mais detalhes
- Solicitar proposta/orçamento
- Marcar horário

Responda coletando:
- Nome completo
- Empresa/segmento
- Melhor dia e horário
- Tipo de necessidade (qual serviço)

Sempre mantenha o tom humano e evite soar robótico."""

    def process_message(self, user_message: str, conversation_history: List[Dict] = None) -> Tuple[str, bool]:
        """
        Processa a mensagem do usuário e retorna a resposta e se há intenção de agendamento
        
        Args:
            user_message: Mensagem do usuário
            conversation_history: Histórico da conversa
            
        Returns:
            Tuple[str, bool]: (resposta, tem_intencao_agendamento)
        """
        try:
            # Prepara o histórico da conversa
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": user_message})
            
            # Chama a API do OpenAI
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Detecta intenção de agendamento
            scheduling_intent = self._detect_scheduling_intent(user_message, ai_response)
            
            return ai_response, scheduling_intent
            
        except Exception as e:
            error_response = "Desculpe, estou com dificuldades técnicas no momento. Você poderia tentar novamente em alguns instantes? Se o problema persistir, posso conectar você diretamente com nossa equipe."
            return error_response, False
    
    def _detect_scheduling_intent(self, user_message: str, ai_response: str) -> bool:
        """
        Detecta se há intenção de agendamento na mensagem do usuário ou na resposta da IA
        """
        scheduling_keywords = [
            'agendar', 'reunião', 'call', 'conversa', 'horário', 'disponibilidade',
            'marcar', 'encontro', 'bate-papo', 'apresentação', 'demonstração',
            'proposta', 'orçamento', 'especialista', 'consultor', 'vendas'
        ]
        
        combined_text = (user_message + " " + ai_response).lower()
        
        return any(keyword in combined_text for keyword in scheduling_keywords)
    
    def extract_scheduling_info(self, conversation_history: List[Dict]) -> Dict:
        """
        Extrai informações de agendamento do histórico da conversa
        """
        full_conversation = " ".join([msg.get('content', '') for msg in conversation_history])
        
        # Patterns para extrair informações
        name_pattern = r'(?:meu nome é|me chamo|sou o|sou a)\s+([A-Za-zÀ-ÿ\s]+)'
        company_pattern = r'(?:trabalho na|da empresa|empresa)\s+([A-Za-zÀ-ÿ0-9\s]+)'
        
        extracted_info = {}
        
        # Extrai nome
        name_match = re.search(name_pattern, full_conversation, re.IGNORECASE)
        if name_match:
            extracted_info['nome'] = name_match.group(1).strip()
        
        # Extrai empresa
        company_match = re.search(company_pattern, full_conversation, re.IGNORECASE)
        if company_match:
            extracted_info['empresa'] = company_match.group(1).strip()
        
        return extracted_info
