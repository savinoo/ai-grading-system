from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.requests.exam_criteria.exam_criteria_create_request import ExamCriteriaCreateRequest
from src.domain.responses.exam_criteria.exam_criteria_response import ExamCriteriaResponse

class CreateExamCriteriaServiceInterface(ABC):
    """
    Interface para serviço de criação de critério de prova.
    """

    @abstractmethod
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
        """
        raise NotImplementedError()
