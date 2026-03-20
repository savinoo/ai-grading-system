from __future__ import annotations

from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

from src.interfaces.services.auth.get_me_interface import GetMeServiceInterface
from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.core.logging_config import get_logger

class GetMeController(ControllerInterface):
    """
    Controller para obter informações do usuário logado.
    
    Attributes:
        __service: Serviço responsável por buscar informações do usuário.
        __logger: Logger para registrar eventos e erros.
    """
    
    def __init__(self, service: GetMeServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
    
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição para obter informações do usuário logado.
        
        Args:
            http_request: Requisição HTTP contendo token_infos.
        
        Returns:
            HttpResponse: Resposta HTTP com as informações do usuário.
        
        Raises:
            HTTPException: Em caso de erros de não encontrado ou banco de dados.
        """
        db = http_request.db
        caller = http_request.caller
        token_infos = http_request.token_infos
        
        self.__logger.debug(
            "Handling get me request from caller: %s - %s - %s",
            caller.caller_app,
            caller.caller_user,
            caller.ip
        )
        
        # Extrai o user_name do token
        sub = token_infos.get("sub")
        
        if not sub:
            self.__logger.error("Token não contém 'sub' (user_name)")
            raise HTTPException(
                status_code=401,
                detail={"error": "Token inválido: sub não encontrado"}
            )
        
        try:
            result = self.__service.execute(db=db, user_uuid=sub)
            return HttpResponse(status_code=200, body=result)
            
        except NotFoundError as nfe:
            self.__logger.warning("Not found error: %s", str(nfe))
            raise HTTPException(
                status_code=404,
                detail={"error": str(nfe)}
            ) from nfe
            
        except SqlError as sql_err:
            self.__logger.error("Database error: %s", repr(sql_err))
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro no banco de dados ao obter informações do usuário"}
            ) from sql_err
            
        except Exception as exc:
            self.__logger.error("Unexpected error: %s", repr(exc))
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal server error"}
            ) from exc
