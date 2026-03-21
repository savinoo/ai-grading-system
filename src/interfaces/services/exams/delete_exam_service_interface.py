from __future__ import annotations

from uuid import UUID
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

class DeleteExamServiceInterface(ABC):
    """
    Serviço para deletar uma prova.
    """
    @abstractmethod
    async def delete_exam(
        self,
        db: Session,
        exam_uuid: UUID,
        teacher_uuid: UUID
    ) -> None:
        """
        Deleta uma prova e todos os seus dados relacionados.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova a ser deletada
            teacher_uuid: UUID do professor (para validação de permissão)
            
        Raises:
            ValidateError: Se a prova não for encontrada ou o professor não tiver permissão
            SqlError: Se houver erro ao deletar
        """
        raise NotImplementedError()
