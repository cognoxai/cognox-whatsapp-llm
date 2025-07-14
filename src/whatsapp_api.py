import requests
import json
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class WhatsAppAPI:
    """
    Cliente para integração com a API do WhatsApp Business
    """
    
    def __init__(self):
        # Configurações da API (devem ser definidas como variáveis de ambiente)
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', 'COGNOX_VERIFY_TOKEN')
        self.api_version = 'v21.0'
        self.base_url = f'https://graph.facebook.com/{self.api_version}'
        
        if not self.access_token or not self.phone_number_id:
            logger.warning("WhatsApp API credentials not configured. Messages will be logged only." )
    
    def send_text_message(self, to: str, message: str) -> bool:
        """
        Envia uma mensagem de texto via WhatsApp Business API
        
        Args:
            to: Número do destinatário (formato: 5511999999999)
            message: Texto da mensagem
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        if not self.access_token or not self.phone_number_id:
            logger.info(f"[SIMULAÇÃO] Enviando para {to}: {message}")
            return True
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'text',
            'text': {
                'body': message
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Mensagem enviada com sucesso para {to}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem para {to}: {str(e)}")
            return False
    
    def send_template_message(self, to: str, template_name: str, language_code: str = 'pt_BR', 
                            components: Optional[list] = None) -> bool:
        """
        Envia uma mensagem template via WhatsApp Business API
        
        Args:
            to: Número do destinatário
            template_name: Nome do template aprovado
            language_code: Código do idioma
            components: Componentes do template (parâmetros)
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        if not self.access_token or not self.phone_number_id:
            logger.info(f"[SIMULAÇÃO] Enviando template {template_name} para {to}")
            return True
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {
                    'code': language_code
                }
            }
        }
        
        if components:
            payload['template']['components'] = components
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Template {template_name} enviado com sucesso para {to}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar template para {to}: {str(e)}")
            return False
    
    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Marca uma mensagem como lida
        
        Args:
            message_id: ID da mensagem
            
        Returns:
            bool: True se marcado com sucesso, False caso contrário
        """
        if not self.access_token or not self.phone_number_id:
            logger.info(f"[SIMULAÇÃO] Marcando mensagem {message_id} como lida")
            return True
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'status': 'read',
            'message_id': message_id
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Mensagem {message_id} marcada como lida")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao marcar mensagem como lida: {str(e)}")
            return False
    
    def validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Valida a assinatura do webhook do WhatsApp
        
        Args:
            payload: Corpo da requisição
            signature: Assinatura do header X-Hub-Signature-256
            
        Returns:
            bool: True se válida, False caso contrário
        """
        import hmac
        import hashlib
        
        app_secret = os.getenv('WHATSAPP_APP_SECRET')
        if not app_secret:
            logger.warning("WHATSAPP_APP_SECRET não configurado. Validação de assinatura desabilitada.")
            return True
        
        try:
            expected_signature = hmac.new(
                app_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Remove o prefixo 'sha256=' se presente
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Erro ao validar assinatura: {str(e)}")
            return False
    
    def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Obtém a URL de um arquivo de mídia
        
        Args:
            media_id: ID do arquivo de mídia
            
        Returns:
            str: URL do arquivo ou None se erro
        """
        if not self.access_token:
            logger.info(f"[SIMULAÇÃO] Obtendo URL para mídia {media_id}")
            return f"https://example.com/media/{media_id}"
        
        url = f"{self.base_url}/{media_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers )
            response.raise_for_status()
            
            data = response.json()
            return data.get('url')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter URL da mídia: {str(e)}")
            return None
    
    def download_media(self, media_url: str, save_path: str) -> bool:
        """
        Baixa um arquivo de mídia
        
        Args:
            media_url: URL do arquivo
            save_path: Caminho para salvar o arquivo
            
        Returns:
            bool: True se baixado com sucesso, False caso contrário
        """
        if not self.access_token:
            logger.info(f"[SIMULAÇÃO] Baixando mídia de {media_url} para {save_path}")
            return True
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(media_url, headers=headers)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Mídia baixada com sucesso: {save_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao baixar mídia: {str(e)}")
            return False
        except IOError as e:
            logger.error(f"Erro ao salvar arquivo: {str(e)}")
            return False

# Instância global da API
whatsapp_api = WhatsAppAPI()
