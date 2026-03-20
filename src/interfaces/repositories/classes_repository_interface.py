from abc import ABC, abstractmethod
from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy.orm import Session

from src.models.entities.classes import Classes

class ClassesRepositoryInterface(ABC):
    """
    Interface para o repositório de Classes.
    """
    
    # ==================== READ OPERATIONS ====================
    
    @abstractmethod
    def get_by_id(self, db: Session, class_id: int) -> Classes:
        """Busca turma por ID."""
        raise NotImplementedError()
    
    @abstractmethod
    def get_by_uuid(self, db: Session, uuid: UUID) -> Classes:
        """Busca turma por UUID."""
        raise NotImplementedError()
    
    @abstractmethod
    def get_all(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Classes]:
        """Lista todas as turmas com paginação."""
        raise NotImplementedError()
    
    @abstractmethod
    def get_by_teacher(
        self,
        db: Session,
        teacher_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Classes]:
        """Lista turmas de um professor específico."""
        raise NotImplementedError()
    
    @abstractmethod
    def get_by_year_semester(
        self,
        db: Session,
        year: int,
        semester: Optional[int] = None,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Classes]:
        """Lista turmas por ano e semestre."""
        raise NotImplementedError()
    
    @abstractmethod
    def count_classes(self, db: Session, *, active_only: bool = False) -> int:
        """Conta o total de turmas."""
        raise NotImplementedError()
    
    # ==================== CREATE OPERATIONS ====================
    
    @abstractmethod
    def create(
        self,
        db: Session,
        *,
        uuid: UUID,
        name: str,
        teacher_uuid: UUID,
        description: Optional[str] = None,
        year: Optional[int] = None,
        semester: Optional[int] = None,
        created_by: Optional[UUID] = None,
        active: bool = True
    ) -> Classes:
        """Cria uma nova turma."""
        raise NotImplementedError()
    
    # ==================== UPDATE OPERATIONS ====================
    
    @abstractmethod
    def update(self, db: Session, class_id: int, **updates) -> Classes:
        """Atualiza uma turma."""
        raise NotImplementedError()
    
    @abstractmethod
    def activate(self, db: Session, class_id: int) -> Classes:
        """Ativa uma turma."""
        raise NotImplementedError()
    
    @abstractmethod
    def deactivate(self, db: Session, class_id: int) -> Classes:
        """Desativa uma turma."""
        raise NotImplementedError()
    
    # ==================== DELETE OPERATIONS ====================
    
    @abstractmethod
    def delete(self, db: Session, class_id: int) -> None:
        """Remove uma turma."""
        raise NotImplementedError()
