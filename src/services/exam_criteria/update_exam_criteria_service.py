from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_criteria.update_exam_criteria_service_interface import UpdateExamCriteriaServiceInterface
from src.interfaces.repositories.exam_criteria_repository_interface import ExamCriteriaRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.domain.requests.exam_criteria.exam_criteria_update_request import ExamCriteriaUpdateRequest
from src.domain.responses.exam_criteria.exam_criteria_response import ExamCriteriaResponse

from src.models.entities.exam_criteria import ExamCriteria

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class UpdateExamCriteriaService(UpdateExamCriteriaServiceInterface):
    """
    Serviço para atualização de critérios de prova.
    """

    def __init__(
        self,
        exam_criteria_repository: ExamCriteriaRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__exam_criteria_repository = exam_criteria_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def update_exam_criteria(
        self,
        db: Session,
        exam_criteria_uuid: UUID,
        request: ExamCriteriaUpdateRequest
    ) -> ExamCriteriaResponse:
        """
        Atualiza um critério de prova (peso e/ou pontuação máxima).
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_uuid: UUID do critério de prova
            request: Dados a serem atualizados
            
        Returns:
            ExamCriteriaResponse: Dados do critério atualizado
            
        Raises:
            ValidateError: Se o critério não existir ou a prova não estiver em DRAFT
        """
        try:
            self.__logger.info("Atualizando critério de prova %s", exam_criteria_uuid)

            # Busca o critério de prova
            try:
                exam_criteria = self.__exam_criteria_repository.get_by_uuid(db, exam_criteria_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Critério de prova não encontrado",
                    context={"exam_criteria_uuid": str(exam_criteria_uuid)},
                    cause=exc
                ) from exc

            # Valida se a prova está em DRAFT
            exam = self.__exams_repository.get_by_uuid(db, exam_criteria.exam_uuid)
            if exam.status != "DRAFT":
                raise ValidateError(
                    message="Critérios só podem ser atualizados em provas com status DRAFT",
                    context={
                        "exam_uuid": str(exam_criteria.exam_uuid),
                        "current_status": exam.status
                    }
                )

            # Prepara os dados para atualização
            updates = {}
            if request.weight is not None:
                updates["weight"] = request.weight
            if request.max_points is not None:
                updates["max_points"] = request.max_points

            # Atualiza o critério
            updated_criteria = self.__exam_criteria_repository.update(
                db,
                exam_criteria.id,
                **updates
            )

            self.__logger.info("Critério de prova atualizado com sucesso: %s", exam_criteria_uuid)
            return self.__format_response(updated_criteria)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao atualizar critério de prova: %s", e)
            raise SqlError(
                message="Erro ao atualizar critério de prova no banco de dados",
                context={"exam_criteria_uuid": str(exam_criteria_uuid)},
                cause=e
            ) from e

    def __format_response(self, exam_criteria_obj: ExamCriteria) -> ExamCriteriaResponse:
        """
        Formata a resposta do critério de prova atualizado.
        
        Args:
            exam_criteria_obj: Entidade ExamCriteria
            
        Returns:
            ExamCriteriaResponse: Resposta formatada
        """
        return ExamCriteriaResponse.model_validate(exam_criteria_obj)
