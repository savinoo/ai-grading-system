from abc import ABC, abstractmethod
from typing import List

from sqlalchemy.orm import Session

from src.domain.responses.grading_criteria.grading_criteria_response import GradingCriteriaResponse

class ListGradingCriteriaServiceInterface(ABC):
    """
    Interface para serviço de listagem de critérios de avaliação.
    """

    @abstractmethod
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
        raise NotImplementedError()
