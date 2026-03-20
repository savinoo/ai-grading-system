# pylint: disable=C0121
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface

from src.models.entities.exam_questions import ExamQuestion

from src.core.logging_config import get_logger

class ExamQuestionRepository(ExamQuestionRepositoryInterface):
    """
    Repositório para operações CRUD da entidade ExamQuestion.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

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
        try:
            stmt = select(ExamQuestion).where(ExamQuestion.id == question_id)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Questão encontrada: ID=%s", question_id)
            return result

        except NoResultFound:
            self.__logger.warning("Questão não encontrada: ID=%s", question_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar questão por ID: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(ExamQuestion).where(ExamQuestion.uuid == uuid)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Questão encontrada: UUID=%s", uuid)
            return result

        except NoResultFound:
            self.__logger.warning("Questão não encontrada: UUID=%s", uuid)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar questão por UUID: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(ExamQuestion).where(ExamQuestion.exam_uuid == exam_uuid)
            if active_only:
                stmt = stmt.where(ExamQuestion.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(ExamQuestion.question_order)
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d questões da prova %s", len(result), exam_uuid)
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar questões da prova: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(func.count(ExamQuestion.id)).where(ExamQuestion.exam_uuid == exam_uuid)  # pylint: disable=not-callable
            if active_only:
                stmt = stmt.where(ExamQuestion.active == True)
            result = db.execute(stmt).scalar()
            self.__logger.debug("Total de questões da prova %s: %d", exam_uuid, result)
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar questões da prova: %s", e, exc_info=True)
            raise

    # ==================== CREATE OPERATIONS ====================

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
        try:
            new_question = ExamQuestion(
                uuid=uuid,
                exam_uuid=exam_uuid,
                statement=statement,
                question_order=question_order,
                points=points,
                active=active
            )

            db.add(new_question)
            db.flush()
            db.refresh(new_question)

            self.__logger.info(
                "Questão criada: UUID=%s (Prova: %s, Ordem: %d)", 
                uuid,
                exam_uuid,
                question_order
            )
            return new_question

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao criar questão: %s", e, exc_info=True)
            raise

    # ==================== UPDATE OPERATIONS ====================

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
        try:
            question_obj = self.get_by_id(db, question_id)

            for key, value in updates.items():
                if hasattr(question_obj, key):
                    setattr(question_obj, key, value)

            db.flush()
            db.refresh(question_obj)

            self.__logger.info("Questão atualizada: ID=%s", question_id)
            return question_obj

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar questão: %s", e, exc_info=True)
            raise

    def activate(self, db: Session, question_id: int) -> ExamQuestion:
        """
        Ativa uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_id: ID da questão
            
        Returns:
            ExamQuestion: Questão ativada
        """
        try:
            return self.update(db, question_id, active=True)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao ativar questão: %s", e, exc_info=True)
            raise

    def deactivate(self, db: Session, question_id: int) -> ExamQuestion:
        """
        Desativa uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_id: ID da questão
            
        Returns:
            ExamQuestion: Questão desativada
        """
        try:
            return self.update(db, question_id, active=False)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao desativar questão: %s", e, exc_info=True)
            raise

    # ==================== DELETE OPERATIONS ====================

    def delete(self, db: Session, question_id: int) -> None:
        """
        Remove uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_id: ID da questão
        """
        try:
            question_obj = self.get_by_id(db, question_id)
            db.delete(question_obj)
            db.flush()

            self.__logger.info("Questão removida: ID=%s", question_id)

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao remover questão: %s", e, exc_info=True)
            raise
