from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.responses.exam_criteria.exam_criteria_response import ExamCriteriaResponse

class ListExamCriteriaServiceInterface(ABC):
    """
    Interface para serviço de listagem de critérios de prova.
    """

    @abstractmethod
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
        raise NotImplementedError()
