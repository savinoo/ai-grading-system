from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.classes.get_class_with_students_service_interface import GetClassWithStudentsServiceInterface

from src.errors.domain.sql_error import SqlError
from src.errors.domain.not_found import NotFoundError

from src.core.logging_config import get_logger

class GetClassWithStudentsController(ControllerInterface):
    """  
    Controller que delega ao GetClassWithStudentsService a busca de uma turma com seus alunos.
    """
    
    def __init__(self, service: GetClassWithStudentsServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
        
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de busca de turma com alunos.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse: Resposta HTTP com os dados da turma e seus alunos
            
        Raises:
            HTTPException: Em caso de erro
        """
        
        db = http_request.db
        caller = http_request.caller
        
        class_uuid_str = http_request.param.get("class_uuid")
        if not class_uuid_str:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID da turma não fornecido"}
            )
        
        try:
            class_uuid = UUID(class_uuid_str)
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID da turma inválido"}
            ) from ve
        
        skip = int(http_request.param.get("skip", 0))
        limit = int(http_request.param.get("limit", 100))
        
        # active_only pode vir como bool ou string dependendo da origem
        active_only_raw = http_request.param.get("active_only", True)
        if isinstance(active_only_raw, bool):
            active_only = active_only_raw
        else:
            active_only = str(active_only_raw).lower() == "true"
        
        self.__logger.debug(
            "Handling get class with students request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )
        
        try:
            result = asyncio.run(
                self.__service.get_class_with_students(
                    db,
                    class_uuid,
                    active_only=active_only,
                    skip=skip,
                    limit=limit
                )
            )
            
            self.__logger.info(
                "Turma %s retornada com %d alunos",
                class_uuid,
                result.total_students
            )
            
            return HttpResponse(
                status_code=200,
                body=result
            )
        
        except NotFoundError as not_found:
            self.__logger.warning("Turma não encontrada: %s", class_uuid)
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Turma não encontrada",
                    "class_uuid": str(class_uuid)
                }
            ) from not_found
        
        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao buscar turma: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao buscar turma",
                    "code": sql_err.code
                }
            ) from sql_err
        
        except Exception as exc:
            self.__logger.error("Erro inesperado ao buscar turma: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno no servidor"}
            ) from exc
