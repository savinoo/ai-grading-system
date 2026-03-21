# pylint: disable=C0121
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.entities.exam_questions import ExamQuestion

class ExamQuestionRepositoryInterface(ABC):
    """
    Repositório para operações CRUD da entidade ExamQuestion.
    """
    # ==================== READ OPERATIONS ====================

    @abstractmethod
    def get_by_id(self, db: Session, question_id: int) -> ExamQuestion:
        """
        Busca questão por ID.
        
        Args:
            db: Sessão do banco de dados
            question_id: ID da questão
            
        Returns:
            ExamQuestion: Entidade da questão
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a questão não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_uuid(self, db: Session, uuid: UUID) -> ExamQuestion:
        """
        Busca questão por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da questão
            
        Returns:
            ExamQuestion: Entidade da questão
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a questão não existir
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
    ) -> Sequence[ExamQuestion]:
        """
        Lista questões de uma prova específica.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas questões ativas
            
        Returns:
            Sequence[ExamQuestion]: Lista de questões da prova
        """
        raise NotImplementedError()

    @abstractmethod
    def count_by_exam(self, db: Session, exam_uuid: UUID, *, active_only: bool = False) -> int:
        """
        Conta o total de questões de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            active_only: Se deve contar apenas questões ativas
            
        Returns:
            int: Total de questões da prova
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
        statement: str,
        question_order: int,
        points: float = 1.0,
        active: bool = True
    ) -> ExamQuestion:
        """
        Cria uma nova questão.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da questão
            exam_uuid: UUID da prova
            statement: Enunciado da questão
            question_order: Ordem da questão na prova
            points: Pontuação da questão
            active: Se a questão está ativa
            
        Returns:
            ExamQuestion: Questão criada
        """
        raise NotImplementedError()

    # ==================== UPDATE OPERATIONS ====================

    @abstractmethod
    def update(self, db: Session, question_id: int, **updates) -> ExamQuestion:
        """
        Atualiza uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_id: ID da questão
            **updates: Campos a atualizar
            
        Returns:
            ExamQuestion: Questão atualizada
        """
        raise NotImplementedError()

    @abstractmethod
    def activate(self, db: Session, question_id: int) -> ExamQuestion:
        """
        Ativa uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_id: ID da questão
            
        Returns:
            ExamQuestion: Questão ativada
        """
        raise NotImplementedError()

    @abstractmethod
    def deactivate(self, db: Session, question_id: int) -> ExamQuestion:
        """
        Desativa uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_id: ID da questão
            
        Returns:
            ExamQuestion: Questão desativada
        """
        raise NotImplementedError()

    # ==================== DELETE OPERATIONS ====================

    @abstractmethod
    def delete(self, db: Session, question_id: int) -> None:
        """
        Remove uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_id: ID da questão
        """
        raise NotImplementedError()
