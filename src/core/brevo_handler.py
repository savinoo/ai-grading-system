from __future__ import annotations

from typing import Dict, Any, Optional
from uuid import UUID

import httpx

from src.core.settings import settings
from src.core.logging_config import get_logger


class BrevoHandler:
    """
    Handler para integração com a API da Brevo (SendInBlue).
    
    Responsável por:
    - Criar/atualizar contatos na Brevo
    - Enviar emails transacionais via templates
    """
    
    def __init__(self):
        self.__logger = get_logger(__name__)
        self.__api_key = settings.BREVO_API_KEY
        self.__base_url = "https://api.brevo.com/v3"
        self.__headers = {
            "accept": "application/json",
            "api-key": self.__api_key,
            "content-type": "application/json"
        }
    
    async def create_or_update_contact(
        self, 
        email: str,
        first_name: str,
        last_name: str,
        user_uuid: UUID,
        user_type: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Cria ou atualiza um contato na Brevo.
        
        Args:
            email: Email do contato
            first_name: Primeiro nome do contato
            last_name: Sobrenome do contato
            user_uuid: UUID do usuário no banco de dados
            user_type: Tipo do usuário (admin, teacher, student)
            attributes: Atributos adicionais do contato
            
        Returns:
            bool: True se sucesso, False se falha
        """
        url = f"{self.__base_url}/contacts"
        
        payload = {
            "email": email,
            "attributes": {
                "NOME": first_name,
                "SOBRENOME": last_name,
                "UUID_DB": str(user_uuid),
                "USER_TYPE": user_type,
                **(attributes or {})
            },
            "updateEnabled": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=self.__headers)
                
                if response.status_code in [201, 204]:
                    self.__logger.info(
                        "Contato criado/atualizado na Brevo: email=%s, uuid=%s",
                        email, user_uuid
                    )
                    return True
                self.__logger.error(
                    "Erro ao criar contato na Brevo: status=%s, response=%s",
                    response.status_code, response.text
                )
                return False
                    
        except httpx.RequestError as e:
            self.__logger.error("Erro de conexão com Brevo API: %s", str(e), exc_info=True)
            return False
        except Exception as e:
            self.__logger.error("Erro inesperado ao criar contato na Brevo: %s", str(e), exc_info=True)
            return False
    
    async def send_verification_email(
        self, 
        email: str, 
        user_uuid: UUID,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Envia email de verificação usando template da Brevo.
        
        Args:
            email: Email do destinatário
            user_uuid: UUID do usuário (usado no template)
            user_name: Nome do usuário (opcional)
            
        Returns:
            bool: True se sucesso, False se falha
        """
        url = f"{self.__base_url}/smtp/email"
        
        payload = {
            "to": [{"email": email, "name": user_name or email}],
            "templateId": settings.BREVO_VERIFICATION_TEMPLATE_ID,
            "params": {
                "USER_NAME": user_name or email,
                "UUID_DB": str(user_uuid)
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=self.__headers)
                
                if response.status_code == 201:
                    self.__logger.info(
                        "Email de verificação enviado via Brevo: email=%s, uuid=%s",
                        email, user_uuid
                    )
                    return True
                self.__logger.error(
                    "Erro ao enviar email via Brevo: status=%s, response=%s",
                    response.status_code, response.text
                )
                return False
                    
        except httpx.RequestError as e:
            self.__logger.error("Erro de conexão com Brevo API: %s", str(e), exc_info=True)
            return False
        except Exception as e:
            self.__logger.error("Erro inesperado ao enviar email via Brevo: %s", str(e), exc_info=True)
            return False
    
    async def send_recovery_code_email(
        self,
        email: str,
        recovery_code: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Envia email com código de recuperação usando template da Brevo.
        
        Primeiro atualiza o atributo RECOVERY_CODE do contato, depois envia o email.
        
        Args:
            email: Email do destinatário
            recovery_code: Código de recuperação (será setado como atributo do contato)
            user_name: Nome do usuário (opcional)
            
        Returns:
            bool: True se sucesso, False se falha
        """
        # Primeiro, atualiza o atributo RECOVERY_CODE do contato
        contact_url = f"{self.__base_url}/contacts"
        contact_payload = {
            "email": email,
            "attributes": {
                "RECOVERY_CODE": recovery_code
            },
            "updateEnabled": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Atualiza o contato com o código
                contact_response = await client.post(
                    contact_url, 
                    json=contact_payload, 
                    headers=self.__headers
                )
                
                if contact_response.status_code not in [201, 204]:
                    self.__logger.error(
                        "Erro ao atualizar atributo RECOVERY_CODE: status=%s, response=%s",
                        contact_response.status_code, contact_response.text
                    )
                    return False
                
                self.__logger.info(
                    "Atributo RECOVERY_CODE atualizado no contato: email=%s",
                    email
                )
                
                # Agora envia o email usando o template
                email_url = f"{self.__base_url}/smtp/email"
                email_payload = {
                    "to": [{"email": email, "name": user_name or email}],
                    "templateId": settings.BREVO_RECOVERY_CODE_TEMPLATE_ID,
                    "params": {
                        "USER_NAME": user_name or email
                    }
                }
                
                email_response = await client.post(
                    email_url, 
                    json=email_payload, 
                    headers=self.__headers
                )
                
                if email_response.status_code == 201:
                    self.__logger.info(
                        "Email de código de recuperação enviado via Brevo: email=%s",
                        email
                    )
                    return True
                self.__logger.error(
                    "Erro ao enviar código via Brevo: status=%s, response=%s",
                    email_response.status_code, email_response.text
                )
                return False
                    
        except httpx.RequestError as e:
            self.__logger.error("Erro de conexão com Brevo API: %s", str(e), exc_info=True)
            return False
        except Exception as e:
            self.__logger.error("Erro inesperado ao enviar código via Brevo: %s", str(e), exc_info=True)
            return False
    
    async def clear_recovery_code(self, email: str) -> bool:
        """
        Limpa o atributo RECOVERY_CODE do contato na Brevo.
        
        Args:
            email: Email do contato
            
        Returns:
            bool: True se sucesso, False se falha
        """
        contact_url = f"{self.__base_url}/contacts"
        contact_payload = {
            "email": email,
            "attributes": {
                "RECOVERY_CODE": ""
            },
            "updateEnabled": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    contact_url,
                    json=contact_payload,
                    headers=self.__headers
                )
                
                if response.status_code in [201, 204]:
                    self.__logger.info(
                        "Atributo RECOVERY_CODE limpo no contato: email=%s",
                        email
                    )
                    return True
                self.__logger.error(
                    "Erro ao limpar RECOVERY_CODE: status=%s, response=%s",
                    response.status_code, response.text
                )
                return False
                    
        except httpx.RequestError as e:
            self.__logger.error("Erro de conexão com Brevo API: %s", str(e), exc_info=True)
            return False
        except Exception as e:
            self.__logger.error("Erro inesperado ao limpar RECOVERY_CODE: %s", str(e), exc_info=True)
            return False
