# pylint: disable=C0121
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.interfaces.repositories.grading_criteria_repository_interface import GradingCriteriaRepositoryInterface

from src.models.entities.grading_criteria import GradingCriteria

from src.core.logging_config import get_logger

class GradingCriteriaRepository(GradingCriteriaRepositoryInterface):
    """
    Repositório para operações de leitura da entidade GradingCriteria.
    Esta entidade contém critérios predefinidos e só permite consultas.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

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
        try:
            stmt = select(GradingCriteria).where(GradingCriteria.id == criteria_id)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Critério encontrado: ID=%s", criteria_id)
            return result

        except NoResultFound:
            self.__logger.warning("Critério não encontrado: ID=%s", criteria_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar critério por ID: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(GradingCriteria).where(GradingCriteria.uuid == uuid)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Critério encontrado: UUID=%s", uuid)
            return result

        except NoResultFound:
            self.__logger.warning("Critério não encontrado: UUID=%s", uuid)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar critério por UUID: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(GradingCriteria).where(GradingCriteria.code == code)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Critério encontrado: code=%s", code)
            return result

        except NoResultFound:
            self.__logger.warning("Critério não encontrado: code=%s", code)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar critério por código: %s", e, exc_info=True)
            raise

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
        try:
            stmt = select(GradingCriteria)
            if active_only:
                stmt = stmt.where(GradingCriteria.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(GradingCriteria.name)
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listados %d critérios", len(result))
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar critérios: %s", e, exc_info=True)
            raise

    def count_criteria(self, db: Session, *, active_only: bool = False) -> int:
        """
        Conta o total de critérios.
        
        Args:
            db: Sessão do banco de dados
            active_only: Se deve contar apenas critérios ativos
            
        Returns:
            int: Total de critérios
        """
        try:
            stmt = select(func.count(GradingCriteria.id))  # pylint: disable=not-callable
            if active_only:
                stmt = stmt.where(GradingCriteria.active == True)
            result = db.execute(stmt).scalar()
            self.__logger.debug("Total de critérios: %d", result)
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar critérios: %s", e, exc_info=True)
            raise
