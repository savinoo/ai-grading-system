# pylint: disable=C0121
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.entities.exam_question_criteria_override import ExamQuestionCriteriaOverride

class ExamQuestionCriteriaOverrideRepositoryInterface(ABC):
    """
    Interface do repositório para operações CRUD da entidade ExamQuestionCriteriaOverride.
    """
    # ==================== READ OPERATIONS ====================

    @abstractmethod
    def get_by_id(self, db: Session, override_id: int) -> ExamQuestionCriteriaOverride:
        """
        Busca sobrescrita de critério por ID.
        
        Args:
            db: Sessão do banco de dados
            override_id: ID da sobrescrita
            
        Returns:
            ExamQuestionCriteriaOverride: Entidade da sobrescrita
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a sobrescrita não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_uuid(self, db: Session, uuid: UUID) -> ExamQuestionCriteriaOverride:
        """
        Busca sobrescrita de critério por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da sobrescrita
            
        Returns:
            ExamQuestionCriteriaOverride: Entidade da sobrescrita
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a sobrescrita não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_question(
        self,
        db: Session,
        question_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[ExamQuestionCriteriaOverride]:
        """
        Lista sobrescritas de critérios de uma questão específica.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas sobrescritas ativas
            
        Returns:
            Sequence[ExamQuestionCriteriaOverride]: Lista de sobrescritas da questão
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_question_and_criteria(
        self,
        db: Session,
        question_uuid: UUID,
        criteria_uuid: UUID
    ) -> Optional[ExamQuestionCriteriaOverride]:
        """
        Busca sobrescrita específica de um critério em uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            criteria_uuid: UUID do critério
            
        Returns:
            Optional[ExamQuestionCriteriaOverride]: Sobrescrita encontrada ou None
        """
        raise NotImplementedError()

    @abstractmethod
    def count_by_question(self, db: Session, question_uuid: UUID, *, active_only: bool = False) -> int:
        """
        Conta o total de sobrescritas de critérios de uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            active_only: Se deve contar apenas sobrescritas ativas
            
        Returns:
            int: Total de sobrescritas da questão
        """
        raise NotImplementedError()

    # ==================== CREATE OPERATIONS ====================

    @abstractmethod
    def create(
        self,
        db: Session,
        *,
        uuid: UUID,
        question_uuid: UUID,
        criteria_uuid: UUID,
        weight_override: Optional[float] = None,
        max_points_override: Optional[float] = None,
        active: bool = True
    ) -> ExamQuestionCriteriaOverride:
        """
        Cria uma nova sobrescrita de critério.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da sobrescrita
            question_uuid: UUID da questão
            criteria_uuid: UUID do critério
            weight_override: Peso sobrescrito do critério
            max_points_override: Pontuação máxima sobrescrita
            active: Se a sobrescrita está ativa
            
        Returns:
            ExamQuestionCriteriaOverride: Sobrescrita criada
        """
        raise NotImplementedError()

    # ==================== UPDATE OPERATIONS ====================

    @abstractmethod
    def update(self, db: Session, override_id: int, **updates) -> ExamQuestionCriteriaOverride:
        """
        Atualiza uma sobrescrita de critério.
        
        Args:
            db: Sessão do banco de dados
            override_id: ID da sobrescrita
            **updates: Campos a atualizar
            
        Returns:
            ExamQuestionCriteriaOverride: Sobrescrita atualizada
        """
        raise NotImplementedError()

    @abstractmethod
    def activate(self, db: Session, override_id: int) -> ExamQuestionCriteriaOverride:
        """
        Ativa uma sobrescrita de critério.
        
        Args:
            db: Sessão do banco de dados
            override_id: ID da sobrescrita
            
        Returns:
            ExamQuestionCriteriaOverride: Sobrescrita ativada
        """
        raise NotImplementedError()

    @abstractmethod
    def deactivate(self, db: Session, override_id: int) -> ExamQuestionCriteriaOverride:
        """
        Desativa uma sobrescrita de critério.
        
        Args:
            db: Sessão do banco de dados
            override_id: ID da sobrescrita
            
        Returns:
            ExamQuestionCriteriaOverride: Sobrescrita desativada
        """
        raise NotImplementedError()

    # ==================== DELETE OPERATIONS ====================

    @abstractmethod
    def delete(self, db: Session, override_id: int) -> None:
        """
        Remove uma sobrescrita de critério.
        
        Args:
            db: Sessão do banco de dados
            override_id: ID da sobrescrita
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_all_by_question(self, db: Session, question_uuid: UUID) -> int:
        """
        Remove todas as sobrescritas de uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            
        Returns:
            int: Número de sobrescritas removidas
        """
        raise NotImplementedError()
