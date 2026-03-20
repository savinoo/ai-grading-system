from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_criteria.delete_exam_criteria_service_interface import DeleteExamCriteriaServiceInterface
from src.interfaces.repositories.exam_criteria_repository_interface import ExamCriteriaRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class DeleteExamCriteriaService(DeleteExamCriteriaServiceInterface):
    """
    Serviço para remoção de critérios de prova.
    """

    def __init__(
        self,
        exam_criteria_repository: ExamCriteriaRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__exam_criteria_repository = exam_criteria_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def delete_exam_criteria(
        self,
        db: Session,
        exam_criteria_uuid: UUID
    ) -> None:
        """
        Remove um critério de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_uuid: UUID do critério de prova
            
        Raises:
            ValidateError: Se o critério não existir ou a prova não estiver em DRAFT
        """
        try:
            self.__logger.info("Removendo critério de prova %s", exam_criteria_uuid)

            # Busca o critério de prova
            try:
                exam_criteria = self.__exam_criteria_repository.get_by_uuid(db, exam_criteria_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Critério de prova não encontrado",
                    context={"exam_criteria_uuid": str(exam_criteria_uuid)},
                    cause=exc
                ) from exc

            # Valida se a prova está em DRAFT
            exam = self.__exams_repository.get_by_uuid(db, exam_criteria.exam_uuid)
            if exam.status != "DRAFT":
                raise ValidateError(
                    message="Critérios só podem ser removidos de provas com status DRAFT",
                    context={
                        "exam_uuid": str(exam_criteria.exam_uuid),
                        "current_status": exam.status
                    }
                )

            # Remove o critério
            self.__exam_criteria_repository.delete(db, exam_criteria.id)

            self.__logger.info("Critério de prova removido com sucesso: %s", exam_criteria_uuid)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao remover critério de prova: %s", e)
            raise SqlError(
                message="Erro ao remover critério de prova do banco de dados",
                context={"exam_criteria_uuid": str(exam_criteria_uuid)},
                cause=e
            ) from e
