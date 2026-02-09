from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_questions.update_exam_question_service_interface import UpdateExamQuestionServiceInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.domain.requests.exam_questions.exam_question_update_request import ExamQuestionUpdateRequest
from src.domain.responses.exam_questions.exam_question_response import ExamQuestionResponse

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class UpdateExamQuestionService(UpdateExamQuestionServiceInterface):
    """
    Serviço para atualização de questões de prova.
    """

    def __init__(
        self,
        exam_question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__exam_question_repository = exam_question_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def update_exam_question(
        self,
        db: Session,
        question_uuid: UUID,
        teacher_uuid: UUID,
        request: ExamQuestionUpdateRequest
    ) -> ExamQuestionResponse:
        """
        Atualiza uma questão existente.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão a ser atualizada
            teacher_uuid: UUID do professor (para validação)
            request: Dados a serem atualizados
            
        Returns:
            ExamQuestionResponse: Questão atualizada
            
        Raises:
            ValidateError: Se a questão não existir ou o professor não tiver permissão
            SqlError: Se houver erro no banco de dados
        """
        try:
            self.__logger.info("Atualizando questão: %s", question_uuid)

            # Busca a questão
            try:
                question = self.__exam_question_repository.get_by_uuid(db, question_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Questão não encontrada",
                    context={"question_uuid": str(question_uuid)}
                ) from exc

            # Busca a prova para validar permissão
            try:
                exam = self.__exams_repository.get_by_uuid(db, question.exam_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Prova associada não encontrada",
                    context={"exam_uuid": str(question.exam_uuid)}
                ) from exc

            # Valida se o professor é o criador da prova
            if str(exam.created_by) != str(teacher_uuid):
                self.__logger.warning(
                    "Professor %s tentou atualizar questão de outro professor",
                    teacher_uuid
                )
                raise ValidateError(
                    message="Você não tem permissão para atualizar esta questão",
                    context={
                        "question_uuid": str(question_uuid),
                        "teacher_uuid": str(teacher_uuid)
                    }
                )

            # Prepara dados para atualização (apenas campos que foram fornecidos)
            updates = {}
            if request.statement is not None:
                updates["statement"] = request.statement
            if request.question_order is not None:
                updates["question_order"] = request.question_order
            if request.points is not None:
                updates["points"] = request.points
            if request.active is not None:
                updates["active"] = request.active

            # Atualiza a questão
            if updates:
                updated_question = self.__exam_question_repository.update(
                    db,
                    question.id,
                    **updates
                )
                db.commit()

                self.__logger.info("Questão atualizada com sucesso: %s", question_uuid)

                return ExamQuestionResponse.model_validate(updated_question)
            else:
                # Se não há nada para atualizar, retorna a questão como está
                self.__logger.info("Nenhuma alteração para aplicar na questão: %s", question_uuid)
                return ExamQuestionResponse.model_validate(question)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao atualizar questão: %s", str(e), exc_info=True)
            db.rollback()
            raise SqlError(
                message="Erro ao atualizar questão",
                context={"question_uuid": str(question_uuid)}
            ) from e
