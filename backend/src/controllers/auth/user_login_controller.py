from __future__ import annotations

from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.errors.domain.unauthorized import UnauthorizedError
from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

from src.interfaces.services.auth.user_login_interface import UserLoginServiceInterface
from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.domain.requests.auth.login import UserLoginRequest

from src.core.logging_config import get_logger

class UserLoginController(ControllerInterface):
    """
    Controller que delega ao UserLoginService a autenticação do usuário.
    
    Attributes:
        __service (UserLoginServiceInterface): Serviço responsável por autenticar o usuário.
        __logger: Logger para registrar eventos e erros.
    """
    
    def __init__(self, service: UserLoginServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
        
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        db = http_request.db
        self.__logger.debug("meta: %s", http_request.caller)
        caller = http_request.caller
        self.__logger.debug("Handling login request from caller: %s - %s - %s", caller.caller_app, caller.caller_user, caller.ip)
        user_login_request: UserLoginRequest = UserLoginRequest(**http_request.body.dict())
        try:
            result = self.__service.login(db, user_login_request, caller)
            return HttpResponse(status_code=200, body=result)
        except NotFoundError as nfe:
            raise HTTPException(status_code=404, detail={"error": str(nfe)}) from nfe
        except UnauthorizedError as ue:
            raise HTTPException(status_code=401, detail={"error": str(ue)}) from ue
        except SqlError as sql_err:
            self.__logger.error("Database error: %s", repr(sql_err))
            raise HTTPException(status_code=500, detail={"error": "Erro no banco de dados enquanto autenticava o usuário"}) from sql_err
        except Exception as exc:  # pylint: disable=broad-except
            self.__logger.error("Unexpected error: %s", repr(exc))
            raise HTTPException(status_code=500, detail={"error": "Internal server error"}) from exc
