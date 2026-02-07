# pylint: disable=C0121
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.entities.student_answers import StudentAnswer

class StudentAnswerRepositoryInterface(ABC):
    """
    Repositório para operações CRUD da entidade StudentAnswer.
    """
    # ==================== READ OPERATIONS ====================

    @abstractmethod
    def get_by_id(self, db: Session, answer_id: int) -> StudentAnswer:
        """
        Busca resposta por ID.
        
        Args:
            db: Sessão do banco de dados
            answer_id: ID da resposta
            
        Returns:
            StudentAnswer: Entidade da resposta
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a resposta não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_uuid(self, db: Session, uuid: UUID) -> StudentAnswer:
        """
        Busca resposta por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da resposta
            
        Returns:
            StudentAnswer: Entidade da resposta
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a resposta não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_exam(
        self,
        db: Session,
        exam_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[StudentAnswer]:
        """
        Lista respostas de uma prova específica.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[StudentAnswer]: Lista de respostas da prova
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_student_and_exam(
        self,
        db: Session,
        student_uuid: UUID,
        exam_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[StudentAnswer]:
        """
        Lista respostas de um aluno em uma prova específica.
        
        Args:
            db: Sessão do banco de dados
            student_uuid: UUID do aluno
            exam_uuid: UUID da prova
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[StudentAnswer]: Lista de respostas do aluno na prova
        """
        raise NotImplementedError()

    @abstractmethod
    def count_by_exam(self, db: Session, exam_uuid: UUID) -> int:
        """
        Conta o total de respostas de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            int: Total de respostas da prova
        """
        raise NotImplementedError()

    @abstractmethod
    def has_answers_for_exam(self, db: Session, exam_uuid: UUID) -> bool:
        """
        Verifica se existem respostas para uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            bool: True se existem respostas, False caso contrário
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
        question_uuid: UUID,
        student_uuid: UUID,
        answer: Optional[str] = None,
        status: str = "SUBMITTED",
        score: Optional[float] = None,
        feedback: Optional[str] = None,
        graded_at: Optional[datetime] = None,
        graded_by: Optional[UUID] = None
    ) -> StudentAnswer:
        """
        Cria uma nova resposta de aluno.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da resposta
            exam_uuid: UUID da prova
            question_uuid: UUID da questão
            student_uuid: UUID do aluno
            answer: Resposta do aluno
            status: Status da resposta (SUBMITTED, GRADED, INVALID)
            score: Pontuação obtida
            feedback: Feedback da correção
            graded_at: Data/hora da correção
            graded_by: UUID do corretor
            
        Returns:
            StudentAnswer: Resposta criada
        """
        raise NotImplementedError()

    # ==================== UPDATE OPERATIONS ====================

    @abstractmethod
    def update(self, db: Session, answer_id: int, **updates) -> StudentAnswer:
        """
        Atualiza uma resposta.
        
        Args:
            db: Sessão do banco de dados
            answer_id: ID da resposta
            **updates: Campos a atualizar
            
        Returns:
            StudentAnswer: Resposta atualizada
        """
        raise NotImplementedError()

    # ==================== DELETE OPERATIONS ====================

    @abstractmethod
    def delete(self, db: Session, answer_id: int) -> None:
        """
        Remove uma resposta.
        
        Args:
            db: Sessão do banco de dados
            answer_id: ID da resposta
        """
        raise NotImplementedError()
