# pylint: disable=C0121
from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.interfaces.repositories.exam_criteria_repository_interface import ExamCriteriaRepositoryInterface

from src.models.entities.exam_criteria import ExamCriteria

from src.core.logging_config import get_logger

class ExamCriteriaRepository(ExamCriteriaRepositoryInterface):
    """
    Repositório para operações CRUD da entidade ExamCriteria.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

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
        try:
            stmt = select(ExamCriteria).where(ExamCriteria.id == exam_criteria_id)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Critério de prova encontrado: ID=%s", exam_criteria_id)
            return result

        except NoResultFound:
            self.__logger.warning("Critério de prova não encontrado: ID=%s", exam_criteria_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar critério de prova por ID: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(ExamCriteria).where(ExamCriteria.uuid == uuid)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Critério de prova encontrado: UUID=%s", uuid)
            return result

        except NoResultFound:
            self.__logger.warning("Critério de prova não encontrado: UUID=%s", uuid)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar critério de prova por UUID: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(ExamCriteria).where(ExamCriteria.exam_uuid == exam_uuid)
            if active_only:
                stmt = stmt.where(ExamCriteria.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(ExamCriteria.created_at)
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listados %d critérios da prova %s", len(result), exam_uuid)
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar critérios da prova: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(func.count(ExamCriteria.id)).where(ExamCriteria.exam_uuid == exam_uuid)  # pylint: disable=not-callable
            if active_only:
                stmt = stmt.where(ExamCriteria.active == True)
            result = db.execute(stmt).scalar()
            self.__logger.debug("Total de critérios da prova %s: %d", exam_uuid, result)
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar critérios da prova: %s", e, exc_info=True)
            raise

    # ==================== CREATE OPERATIONS ====================

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
        try:
            new_exam_criteria = ExamCriteria(
                uuid=uuid,
                exam_uuid=exam_uuid,
                criteria_uuid=criteria_uuid,
                weight=weight,
                max_points=max_points,
                active=active
            )

            db.add(new_exam_criteria)
            db.commit()
            db.refresh(new_exam_criteria)

            self.__logger.info(
                "Critério de prova criado: UUID=%s (Prova: %s, Critério: %s)",
                uuid,
                exam_uuid,
                criteria_uuid
            )
            return new_exam_criteria

        except SQLAlchemyError as e:
            db.rollback()
            self.__logger.error("Erro ao criar critério de prova: %s", e, exc_info=True)
            raise

    # ==================== UPDATE OPERATIONS ====================

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
        try:
            exam_criteria_obj = self.get_by_id(db, exam_criteria_id)

            for key, value in updates.items():
                if hasattr(exam_criteria_obj, key):
                    setattr(exam_criteria_obj, key, value)

            db.commit()
            db.refresh(exam_criteria_obj)

            self.__logger.info("Critério de prova atualizado: ID=%s", exam_criteria_id)
            return exam_criteria_obj

        except SQLAlchemyError as e:
            db.rollback()
            self.__logger.error("Erro ao atualizar critério de prova: %s", e, exc_info=True)
            raise

    def activate(self, db: Session, exam_criteria_id: int) -> ExamCriteria:
        """
        Ativa um critério de prova.
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_id: ID do critério de prova
            
        Returns:
            ExamCriteria: Critério de prova ativado
        """
        try:
            return self.update(db, exam_criteria_id, active=True)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao ativar critério de prova: %s", e, exc_info=True)
            raise

    def deactivate(self, db: Session, exam_criteria_id: int) -> ExamCriteria:
        """
        Desativa um critério de prova.
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_id: ID do critério de prova
            
        Returns:
            ExamCriteria: Critério de prova desativado
        """
        try:
            return self.update(db, exam_criteria_id, active=False)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao desativar critério de prova: %s", e, exc_info=True)
            raise

    # ==================== DELETE OPERATIONS ====================

    def delete(self, db: Session, exam_criteria_id: int) -> None:
        """
        Remove um critério de prova.
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_id: ID do critério de prova
        """
        try:
            exam_criteria_obj = self.get_by_id(db, exam_criteria_id)
            db.delete(exam_criteria_obj)
            db.commit()

            self.__logger.info("Critério de prova removido: ID=%s", exam_criteria_id)

        except SQLAlchemyError as e:
            db.rollback()
            self.__logger.error("Erro ao remover critério de prova: %s", e, exc_info=True)
            raise
