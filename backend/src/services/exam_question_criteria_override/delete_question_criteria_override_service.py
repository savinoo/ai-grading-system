from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_question_criteria_override.delete_question_criteria_override_service_interface import (
    DeleteQuestionCriteriaOverrideServiceInterface,
)
from src.interfaces.repositories.exam_question_criteria_override_repository_interface import (
    ExamQuestionCriteriaOverrideRepositoryInterface,
)
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class DeleteQuestionCriteriaOverrideService(DeleteQuestionCriteriaOverrideServiceInterface):
    """
    Serviço para remoção de sobrescritas de critérios de questões.
    """

    def __init__(
        self,
        override_repository: ExamQuestionCriteriaOverrideRepositoryInterface,
        question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__override_repository = override_repository
        self.__question_repository = question_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def delete_question_criteria_override(
        self,
        db: Session,
        override_uuid: UUID
    ) -> None:
        """
        Remove uma sobrescrita de critério.
        """
        try:
            self.__logger.info("Removendo sobrescrita %s", override_uuid)

            try:
                override = self.__override_repository.get_by_uuid(db, override_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Sobrescrita não encontrada",
                    context={"override_uuid": str(override_uuid)},
                    cause=exc
                ) from exc

            question = self.__question_repository.get_by_uuid(db, override.question_uuid)

            exam = self.__exams_repository.get_by_uuid(db, question.exam_uuid)
            if exam.status != "DRAFT":
                raise ValidateError(
                    message="Sobrescritas só podem ser removidas de provas em status DRAFT",
                    context={
                        "exam_uuid": str(question.exam_uuid),
                        "current_status": exam.status
                    }
                )

            if question.is_graded:
                raise ValidateError(
                    message="Não é possível remover sobrescritas de questões já corrigidas",
                    context={"question_uuid": str(override.question_uuid)}
                )

            self.__override_repository.delete(db, override.id)

            self.__logger.info("Sobrescrita removida com sucesso: %s", override_uuid)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao remover sobrescrita: %s", e)
            raise SqlError(
                message="Erro ao remover sobrescrita no banco de dados",
                context={"override_uuid": str(override_uuid)},
                cause=e
            ) from e
