from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exams.get_exam_by_uuid_service_interface import GetExamByUuidServiceInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.domain.responses.exams.exam_response import ExamResponse

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class GetExamByUuidService(GetExamByUuidServiceInterface):
    """
    Serviço para buscar uma prova por UUID.
    """

    def __init__(self, repository: ExamsRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)

    async def get_exam_by_uuid(
        self,
        db: Session,
        exam_uuid: UUID
    ) -> ExamResponse:
        """
        Busca uma prova por UUID.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            ExamResponse: Dados da prova
            
        Raises:
            NotFoundError: Se a prova não for encontrada
        """
        try:
            self.__logger.info("Buscando prova: %s", exam_uuid)

            exam = self.__repository.get_by_uuid(db, exam_uuid)

            self.__logger.debug("Prova encontrada: %s", exam.title)

            return ExamResponse.model_validate(exam)

        except NoResultFound as e:
            self.__logger.warning("Prova não encontrada: %s", exam_uuid)
            raise NotFoundError(
                message="Prova não encontrada",
                context={"exam_uuid": str(exam_uuid)}
            ) from e
        except Exception as e:
            self.__logger.error("Erro ao buscar prova: %s", str(e), exc_info=True)
            raise SqlError(
                message="Erro ao buscar prova",
                context={"exam_uuid": str(exam_uuid)}
            ) from e
