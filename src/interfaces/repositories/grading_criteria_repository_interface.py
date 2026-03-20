# pylint: disable=C0121
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.entities.grading_criteria import GradingCriteria

class GradingCriteriaRepositoryInterface(ABC):
    """
    Repositório para operações de leitura da entidade GradingCriteria.
    Esta entidade contém critérios predefinidos e só permite consultas.
    """
    # ==================== READ OPERATIONS ====================

    @abstractmethod
    def get_by_id(self, db: Session, criteria_id: int) -> GradingCriteria:
        """
        Busca critério por ID.
        
        Args:
            db: Sessão do banco de dados
            criteria_id: ID do critério
            
        Returns:
            GradingCriteria: Entidade do critério
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o critério não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_uuid(self, db: Session, uuid: UUID) -> GradingCriteria:
        """
        Busca critério por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do critério
            
        Returns:
            GradingCriteria: Entidade do critério
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o critério não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_code(self, db: Session, code: str) -> GradingCriteria:
        """
        Busca critério por código.
        
        Args:
            db: Sessão do banco de dados
            code: Código único do critério
            
        Returns:
            GradingCriteria: Entidade do critério
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o critério não existir
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
    ) -> Sequence[GradingCriteria]:
        """
        Lista todos os critérios de avaliação com paginação.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas critérios ativos
            
        Returns:
            Sequence[GradingCriteria]: Lista de critérios
        """
        raise NotImplementedError()

    @abstractmethod
    def count_criteria(self, db: Session, *, active_only: bool = False) -> int:
        """
        Conta o total de critérios.
        
        Args:
            db: Sessão do banco de dados
            active_only: Se deve contar apenas critérios ativos
            
        Returns:
            int: Total de critérios
        """
        raise NotImplementedError()
