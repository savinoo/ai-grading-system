"""
Controller para listar análises pedagógicas de todas as turmas do professor.
"""

from fastapi import HTTPException

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.services.analytics.analytics_service import AnalyticsService
from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ListClassesAnalyticsController(ControllerInterface):
    """Retorna sumário analítico de todas as turmas do professor autenticado."""

    def __init__(self, service: AnalyticsService) -> None:
        self.__service = service

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        logger.info(
            "Listando analytics das turmas — IP: %s",
            http_request.caller.ip,
        )

        try:
            teacher_uuid = http_request.token_infos.get("sub")
            if not teacher_uuid:
                raise ValueError("UUID do professor não encontrado no token")

            from uuid import UUID
            summaries = self.__service.list_classes_analytics(
                db=http_request.db,
                teacher_uuid=UUID(teacher_uuid),
            )

            return HttpResponse(
                status_code=200,
                body=[s.model_dump(mode="json") for s in summaries],
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Erro ao listar analytics de turmas: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from e
