from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from src.models.entities.class_student import ClassStudent

class ClassStudentRepositoryInterface(ABC):
    """
    Interface para o repositório de ClassStudent (relacionamento turma-aluno).
    """
    
    # ==================== READ OPERATIONS ====================
    
    @abstractmethod
    def get_by_id(self, db: Session, class_student_id: int) -> ClassStudent:
        """Busca relacionamento por ID."""
        raise NotImplementedError()
    
    @abstractmethod
    def get_students_by_class(
        self,
        db: Session,
        class_uuid: UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[ClassStudent]:
        """Lista alunos de uma turma."""
        raise NotImplementedError()
    
    @abstractmethod
    def get_classes_by_student(
        self,
        db: Session,
        student_uuid: UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[ClassStudent]:
        """Lista turmas de um aluno."""
        raise NotImplementedError()
    
    @abstractmethod
    def exists(self, db: Session, class_uuid: UUID, student_uuid: UUID) -> bool:
        """Verifica se o aluno já está matriculado na turma."""
        raise NotImplementedError()
    
    @abstractmethod
    def count_students_in_class(self, db: Session, class_uuid: UUID, *, active_only: bool = True) -> int:
        """Conta alunos em uma turma."""
        raise NotImplementedError()
    
    # ==================== CREATE OPERATIONS ====================
    
    @abstractmethod
    def create(
        self,
        db: Session,
        *,
        class_uuid: UUID,
        student_uuid: UUID,
        enrolled_at: datetime = None,
        active: bool = True
    ) -> ClassStudent:
        """Matricula um aluno em uma turma."""
        raise NotImplementedError()
    
    @abstractmethod
    def bulk_create(
        self,
        db: Session,
        class_uuid: UUID,
        student_uuids: list[UUID]
    ) -> int:
        """Matricula múltiplos alunos em uma turma."""
        raise NotImplementedError()
    
    # ==================== UPDATE OPERATIONS ====================
    
    @abstractmethod
    def activate(self, db: Session, class_student_id: int) -> ClassStudent:
        """Ativa matrícula."""
        raise NotImplementedError()
    
    @abstractmethod
    def deactivate(self, db: Session, class_student_id: int) -> ClassStudent:
        """Desativa matrícula."""
        raise NotImplementedError()
    
    # ==================== DELETE OPERATIONS ====================
    
    @abstractmethod
    def delete(self, db: Session, class_student_id: int) -> None:
        """Remove matrícula."""
        raise NotImplementedError()
    
    @abstractmethod
    def remove_student_from_class(self, db: Session, class_uuid: UUID, student_uuid: UUID) -> None:
        """Remove um aluno de uma turma."""
        raise NotImplementedError()
