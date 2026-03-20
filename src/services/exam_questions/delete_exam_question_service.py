from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_questions.delete_exam_question_service_interface import DeleteExamQuestionServiceInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class DeleteExamQuestionService(DeleteExamQuestionServiceInterface):
    """
    Serviço para remoção de questões de prova.
    """

    def __init__(
        self,
        exam_question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__exam_question_repository = exam_question_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def delete_exam_question(
        self,
        db: Session,
        question_uuid: UUID
    ) -> None:
        """
        Remove uma questão de uma prova.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            
        Raises:
            ValidateError: Se a prova não estiver em DRAFT ou questão já foi corrigida
        """
        try:
            self.__logger.info("Removendo questão %s", question_uuid)

            # Busca a questão
            try:
                question = self.__exam_question_repository.get_by_uuid(db, question_uuid)
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
                    message="Questões só podem ser removidas de provas em status DRAFT",
                    context={
                        "exam_uuid": str(question.exam_uuid),
                        "current_status": exam.status
                    }
                )

            # Valida se a questão não foi corrigida
            if question.is_graded:
                raise ValidateError(
                    message="Não é possível remover uma questão que já foi corrigida",
                    context={"question_uuid": str(question_uuid)}
                )

            # Remove a questão (cascade deletará as respostas)
            self.__exam_question_repository.delete(db, question.id)

            self.__logger.info("Questão removida com sucesso: %s", question_uuid)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao remover questão: %s", e)
            raise SqlError(
                message="Erro ao remover questão do banco de dados",
                context={"question_uuid": str(question_uuid)},
                cause=e
            ) from e
