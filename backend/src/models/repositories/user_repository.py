# pylint: disable=C0121
from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.models.entities.user import User

from src.interfaces.repositories.user_repository_interface import UserRepositoryInterface

from src.core.logging_config import get_logger

class UserRepository(UserRepositoryInterface):
    """
    Repositório para operações CRUD da entidade User.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

    def get_by_id(self, db: Session, user_id: int) -> User:
        """
        Busca usuário por ID.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Entidade do usuário
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o usuário não existir
        """
        try:
            self.__logger.debug("Buscando usuário por ID: %s", user_id)
            stmt = select(User).where(User.id == user_id)
            result = db.execute(stmt).scalar_one_or_none()
            
            if not result:
                raise NoResultFound(f"Usuário com ID {user_id} não encontrado")
            
            return result
        except NoResultFound:
            self.__logger.warning("Usuário ID %s não encontrado", user_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar usuário ID %s: %s", user_id, e, exc_info=True)
            raise

    def get_by_uuid(self, db: Session, uuid: UUID) -> User:
        """
        Busca usuário por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do usuário
            
        Returns:
            User: Entidade do usuário
            
        Raises:
            SQLAlchemyError: Em caso de erro de banco de dados
            NoResultFound: Se o usuário não existir
        """
        try:
            self.__logger.debug("Buscando usuário por UUID: %s", uuid)
            stmt = select(User).where(User.uuid == uuid)
            result = db.execute(stmt).scalar_one_or_none()
            
            if not result:
                raise NoResultFound(f"Usuário com UUID {uuid} não encontrado")
            
            return result
        except NoResultFound:
            self.__logger.warning("Usuário UUID %s não encontrado", uuid)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar usuário UUID %s: %s", uuid, e, exc_info=True)
            raise

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Busca usuário por email.
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            
        Returns:
            Optional[User]: Usuário encontrado ou None
        """
        try:
            self.__logger.debug("Buscando usuário por email: %s", email)
            stmt = select(User).where(User.email == email)
            return db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar usuário por email %s: %s", email, e, exc_info=True)
            raise

    def get_active_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Busca usuário ativo e verificado por email.
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            
        Returns:
            Optional[User]: Usuário encontrado ou None
        """
        try:
            self.__logger.debug("Buscando usuário ativo por email: %s", email)
            stmt = (
                select(User)
                .where(
                    User.email == email,
                    User.active == True,
                    User.deleted_at.is_(None)
                )
            )
            return db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar usuário ativo %s: %s", email, e, exc_info=True)
            raise

    def get_all(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> Sequence[User]:
        """
        Lista todos os usuários com paginação.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            include_deleted: Se deve incluir usuários deletados
            
        Returns:
            Sequence[User]: Lista de usuários
        """
        try:
            self.__logger.debug("Listando usuários (skip=%s, limit=%s)", skip, limit)
            stmt = select(User)
            
            if not include_deleted:
                stmt = stmt.where(User.deleted_at.is_(None))
            
            stmt = stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
            
            return db.execute(stmt).scalars().all()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar usuários: %s", e, exc_info=True)
            raise

    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> Sequence[User]:
        """
        Lista usuários ativos.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[User]: Lista de usuários ativos
        """
        try:
            self.__logger.debug("Listando usuários ativos")
            stmt = (
                select(User)
                .where(
                    User.active == True,
                    User.deleted_at.is_(None)
                )
                .offset(skip)
                .limit(limit)
                .order_by(User.created_at.desc())
            )
            return db.execute(stmt).scalars().all()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar usuários ativos: %s", e, exc_info=True)
            raise

    def get_by_user_type(
        self,
        db: Session,
        user_type: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[User]:
        """
        Lista usuários por tipo.
        
        Args:
            db: Sessão do banco de dados
            user_type: Tipo de usuário (user, admin, etc)
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[User]: Lista de usuários do tipo especificado
        """
        try:
            self.__logger.debug("Listando usuários do tipo: %s", user_type)
            stmt = (
                select(User)
                .where(
                    User.user_type == user_type,
                    User.deleted_at.is_(None)
                )
                .offset(skip)
                .limit(limit)
                .order_by(User.created_at.desc())
            )
            return db.execute(stmt).scalars().all()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar usuários tipo %s: %s", user_type, e, exc_info=True)
            raise

    def search_users(
        self,
        db: Session,
        search_term: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[User]:
        """
        Busca usuários por termo (email).
        
        Args:
            db: Sessão do banco de dados
            search_term: Termo de busca
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Sequence[User]: Lista de usuários encontrados
        """
        try:
            self.__logger.debug("Buscando usuários com termo: %s", search_term)
            search_pattern = f"%{search_term}%"
            stmt = (
                select(User)
                .where(
                    User.email.ilike(search_pattern),
                    User.deleted_at.is_(None)
                )
                .offset(skip)
                .limit(limit)
                .order_by(User.created_at.desc())
            )
            return db.execute(stmt).scalars().all()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar usuários: %s", e, exc_info=True)
            raise

    def count_users(self, db: Session, *, active_only: bool = False) -> int:
        """
        Conta o total de usuários.
        
        Args:
            db: Sessão do banco de dados
            active_only: Se deve contar apenas usuários ativos
            
        Returns:
            int: Total de usuários
        """
        try:
            stmt = select(func.count(User.id)).where(User.deleted_at.is_(None))  # pylint: disable=not-callable
            
            if active_only:
                stmt = stmt.where(User.active == True)
            
            result = db.execute(stmt).scalar()
            return result or 0
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar usuários: %s", e, exc_info=True)
            raise

    def exists_by_email(self, db: Session, email: str) -> bool:
        """
        Verifica se existe usuário com o email.
        
        Args:
            db: Sessão do banco de dados
            email: Email a verificar
            
        Returns:
            bool: True se existir, False caso contrário
        """
        try:
            stmt = (
                select(func.count(User.id))  # pylint: disable=not-callable
                .where(
                    User.email == email,
                    User.deleted_at.is_(None)
                )
            )
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
        email: str,
        first_name: str,
        last_name: str,
        password_hash: str,
        user_type: str = "user",
        active: bool = True,
        email_verified: bool = False
    ) -> User:
        """
        Cria um novo usuário.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do usuário
            email: Email do usuário
            first_name: Primeiro nome do usuário
            last_name: Sobrenome do usuário
            password_hash: Senha hash
            user_type: Tipo de usuário
            active: Se o usuário está ativo
            email_verified: Se o email foi verificado
            
        Returns:
            User: Usuário criado
        """
        try:
            self.__logger.debug("Criando usuário: %s", email)
            
            now = datetime.now()
            user = User(
                uuid=uuid,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=password_hash,
                user_type=user_type,
                active=active,
                email_verified=email_verified,
                created_at=now,
                updated_at=now
            )
            
            db.add(user)
            db.flush()  # Para obter o ID gerado
            db.refresh(user)
            
            self.__logger.info("Usuário criado: ID=%s, email=%s", user.id, email)
            return user
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao criar usuário %s: %s", email, e, exc_info=True)
            raise

    def bulk_create(self, db: Session, users_data: list[dict]) -> int:
        """
        Cria múltiplos usuários em lote.
        
        Args:
            db: Sessão do banco de dados
            users_data: Lista de dicionários com dados dos usuários
            
        Returns:
            int: Número de usuários criados
        """
        if not users_data:
            return 0
        
        try:
            self.__logger.debug("Criando %d usuários em lote", len(users_data))
            
            now = datetime.now()
            users = []
            for data in users_data:
                user = User(
                    created_at=now,
                    updated_at=now,
                    **data
                )
                users.append(user)
            
            db.add_all(users)
            db.flush()
            
            self.__logger.info("Criados %d usuários em lote", len(users))
            return len(users)
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro no bulk create de usuários: %s", e, exc_info=True)
            raise

    # ==================== UPDATE OPERATIONS ====================

    def update(self, db: Session, user_id: int, **updates) -> User:
        """
        Atualiza um usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            **updates: Campos a atualizar
            
        Returns:
            User: Usuário atualizado
        """
        try:
            self.__logger.debug("Atualizando usuário ID %s: %s", user_id, updates)
            
            user = self.get_by_id(db, user_id)
            
            # Adiciona updated_at automaticamente
            updates['updated_at'] = datetime.now()
            
            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            db.flush()
            db.refresh(user)
            
            self.__logger.info("Usuário ID %s atualizado", user_id)
            return user
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar usuário ID %s: %s", user_id, e, exc_info=True)
            raise

    def update_password(self, db: Session, user_id: int, password_hash: str) -> User:
        """
        Atualiza a senha do usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            password_hash: Nova senha hash
            
        Returns:
            User: Usuário atualizado
        """
        try:
            self.__logger.debug("Atualizando senha do usuário ID %s", user_id)
            return self.update(db, user_id, password_hash=password_hash)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar senha do usuário ID %s: %s", user_id, e, exc_info=True)
            raise

    def activate(self, db: Session, user_id: int) -> User:
        """
        Ativa um usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário ativado
        """
        try:
            self.__logger.debug("Ativando usuário ID %s", user_id)
            return self.update(db, user_id, active=True)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao ativar usuário ID %s: %s", user_id, e, exc_info=True)
            raise

    def deactivate(self, db: Session, user_id: int) -> User:
        """
        Desativa um usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário desativado
        """
        try:
            self.__logger.debug("Desativando usuário ID %s", user_id)
            return self.update(db, user_id, active=False)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao desativar usuário ID %s: %s", user_id, e, exc_info=True)
            raise

    def verify_email(self, db: Session, user_id: int) -> User:
        """
        Marca o email do usuário como verificado.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário com email verificado
        """
        try:
            self.__logger.debug("Verificando email do usuário ID %s", user_id)
            return self.update(db, user_id, email_verified=True)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao verificar email do usuário ID %s: %s", user_id, e, exc_info=True)
            raise

    def update_last_login_at(self, db: Session, user_id: int) -> User:
        """
        Atualiza o timestamp do último login.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário atualizado
        """
        try:
            self.__logger.debug("Atualizando último login do usuário ID %s", user_id)
            return self.update(db, user_id, last_login_at=datetime.now())
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao atualizar último login do usuário ID %s: %s", user_id, e, exc_info=True)
            raise

    def bulk_update(self, db: Session, mappings: list[dict], *, batch_size: int = 300) -> int:
        """
        Atualiza múltiplos usuários em lote.
        
        Args:
            db: Sessão do banco de dados
            mappings: Lista de dicts com 'id' e campos a atualizar
            batch_size: Tamanho do lote
            
        Returns:
            int: Número de usuários atualizados
            
        Example:
            mappings = [
                {"id": 1, "active": True, "user_type": "admin"},
                {"id": 2, "email_verified": True}
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
                db.bulk_update_mappings(User, chunk)
                total += len(chunk)
            
            db.flush()
            
            self.__logger.info("Bulk update: %d usuários em %d lotes", 
                             total, (len(mappings) + batch_size - 1) // batch_size)
            return total
            
        except SQLAlchemyError as e:
            self.__logger.error("Erro no bulk update: %s", e, exc_info=True)
            raise

    # ==================== DELETE OPERATIONS ====================

    def soft_delete(self, db: Session, user_id: int) -> User:
        """
        Soft delete - marca usuário como deletado.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário deletado (soft)
        """
        try:
            self.__logger.debug("Soft delete do usuário ID %s", user_id)
            return self.update(
                db,
                user_id,
                deleted_at=datetime.now(),
                active=False
            )
        except SQLAlchemyError as e:
            self.__logger.error("Erro no soft delete do usuário ID %s: %s", user_id, e, exc_info=True)
            raise

    def restore(self, db: Session, user_id: int) -> User:
        """
        Restaura um usuário deletado (soft).
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário restaurado
        """
        try:
            self.__logger.debug("Restaurando usuário ID %s", user_id)
            _user = self.get_by_id(db, user_id)
            return self.update(db, user_id, deleted_at=None, active=True)
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao restaurar usuário ID %s: %s", user_id, e, exc_info=True)
            raise

    # ==================== RECOVERY CODE OPERATIONS ====================

    def set_recovery_code(
        self, 
        db: Session, 
        user_id: int, 
        code_hash: str, 
        expires_at: datetime
    ) -> User:
        """
        Define um código de recuperação para o usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            code_hash: Hash do código de recuperação
            expires_at: Timestamp de expiração do código
            
        Returns:
            User: Usuário atualizado
        """
        try:
            self.__logger.debug("Definindo código de recuperação para usuário ID %s", user_id)
            return self.update(
                db,
                user_id,
                recovery_code_hash=code_hash,
                recovery_code_expires_at=expires_at,
                recovery_code_attempts=0
            )
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao definir código de recuperação ID %s: %s", user_id, e, exc_info=True)
            raise

    def increment_recovery_code_attempts(self, db: Session, user_id: int) -> User:
        """
        Incrementa o contador de tentativas do código de recuperação.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário atualizado
        """
        try:
            self.__logger.debug("Incrementando tentativas de código para usuário ID %s", user_id)
            user = self.get_by_id(db, user_id)
            return self.update(
                db,
                user_id,
                recovery_code_attempts=user.recovery_code_attempts + 1
            )
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao incrementar tentativas ID %s: %s", user_id, e, exc_info=True)
            raise

    def clear_recovery_code(self, db: Session, user_id: int) -> User:
        """
        Limpa o código de recuperação do usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário atualizado
        """
        try:
            self.__logger.debug("Limpando código de recuperação do usuário ID %s", user_id)
            return self.update(
                db,
                user_id,
                recovery_code_hash=None,
                recovery_code_expires_at=None,
                recovery_code_attempts=0
            )
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao limpar código de recuperação ID %s: %s", user_id, e, exc_info=True)
            raise
