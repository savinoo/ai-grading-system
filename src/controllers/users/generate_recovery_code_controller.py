from __future__ import annotations

import asyncio

from fastapi import HTTPException

from src.core.logging_config import get_logger

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.users.generate_recovery_code_service_interface import (
    GenerateRecoveryCodeServiceInterface
)

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError


class GenerateRecoveryCodeController(ControllerInterface):
    """
    Controller responsável por gerar código de recuperação.
    """
    
    def __init__(self, service: GenerateRecoveryCodeServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
    
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de geração de código de recuperação.
        
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
            # Serviço é async, então usamos asyncio.run
            result = asyncio.run(self.__service.generate_recovery_code(db, email))
            
            self.__logger.info(
                "Código de recuperação gerado para: %s",
                result.get("email")
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
            self.__logger.error("Erro ao gerar código: %s", str(sql_err))
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro ao gerar código de recuperação",
                    "code": sql_err.code
                }
            ) from sql_err
        
        except Exception as e:
            self.__logger.error("Erro inesperado: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
