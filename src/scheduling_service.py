import requests
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class SchedulingService:
    """
    Serviço para integração com sistemas de agendamento (Calendly, Google Calendar, etc.)
    """
    
    def __init__(self):
        # Configurações do Calendly
        self.calendly_token = os.getenv("CALENDLY_ACCESS_TOKEN")
        self.calendly_user_uri = os.getenv("CALENDLY_USER_URI")
        self.calendly_base_url = "https://api.calendly.com"
        
        # Configurações do Google Calendar (alternativa )
        self.google_calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        self.google_service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        
        if not self.calendly_token:
            logger.warning("Calendly não configurado. Usando modo simulação.")
    
    def get_available_slots(self, start_date: str, end_date: str, duration_minutes: int = 60) -> List[Dict]:
        """
        Obtém horários disponíveis para agendamento
        
        Args:
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)
            duration_minutes: Duração da reunião em minutos
            
        Returns:
            List[Dict]: Lista de horários disponíveis
        """
        if not self.calendly_token:
            return self._get_mock_available_slots(start_date, end_date)
        
        try:
            # Busca event types do usuário
            event_types = self._get_event_types()
            if not event_types:
                logger.error("Nenhum event type encontrado")
                return []
            
            # Usa o primeiro event type disponível
            event_type_uri = event_types[0]["uri"]
            
            # Busca horários disponíveis
            url = f"{self.calendly_base_url}/scheduling/available_times"
            headers = {
                "Authorization": f"Bearer {self.calendly_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "event_type": event_type_uri,
                "start_time": f"{start_date}T00:00:00Z",
                "end_time": f"{end_date}T23:59:59Z"
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            available_times = data.get("collection", [])
            
            # Formata os horários para retorno
            formatted_slots = []
            for slot in available_times:
                start_time = datetime.fromisoformat(slot["start_time"].replace("Z", "+00:00"))
                formatted_slots.append({
                    "start_time": start_time.strftime("%Y-%m-%d %H:%M"),
                    "end_time": (start_time + timedelta(minutes=duration_minutes)).strftime("%Y-%m-%d %H:%M"),
                    "available": True,
                    "event_type_uri": event_type_uri
                })
            
            return formatted_slots
            
        except Exception as e:
            logger.error(f"Erro ao buscar horários disponíveis: {str(e)}")
            return self._get_mock_available_slots(start_date, end_date)
    
    def schedule_meeting(self, scheduling_info: Dict) -> Tuple[bool, str]:
        """
        Agenda uma reunião
        
        Args:
            scheduling_info: Informações do agendamento
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem/link)
        """
        if not self.calendly_token:
            return self._schedule_mock_meeting(scheduling_info)
        
        try:
            # Para Calendly, geralmente o agendamento é feito via link público
            # Aqui implementamos uma versão simplificada
            
            event_types = self._get_event_types()
            if not event_types:
                return False, "Erro: Nenhum tipo de evento configurado"
            
            # Gera link de agendamento personalizado
            event_type = event_types[0]
            scheduling_link = event_type.get("scheduling_url", "")
            
            if scheduling_link:
                # Adiciona parâmetros pré-preenchidos se possível
                prefilled_params = []
                if scheduling_info.get("name"):
                    prefilled_params.append(f"name={scheduling_info["name"]}")
                if scheduling_info.get("company"):
                    prefilled_params.append(f"company={scheduling_info["company"]}")
                
                if prefilled_params:
                    separator = "&" if "?" in scheduling_link else "?"
                    scheduling_link += separator + "&".join(prefilled_params)
                
                return True, scheduling_link
            else:
                return False, "Erro: Link de agendamento não disponível"
                
        except Exception as e:
            logger.error(f"Erro ao agendar reunião: {str(e)}")
            return False, f"Erro interno: {str(e)}"
    
    def create_direct_booking(self, scheduling_info: Dict) -> Tuple[bool, str]:
        """
        Cria um agendamento direto (se suportado pela API)
        
        Args:
            scheduling_info: Informações do agendamento
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem/link)
        """
        # Implementação para criação real via API
        # Nota: Calendly API v2 tem limitações para criação direta
        # Esta é uma implementação conceitual
        
        if not self.calendly_token:
            return self._schedule_mock_meeting(scheduling_info)
        
        try:
            # Para implementação real, seria necessário usar Calendly Webhooks
            # ou integração com Google Calendar diretamente
            
            # Por enquanto, retorna link de agendamento
            return self.schedule_meeting(scheduling_info)
            
        except Exception as e:
            logger.error(f"Erro ao criar agendamento direto: {str(e)}")
            return False, f"Erro interno: {str(e)}"
    
    def parse_time_preference(self, time_text: str) -> Optional[Dict]:
        """
        Analisa preferência de horário em texto natural
        
        Args:
            time_text: Texto com preferência de horário
            
        Returns:
            Dict: Informações de data/hora extraídas
        """
        time_text = time_text.lower()
        
        # Padrões para dias da semana
        weekdays = {
            "segunda": 0, "segunda-feira": 0,
            "terça": 1, "terça-feira": 1,
            "quarta": 2, "quarta-feira": 2,
            "quinta": 3, "quinta-feira": 3,
            "sexta": 4, "sexta-feira": 4,
            "sábado": 5, "sabado": 5,
            "domingo": 6
        }
        
        # Padrões para horários
        time_patterns = [
            r"(\d{1,2}):(\d{2})",  # 14:30
            r"(\d{1,2})h(\d{2})",  # 14h30
            r"(\d{1,2})h",         # 14h
            r"(\d{1,2})\s*horas",  # 14 horas
        ]
        
        result = {}
        
        # Busca dia da semana
        for day_name, day_num in weekdays.items():
            if day_name in time_text:
                # Calcula próxima ocorrência deste dia
                today = datetime.now()
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:  # Se já passou esta semana
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                result["date"] = target_date.strftime("%Y-%m-%d")
                break
        
        # Busca horário
        for pattern in time_patterns:
            match = re.search(pattern, time_text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if len(match.groups()) > 1 else 0
                
                # Ajusta para formato 24h se necessário
                if "tarde" in time_text and hour < 12:
                    hour += 12
                elif "manhã" in time_text and hour > 12:
                    hour -= 12
                
                result["time"] = f"{hour:02d}:{minute:02d}"
                break
        
        # Busca referências relativas
        if "amanhã" in time_text:
            tomorrow = datetime.now() + timedelta(days=1)
            result["date"] = tomorrow.strftime("%Y-%m-%d")
        elif "hoje" in time_text:
            result["date"] = datetime.now().strftime("%Y-%m-%d")
        elif "próxima semana" in time_text:
            next_week = datetime.now() + timedelta(days=7)
            result["date"] = next_week.strftime("%Y-%m-%d")
        
        return result if result else None
    
    def _get_event_types(self) -> List[Dict]:
        """
        Obtém tipos de eventos do Calendly
        """
        try:
            url = f"{self.calendly_base_url}/event_types"
            headers = {
                "Authorization": f"Bearer {self.calendly_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "user": self.calendly_user_uri,
                "active": "true"
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("collection", [])
            
        except Exception as e:
            logger.error(f"Erro ao buscar event types: {str(e)}")
            return []
    
    def _get_mock_available_slots(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Retorna horários simulados para demonstração
        """
        slots = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current_date <= end_date_obj:
            # Pula fins de semana
            if current_date.weekday() < 5:  # Segunda a sexta
                # Horários de manhã (9h às 12h)
                for hour in [9, 10, 11]:
                    slots.append({
                        "start_time": current_date.replace(hour=hour, minute=0).strftime("%Y-%m-%d %H:%M"),
                        "end_time": current_date.replace(hour=hour+1, minute=0).strftime("%Y-%m-%d %H:%M"),
                        "available": True,
                        "event_type_uri": "mock_event_type"
                    })
                
                # Horários de tarde (14h às 17h)
                for hour in [14, 15, 16, 17]:
                    slots.append({
                        "start_time": current_date.replace(hour=hour, minute=0).strftime("%Y-%m-%d %H:%M"),
                        "end_time": current_date.replace(hour=hour+1, minute=0).strftime("%Y-%m-%d %H:%M"),
                        "available": True,
                        "event_type_uri": "mock_event_type"
                    })
            
            current_date += timedelta(days=1)
        
        return slots[:10]  # Retorna apenas os primeiros 10 slots
    
    def _schedule_mock_meeting(self, scheduling_info: Dict) -> Tuple[bool, str]:
        """
        Simula agendamento para demonstração
        """
        name = scheduling_info.get("name", "Cliente")
        company = scheduling_info.get("company", "")
        preferred_time = scheduling_info.get("preferred_time", "horário preferido")
        
        mock_link = f"https://calendly.com/cognox-ai/reuniao?name={name}&company={company}"
        
        return True, mock_link

# Instância global do serviço
scheduling_service = SchedulingService( )
