from __future__ import annotations

import asyncio
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.users.create_user_service_interface import CreateUserServiceInterface

from src.errors.domain.already_existing import AlreadyExistingError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger


class CreateUserController(ControllerInterface):
    """
    Controller que delega ao CreateUserService a criação de um novo usuário.
    """
    
    def __init__(self, service: CreateUserServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
    
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de criação de usuário.
        
        Args:
            http_request: Requisição HTTP contendo os dados do usuário
            
        Returns:
            HttpResponse: Resposta HTTP com os dados do usuário criado
            
        Raises:
            HTTPException: Em caso de erro (409 para email duplicado, 500 para erros de BD)
        """
        
        db = http_request.db
        caller = http_request.caller
        
        self.__logger.debug(
            "Handling create user request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )
        
        try:
            # O body já vem validado como UserCreateRequest pela rota FastAPI
            request = http_request.body
            
            # Delega ao serviço (agora async)
            result = asyncio.run(self.__service.create_user(db, request))
            
            self.__logger.info("Usuário criado com sucesso: %s", result.email)
            
            return HttpResponse(
                status_code=201,
                body={
                    "message": "Usuário criado com sucesso",
                    "data": result.model_dump(mode="json")
                }
            )
            
        except AlreadyExistingError as existing_err:
            self.__logger.warning("Email já cadastrado: %s", repr(existing_err))
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Email já está cadastrado",
                    "code": existing_err.code,
                    "context": existing_err.context
                }
            ) from existing_err
            
        except SqlError as sql_err:
            self.__logger.error("Erro de Banco de Dados: %s", repr(sql_err))
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao criar usuário",
                    "code": sql_err.code
                }
            ) from sql_err
            
        except ValueError as val_err:
            # Erros de validação do Pydantic
            self.__logger.warning("Erro de validação: %s", repr(val_err))
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Dados inválidos",
                    "message": str(val_err)
                }
            ) from val_err
            
        except Exception as exc:  # pylint: disable=broad-except
            self.__logger.error("Erro inesperado: %s", repr(exc), exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno no servidor"}
            ) from exc
