# pylint: disable=C0121
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.entities.user import User

class UserRepositoryInterface(ABC):
    """
    Repositório para operações CRUD da entidade User.
    """

    # ==================== READ OPERATIONS ====================
    @abstractmethod
    def get_by_id(self, db: Session, user_id: int) -> User:
        """
        Busca usuário por ID.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Entidade do usuário
            
        Raises:
            NoResultFound: Se o usuário não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_uuid(self, db: Session, uuid: UUID) -> User:
        """
        Busca usuário por UUID.
        
        Args:
            db: Sessão do banco de dados
            uuid: UUID do usuário
            
        Returns:
            User: Entidade do usuário
            
        Raises:
            NoResultFound: Se o usuário não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Busca usuário por email.
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            
        Returns:
            Optional[User]: Usuário encontrado ou None
        """
        raise NotImplementedError()

    @abstractmethod
    def get_active_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Busca usuário ativo e verificado por email.
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            
        Returns:
            Optional[User]: Usuário encontrado ou None
        """
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
    def count_users(self, db: Session, *, active_only: bool = False) -> int:
        """
        Conta o total de usuários.
        
        Args:
            db: Sessão do banco de dados
            active_only: Se deve contar apenas usuários ativos
            
        Returns:
            int: Total de usuários
        """
        raise NotImplementedError()

    @abstractmethod
    def exists_by_email(self, db: Session, email: str) -> bool:
        """
        Verifica se existe usuário com o email.
        
        Args:
            db: Sessão do banco de dados
            email: Email a verificar
            
        Returns:
            bool: True se existir, False caso contrário
        """
        raise NotImplementedError()

    # ==================== CREATE OPERATIONS ====================

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
    def bulk_create(self, db: Session, users_data: list[dict]) -> int:
        """
        Cria múltiplos usuários em lote.
        
        Args:
            db: Sessão do banco de dados
            users_data: Lista de dicionários com dados dos usuários
            
        Returns:
            int: Número de usuários criados
        """
        raise NotImplementedError()

    # ==================== UPDATE OPERATIONS ====================

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
    def activate(self, db: Session, user_id: int) -> User:
        """
        Ativa um usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário ativado
        """
        raise NotImplementedError()

    @abstractmethod
    def deactivate(self, db: Session, user_id: int) -> User:
        """
        Desativa um usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário desativado
        """
        raise NotImplementedError()

    @abstractmethod
    def verify_email(self, db: Session, user_id: int) -> User:
        """
        Marca o email do usuário como verificado.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário com email verificado
        """
        raise NotImplementedError()

    @abstractmethod
    def update_last_login_at(self, db: Session, user_id: int) -> User:
        """
        Atualiza o timestamp do último login.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário atualizado
        """
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

    # ==================== DELETE OPERATIONS ====================

    @abstractmethod
    def soft_delete(self, db: Session, user_id: int) -> User:
        """
        Soft delete - marca usuário como deletado.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário deletado (soft)
        """
        raise NotImplementedError()

    @abstractmethod
    def restore(self, db: Session, user_id: int) -> User:
        """
        Restaura um usuário deletado (soft).
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário restaurado
        """
        raise NotImplementedError()
    
    # ==================== RECOVERY CODE OPERATIONS ====================

    @abstractmethod
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
        raise NotImplementedError()
    
    @abstractmethod
    def increment_recovery_code_attempts(self, db: Session, user_id: int) -> User:
        """
        Incrementa o contador de tentativas do código de recuperação.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário atualizado
        """
        raise NotImplementedError()
    
    @abstractmethod
    def clear_recovery_code(self, db: Session, user_id: int) -> User:
        """
        Limpa o código de recuperação do usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            
        Returns:
            User: Usuário atualizado
        """
        raise NotImplementedError()
