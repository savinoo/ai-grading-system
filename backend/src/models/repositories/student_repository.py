# pylint: disable=C0121
from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.models.entities.student import Student

from src.interfaces.repositories.student_repository_interface import StudentRepositoryInterface

from src.core.logging_config import get_logger

class StudentRepository(StudentRepositoryInterface):
    """
    Repositório para operações CRUD da entidade Student.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

    def get_by_id(self, db: Session, student_id: int) -> Student:
        """
        Busca estudante por ID.
        
        Args:
            db: Sessão do banco de dados
            student_id: ID do estudante
            
        Returns:
            Student: Entidade do estudante
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o estudante não existir
        """
        try:
            self.__logger.debug("Buscando estudante por ID: %s", student_id)
            stmt = select(Student).where(Student.id == student_id)
            result = db.execute(stmt).scalar_one_or_none()
            
            if not result:
                raise NoResultFound(f"Estudante com ID {student_id} não encontrado")
            
            return result
        except NoResultFound:
            self.__logger.warning("Estudante ID %s não encontrado", student_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar estudante ID %s: %s", student_id, e, exc_info=True)
            raise

    def get_by_uuid(self, db: Session, uuid: UUID) -> Student:
        """
        Busca estudante por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do estudante
            
        Returns:
            Student: Entidade do estudante
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o estudante não existir
        """
        try:
            self.__logger.debug("Buscando estudante por UUID: %s", uuid)
            stmt = select(Student).where(Student.uuid == uuid)
            result = db.execute(stmt).scalar_one_or_none()
            
            if not result:
                raise NoResultFound(f"Estudante com UUID {uuid} não encontrado")
            
            return result
        except NoResultFound:
            self.__logger.warning("Estudante UUID %s não encontrado", uuid)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar estudante UUID %s: %s", uuid, e, exc_info=True)
            raise

    def get_by_email(self, db: Session, email: str) -> Optional[Student]:
        """
        Busca estudante por email.
        
        Args:
            db: Sessão do banco de dados
            email: Email do estudante
            
        Returns:
            Optional[Student]: Estudante encontrado ou None
        """
        try:
            self.__logger.debug("Buscando estudante por email: %s", email)
            stmt = select(Student).where(Student.email == email)
            return db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar estudante por email %s: %s", email, e, exc_info=True)
            raise

    def get_all(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Sequence[Student]:
        """
        Lista todos os estudantes com paginação.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas estudantes ativos
            
        Returns:
            Sequence[Student]: Lista de estudantes
        """
        try:
            self.__logger.debug("Listando estudantes (skip=%s, limit=%s)", skip, limit)
            stmt = select(Student)
            
            if active_only:
                stmt = stmt.where(Student.active == True)
            
            stmt = stmt.offset(skip).limit(limit).order_by(Student.created_at.desc())
            
            return db.execute(stmt).scalars().all()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar estudantes: %s", e, exc_info=True)
            raise

    def get_active_students(self, db: Session, *, skip: int = 0, limit: int = 100) -> Sequence[Student]:
        """
        Lista estudantes ativos.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[Student]: Lista de estudantes ativos
        """
        try:
            self.__logger.debug("Listando estudantes ativos")
            stmt = (
                select(Student)
                .where(Student.active == True)
                .offset(skip)
                .limit(limit)
                .order_by(Student.created_at.desc())
            )
            return db.execute(stmt).scalars().all()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar estudantes ativos: %s", e, exc_info=True)
            raise

    def search_students(
        self,
        db: Session,
        search_term: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Student]:
        """
        Busca estudantes por termo (nome, email ou matrícula).
        
        Args:
            db: Sessão do banco de dados
            search_term: Termo de busca
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[Student]: Lista de estudantes encontrados
        """
        try:
            self.__logger.debug("Buscando estudantes com termo: %s", search_term)
            search_pattern = f"%{search_term}%"
            stmt = (
                select(Student)
                .where(
                    or_(
                        Student.full_name.ilike(search_pattern),
                        Student.email.ilike(search_pattern),
                        Student.registration_number.ilike(search_pattern)
                    )
                )
                .offset(skip)
                .limit(limit)
                .order_by(Student.created_at.desc())
            )
            return db.execute(stmt).scalars().all()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar estudantes: %s", e, exc_info=True)
            raise

    def count_students(self, db: Session, *, active_only: bool = False) -> int:
        """
        Conta o total de estudantes.
        
        Args:
            db: Sessão do banco de dados
            active_only: Se deve contar apenas estudantes ativos
            
        Returns:
            int: Total de estudantes
        """
        try:
            stmt = select(func.count(Student.id))  # pylint: disable=not-callable
            
            if active_only:
                stmt = stmt.where(Student.active == True)
            
            result = db.execute(stmt).scalar()
            return result or 0
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar estudantes: %s", e, exc_info=True)
            raise

    def exists_by_email(self, db: Session, email: str) -> bool:
        """
        Verifica se existe estudante com o email.
        
        Args:
            db: Sessão do banco de dados
            email: Email a verificar
            
        Returns:
            bool: True se existir, False caso contrário
        """
        try:
            stmt = select(func.count(Student.id)).where(Student.email == email)  # pylint: disable=not-callable
            count = db.execute(stmt).scalar()
            return (count or 0) > 0
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao verificar existência do email %s: %s", email, e, exc_info=True)
            raise

    # ==================== CREATE OPERATIONS ====================

    def create(
        self,
        db: Session,
        *,
        uuid: UUID,
        full_name: str,
        email: Optional[str] = None,
        active: bool = True
    ) -> Student:
        """
        Cria um novo estudante.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do estudante
            full_name: Nome completo do estudante
            email: Email do estudante
            active: Se o estudante está ativo
            
        Returns:
            Student: Estudante criado
        """
        try:
            self.__logger.debug("Criando estudante: %s", full_name)
            
            now = datetime.now()
            student = Student(
                uuid=uuid,
                full_name=full_name,
                email=email,
                active=active,
                created_at=now,
                updated_at=now
            )
            
            db.add(student)
            db.flush()  # Para obter o ID gerado
            db.refresh(student)
            
            self.__logger.info("Estudante criado: ID=%s, nome=%s", student.id, full_name)
            return student
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao criar estudante %s: %s", full_name, e, exc_info=True)
            raise

    def bulk_create(self, db: Session, students_data: list[dict]) -> int:
        """
        Cria múltiplos estudantes em lote.
        
        Args:
            db: Sessão do banco de dados
            students_data: Lista de dicionários com dados dos estudantes
            
        Returns:
            int: Número de estudantes criados
        """
        if not students_data:
            return 0
        
        try:
            self.__logger.debug("Criando %d estudantes em lote", len(students_data))
            
            now = datetime.now()
            students = []
            for data in students_data:
                student = Student(
                    created_at=now,
                    updated_at=now,
                    **data
                )
                students.append(student)
            
            db.add_all(students)
            db.flush()
            
            self.__logger.info("Criados %d estudantes em lote", len(students))
            return len(students)
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro no bulk create de estudantes: %s", e, exc_info=True)
            raise

    # ==================== UPDATE OPERATIONS ====================

    def update(self, db: Session, student_id: int, **updates) -> Student:
        """
        Atualiza um estudante.
        
        Args:
            db: Sessão do banco de dados
            student_id: ID do estudante
            **updates: Campos a atualizar
            
        Returns:
            Student: Estudante atualizado
        """
        try:
            self.__logger.debug("Atualizando estudante ID %s: %s", student_id, updates)
            
            student = self.get_by_id(db, student_id)
            
            # Adiciona updated_at automaticamente
            updates['updated_at'] = datetime.now()
            
            for key, value in updates.items():
                if hasattr(student, key):
                    setattr(student, key, value)
            
            db.flush()
            db.refresh(student)
            
            self.__logger.info("Estudante ID %s atualizado", student_id)
            return student
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar estudante ID %s: %s", student_id, e, exc_info=True)
            raise

    def activate(self, db: Session, student_id: int) -> Student:
        """
        Ativa um estudante.
        
        Args:
            db: Sessão do banco de dados
            student_id: ID do estudante
            
        Returns:
            Student: Estudante ativado
        """
        try:
            self.__logger.debug("Ativando estudante ID %s", student_id)
            return self.update(db, student_id, active=True)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao ativar estudante ID %s: %s", student_id, e, exc_info=True)
            raise

    def deactivate(self, db: Session, student_id: int) -> Student:
        """
        Desativa um estudante.
        
        Args:
            db: Sessão do banco de dados
            student_id: ID do estudante
            
        Returns:
            Student: Estudante desativado
        """
        try:
            self.__logger.debug("Desativando estudante ID %s", student_id)
            return self.update(db, student_id, active=False)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao desativar estudante ID %s: %s", student_id, e, exc_info=True)
            raise

    def bulk_update(self, db: Session, mappings: list[dict], *, batch_size: int = 300) -> int:
        """
        Atualiza múltiplos estudantes em lote.
        
        Args:
            db: Sessão do banco de dados
            mappings: Lista de dicts com 'id' e campos a atualizar
            batch_size: Tamanho do lote
            
        Returns:
            int: Número de estudantes atualizados
            
        Example:
            mappings = [
                {"id": 1, "active": True, "email": "novo@email.com"},
                {"id": 2, "full_name": "Nome Atualizado"}
            ]
        """
        if not mappings:
            return 0
        
        try:
            total = 0
            now = datetime.now()
            
            # Adiciona updated_at em todos os mappings
            for mapping in mappings:
                mapping['updated_at'] = now
            
            for i in range(0, len(mappings), batch_size):
                chunk = mappings[i:i + batch_size]
                db.bulk_update_mappings(Student, chunk)
                total += len(chunk)
            
            db.flush()
            
            self.__logger.info("Bulk update: %d estudantes em %d lotes", 
                             total, (len(mappings) + batch_size - 1) // batch_size)
            return total
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro no bulk update: %s", e, exc_info=True)
            raise

    # ==================== DELETE OPERATIONS ====================

    def delete(self, db: Session, student_id: int) -> None:
        """
        Remove um estudante permanentemente.
        
        Args:
            db: Sessão do banco de dados
            student_id: ID do estudante
        """
        try:
            self.__logger.debug("Deletando estudante ID %s", student_id)
            student = self.get_by_id(db, student_id)
            
            db.delete(student)
            db.flush()
            
            self.__logger.info("Estudante ID %s deletado", student_id)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao deletar estudante ID %s: %s", student_id, e, exc_info=True)
            raise
