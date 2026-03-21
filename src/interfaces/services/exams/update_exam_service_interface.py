from __future__ import annotations

from uuid import UUID
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.requests.exams.exam_update_request import ExamUpdateRequest
from src.domain.responses.exams.exam_response import ExamResponse

class UpdateExamServiceInterface(ABC):
    """
    Serviço para atualização de provas.
    """
    @abstractmethod
    async def update_exam(
        self,
        db: Session,
        exam_uuid: UUID,
        request: ExamUpdateRequest
    ) -> ExamResponse:
        """
        Atualiza uma prova.
        Apenas permite atualização se status = DRAFT.
        Para class_uuid, só permite se não houver respostas de alunos.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova a ser atualizada
            request: Dados a serem atualizados
            
        Returns:
            ExamResponse: Dados da prova atualizada
            
        Raises:
            NotFoundError: Se a prova não for encontrada
            ValidateError: Se a prova não estiver em status DRAFT ou se houver respostas
        """
        raise NotImplementedError()
