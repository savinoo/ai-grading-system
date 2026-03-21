from __future__ import annotations

from abc import ABC, abstractmethod

from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.responses.classes.classes_response import ClassesResponse

class GetClassesServiceInterface(ABC):
    """ 
    Serviço para buscar turma com seus alunos.
    """
    
    @abstractmethod  
    async def get_classes(
        self,
        db: Session,
        teacher_uuid: UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> ClassesResponse:
        """
        Busca todas as turmas de um professor.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            active_only: Se deve retornar apenas alunos ativos
            skip: Número de alunos a pular na paginação
            limit: Número máximo de alunos a retornar
            
        Returns:
            ClassesResponse: Lista de turmas do professor
        """
        raise NotImplementedError()
