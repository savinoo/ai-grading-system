# pylint: disable=C0121
from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.models.entities.exams import Exams

from src.core.logging_config import get_logger

class ExamsRepository(ExamsRepositoryInterface):
    """
    Repositório para operações CRUD da entidade Exams.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

    def get_by_id(self, db: Session, exam_id: int) -> Exams:
        """
        Busca prova por ID.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
            
        Returns:
            Exams: Entidade da prova
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a prova não existir
        """
        try:
            stmt = select(Exams).where(Exams.id == exam_id)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Prova encontrada: ID=%s", exam_id)
            return result

        except NoResultFound:
            self.__logger.warning("Prova não encontrada: ID=%s", exam_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar prova por ID: %s", e, exc_info=True)
            raise

    def get_by_uuid(self, db: Session, uuid: UUID) -> Exams:
        """
        Busca prova por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da prova
            
        Returns:
            Exams: Entidade da prova
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se a prova não existir
        """
        try:
            stmt = select(Exams).where(Exams.uuid == uuid)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Prova encontrada: UUID=%s", uuid)
            return result

        except NoResultFound:
            self.__logger.warning("Prova não encontrada: UUID=%s", uuid)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar prova por UUID: %s", e, exc_info=True)
            raise

    def get_all(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Exams]:
        """
        Lista todas as provas com paginação.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas provas ativas
            
        Returns:
            Sequence[Exams]: Lista de provas
        """
        try:
            stmt = select(Exams)
            if active_only:
                stmt = stmt.where(Exams.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(Exams.created_at.desc())
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d provas", len(result))
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar provas: %s", e, exc_info=True)
            raise

    def get_by_teacher(
        self,
        db: Session,
        teacher_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Exams]:
        """
        Lista provas de um professor específico.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor (created_by)
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas provas ativas
            
        Returns:
            Sequence[Exams]: Lista de provas do professor
        """
        try:
            stmt = select(Exams).where(Exams.created_by == teacher_uuid)
            if active_only:
                stmt = stmt.where(Exams.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(Exams.created_at.desc())
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d provas do professor %s", len(result), teacher_uuid)
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar provas do professor: %s", e, exc_info=True)
            raise

    def get_by_class(
        self,
        db: Session,
        class_uuid: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Exams]:
        """
        Lista provas de uma turma específica.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas provas ativas
            
        Returns:
            Sequence[Exams]: Lista de provas da turma
        """
        try:
            stmt = select(Exams).where(Exams.class_uuid == class_uuid)
            if active_only:
                stmt = stmt.where(Exams.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(Exams.created_at.desc())
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d provas da turma %s", len(result), class_uuid)
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar provas da turma: %s", e, exc_info=True)
            raise

    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Exams]:
        """
        Lista provas por status.
        
        Args:
            db: Sessão do banco de dados
            status: Status da prova (DRAFT, PUBLISHED, ARCHIVED, FINISHED)
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas provas ativas
            
        Returns:
            Sequence[Exams]: Lista de provas com o status especificado
        """
        try:
            stmt = select(Exams).where(Exams.status == status)
            if active_only:
                stmt = stmt.where(Exams.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(Exams.created_at.desc())
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d provas com status %s", len(result), status)
            return result

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar provas por status: %s", e, exc_info=True)
            raise

    def count_exams(self, db: Session, *, active_only: bool = False) -> int:
        """
        Conta o total de provas.
        
        Args:
            db: Sessão do banco de dados
            active_only: Se deve contar apenas provas ativas
            
        Returns:
            int: Total de provas
        """
        try:
            stmt = select(func.count(Exams.id))  # pylint: disable=not-callable
            if active_only:
                stmt = stmt.where(Exams.active == True)
            result = db.execute(stmt).scalar()
            self.__logger.debug("Total de provas: %d", result)
            return result or 0

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar provas: %s", e, exc_info=True)
            raise

    # ==================== CREATE OPERATIONS ====================

    def create(
        self,
        db: Session,
        *,
        uuid: UUID,
        title: str,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None,
        class_uuid: Optional[UUID] = None,
        status: str = "DRAFT",
        starts_at: Optional[datetime] = None,
        ends_at: Optional[datetime] = None,
        active: bool = True
    ) -> Exams:
        """
        Cria uma nova prova.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID da prova
            title: Título da prova
            description: Descrição da prova
            created_by: UUID do professor criador
            class_uuid: UUID da turma
            status: Status da prova (DRAFT, PUBLISHED, ARCHIVED, FINISHED)
            starts_at: Data/hora de início
            ends_at: Data/hora de término
            active: Se a prova está ativa
            
        Returns:
            Exams: Prova criada
        """
        try:
            new_exam = Exams(
                uuid=uuid,
                title=title,
                description=description,
                created_by=created_by,
                class_uuid=class_uuid,
                status=status,
                starts_at=starts_at,
                ends_at=ends_at,
                active=active
            )

            db.add(new_exam)
            db.flush()
            db.refresh(new_exam)

            self.__logger.info("Prova criada: %s (UUID: %s)", title, uuid)
            return new_exam

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao criar prova: %s", e, exc_info=True)
            raise

    # ==================== UPDATE OPERATIONS ====================

    def update(self, db: Session, exam_id: int, **updates) -> Exams:
        """
        Atualiza uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
            **updates: Campos a atualizar
            
        Returns:
            Exams: Prova atualizada
        """
        try:
            exam_obj = self.get_by_id(db, exam_id)

            for key, value in updates.items():
                if hasattr(exam_obj, key):
                    setattr(exam_obj, key, value)

            db.flush()
            db.refresh(exam_obj)

            self.__logger.info("Prova atualizada: ID=%s", exam_id)
            return exam_obj

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar prova: %s", e, exc_info=True)
            raise

    def activate(self, db: Session, exam_id: int) -> Exams:
        """
        Ativa uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
            
        Returns:
            Exams: Prova ativada
        """
        try:
            return self.update(db, exam_id, active=True)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao ativar prova: %s", e, exc_info=True)
            raise

    def deactivate(self, db: Session, exam_id: int) -> Exams:
        """
        Desativa uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
            
        Returns:
            Exams: Prova desativada
        """
        try:
            return self.update(db, exam_id, active=False)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao desativar prova: %s", e, exc_info=True)
            raise

    def update_status(self, db: Session, exam_id: int, status: str) -> Exams:
        """
        Atualiza o status de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
            status: Novo status (DRAFT, PUBLISHED, ARCHIVED, FINISHED)
            
        Returns:
            Exams: Prova com status atualizado
        """
        try:
            return self.update(db, exam_id, status=status)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar status da prova: %s", e, exc_info=True)
            raise

    # ==================== DELETE OPERATIONS ====================

    def delete(self, db: Session, exam_id: int) -> None:
        """
        Remove uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_id: ID da prova
        """
        try:
            exam_obj = self.get_by_id(db, exam_id)
            db.delete(exam_obj)
            db.flush()

            self.__logger.info("Prova removida: ID=%s", exam_id)

        except SQLAlchemyError as e:
            self.__logger.error("Erro ao remover prova: %s", e, exc_info=True)
            raise
