# pylint: disable=C0121
from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.models.entities.classes import Classes

from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface

from src.core.logging_config import get_logger

class ClassesRepository(ClassesRepositoryInterface):
    """
    Repositório para operações CRUD da entidade Class.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

    def get_by_id(self, db: Session, class_id: int) -> Classes:
        """
        Busca turma por ID.
        
        Args:
            db: Sessão do banco de dados
            class_id: ID da turma
            
        Returns:
            Class: Entidade da turma
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a turma não existir
        """
        try:
            stmt = select(Classes).where(Classes.id == class_id)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Turma encontrada: ID=%s", class_id)
            return result
            
        except NoResultFound:
            self.__logger.warning("Turma não encontrada: ID=%s", class_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar turma por ID: %s", e, exc_info=True)
            raise

    def get_by_uuid(self, db: Session, uuid: UUID) -> Classes:
        """
        Busca turma por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da turma
            
        Returns:
            Class: Entidade da turma
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a turma não existir
        """
        try:
            stmt = select(Classes).where(Classes.uuid == uuid)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Turma encontrada: UUID=%s", uuid)
            return result
            
        except NoResultFound:
            self.__logger.warning("Turma não encontrada: UUID=%s", uuid)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar turma por UUID: %s", e, exc_info=True)
            raise

    def get_all(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Classes]:
        """
        Lista todas as turmas com paginação.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas turmas ativas
            
        Returns:
            Sequence[Class]: Lista de turmas
        """
        try:
            stmt = select(Classes)
            if active_only:
                stmt = stmt.where(Classes.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(Classes.created_at.desc())
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d turmas", len(result))
            return result
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar turmas: %s", e, exc_info=True)
            raise

    def get_by_teacher(
        self,
        db: Session,
        teacher_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Classes]:
        """
        Lista turmas de um professor específico.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas turmas ativas
            
        Returns:
            Sequence[Class]: Lista de turmas do professor
        """
        try:
            stmt = select(Classes).where(Classes.teacher_uuid == teacher_uuid)
            if active_only:
                stmt = stmt.where(Classes.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(Classes.created_at.desc())
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d turmas do professor %s", len(result), teacher_uuid)
            return result
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar turmas do professor: %s", e, exc_info=True)
            raise

    def get_by_year_semester(
        self,
        db: Session,
        year: int,
        semester: Optional[int] = None,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Classes]:
        """
        Lista turmas por ano e semestre.
        
        Args:
            db: Sessão do banco de dados
            year: Ano
            semester: Semestre (1 ou 2)
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[Class]: Lista de turmas
        """
        try:
            stmt = select(Classes).where(Classes.year == year)
            if semester is not None:
                stmt = stmt.where(Classes.semester == semester)
            stmt = stmt.offset(skip).limit(limit).order_by(Classes.created_at.desc())
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d turmas para ano=%s, semestre=%s", len(result), year, semester)
            return result
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar turmas por ano/semestre: %s", e, exc_info=True)
            raise

    def count_classes(self, db: Session, *, active_only: bool = False) -> int:
        """
        Conta o total de turmas.
        
        Args:
            db: Sessão do banco de dados
            active_only: Se deve contar apenas turmas ativas
            
        Returns:
            int: Total de turmas
        """
        try:
            stmt = select(func.count(Classes.id))# pylint: disable=not-callable
            if active_only:
                stmt = stmt.where(Classes.active == True)
            result = db.execute(stmt).scalar()
            self.__logger.debug("Total de turmas: %d", result)
            return result or 0
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar turmas: %s", e, exc_info=True)
            raise

    # ==================== CREATE OPERATIONS ====================

    def create(
        self,
        db: Session,
        *,
        uuid: UUID,
        name: str,
        teacher_uuid: UUID,
        description: Optional[str] = None,
        year: Optional[int] = None,
        semester: Optional[int] = None,
        created_by: Optional[UUID] = None,
        active: bool = True
    ) -> Classes:
        """
        Cria uma nova turma.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da turma
            name: Nome da turma
            teacher_uuid: UUID do professor
            description: Descrição da turma
            year: Ano
            semester: Semestre (1 ou 2)
            created_by: UUID do criador
            active: Se a turma está ativa
            
        Returns:
            Class: Turma criada
        """
        try:
            new_class = Classes(
                uuid=uuid,
                name=name,
                teacher_uuid=teacher_uuid,
                description=description,
                year=year,
                semester=semester,
                created_by=created_by,
                active=active
            )
            
            db.add(new_class)
            db.flush()
            db.refresh(new_class)
            
            self.__logger.info("Turma criada: %s (UUID: %s)", name, uuid)
            return new_class
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao criar turma: %s", e, exc_info=True)
            raise

    # ==================== UPDATE OPERATIONS ====================

    def update(self, db: Session, class_id: int, **updates) -> Classes:
        """
        Atualiza uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_id: ID da turma
            **updates: Campos a atualizar
            
        Returns:
            Class: Turma atualizada
        """
        try:
            class_obj = self.get_by_id(db, class_id)
            
            for key, value in updates.items():
                if hasattr(class_obj, key):
                    setattr(class_obj, key, value)
            
            db.flush()
            db.refresh(class_obj)
            
            self.__logger.info("Turma atualizada: ID=%s", class_id)
            return class_obj
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar turma: %s", e, exc_info=True)
            raise

    def activate(self, db: Session, class_id: int) -> Classes:
        """
        Ativa uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_id: ID da turma
            
        Returns:
            Class: Turma ativada
        """
        try:
            return self.update(db, class_id, active=True)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao ativar turma: %s", e, exc_info=True)
            raise

    def deactivate(self, db: Session, class_id: int) -> Classes:
        """
        Desativa uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_id: ID da turma
            
        Returns:
            Class: Turma desativada
        """
        try:
            return self.update(db, class_id, active=False)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao desativar turma: %s", e, exc_info=True)
            raise

    # ==================== DELETE OPERATIONS ====================

    def delete(self, db: Session, class_id: int) -> None:
        """
        Remove uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_id: ID da turma
        """
        try:
            class_obj = self.get_by_id(db, class_id)
            db.delete(class_obj)
            db.flush()
            
            self.__logger.info("Turma removida: ID=%s", class_id)
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao remover turma: %s", e, exc_info=True)
            raise
