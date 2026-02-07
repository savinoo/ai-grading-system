from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from src.interfaces.services.exams.get_exams_by_teacher_service_interface import GetExamsByTeacherServiceInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.domain.responses.exams.exams_list_response import ExamsListResponse
from src.domain.responses.exams.exam_response import ExamResponse

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class GetExamsByTeacherService(GetExamsByTeacherServiceInterface):
    """
    Serviço para listar provas de um professor.
    """

    def __init__(self, repository: ExamsRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)

    async def get_exams_by_teacher(
        self,
        db: Session,
        teacher_uuid: UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> ExamsListResponse:
        """
        Busca todas as provas ativas de um professor.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            active_only: Se deve retornar apenas provas ativas
            skip: Número de provas a pular na paginação
            limit: Número máximo de provas a retornar
            
        Returns:
            ExamsListResponse: Lista de provas do professor
        """
        try:
            self.__logger.info("Buscando provas para o professor: %s", teacher_uuid)

            exams = self.__repository.get_by_teacher(
                db,
                teacher_uuid,
                skip=skip,
                limit=limit,
                active_only=active_only
            )

            exams_data = [ExamResponse.model_validate(exam) for exam in exams]

            self.__logger.debug("Encontradas %d provas para o professor %s", len(exams_data), teacher_uuid)

            return ExamsListResponse(
                exams=exams_data,
                total=len(exams_data)
            )

        except Exception as e:
            self.__logger.error("Erro ao buscar provas do professor: %s", str(e), exc_info=True)
            raise SqlError(
                message="Erro ao buscar provas",
                context={"teacher_uuid": str(teacher_uuid)}
            ) from e
