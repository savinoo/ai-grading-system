from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_question_criteria_override.reset_question_criteria_service_interface import ResetQuestionCriteriaServiceInterface
from src.interfaces.repositories.exam_question_criteria_override_repository_interface import ExamQuestionCriteriaOverrideRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class ResetQuestionCriteriaService(ResetQuestionCriteriaServiceInterface):
    """
    Serviço para resetar critérios de uma questão para os originais da prova.
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

    async def reset_question_criteria(
        self,
        db: Session,
        question_uuid: UUID
    ) -> int:
        """
        Remove todas as sobrescritas de critérios de uma questão,
        resetando para os critérios originais da prova.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            
        Returns:
            int: Número de sobrescritas removidas
            
        Raises:
            ValidateError: Se validações falharem
        """
        try:
            self.__logger.info("Resetando critérios da questão %s", question_uuid)

            # Busca a questão
            try:
                question = self.__question_repository.get_by_uuid(db, question_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Questão não encontrada",
                    context={"question_uuid": str(question_uuid)},
                    cause=exc
                ) from exc

            # Valida se a prova está em DRAFT
            exam = self.__exams_repository.get_by_uuid(db, question.exam_uuid)
            if exam.status != "DRAFT":
                raise ValidateError(
                    message="Critérios só podem ser resetados em provas em status DRAFT",
                    context={
                        "exam_uuid": str(question.exam_uuid),
                        "current_status": exam.status
                    }
                )

            # Valida se a questão não foi corrigida
            if question.is_graded:
                raise ValidateError(
                    message="Não é possível resetar critérios de questões já corrigidas",
                    context={"question_uuid": str(question_uuid)}
                )

            # Remove todas as sobrescritas
            deleted_count = self.__override_repository.delete_all_by_question(
                db,
                question_uuid
            )

            self.__logger.info(
                "Critérios resetados: %d sobrescritas removidas da questão %s",
                deleted_count,
                question_uuid
            )
            return deleted_count

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao resetar critérios: %s", e)
            raise SqlError(
                message="Erro ao resetar critérios no banco de dados",
                context={"question_uuid": str(question_uuid)},
                cause=e
            ) from e
