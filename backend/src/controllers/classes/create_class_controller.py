from __future__ import annotations

import asyncio
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.classes.create_class_service_interface import CreateClassServiceInterface

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class CreateClassController(ControllerInterface):
    """  
    Controller que delega ao CreateClassService a criação de uma nova turma.
    """
    
    def __init__(self, service: CreateClassServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
        
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de criação de turma.
        
        Args:
            http_request: Requisição HTTP contendo os dados da turma
            
        Returns:
            HttpResponse: Resposta HTTP com os dados da turma criada
            
        Raises:
            HTTPException: Em caso de erro
        """
        
        db = http_request.db
        caller = http_request.caller
        token_infos = http_request.token_infos
        
        self.__logger.debug(
            "Handling create class request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )
        
        try:
            request = http_request.body
            
            if not token_infos or not token_infos.get("sub"):
                raise HTTPException(
                    status_code=401,
                    detail={"error": "Usuário não autenticado"}
                )
            
            teacher_uuid = token_infos.get("sub")
            
            result = asyncio.run(self.__service.create_class(db, request, teacher_uuid))
            
            self.__logger.info("Turma criada com sucesso: %s", result.uuid)
            
            return HttpResponse(
                status_code=201,
                body=result
            )
        
        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao criar turma: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao criar turma",
                    "code": sql_err.code
                }
            ) from sql_err
        
        except ValueError as val_err:
            self.__logger.error("Erro de valor ao criar turma: %s", val_err, exc_info=True)
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Dados inválidos",
                    "message": str(val_err)
                }
            ) from val_err
        
        except Exception as exc:
            self.__logger.error("Erro inesperado ao criar turma: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno no servidor"}
            ) from exc
