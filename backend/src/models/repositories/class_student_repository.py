# pylint: disable=C0121
# pylint: disable=not-callable
from __future__ import annotations

from typing import Sequence
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.models.entities.class_student import ClassStudent

from src.interfaces.repositories.class_student_repository_interface import ClassStudentRepositoryInterface

from src.core.logging_config import get_logger

class ClassStudentRepository(ClassStudentRepositoryInterface):
    """
    Repositório para operações CRUD da entidade ClassStudent.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

    def get_by_id(self, db: Session, class_student_id: int) -> ClassStudent:
        """
        Busca relacionamento por ID.
        
        Args:
            db: Sessão do banco de dados
            class_student_id: ID do relacionamento
            
        Returns:
            ClassStudent: Entidade do relacionamento
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o relacionamento não existir
        """
        try:
            stmt = select(ClassStudent).where(ClassStudent.id == class_student_id)
            result = db.execute(stmt).scalar_one()
            self.__logger.debug("Relacionamento encontrado: ID=%s", class_student_id)
            return result
            
        except NoResultFound:
            self.__logger.warning("Relacionamento não encontrado: ID=%s", class_student_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar relacionamento por ID: %s", e, exc_info=True)
            raise

    def get_students_by_class(
        self,
        db: Session,
        class_uuid: UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[ClassStudent]:
        """
        Lista alunos de uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            active_only: Se deve retornar apenas matrículas ativas
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[ClassStudent]: Lista de relacionamentos
        """
        try:
            stmt = select(ClassStudent).where(ClassStudent.class_uuid == class_uuid)
            if active_only:
                stmt = stmt.where(ClassStudent.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(ClassStudent.enrolled_at.desc())
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listados %d alunos na turma %s", len(result), class_uuid)
            return result
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar alunos da turma: %s", e, exc_info=True)
            raise

    def get_classes_by_student(
        self,
        db: Session,
        student_uuid: UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[ClassStudent]:
        """
        Lista turmas de um aluno.
        
        Args:
            db: Sessão do banco de dados
            student_uuid: UUID do aluno
            active_only: Se deve retornar apenas matrículas ativas
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[ClassStudent]: Lista de relacionamentos
        """
        try:
            stmt = select(ClassStudent).where(ClassStudent.student_uuid == student_uuid)
            if active_only:
                stmt = stmt.where(ClassStudent.active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(ClassStudent.enrolled_at.desc())
            result = db.execute(stmt).scalars().all()
            self.__logger.debug("Listadas %d turmas do aluno %s", len(result), student_uuid)
            return result
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar turmas do aluno: %s", e, exc_info=True)
            raise

    def exists(self, db: Session, class_uuid: UUID, student_uuid: UUID) -> bool:
        """
        Verifica se o aluno já está matriculado na turma.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            student_uuid: UUID do aluno
            
        Returns:
            bool: True se existe, False caso contrário
        """
        try:
            stmt = select(func.count(ClassStudent.id)).where(
                and_(
                    ClassStudent.class_uuid == class_uuid,
                    ClassStudent.student_uuid == student_uuid
                )
            )
            result = db.execute(stmt).scalar()
            exists = result > 0
            self.__logger.debug("Aluno %s na turma %s: %s", student_uuid, class_uuid, exists)
            return exists
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao verificar existência de matrícula: %s", e, exc_info=True)
            raise

    def count_students_in_class(self, db: Session, class_uuid: UUID, *, active_only: bool = True) -> int:
        """
        Conta alunos em uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            active_only: Se deve contar apenas matrículas ativas
            
        Returns:
            int: Total de alunos
        """
        try:
            stmt = select(func.count(ClassStudent.id)).where(ClassStudent.class_uuid == class_uuid)
            if active_only:
                stmt = stmt.where(ClassStudent.active == True)
            result = db.execute(stmt).scalar()
            self.__logger.debug("Total de alunos na turma %s: %d", class_uuid, result or 0)
            return result or 0
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar alunos da turma: %s", e, exc_info=True)
            raise

    # ==================== CREATE OPERATIONS ====================

    def create(
        self,
        db: Session,
        *,
        class_uuid: UUID,
        student_uuid: UUID,
        enrolled_at: datetime = None,
        active: bool = True
    ) -> ClassStudent:
        """
        Matricula um aluno em uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            student_uuid: UUID do aluno
            enrolled_at: Data de matrícula
            active: Se a matrícula está ativa
            
        Returns:
            ClassStudent: Relacionamento criado
        """
        try:
            new_enrollment = ClassStudent(
                class_uuid=class_uuid,
                student_uuid=student_uuid,
                enrolled_at=enrolled_at or datetime.now(),
                active=active
            )
            
            db.add(new_enrollment)
            db.commit()
            db.refresh(new_enrollment)
            
            self.__logger.info("Aluno %s matriculado na turma %s", student_uuid, class_uuid)
            return new_enrollment
            
        except SQLAlchemyError as e:
            db.rollback()
            self.__logger.error("Erro ao matricular aluno: %s", e, exc_info=True)
            raise

    def bulk_create(
        self,
        db: Session,
        class_uuid: UUID,
        student_uuids: list[UUID]
    ) -> int:
        """
        Matricula múltiplos alunos em uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            student_uuids: Lista de UUIDs dos alunos
            
        Returns:
            int: Número de alunos matriculados
        """
        if not student_uuids:
            return 0
        
        try:
            enrollments = [
                ClassStudent(
                    class_uuid=class_uuid,
                    student_uuid=student_uuid,
                    enrolled_at=datetime.now(),
                    active=True
                )
                for student_uuid in student_uuids
            ]
            
            db.add_all(enrollments)
            db.commit()
            
            count = len(enrollments)
            self.__logger.info("%d alunos matriculados na turma %s", count, class_uuid)
            return count
            
        except SQLAlchemyError as e:
            db.rollback()
            self.__logger.error("Erro ao matricular alunos em lote: %s", e, exc_info=True)
            raise

    # ==================== UPDATE OPERATIONS ====================

    def activate(self, db: Session, class_student_id: int) -> ClassStudent:
        """
        Ativa matrícula.
        
        Args:
            db: Sessão do banco de dados
            class_student_id: ID do relacionamento
            
        Returns:
            ClassStudent: Relacionamento ativado
        """
        try:
            enrollment = self.get_by_id(db, class_student_id)
            enrollment.active = True
            
            db.commit()
            db.refresh(enrollment)
            
            self.__logger.info("Matrícula ativada: ID=%s", class_student_id)
            return enrollment
            
        except SQLAlchemyError as e:
            db.rollback()
            self.__logger.error("Erro ao ativar matrícula: %s", e, exc_info=True)
            raise

    def deactivate(self, db: Session, class_student_id: int) -> ClassStudent:
        """
        Desativa matrícula.
        
        Args:
            db: Sessão do banco de dados
            class_student_id: ID do relacionamento
            
        Returns:
            ClassStudent: Relacionamento desativado
        """
        try:
            enrollment = self.get_by_id(db, class_student_id)
            enrollment.active = False
            
            db.commit()
            db.refresh(enrollment)
            
            self.__logger.info("Matrícula desativada: ID=%s", class_student_id)
            return enrollment
            
        except SQLAlchemyError as e:
            db.rollback()
            self.__logger.error("Erro ao desativar matrícula: %s", e, exc_info=True)
            raise

    # ==================== DELETE OPERATIONS ====================

    def delete(self, db: Session, class_student_id: int) -> None:
        """
        Remove matrícula.
        
        Args:
            db: Sessão do banco de dados
            class_student_id: ID do relacionamento
        """
        try:
            enrollment = self.get_by_id(db, class_student_id)
            db.delete(enrollment)
            db.commit()
            
            self.__logger.info("Matrícula removida: ID=%s", class_student_id)
            
        except SQLAlchemyError as e:
            db.rollback()
            self.__logger.error("Erro ao remover matrícula: %s", e, exc_info=True)
            raise

    def remove_student_from_class(self, db: Session, class_uuid: UUID, student_uuid: UUID) -> None:
        """
        Remove um aluno de uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            student_uuid: UUID do aluno
        """
        try:
            stmt = select(ClassStudent).where(
                and_(
                    ClassStudent.class_uuid == class_uuid,
                    ClassStudent.student_uuid == student_uuid
                )
            )
            enrollment = db.execute(stmt).scalar_one()
            db.delete(enrollment)
            db.commit()
            
            self.__logger.info("Aluno %s removido da turma %s", student_uuid, class_uuid)
            
        except NoResultFound:
            self.__logger.warning("Matrícula não encontrada: aluno %s na turma %s", student_uuid, class_uuid)
            raise
        except SQLAlchemyError as e:
            db.rollback()
            self.__logger.error("Erro ao remover aluno da turma: %s", e, exc_info=True)
            raise
