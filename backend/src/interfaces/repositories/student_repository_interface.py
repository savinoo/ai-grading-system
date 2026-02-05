# pylint: disable=C0121
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.entities.student import Student

class StudentRepositoryInterface(ABC):
    """
    Interface do repositório para operações CRUD da entidade Student.
    """

    # ==================== READ OPERATIONS ====================
    
    @abstractmethod
    def get_by_id(self, db: Session, student_id: int) -> Student:
        """
        Busca estudante por ID.
        
        Args:
            db: Sessão do banco de dados
            student_id: ID do estudante
            
        Returns:
            Student: Entidade do estudante
            
        Raises:
            NoResultFound: Se o estudante não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_uuid(self, db: Session, uuid: UUID) -> Student:
        """
        Busca estudante por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do estudante
            
        Returns:
            Student: Entidade do estudante
            
        Raises:
            NoResultFound: Se o estudante não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_email(self, db: Session, email: str) -> Optional[Student]:
        """
        Busca estudante por email.
        
        Args:
            db: Sessão do banco de dados
            email: Email do estudante
            
        Returns:
            Optional[Student]: Estudante encontrado ou None
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
    ) -> Sequence[Student]:
        """
        Lista todos os estudantes com paginação.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas estudantes ativos
            
        Returns:
            Sequence[Student]: Lista de estudantes
        """
        raise NotImplementedError()

    @abstractmethod
    def get_active_students(self, db: Session, *, skip: int = 0, limit: int = 100) -> Sequence[Student]:
        """
        Lista estudantes ativos.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[Student]: Lista de estudantes ativos
        """
        raise NotImplementedError()

    @abstractmethod
    def search_students(
        self,
        db: Session,
        search_term: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Student]:
        """
        Busca estudantes por termo (nome, email ou matrícula).
        
        Args:
            db: Sessão do banco de dados
            search_term: Termo de busca
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[Student]: Lista de estudantes encontrados
        """
        raise NotImplementedError()

    @abstractmethod
    def count_students(self, db: Session, *, active_only: bool = False) -> int:
        """
        Conta o total de estudantes.
        
        Args:
            db: Sessão do banco de dados
            active_only: Se deve contar apenas estudantes ativos
            
        Returns:
            int: Total de estudantes
        """
        raise NotImplementedError()

    @abstractmethod
    def exists_by_email(self, db: Session, email: str) -> bool:
        """
        Verifica se existe estudante com o email.
        
        Args:
            db: Sessão do banco de dados
            email: Email a verificar
            
        Returns:
            bool: True se existir, False caso contrário
        """
        raise NotImplementedError()

    # ==================== CREATE OPERATIONS ====================

    @abstractmethod
    def create(
        self,
        db: Session,
        *,
        uuid: UUID,
        full_name: str,
        email: Optional[str] = None,
        active: bool = True
    ) -> Student:
        """
        Cria um novo estudante.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do estudante
            full_name: Nome completo do estudante
            email: Email do estudante
            active: Se o estudante está ativo
            
        Returns:
            Student: Estudante criado
        """
        raise NotImplementedError()

    @abstractmethod
    def bulk_create(self, db: Session, students_data: list[dict]) -> int:
        """
        Cria múltiplos estudantes em lote.
        
        Args:
            db: Sessão do banco de dados
            students_data: Lista de dicionários com dados dos estudantes
            
        Returns:
            int: Número de estudantes criados
        """
        raise NotImplementedError()

    # ==================== UPDATE OPERATIONS ====================

    @abstractmethod
    def update(self, db: Session, student_id: int, **updates) -> Student:
        """
        Atualiza um estudante.
        
        Args:
            db: Sessão do banco de dados
            student_id: ID do estudante
            **updates: Campos a atualizar
            
        Returns:
            Student: Estudante atualizado
        """
        raise NotImplementedError()

    @abstractmethod
    def activate(self, db: Session, student_id: int) -> Student:
        """
        Ativa um estudante.
        
        Args:
            db: Sessão do banco de dados
            student_id: ID do estudante
            
        Returns:
            Student: Estudante ativado
        """
        raise NotImplementedError()

    @abstractmethod
    def deactivate(self, db: Session, student_id: int) -> Student:
        """
        Desativa um estudante.
        
        Args:
            db: Sessão do banco de dados
            student_id: ID do estudante
            
        Returns:
            Student: Estudante desativado
        """
        raise NotImplementedError()

    @abstractmethod
    def bulk_update(self, db: Session, mappings: list[dict], *, batch_size: int = 300) -> int:
        """
        Atualiza múltiplos estudantes em lote.
        
        Args:
            db: Sessão do banco de dados
            mappings: Lista de dicts com 'id' e campos a atualizar
            batch_size: Tamanho do lote
            
        Returns:
            int: Número de estudantes atualizados
            
        Example:
            mappings = [
                {"id": 1, "active": True, "email": "novo@email.com"},
                {"id": 2, "full_name": "Nome Atualizado"}
            ]
        """
        raise NotImplementedError()

    # ==================== DELETE OPERATIONS ====================

    @abstractmethod
    def delete(self, db: Session, student_id: int) -> None:
        """
        Remove um estudante permanentemente.
        
        Args:
            db: Sessão do banco de dados
            student_id: ID do estudante
        """
        raise NotImplementedError()
