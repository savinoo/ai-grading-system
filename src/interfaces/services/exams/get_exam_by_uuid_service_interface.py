from __future__ import annotations

from uuid import UUID
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.responses.exams.exam_response import ExamResponse

class GetExamByUuidServiceInterface(ABC):
    """
    Serviço para buscar uma prova por UUID.
    """
    @abstractmethod
    async def get_exam_by_uuid(
        self,
        db: Session,
        exam_uuid: UUID
    ) -> ExamResponse:
        """
        Busca uma prova por UUID.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            ExamResponse: Dados da prova
            
        Raises:
            NotFoundError: Se a prova não for encontrada
        """
        raise NotImplementedError()
