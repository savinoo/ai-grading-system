from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_question_criteria_override.create_question_criteria_override_service_interface import CreateQuestionCriteriaOverrideServiceInterface
from src.interfaces.repositories.exam_question_criteria_override_repository_interface import ExamQuestionCriteriaOverrideRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.grading_criteria_repository_interface import GradingCriteriaRepositoryInterface

from src.domain.requests.exam_question_criteria_override.criteria_override_create_request import ExamQuestionCriteriaOverrideCreateRequest
from src.domain.responses.exam_question_criteria_override.criteria_override_response import ExamQuestionCriteriaOverrideResponse

from src.models.entities.exam_question_criteria_override import ExamQuestionCriteriaOverride

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class CreateQuestionCriteriaOverrideService(CreateQuestionCriteriaOverrideServiceInterface):
    """
    Serviço para criação de sobrescritas de critérios de questões.
    """

    def __init__(
        self,
        override_repository: ExamQuestionCriteriaOverrideRepositoryInterface,
        question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface,
        grading_criteria_repository: GradingCriteriaRepositoryInterface
    ) -> None:
        self.__override_repository = override_repository
        self.__question_repository = question_repository
        self.__exams_repository = exams_repository
        self.__grading_criteria_repository = grading_criteria_repository
        self.__logger = get_logger(__name__)

    async def create_question_criteria_override(
        self,
        db: Session,
        request: ExamQuestionCriteriaOverrideCreateRequest
    ) -> ExamQuestionCriteriaOverrideResponse:
        """
        Cria uma sobrescrita de critério para uma questão.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da sobrescrita a ser criada
            
        Returns:
            ExamQuestionCriteriaOverrideResponse: Dados da sobrescrita criada
            
        Raises:
            ValidateError: Se validações falharem
        """
        try:
            self.__logger.info(
                "Criando sobrescrita de critério para questão %s",
                request.question_uuid
            )

            # Busca a questão
            try:
                question = self.__question_repository.get_by_uuid(db, request.question_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Questão não encontrada",
                    context={"question_uuid": str(request.question_uuid)},
                    cause=exc
                ) from exc

            # Valida se a prova está em DRAFT
            exam = self.__exams_repository.get_by_uuid(db, question.exam_uuid)
            if exam.status != "DRAFT":
                raise ValidateError(
                    message="Sobrescritas só podem ser criadas em provas em status DRAFT",
                    context={
                        "exam_uuid": str(question.exam_uuid),
                        "current_status": exam.status
                    }
                )

            # Valida se a questão não foi corrigida
            if question.is_graded:
                raise ValidateError(
                    message="Não é possível criar sobrescritas para questões já corrigidas",
                    context={"question_uuid": str(request.question_uuid)}
                )

            # Valida se o critério existe
            try:
                self.__grading_criteria_repository.get_by_uuid(db, request.criteria_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Critério de avaliação não encontrado",
                    context={"criteria_uuid": str(request.criteria_uuid)},
                    cause=exc
                ) from exc

            # Verifica se já existe uma sobrescrita para este critério
            existing = self.__override_repository.get_by_question_and_criteria(
                db,
                request.question_uuid,
                request.criteria_uuid
            )
            if existing:
                raise ValidateError(
                    message="Já existe uma sobrescrita para este critério nesta questão",
                    context={
                        "question_uuid": str(request.question_uuid),
                        "criteria_uuid": str(request.criteria_uuid)
                    }
                )

            # Cria a sobrescrita
            override_obj = self.__override_repository.create(
                db,
                uuid=uuid4(),
                question_uuid=request.question_uuid,
                criteria_uuid=request.criteria_uuid,
                weight_override=request.weight_override,
                max_points_override=request.max_points_override,
                active=True if request.active is None else request.active
            )

            self.__logger.info("Sobrescrita criada com sucesso: %s", override_obj.uuid)
            return self.__format_response(override_obj)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao criar sobrescrita: %s", e)
            raise SqlError(
                message="Erro ao criar sobrescrita no banco de dados",
                context={
                    "question_uuid": str(request.question_uuid),
                    "criteria_uuid": str(request.criteria_uuid)
                },
                cause=e
            ) from e

    def __format_response(
        self,
        override_obj: ExamQuestionCriteriaOverride
    ) -> ExamQuestionCriteriaOverrideResponse:
        """Formata a resposta."""
        return ExamQuestionCriteriaOverrideResponse.model_validate(override_obj)
