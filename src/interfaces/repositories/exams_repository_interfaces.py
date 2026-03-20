# pylint: disable=C0121
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.entities.exams import Exams

class ExamsRepositoryInterface(ABC):
    """
    Repositório para operações CRUD da entidade Exams.
    """
    # ==================== READ OPERATIONS ====================

    @abstractmethod
    def get_by_id(self, db: Session, exam_id: int) -> Exams:
        """
        Busca prova por ID.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
            
        Returns:
            Exams: Entidade da prova
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a prova não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_uuid(self, db: Session, uuid: UUID) -> Exams:
        """
        Busca prova por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da prova
            
        Returns:
            Exams: Entidade da prova
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a prova não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_all(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Exams]:
        """
        Lista todas as provas com paginação.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas provas ativas
            
        Returns:
            Sequence[Exams]: Lista de provas
        """
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
    ) -> Sequence[Exams]:
        """
        Lista provas de um professor específico.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor (created_by)
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas provas ativas
            
        Returns:
            Sequence[Exams]: Lista de provas do professor
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_class(
        self,
        db: Session,
        class_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Exams]:
        """
        Lista provas de uma turma específica.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas provas ativas
            
        Returns:
            Sequence[Exams]: Lista de provas da turma
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Exams]:
        """
        Lista provas por status.
        
        Args:
            db: Sessão do banco de dados
            status: Status da prova (DRAFT, PUBLISHED, ARCHIVED, FINISHED)
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas provas ativas
            
        Returns:
            Sequence[Exams]: Lista de provas com o status especificado
        """
        raise NotImplementedError()

    @abstractmethod
    def count_exams(self, db: Session, *, active_only: bool = False) -> int:
        """
        Conta o total de provas.
        
        Args:
            db: Sessão do banco de dados
            active_only: Se deve contar apenas provas ativas
            
        Returns:
            int: Total de provas
        """
        raise NotImplementedError()

    @abstractmethod
    def count_by_teacher(self, db: Session, teacher_uuid: UUID, *, active_only: bool = True) -> int:
        """
        Conta total de provas de um professor.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            active_only: Se deve contar apenas provas ativas
            
        Returns:
            int: Total de provas do professor
        """
        raise NotImplementedError()

    @abstractmethod
    def count_by_teacher_and_status(
        self,
        db: Session,
        teacher_uuid: UUID,
        status: str,
        *,
        active_only: bool = True
    ) -> int:
        """
        Conta provas de um professor por status.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            status: Status da prova (DRAFT, ACTIVE, GRADING, GRADED, FINALIZED)
            active_only: Se deve contar apenas provas ativas
            
        Returns:
            int: Total de provas com o status especificado
        """
        raise NotImplementedError()

    # ==================== CREATE OPERATIONS ====================

    @abstractmethod
    def create(
        self,
        db: Session,
        *,
        uuid: UUID,
        title: str,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None,
        class_uuid: Optional[UUID] = None,
        status: str = "DRAFT",
        starts_at: Optional[datetime] = None,
        ends_at: Optional[datetime] = None,
        active: bool = True
    ) -> Exams:
        """
        Cria uma nova prova.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da prova
            title: Título da prova
            description: Descrição da prova
            created_by: UUID do professor criador
            class_uuid: UUID da turma
            status: Status da prova (DRAFT, PUBLISHED, ARCHIVED, FINISHED)
            starts_at: Data/hora de início
            ends_at: Data/hora de término
            active: Se a prova está ativa
            
        Returns:
            Exams: Prova criada
        """
        raise NotImplementedError()

    # ==================== UPDATE OPERATIONS ====================

    @abstractmethod
    def update(self, db: Session, exam_id: int, **updates) -> Exams:
        """
        Atualiza uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
            **updates: Campos a atualizar
            
        Returns:
            Exams: Prova atualizada
        """
        raise NotImplementedError()

    @abstractmethod
    def activate(self, db: Session, exam_id: int) -> Exams:
        """
        Ativa uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
            
        Returns:
            Exams: Prova ativada
        """
        raise NotImplementedError()

    @abstractmethod
    def deactivate(self, db: Session, exam_id: int) -> Exams:
        """
        Desativa uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
            
        Returns:
            Exams: Prova desativada
        """
        raise NotImplementedError()

    @abstractmethod
    def update_status(self, db: Session, exam_id: int, status: str) -> Exams:
        """
        Atualiza o status de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
            status: Novo status (DRAFT, PUBLISHED, ARCHIVED, FINISHED)
            
        Returns:
            Exams: Prova com status atualizado
        """
        raise NotImplementedError()

    # ==================== DELETE OPERATIONS ====================

    @abstractmethod
    def delete(self, db: Session, exam_id: int) -> None:
        """
        Remove uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
        """
        raise NotImplementedError()
