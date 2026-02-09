from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.student_answers.list_student_answers_service_interface import ListStudentAnswersServiceInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.domain.responses.student_answers.student_answer_response import StudentAnswerResponse

from src.models.entities.student_answers import StudentAnswer

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger


class ListStudentAnswersService(ListStudentAnswersServiceInterface):
    """
    Serviço para listagem de respostas de alunos de uma questão.
    """

    def __init__(
        self,
        student_answer_repository: StudentAnswerRepositoryInterface,
        exam_question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__student_answer_repository = student_answer_repository
        self.__exam_question_repository = exam_question_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def list_student_answers(
        self,
        db: Session,
        question_uuid: str,
        teacher_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentAnswerResponse]:
        """
        Lista respostas de alunos de uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            teacher_uuid: UUID do professor autenticado
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            List[StudentAnswerResponse]: Lista de respostas
            
        Raises:
            ValidateError: Se a questão não existe ou não pertence ao professor
            SqlError: Em caso de erro de banco de dados
        """
        try:
            self.__logger.info(
                "Listando respostas da questão %s (skip=%d, limit=%d)",
                question_uuid, skip, limit
            )

            # Valida se a questão existe
            try:
                question = self.__exam_question_repository.get_by_uuid(db, UUID(question_uuid))
            except NoResultFound as exc:
                raise ValidateError(
                    message="Questão não encontrada",
                    context={"question_uuid": question_uuid},
                    cause=exc
                ) from exc

            # Verifica permissão através da prova
            try:
                exam = self.__exams_repository.get_by_uuid(db, question.exam_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Prova associada à questão não encontrada",
                    context={"question_uuid": question_uuid},
                    cause=exc
                ) from exc

            if str(exam.created_by) != str(teacher_uuid):
                raise ValidateError(
                    message="Você não tem permissão para acessar as respostas desta questão",
                    context={
                        "question_uuid": question_uuid,
                        "teacher_uuid": teacher_uuid
                    }
                )

            # Busca as respostas
            student_answers = self.__student_answer_repository.get_by_question(
                db,
                UUID(question_uuid),
                skip=skip,
                limit=limit
            )

            self.__logger.info("Total de respostas encontradas: %d", len(student_answers))
            return [self.__format_response(answer) for answer in student_answers]

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao listar respostas: %s", e)
            raise SqlError(
                message="Erro ao listar respostas de alunos",
                context={"question_uuid": question_uuid},
                cause=e
            ) from e

    def __format_response(self, answer_obj: StudentAnswer) -> StudentAnswerResponse:
        """
        Formata a resposta de uma resposta de aluno.
        
        Args:
            answer_obj: Entidade StudentAnswer
            
        Returns:
            StudentAnswerResponse: Resposta formatada
        """
        return StudentAnswerResponse.model_validate(answer_obj)
