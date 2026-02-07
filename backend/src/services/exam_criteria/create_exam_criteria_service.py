from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_criteria.create_exam_criteria_service_interface import CreateExamCriteriaServiceInterface
from src.interfaces.repositories.exam_criteria_repository_interface import ExamCriteriaRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.grading_criteria_repository_interface import GradingCriteriaRepositoryInterface

from src.domain.requests.exam_criteria.exam_criteria_create_request import ExamCriteriaCreateRequest
from src.domain.responses.exam_criteria.exam_criteria_response import ExamCriteriaResponse

from src.models.entities.exam_criteria import ExamCriteria

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class CreateExamCriteriaService(CreateExamCriteriaServiceInterface):
    """
    Serviço para criação de critérios de prova.
    """

    def __init__(
        self,
        exam_criteria_repository: ExamCriteriaRepositoryInterface,
        exams_repository: ExamsRepositoryInterface,
        grading_criteria_repository: GradingCriteriaRepositoryInterface
    ) -> None:
        self.__exam_criteria_repository = exam_criteria_repository
        self.__exams_repository = exams_repository
        self.__grading_criteria_repository = grading_criteria_repository
        self.__logger = get_logger(__name__)

    async def create_exam_criteria(
        self,
        db: Session,
        request: ExamCriteriaCreateRequest
    ) -> ExamCriteriaResponse:
        """
        Cria um novo critério para uma prova.
        
        Args:
            db: Sessão do banco de dados
            request: Dados do critério a ser criado
            
        Returns:
            ExamCriteriaResponse: Dados do critério criado
            
        Raises:
            ValidateError: Se a prova não existir, não estiver em DRAFT ou critério não existir
        """
        try:
            self.__logger.info(
                "Criando critério para prova %s com critério %s",
                request.exam_uuid,
                request.criteria_uuid
            )

            # Valida se a prova existe e está em DRAFT
            try:
                exam = self.__exams_repository.get_by_uuid(db, request.exam_uuid)
                if exam.status != "DRAFT":
                    raise ValidateError(
                        message="Critérios só podem ser adicionados a provas em status DRAFT",
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

            # Valida se o critério de avaliação existe
            try:
                self.__grading_criteria_repository.get_by_uuid(db, request.criteria_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Critério de avaliação não encontrado",
                    context={"criteria_uuid": str(request.criteria_uuid)},
                    cause=exc
                ) from exc

            # Cria o critério da prova
            exam_criteria_obj = self.__exam_criteria_repository.create(
                db,
                uuid=uuid4(),
                exam_uuid=request.exam_uuid,
                criteria_uuid=request.criteria_uuid,
                weight=request.weight,
                max_points=request.max_points,
                active=True
            )

            self.__logger.info("Critério de prova criado com sucesso: %s", exam_criteria_obj.uuid)
            return self.__format_response(exam_criteria_obj)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao criar critério de prova: %s", e)
            raise SqlError(
                message="Erro ao criar critério de prova no banco de dados",
                context={
                    "exam_uuid": str(request.exam_uuid),
                    "criteria_uuid": str(request.criteria_uuid)
                },
                cause=e
            ) from e

    def __format_response(self, exam_criteria_obj: ExamCriteria) -> ExamCriteriaResponse:
        """
        Formata a resposta do critério de prova criado.
        
        Args:
            exam_criteria_obj: Entidade ExamCriteria
            
        Returns:
            ExamCriteriaResponse: Resposta formatada
        """
        return ExamCriteriaResponse.model_validate(exam_criteria_obj)
