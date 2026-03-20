from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from src.interfaces.services.grading_criteria.list_grading_criteria_service_interface import ListGradingCriteriaServiceInterface
from src.interfaces.repositories.grading_criteria_repository_interface import GradingCriteriaRepositoryInterface

from src.domain.responses.grading_criteria.grading_criteria_response import GradingCriteriaResponse

from src.models.entities.grading_criteria import GradingCriteria

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class ListGradingCriteriaService(ListGradingCriteriaServiceInterface):
    """
    Serviço para listagem de critérios de avaliação disponíveis.
    """

    def __init__(self, repository: GradingCriteriaRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)

    async def list_grading_criteria(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[GradingCriteriaResponse]:
        """
        Lista critérios de avaliação disponíveis.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas critérios ativos
            
        Returns:
            List[GradingCriteriaResponse]: Lista de critérios de avaliação
        """
        try:
            self.__logger.info("Listando critérios de avaliação (skip=%d, limit=%d, active_only=%s)", skip, limit, active_only)

            criteria_list = self.__repository.get_all(
                db,
                skip=skip,
                limit=limit,
                active_only=active_only
            )

            self.__logger.info("Total de critérios encontrados: %d", len(criteria_list))
            return [self.__format_response(criteria) for criteria in criteria_list]

        except Exception as e:
            self.__logger.error("Erro ao listar critérios de avaliação: %s", e)
            raise SqlError(
                message="Erro ao listar critérios de avaliação",
                context={"skip": skip, "limit": limit},
                cause=e
            ) from e

    def __format_response(self, criteria_obj: GradingCriteria) -> GradingCriteriaResponse:
        """
        Formata a resposta de um critério de avaliação.
        
        Args:
            criteria_obj: Entidade GradingCriteria
            
        Returns:
            GradingCriteriaResponse: Resposta formatada
        """
        return GradingCriteriaResponse.model_validate(criteria_obj)
