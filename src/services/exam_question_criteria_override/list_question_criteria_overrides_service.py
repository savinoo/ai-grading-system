from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exam_question_criteria_override.list_question_criteria_overrides_service_interface import ListQuestionCriteriaOverridesServiceInterface
from src.interfaces.repositories.exam_question_criteria_override_repository_interface import ExamQuestionCriteriaOverrideRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.domain.responses.exam_question_criteria_override.criteria_override_response import ExamQuestionCriteriaOverrideResponse

from src.models.entities.exam_question_criteria_override import ExamQuestionCriteriaOverride

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger


class ListQuestionCriteriaOverridesService(ListQuestionCriteriaOverridesServiceInterface):
    """
    Serviço para listagem de critérios customizados de uma questão.
    """

    def __init__(
        self,
        criteria_override_repository: ExamQuestionCriteriaOverrideRepositoryInterface,
        exam_question_repository: ExamQuestionRepositoryInterface,
        exams_repository: ExamsRepositoryInterface
    ) -> None:
        self.__criteria_override_repository = criteria_override_repository
        self.__exam_question_repository = exam_question_repository
        self.__exams_repository = exams_repository
        self.__logger = get_logger(__name__)

    async def list_question_criteria_overrides(
        self,
        db: Session,
        question_uuid: str,
        teacher_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[ExamQuestionCriteriaOverrideResponse]:
        """
        Lista critérios customizados de uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            teacher_uuid: UUID do professor autenticado
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas critérios ativos
            
        Returns:
            List[ExamQuestionCriteriaOverrideResponse]: Lista de critérios customizados
            
        Raises:
            ValidateError: Se a questão não existe ou não pertence ao professor
            SqlError: Em caso de erro de banco de dados
        """
        try:
            self.__logger.info(
                "Listando critérios customizados da questão %s (skip=%d, limit=%d, active_only=%s)",
                question_uuid, skip, limit, active_only
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
                    message="Você não tem permissão para acessar os critérios desta questão",
                    context={
                        "question_uuid": question_uuid,
                        "teacher_uuid": teacher_uuid
                    }
                )

            # Busca os critérios customizados
            criteria_overrides = self.__criteria_override_repository.get_by_question(
                db,
                UUID(question_uuid),
                skip=skip,
                limit=limit,
                active_only=active_only
            )

            self.__logger.info("Total de critérios customizados encontrados: %d", len(criteria_overrides))
            return [self.__format_response(override) for override in criteria_overrides]

        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao listar critérios customizados: %s", e)
            raise SqlError(
                message="Erro ao listar critérios customizados",
                context={"question_uuid": question_uuid},
                cause=e
            ) from e

    def __format_response(self, override_obj: ExamQuestionCriteriaOverride) -> ExamQuestionCriteriaOverrideResponse:
        """
        Formata a resposta de um critério customizado.
        
        Args:
            override_obj: Entidade ExamQuestionCriteriaOverride
            
        Returns:
            ExamQuestionCriteriaOverrideResponse: Resposta formatada
        """
        return ExamQuestionCriteriaOverrideResponse.model_validate(override_obj)
