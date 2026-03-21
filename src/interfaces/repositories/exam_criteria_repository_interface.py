# pylint: disable=C0121
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.entities.exam_criteria import ExamCriteria

class ExamCriteriaRepositoryInterface(ABC):
    """
    Repositório para operações CRUD da entidade ExamCriteria.
    """
    # ==================== READ OPERATIONS ====================

    @abstractmethod
    def get_by_id(self, db: Session, exam_criteria_id: int) -> ExamCriteria:
        """
        Busca critério de prova por ID.
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_id: ID do critério de prova
            
        Returns:
            ExamCriteria: Entidade do critério de prova
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o critério não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_uuid(self, db: Session, uuid: UUID) -> ExamCriteria:
        """
        Busca critério de prova por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do critério de prova
            
        Returns:
            ExamCriteria: Entidade do critério de prova
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o critério não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_exam(
        self,
        db: Session,
        exam_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[ExamCriteria]:
        """
        Lista critérios de uma prova específica.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas critérios ativos
            
        Returns:
            Sequence[ExamCriteria]: Lista de critérios da prova
        """
        raise NotImplementedError()

    @abstractmethod
    def count_by_exam(self, db: Session, exam_uuid: UUID, *, active_only: bool = False) -> int:
        """
        Conta o total de critérios de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            active_only: Se deve contar apenas critérios ativos
            
        Returns:
            int: Total de critérios da prova
        """
        raise NotImplementedError()

    # ==================== CREATE OPERATIONS ====================

    @abstractmethod
    def create(
        self,
        db: Session,
        *,
        uuid: UUID,
        exam_uuid: UUID,
        criteria_uuid: UUID,
        weight: float = 1.0,
        max_points: Optional[float] = None,
        active: bool = True
    ) -> ExamCriteria:
        """
        Cria um novo critério de prova.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do critério de prova
            exam_uuid: UUID da prova
            criteria_uuid: UUID do critério de avaliação
            weight: Peso do critério (padrão: 1.0)
            max_points: Pontuação máxima do critério
            active: Se o critério está ativo
            
        Returns:
            ExamCriteria: Critério de prova criado
        """
        raise NotImplementedError()

    # ==================== UPDATE OPERATIONS ====================

    @abstractmethod
    def update(self, db: Session, exam_criteria_id: int, **updates) -> ExamCriteria:
        """
        Atualiza um critério de prova.
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_id: ID do critério de prova
            **updates: Campos a atualizar
            
        Returns:
            ExamCriteria: Critério de prova atualizado
        """
        raise NotImplementedError()

    @abstractmethod
    def activate(self, db: Session, exam_criteria_id: int) -> ExamCriteria:
        """
        Ativa um critério de prova.
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_id: ID do critério de prova
            
        Returns:
            ExamCriteria: Critério de prova ativado
        """
        raise NotImplementedError()

    @abstractmethod
    def deactivate(self, db: Session, exam_criteria_id: int) -> ExamCriteria:
        """
        Desativa um critério de prova.
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_id: ID do critério de prova
            
        Returns:
            ExamCriteria: Critério de prova desativado
        """
        raise NotImplementedError()

    # ==================== DELETE OPERATIONS ====================

    @abstractmethod
    def delete(self, db: Session, exam_criteria_id: int) -> None:
        """
        Remove um critério de prova.
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_id: ID do critério de prova
        """
        raise NotImplementedError()
