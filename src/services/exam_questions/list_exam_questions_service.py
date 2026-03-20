from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_questions.list_exam_questions_service_interface import ListExamQuestionsServiceInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.domain.responses.exam_questions.exam_question_response import ExamQuestionResponse

from src.models.entities.exam_questions import ExamQuestion

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger


class ListExamQuestionsService(ListExamQuestionsServiceInterface):
    """
    Serviço para listagem de questões de uma prova.
    """

    def __init__(
        self,
        exam_question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__exam_question_repository = exam_question_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def list_exam_questions(
        self,
        db: Session,
        exam_uuid: str,
        teacher_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[ExamQuestionResponse]:
        """
        Lista questões de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            teacher_uuid: UUID do professor autenticado
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas questões ativas
            
        Returns:
            List[ExamQuestionResponse]: Lista de questões da prova
            
        Raises:
            ValidateError: Se a prova não existe ou não pertence ao professor
            SqlError: Em caso de erro de banco de dados
        """
        try:
            self.__logger.info(
                "Listando questões da prova %s (skip=%d, limit=%d, active_only=%s)",
                exam_uuid, skip, limit, active_only
            )

            # Valida se a prova existe e pertence ao professor
            try:
                exam = self.__exams_repository.get_by_uuid(db, exam_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Prova não encontrada",
                    context={"exam_uuid": exam_uuid},
                    cause=exc
                ) from exc

            # Verifica permissão
            if str(exam.created_by) != str(teacher_uuid):
                raise ValidateError(
                    message="Você não tem permissão para acessar as questões desta prova",
                    context={
                        "exam_uuid": exam_uuid,
                        "teacher_uuid": teacher_uuid
                    }
                )

            # Busca as questões
            questions = self.__exam_question_repository.get_by_exam(
                db,
                exam_uuid,
                skip=skip,
                limit=limit,
                active_only=active_only
            )

            self.__logger.info("Total de questões encontradas: %d", len(questions))
            return [self.__format_response(q) for q in questions]

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao listar questões: %s", e)
            raise SqlError(
                message="Erro ao listar questões",
                context={"exam_uuid": exam_uuid},
                cause=e
            ) from e

    def __format_response(self, question_obj: ExamQuestion) -> ExamQuestionResponse:
        """
        Formata a resposta de uma questão.
        
        Args:
            question_obj: Entidade ExamQuestion
            
        Returns:
            ExamQuestionResponse: Resposta formatada
        """
        return ExamQuestionResponse.model_validate(question_obj)

