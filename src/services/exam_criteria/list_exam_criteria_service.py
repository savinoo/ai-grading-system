from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from src.interfaces.services.exam_criteria.list_exam_criteria_service_interface import ListExamCriteriaServiceInterface
from src.interfaces.repositories.exam_criteria_repository_interface import ExamCriteriaRepositoryInterface

from src.domain.responses.exam_criteria.exam_criteria_response import ExamCriteriaResponse

from src.models.entities.exam_criteria import ExamCriteria

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class ListExamCriteriaService(ListExamCriteriaServiceInterface):
    """
    Serviço para listagem de critérios de uma prova.
    """

    def __init__(self, repository: ExamCriteriaRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)

    async def list_exam_criteria(
        self,
        db: Session,
        exam_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[ExamCriteriaResponse]:
        """
        Lista critérios de uma prova específica.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas critérios ativos
            
        Returns:
            List[ExamCriteriaResponse]: Lista de critérios da prova
        """
        try:
            self.__logger.info(
                "Listando critérios da prova %s (skip=%d, limit=%d, active_only=%s)",
                exam_uuid,
                skip,
                limit,
                active_only
            )

            criteria_list = self.__repository.get_by_exam(
                db,
                exam_uuid,
                skip=skip,
                limit=limit,
                active_only=active_only
            )

            self.__logger.info("Total de critérios encontrados: %d", len(criteria_list))
            
            responses = []
            for criteria in criteria_list:
                response = self.__format_response(criteria)
                responses.append(response)
                # Log do que está sendo retornado
                self.__logger.info(
                    "Critério %s: name=%s, description=%s",
                    response.uuid,
                    response.grading_criteria_name,
                    response.grading_criteria_description
                )
            
            return responses

        except Exception as e:
            self.__logger.error("Erro ao listar critérios da prova: %s", e)
            raise SqlError(
                message="Erro ao listar critérios da prova",
                context={"exam_uuid": str(exam_uuid)},
                cause=e
            ) from e

    def __format_response(self, exam_criteria_obj: ExamCriteria) -> ExamCriteriaResponse:
        """
        Formata a resposta de um critério de prova.
        
        Args:
            exam_criteria_obj: Entidade ExamCriteria
            
        Returns:
            ExamCriteriaResponse: Resposta formatada
        """
        response = ExamCriteriaResponse.model_validate(exam_criteria_obj)
        
        # Adicionar dados do grading_criteria se disponível
        try:
            if exam_criteria_obj.grading_criteria:
                response.grading_criteria_name = exam_criteria_obj.grading_criteria.name
                response.grading_criteria_description = exam_criteria_obj.grading_criteria.description
                self.__logger.info(
                    "Critério %s carregado com nome: %s",
                    exam_criteria_obj.uuid,
                    exam_criteria_obj.grading_criteria.name
                )
            else:
                self.__logger.warning("grading_criteria é None para exam_criteria %s", exam_criteria_obj.uuid)
        except Exception as e:
            self.__logger.error("Erro ao acessar grading_criteria: %s", e, exc_info=True)
        
        return response
