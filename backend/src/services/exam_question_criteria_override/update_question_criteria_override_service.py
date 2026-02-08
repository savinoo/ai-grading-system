from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_question_criteria_override.update_question_criteria_override_service_interface import (
    UpdateQuestionCriteriaOverrideServiceInterface,
)
from src.interfaces.repositories.exam_question_criteria_override_repository_interface import (
    ExamQuestionCriteriaOverrideRepositoryInterface,
)
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.domain.requests.exam_question_criteria_override.criteria_override_update_request import (
    ExamQuestionCriteriaOverrideUpdateRequest,
)
from src.domain.responses.exam_question_criteria_override.criteria_override_response import (
    ExamQuestionCriteriaOverrideResponse,
)

from src.models.entities.exam_question_criteria_override import ExamQuestionCriteriaOverride

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class UpdateQuestionCriteriaOverrideService(UpdateQuestionCriteriaOverrideServiceInterface):
    """
    Serviço para atualização de sobrescritas de critérios de questões.
    """

    def __init__(
        self,
        override_repository: ExamQuestionCriteriaOverrideRepositoryInterface,
        question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__override_repository = override_repository
        self.__question_repository = question_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def update_question_criteria_override(
        self,
        db: Session,
        override_uuid: UUID,
        request: ExamQuestionCriteriaOverrideUpdateRequest
    ) -> ExamQuestionCriteriaOverrideResponse:
        """
        Atualiza uma sobrescrita de critério para uma questão.
        """
        try:
            self.__logger.info("Atualizando sobrescrita %s", override_uuid)

            try:
                override = self.__override_repository.get_by_uuid(db, override_uuid)
            except NoResultFound as exc:
                raise ValidateError(
                    message="Sobrescrita não encontrada",
                    context={"override_uuid": str(override_uuid)},
                    cause=exc
                ) from exc

            question = self.__question_repository.get_by_uuid(db, override.question_uuid)

            exam = self.__exams_repository.get_by_uuid(db, question.exam_uuid)
            if exam.status != "DRAFT":
                raise ValidateError(
                    message="Sobrescritas só podem ser atualizadas em provas em status DRAFT",
                    context={
                        "exam_uuid": str(question.exam_uuid),
                        "current_status": exam.status
                    }
                )

            if question.is_graded:
                raise ValidateError(
                    message="Não é possível atualizar sobrescritas de questões já corrigidas",
                    context={"question_uuid": str(override.question_uuid)}
                )

            updates = {}
            if request.weight_override is not None:
                updates["weight_override"] = request.weight_override
            if request.max_points_override is not None:
                updates["max_points_override"] = request.max_points_override
            if request.active is not None:
                updates["active"] = request.active

            if updates:
                override_obj = self.__override_repository.update(db, override.id, **updates)
            else:
                override_obj = override

            self.__logger.info("Sobrescrita atualizada com sucesso: %s", override_uuid)
            return self.__format_response(override_obj)

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao atualizar sobrescrita: %s", e)
            raise SqlError(
                message="Erro ao atualizar sobrescrita no banco de dados",
                context={"override_uuid": str(override_uuid)},
                cause=e
            ) from e

    def __format_response(
        self,
        override_obj: ExamQuestionCriteriaOverride
    ) -> ExamQuestionCriteriaOverrideResponse:
        """Formata a resposta."""
        return ExamQuestionCriteriaOverrideResponse.model_validate(override_obj)
