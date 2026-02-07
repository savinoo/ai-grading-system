from __future__ import annotations

from uuid import UUID
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.requests.exams.exam_create_request import ExamCreateRequest
from src.domain.responses.exams.exam_create_response import ExamCreateResponse

class CreateExamServiceInterface(ABC):
    """
    Serviço para criação de provas.
    """
    @abstractmethod
    async def create_exam(
        self,
        db: Session,
        request: ExamCreateRequest,
        teacher_uuid: UUID
    ) -> ExamCreateResponse:
        """
        Cria uma nova prova.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da prova a ser criada
            teacher_uuid: UUID do professor que está criando a prova
            
        Returns:
            ExamCreateResponse: Dados da prova criada
        """
        raise NotImplementedError()
