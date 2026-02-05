from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException

from src.core.logging_config import get_logger

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.users.verify_email_service_interface import VerifyEmailServiceInterface

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError


class VerifyEmailController(ControllerInterface):
    """
    Controller responsável por verificar o email de um usuário.
    """
    
    def __init__(self, service: VerifyEmailServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
    
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de verificação de email.
        
        Args:
            http_request: Requisição HTTP contendo o UUID do usuário
            
        Returns:
            HttpResponse: Resposta HTTP com tokens de autenticação
            
        Raises:
            HTTPException: Em caso de erro (404 se usuário não encontrado, 500 para erros de BD)
        """
        db = http_request.db
        caller = http_request.caller
        
        # O UUID vem nos path params
        user_uuid_str = http_request.param.get("uuid")
        
        if not user_uuid_str:
            self.__logger.error("UUID não fornecido na requisição")
            raise HTTPException(
                status_code=400,
                detail="UUID do usuário é obrigatório"
            )
        
        try:
            user_uuid = UUID(user_uuid_str)
        except ValueError as e:
            self.__logger.warning("UUID inválido: %s", user_uuid_str)
            raise HTTPException(
                status_code=400,
                detail="UUID inválido"
            ) from e
        
        try:
            result = self.__service.verify_email(db, user_uuid, caller)
            
            self.__logger.info(
                "Email verificado e usuário logado: %s (já verificado: %s)",
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
            self.__logger.error("Erro de banco de dados: %s", str(sql_err))
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro ao verificar email",
                    "code": sql_err.code
                }
            ) from sql_err
        
        except Exception as e:
            self.__logger.error("Erro inesperado: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
