from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound, IntegrityError

from src.interfaces.services.student_answers.create_student_answer_service_interface import CreateStudentAnswerServiceInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.student_repository_interface import StudentRepositoryInterface

from src.domain.requests.student_answers.student_answer_create_request import StudentAnswerCreateRequest
from src.domain.responses.student_answers.student_answer_response import StudentAnswerResponse

from src.models.entities.student_answers import StudentAnswer

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class CreateStudentAnswerService(CreateStudentAnswerServiceInterface):
    """
    Serviço para criação de respostas de alunos.
    """

    def __init__(
        self,
        student_answer_repository: StudentAnswerRepositoryInterface,
        question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface,
        student_repository: StudentRepositoryInterface
    ) -> None:
        self.__student_answer_repository = student_answer_repository
        self.__question_repository = question_repository
        self.__exams_repository = exams_repository
        self.__student_repository = student_repository
        self.__logger = get_logger(__name__)

    async def create_student_answer(
        self,
        db: Session,
        request: StudentAnswerCreateRequest
    ) -> StudentAnswerResponse:
        """
        Cria uma nova resposta de aluno.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da resposta a ser criada
            
        Returns:
            StudentAnswerResponse: Dados da resposta criada
            
        Raises:
            ValidateError: Se validações falharem
        """
        try:
            self.__logger.info(
                "Criando resposta para questão %s do aluno %s",
                request.question_uuid,
                request.student_uuid
            )

            # Valida se a prova existe e está em DRAFT
            try:
                exam = self.__exams_repository.get_by_uuid(db, request.exam_uuid)
                if exam.status != "DRAFT":
                    raise ValidateError(
                        message="Respostas só podem ser criadas para provas em status DRAFT",
                        context={
                            "exam_uuid": str(request.exam_uuid),
                            "current_status": exam.status
                        }
                    )
            except NoResultFound as exc:
                raise ValidateError(
                    message="Prova não encontrada",
                    context={"exam_uuid": str(request.exam_uuid)},
                    cause=exc
                ) from exc

            # Valida se a questão existe e pertence à prova
            try:
                question = self.__question_repository.get_by_uuid(db, request.question_uuid)
                if question.exam_uuid != request.exam_uuid:
                    raise ValidateError(
                        message="A questão não pertence à prova informada",
                        context={
                            "question_uuid": str(request.question_uuid),
                            "exam_uuid": str(request.exam_uuid)
                        }
                    )
                if question.is_graded:
                    raise ValidateError(
                        message="Não é possível criar respostas para questões já corrigidas",
                        context={"question_uuid": str(request.question_uuid)}
                    )
            except NoResultFound as exc:
                raise ValidateError(
                    message="Questão não encontrada",
                    context={"question_uuid": str(request.question_uuid)},
                    cause=exc
                ) from exc

            # Valida se o aluno existe
            try:
                self.__student_repository.get_by_uuid(db, request.student_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Aluno não encontrado",
                    context={"student_uuid": str(request.student_uuid)},
                    cause=exc
                ) from exc

            # Cria a resposta
            try:
                answer_obj = self.__student_answer_repository.create(
                    db,
                    uuid=uuid4(),
                    exam_uuid=request.exam_uuid,
                    question_uuid=request.question_uuid,
                    student_uuid=request.student_uuid,
                    answer=request.answer,
                    status="SUBMITTED"
                )
            except IntegrityError as exc:
                raise ValidateError(
                    message="Já existe uma resposta deste aluno para esta questão",
                    context={
                        "student_uuid": str(request.student_uuid),
                        "question_uuid": str(request.question_uuid)
                    },
                    cause=exc
                ) from exc

            self.__logger.info("Resposta criada com sucesso: %s", answer_obj.uuid)
            return self.__format_response(answer_obj)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao criar resposta: %s", e)
            raise SqlError(
                message="Erro ao criar resposta no banco de dados",
                context={
                    "student_uuid": str(request.student_uuid),
                    "question_uuid": str(request.question_uuid)
                },
                cause=e
            ) from e

    def __format_response(self, answer_obj: StudentAnswer) -> StudentAnswerResponse:
        """Formata a resposta."""
        return StudentAnswerResponse.model_validate(answer_obj)
