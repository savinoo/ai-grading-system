from __future__ import annotations

from uuid import UUID
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.responses.exams.exams_list_response import ExamsListResponse

class GetExamsByTeacherServiceInterface(ABC):
    """
    Serviço para listar provas de um professor.
    """
    @abstractmethod
    async def get_exams_by_teacher(
        self,
        db: Session,
        teacher_uuid: UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> ExamsListResponse:
        """
        Busca todas as provas ativas de um professor.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            active_only: Se deve retornar apenas provas ativas
            skip: Número de provas a pular na paginação
            limit: Número máximo de provas a retornar
            
        Returns:
            ExamsListResponse: Lista de provas do professor
        """
        raise NotImplementedError()
