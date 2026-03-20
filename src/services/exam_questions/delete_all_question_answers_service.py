from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_questions.delete_all_question_answers_service_interface import DeleteAllQuestionAnswersServiceInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class DeleteAllQuestionAnswersService(DeleteAllQuestionAnswersServiceInterface):
    """
    Serviço para remoção de todas as respostas de uma questão.
    """

    def __init__(
        self,
        exam_question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface,
        student_answer_repository: StudentAnswerRepositoryInterface
    ) -> None:
        self.__exam_question_repository = exam_question_repository
        self.__exams_repository = exams_repository
        self.__student_answer_repository = student_answer_repository
        self.__logger = get_logger(__name__)

    async def delete_all_question_answers(
        self,
        db: Session,
        question_uuid: UUID
    ) -> int:
        """
        Remove todas as respostas de uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            
        Returns:
            int: Número de respostas removidas
            
        Raises:
            ValidateError: Se a prova não estiver em DRAFT ou questão já foi corrigida
        """
        try:
            self.__logger.info("Removendo todas as respostas da questão %s", question_uuid)

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
                    message="Respostas só podem ser removidas de provas em status DRAFT",
                    context={
                        "exam_uuid": str(question.exam_uuid),
                        "current_status": exam.status
                    }
                )

            # Valida se a questão não foi corrigida
            if question.is_graded:
                raise ValidateError(
                    message="Não é possível remover respostas de uma questão que já foi corrigida",
                    context={"question_uuid": str(question_uuid)}
                )

            # Lista todas as respostas e remove uma a uma
            answers = self.__student_answer_repository.get_by_question(
                db,
                question_uuid,
                skip=0,
                limit=10000  # Limite alto para pegar todas
            )

            deleted_count = 0
            for answer in answers:
                self.__student_answer_repository.delete(db, answer.id)
                deleted_count += 1

            self.__logger.info(
                "Removidas %d respostas da questão %s",
                deleted_count,
                question_uuid
            )
            return deleted_count

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao remover respostas da questão: %s", e)
            raise SqlError(
                message="Erro ao remover respostas do banco de dados",
                context={"question_uuid": str(question_uuid)},
                cause=e
            ) from e
