from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound, IntegrityError

from src.interfaces.services.exam_questions.create_exam_question_service_interface import CreateExamQuestionServiceInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.domain.requests.exam_questions.exam_question_create_request import ExamQuestionCreateRequest
from src.domain.responses.exam_questions.exam_question_response import ExamQuestionResponse

from src.models.entities.exam_questions import ExamQuestion

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class CreateExamQuestionService(CreateExamQuestionServiceInterface):
    """
    Serviço para criação de questões de prova.
    """

    def __init__(
        self,
        exam_question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__exam_question_repository = exam_question_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def create_exam_question(
        self,
        db: Session,
        request: ExamQuestionCreateRequest
    ) -> ExamQuestionResponse:
        """
        Cria uma nova questão para uma prova.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da questão a ser criada
            
        Returns:
            ExamQuestionResponse: Dados da questão criada
            
        Raises:
            ValidateError: Se a prova não existir ou não estiver em DRAFT
        """
        try:
            self.__logger.info(
                "Criando questão para prova %s (ordem: %d)",
                request.exam_uuid,
                request.question_order
            )

            # Valida se a prova existe e está em DRAFT
            try:
                exam = self.__exams_repository.get_by_uuid(db, request.exam_uuid)
                if exam.status != "DRAFT":
                    raise ValidateError(
                        message="Questões só podem ser adicionadas a provas em status DRAFT",
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

            # Cria a questão
            try:
                question_obj = self.__exam_question_repository.create(
                    db,
                    uuid=uuid4(),
                    exam_uuid=request.exam_uuid,
                    statement=request.statement,
                    question_order=request.question_order,
                    points=request.points,
                    active=True
                )
            except IntegrityError as exc:
                raise ValidateError(
                    message="Já existe uma questão com esta ordem nesta prova",
                    context={
                        "exam_uuid": str(request.exam_uuid),
                        "question_order": request.question_order
                    },
                    cause=exc
                ) from exc

            self.__logger.info("Questão criada com sucesso: %s", question_obj.uuid)
            return self.__format_response(question_obj)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao criar questão: %s", e)
            raise SqlError(
                message="Erro ao criar questão no banco de dados",
                context={
                    "exam_uuid": str(request.exam_uuid),
                    "question_order": request.question_order
                },
                cause=e
            ) from e

    def __format_response(self, question_obj: ExamQuestion) -> ExamQuestionResponse:
        """
        Formata a resposta da questão criada.
        
        Args:
            question_obj: Entidade ExamQuestion
            
        Returns:
            ExamQuestionResponse: Resposta formatada
        """
        return ExamQuestionResponse.model_validate(question_obj)
