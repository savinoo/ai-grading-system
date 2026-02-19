"""
Controller para buscar análise de desempenho individual de um aluno em uma turma.
"""

from uuid import UUID

from fastapi import HTTPException

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.services.analytics.analytics_service import AnalyticsService
from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.errors.domain.not_found import NotFoundError
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class GetStudentPerformanceController(ControllerInterface):
    """Retorna perfil de desempenho individual de um aluno em uma turma."""

    def __init__(self, service: AnalyticsService) -> None:
        self.__service = service

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        logger.info(
            "Buscando performance do aluno — IP: %s",
            http_request.caller.ip,
        )

        try:
            class_uuid_str = http_request.param.get("class_uuid")
            student_uuid_str = http_request.param.get("student_uuid")

            if not class_uuid_str:
                raise ValueError("class_uuid é obrigatório")
            if not student_uuid_str:
                raise ValueError("student_uuid é obrigatório")

            teacher_uuid = http_request.token_infos.get("sub")
            if not teacher_uuid:
                raise ValueError("UUID do professor não encontrado no token")

            performance = self.__service.get_student_performance(
                db=http_request.db,
                student_uuid=UUID(student_uuid_str),
                class_uuid=UUID(class_uuid_str),
                teacher_uuid=UUID(teacher_uuid),
            )

            return HttpResponse(
                status_code=200,
                body=performance.model_dump(mode="json"),
            )

        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Erro ao buscar performance do aluno: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from e
