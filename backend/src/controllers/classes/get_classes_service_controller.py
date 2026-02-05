from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.classes.get_classes_service_interface import GetClassesServiceInterface

from src.errors.domain.sql_error import SqlError
from src.errors.domain.not_found import NotFoundError

from src.core.logging_config import get_logger

class GetClassesServiceController(ControllerInterface):
    """  
    Controller que delega ao GetClassesService a busca de turmas.
    """
    
    def __init__(self, service: GetClassesServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
        
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de busca de turmas.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse: Resposta HTTP com os dados das turmas
            
        Raises:
            HTTPException: Em caso de erro
        """
        
        db = http_request.db
        caller = http_request.caller
        
        self.__logger.debug(
            "Handling get class with students request from caller: %s - %s - %s", 
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
                self.__service.get_classes(
                    db,
                    teacher_uuid,
                    active_only=active_only,
                    skip=skip,
                    limit=limit
                )
            )
            
            self.__logger.info(
                "Turmas buscadas com sucesso para o professor: %s",
                teacher_uuid
            )
            
            return HttpResponse(
                status_code=200, 
                body=result
            )
        except NotFoundError as nfe:
            self.__logger.warning(
                "Nenhuma turma encontrada para o professor %s: %s",
                teacher_uuid,
                nfe
            )
            raise HTTPException(
                status_code=404,
                detail={"error": "Nenhuma turma encontrada para o professor"}
            ) from nfe
        
        except SqlError as sqle:
            self.__logger.error(
                "Erro de SQL ao buscar turmas para o professor %s: %s",
                teacher_uuid,
                sqle
            )
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro ao acessar o banco de dados"}
            ) from sqle
            
        except Exception as e:
            self.__logger.error(
                "Erro inesperado ao buscar turmas para o professor %s: %s",
                teacher_uuid,
                e,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno do servidor"}
            ) from e
