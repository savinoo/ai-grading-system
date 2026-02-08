# pylint: disable=C0121
from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.interfaces.repositories.exam_question_criteria_override_repository_interface import ExamQuestionCriteriaOverrideRepositoryInterface

from src.models.entities.exam_question_criteria_override import ExamQuestionCriteriaOverride

from src.core.logging_config import get_logger

class ExamQuestionCriteriaOverrideRepository(ExamQuestionCriteriaOverrideRepositoryInterface):
    """
    Repositório para operações CRUD da entidade ExamQuestionCriteriaOverride.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

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
        try:
            stmt = select(ExamQuestionCriteriaOverride).where(
                ExamQuestionCriteriaOverride.id == override_id
            )
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Sobrescrita de critério encontrada: ID=%s", override_id)
            return result

        except NoResultFound:
            self.__logger.warning("Sobrescrita de critério não encontrada: ID=%s", override_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar sobrescrita por ID: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(ExamQuestionCriteriaOverride).where(
                ExamQuestionCriteriaOverride.uuid == uuid
            )
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Sobrescrita de critério encontrada: UUID=%s", uuid)
            return result

        except NoResultFound:
            self.__logger.warning("Sobrescrita de critério não encontrada: UUID=%s", uuid)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar sobrescrita por UUID: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(ExamQuestionCriteriaOverride).where(
                ExamQuestionCriteriaOverride.question_uuid == question_uuid
            )
            if active_only:
                stmt = stmt.where(ExamQuestionCriteriaOverride.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(ExamQuestionCriteriaOverride.created_at)
            result = db.execute(stmt).scalars().all()
            self.__logger.debug(
                "Listadas %d sobrescritas de critérios da questão %s",
                len(result),
                question_uuid
            )
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar sobrescritas da questão: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(ExamQuestionCriteriaOverride).where(
                ExamQuestionCriteriaOverride.question_uuid == question_uuid,
                ExamQuestionCriteriaOverride.criteria_uuid == criteria_uuid
            )
            result = db.execute(stmt).scalar_one_or_none()
            if result:
                self.__logger.debug(
                    "Sobrescrita encontrada para questão %s e critério %s",
                    question_uuid,
                    criteria_uuid
                )
            else:
                self.__logger.debug(
                    "Nenhuma sobrescrita encontrada para questão %s e critério %s",
                    question_uuid,
                    criteria_uuid
                )
            return result

        except SQLAlchemyError as e:
            self.__logger.error(
                "Erro ao buscar sobrescrita por questão e critério: %s",
                e,
                exc_info=True
            )
            raise

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
        try:
            stmt = select(func.count(ExamQuestionCriteriaOverride.id)).where(  # pylint: disable=not-callable
                ExamQuestionCriteriaOverride.question_uuid == question_uuid
            )
            if active_only:
                stmt = stmt.where(ExamQuestionCriteriaOverride.active == True)
            result = db.execute(stmt).scalar()
            self.__logger.debug("Total de sobrescritas da questão %s: %d", question_uuid, result)
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar sobrescritas da questão: %s", e, exc_info=True)
            raise

    # ==================== CREATE OPERATIONS ====================

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
        try:
            new_override = ExamQuestionCriteriaOverride(
                uuid=uuid,
                question_uuid=question_uuid,
                criteria_uuid=criteria_uuid,
                weight_override=weight_override,
                max_points_override=max_points_override,
                active=active
            )

            db.add(new_override)
            db.flush()
            db.refresh(new_override)

            self.__logger.info(
                "Sobrescrita de critério criada: UUID=%s (Questão: %s, Critério: %s)",
                uuid,
                question_uuid,
                criteria_uuid
            )
            return new_override

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao criar sobrescrita de critério: %s", e, exc_info=True)
            raise

    # ==================== UPDATE OPERATIONS ====================

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
        try:
            override_obj = self.get_by_id(db, override_id)

            for key, value in updates.items():
                if hasattr(override_obj, key):
                    setattr(override_obj, key, value)

            db.flush()
            db.refresh(override_obj)

            self.__logger.info("Sobrescrita de critério atualizada: ID=%s", override_id)
            return override_obj

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar sobrescrita: %s", e, exc_info=True)
            raise

    def activate(self, db: Session, override_id: int) -> ExamQuestionCriteriaOverride:
        """
        Ativa uma sobrescrita de critério.
        
        Args:
            db: Sessão do banco de dados
            override_id: ID da sobrescrita
            
        Returns:
            ExamQuestionCriteriaOverride: Sobrescrita ativada
        """
        try:
            return self.update(db, override_id, active=True)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao ativar sobrescrita: %s", e, exc_info=True)
            raise

    def deactivate(self, db: Session, override_id: int) -> ExamQuestionCriteriaOverride:
        """
        Desativa uma sobrescrita de critério.
        
        Args:
            db: Sessão do banco de dados
            override_id: ID da sobrescrita
            
        Returns:
            ExamQuestionCriteriaOverride: Sobrescrita desativada
        """
        try:
            return self.update(db, override_id, active=False)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao desativar sobrescrita: %s", e, exc_info=True)
            raise

    # ==================== DELETE OPERATIONS ====================

    def delete(self, db: Session, override_id: int) -> None:
        """
        Remove uma sobrescrita de critério.
        
        Args:
            db: Sessão do banco de dados
            override_id: ID da sobrescrita
        """
        try:
            override_obj = self.get_by_id(db, override_id)
            db.delete(override_obj)
            db.flush()

            self.__logger.info("Sobrescrita de critério removida: ID=%s", override_id)

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao remover sobrescrita: %s", e, exc_info=True)
            raise

    def delete_all_by_question(self, db: Session, question_uuid: UUID) -> int:
        """
        Remove todas as sobrescritas de uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            
        Returns:
            int: Número de sobrescritas removidas
        """
        try:
            stmt = delete(ExamQuestionCriteriaOverride).where(
                ExamQuestionCriteriaOverride.question_uuid == question_uuid
            )
            result = db.execute(stmt)
            db.flush()

            deleted_count = result.rowcount or 0
            self.__logger.info(
                "Removidas %d sobrescritas da questão %s",
                deleted_count,
                question_uuid
            )
            return deleted_count

        except SQLAlchemyError as e:
            self.__logger.error(
                "Erro ao remover todas as sobrescritas da questão: %s",
                e,
                exc_info=True
            )
            raise
