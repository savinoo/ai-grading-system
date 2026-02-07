from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exams.get_exams_by_teacher_service import GetExamsByTeacherService

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class GetExamsByTeacherController(ControllerInterface):
    """  
    Controller que delega ao GetExamsByTeacherService a busca de provas por professor.
    """

    def __init__(self, service: GetExamsByTeacherService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de busca de provas por professor.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse: Resposta HTTP com os dados das provas
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller

        self.__logger.debug(
            "Handling get exams by teacher request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        teacher_uuid_str = http_request.param.get("teacher_uuid")
        if not teacher_uuid_str:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID do professor não fornecido"}
            )

        try:
            teacher_uuid = UUID(teacher_uuid_str)
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID do professor inválido"}
            ) from ve

        skip = int(http_request.param.get("skip", 0))
        limit = int(http_request.param.get("limit", 100))

        # active_only pode vir como bool ou string dependendo da origem
        active_only_raw = http_request.param.get("active_only", True)
        if isinstance(active_only_raw, bool):
            active_only = active_only_raw
        else:
            active_only = str(active_only_raw).lower() == "true"

        try:
            result = asyncio.run(
                self.__service.get_exams_by_teacher(
                    db,
                    teacher_uuid,
                    active_only=active_only,
                    skip=skip,
                    limit=limit
                )
            )

            self.__logger.info("Provas recuperadas com sucesso para professor: %s", teacher_uuid)

            return HttpResponse(
                status_code=200,
                body=result
            )

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao buscar provas: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao buscar provas",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.error("Erro inesperado ao buscar provas: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno ao buscar provas"}
            ) from e
