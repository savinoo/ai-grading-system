from __future__ import annotations

from fastapi import HTTPException

from src.core.logging_config import get_logger

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.async_controllers_interface import AsyncControllerInterface
from src.interfaces.services.users.resend_verification_email_service_interface import (
    ResendVerificationEmailServiceInterface
)

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError


class ResendVerificationEmailController(AsyncControllerInterface):
    """
    Controller responsável por reenviar email de verificação.
    """
    
    def __init__(self, service: ResendVerificationEmailServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger("controllers")
    
    async def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de reenvio de email de verificação.
        
        Args:
            http_request: Requisição HTTP contendo o email do usuário
            
        Returns:
            HttpResponse: Resposta HTTP com confirmação
            
        Raises:
            HTTPException: Em caso de erro
        """
        db = http_request.db
        body = http_request.body
        
        email = body.get("email")
        
        if not email:
            self.__logger.error("Email não fornecido na requisição")
            raise HTTPException(
                status_code=400,
                detail="Email é obrigatório"
            )
        
        try:
            result = await self.__service.resend_verification_email(db, email)
            
            self.__logger.info(
                "Email de verificação processado para: %s (já verificado: %s)",
                result.get("email"),
                result.get("already_verified")
            )
            
            return HttpResponse(
                status_code=200,
                body=result
            )
            
        except NotFoundError as nfe:
            self.__logger.warning("Usuário não encontrado: %s", str(nfe))
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Usuário não encontrado",
                    "code": nfe.code,
                    "context": nfe.context
                }
            ) from nfe
        
        except SqlError as sql_err:
            self.__logger.error("Erro ao processar reenvio: %s", str(sql_err))
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro ao enviar email de verificação",
                    "code": sql_err.code
                }
            ) from sql_err
        
        except Exception as e:
            self.__logger.error("Erro inesperado: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
