from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.student_answers.delete_student_answer_service_interface import DeleteStudentAnswerServiceInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class DeleteStudentAnswerService(DeleteStudentAnswerServiceInterface):
    """
    Serviço para remoção de respostas de alunos.
    """

    def __init__(
        self,
        student_answer_repository: StudentAnswerRepositoryInterface,
        question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__student_answer_repository = student_answer_repository
        self.__question_repository = question_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def delete_student_answer(
        self,
        db: Session,
        answer_uuid: UUID
    ) -> None:
        """
        Remove uma resposta de aluno.
        
        Args:
            db: Sessão do banco de dados
            answer_uuid: UUID da resposta
            
        Raises:
            ValidateError: Se validações falharem
        """
        try:
            self.__logger.info("Removendo resposta %s", answer_uuid)

            # Busca a resposta
            try:
                answer = self.__student_answer_repository.get_by_uuid(db, answer_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Resposta não encontrada",
                    context={"answer_uuid": str(answer_uuid)},
                    cause=exc
                ) from exc

            # Busca a questão
            question = self.__question_repository.get_by_uuid(db, answer.question_uuid)

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

            # Valida se a resposta não foi corrigida
            if answer.is_graded:
                raise ValidateError(
                    message="Não é possível remover respostas que já foram corrigidas",
                    context={"answer_uuid": str(answer_uuid)}
                )

            # Remove a resposta
            self.__student_answer_repository.delete(db, answer.id)

            self.__logger.info("Resposta removida com sucesso: %s", answer_uuid)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao remover resposta: %s", e)
            raise SqlError(
                message="Erro ao remover resposta do banco de dados",
                context={"answer_uuid": str(answer_uuid)},
                cause=e
            ) from e
