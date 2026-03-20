from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.classes.remove_student_from_class_service_interface import RemoveStudentFromClassServiceInterface

from src.errors.domain.sql_error import SqlError
from src.errors.domain.not_found import NotFoundError

from src.core.logging_config import get_logger

class RemoveStudentFromClassController(ControllerInterface):
    """  
    Controller que delega ao RemoveStudentFromClassService a remoção de um aluno de uma turma.
    """
    
    def __init__(self, service: RemoveStudentFromClassServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
        
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de remoção de aluno de uma turma.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse: Resposta HTTP com informações sobre a remoção
            
        Raises:
            HTTPException: Em caso de erro
        """
        
        db = http_request.db
        caller = http_request.caller
        
        class_uuid_str = http_request.param.get("class_uuid")
        student_uuid_str = http_request.param.get("student_uuid")
        
        if not class_uuid_str:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID da turma não fornecido"}
            )
        
        if not student_uuid_str:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID do aluno não fornecido"}
            )
        
        try:
            class_uuid = UUID(class_uuid_str)
            student_uuid = UUID(student_uuid_str)
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID inválido"}
            ) from ve
        
        self.__logger.debug(
            "Handling remove student from class request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )
        
        try:
            result = asyncio.run(
                self.__service.remove_student_from_class(db, class_uuid, student_uuid)
            )
            
            self.__logger.info(
                "Aluno %s removido da turma %s",
                student_uuid,
                class_uuid
            )
            
            return HttpResponse(
                status_code=200,
                body=result
            )
        
        except NotFoundError as not_found:
            self.__logger.warning("Recurso não encontrado: %s", not_found.message)
            raise HTTPException(
                status_code=404,
                detail={"error": not_found.message}
            ) from not_found
        
        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao remover aluno: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao remover aluno",
                    "code": sql_err.code
                }
            ) from sql_err
        
        except Exception as exc:
            self.__logger.error("Erro inesperado ao remover aluno: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno no servidor"}
            ) from exc
