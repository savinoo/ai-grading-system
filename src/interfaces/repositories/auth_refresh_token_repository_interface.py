from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from src.models.entities.auth_refresh_token import AuthRefreshToken


class AuthRefreshTokenRepositoryInterface(ABC):
    """
    Interface do repositório para operações CRUD da entidade AuthRefreshToken.
    """

    # ==================== READ OPERATIONS ====================
    
    @abstractmethod
    def get_by_id(self, db: Session, token_id: int) -> AuthRefreshToken:
        """
        Busca token por ID.
        
        Args:
            db: Sessão do banco de dados
            token_id: ID do token
            
        Returns:
            AuthRefreshToken: Entidade do token
            
        Raises:
            NoResultFound: Se o token não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def get_by_jti(self, db: Session, jti: UUID) -> Optional[AuthRefreshToken]:
        """
        Busca token por JTI (JWT ID).
        
        Args:
            db: Sessão do banco de dados
            jti: JWT ID único do token
            
        Returns:
            Optional[AuthRefreshToken]: Token encontrado ou None
        """
        raise NotImplementedError()

    @abstractmethod
    def get_active_by_jti(self, db: Session, jti: UUID) -> Optional[AuthRefreshToken]:
        """
        Busca token ativo (não revogado e não expirado) por JTI.
        
        Args:
            db: Sessão do banco de dados
            jti: JWT ID único do token
            
        Returns:
            Optional[AuthRefreshToken]: Token ativo encontrado ou None
        """
        raise NotImplementedError()

    @abstractmethod
    def get_all_by_subject(
        self,
        db: Session,
        subject: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = False
    ) -> Sequence[AuthRefreshToken]:
        """
        Lista todos os tokens de um usuário com paginação.
        
        Args:
            db: Sessão do banco de dados
            subject: UUID do usuário (subject)
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            only_active: Se deve retornar apenas tokens ativos
            
        Returns:
            Sequence[AuthRefreshToken]: Lista de tokens
        """
        raise NotImplementedError()

    @abstractmethod
    def count_active_by_subject(self, db: Session, subject: UUID) -> int:
        """
        Conta quantos tokens ativos o usuário possui.
        
        Args:
            db: Sessão do banco de dados
            subject: UUID do usuário
            
        Returns:
            int: Quantidade de tokens ativos
        """
        raise NotImplementedError()

    # ==================== WRITE OPERATIONS ====================

    @abstractmethod
    def create(
        self,
        db: Session,
        jti: UUID,
        subject: UUID,
        issued_at: datetime,
        not_before: datetime,
        expires_at: datetime,
        scopes: list[str],
        issued_ip: Optional[str] = None,
        token_version: int = 1
    ) -> AuthRefreshToken:
        """
        Cria um novo token de refresh.
        
        Args:
            db: Sessão do banco de dados
            jti: JWT ID único do token
            subject: UUID do usuário
            issued_at: Data/hora de emissão
            not_before: Data/hora a partir da qual o token é válido
            expires_at: Data/hora de expiração
            scopes: Lista de escopos do token
            issued_ip: IP de emissão (opcional)
            token_version: Versão do token (padrão: 1)
            
        Returns:
            AuthRefreshToken: Token criado
        """
        raise NotImplementedError()

    @abstractmethod
    def revoke_by_jti(self, db: Session, jti: UUID) -> AuthRefreshToken:
        """
        Revoga um token específico por JTI.
        
        Args:
            db: Sessão do banco de dados
            jti: JWT ID do token
            
        Returns:
            AuthRefreshToken: Token revogado
            
        Raises:
            NoResultFound: Se o token não existir
        """
        raise NotImplementedError()

    @abstractmethod
    def revoke_all_by_subject(self, db: Session, subject: UUID) -> int:
        """
        Revoga todos os tokens ativos de um usuário.
        
        Args:
            db: Sessão do banco de dados
            subject: UUID do usuário
            
        Returns:
            int: Número de tokens revogados
        """
        raise NotImplementedError()

    @abstractmethod
    def rotate_token(self, db: Session, old_jti: UUID, new_token: AuthRefreshToken) -> AuthRefreshToken:
        """
        Rotaciona um token (marca o antigo como ROTATED e cria um novo).
        
        Args:
            db: Sessão do banco de dados
            old_jti: JTI do token antigo
            new_token: Novo token a ser criado
            
        Returns:
            AuthRefreshToken: Novo token criado
        """
        raise NotImplementedError()

    @abstractmethod
    def mark_as_expired(self, db: Session, jti: UUID) -> AuthRefreshToken:
        """
        Marca um token como expirado.
        
        Args:
            db: Sessão do banco de dados
            jti: JWT ID do token
            
        Returns:
            AuthRefreshToken: Token marcado como expirado
        """
        raise NotImplementedError()

    # ==================== UTILITY OPERATIONS ====================

    @abstractmethod
    def exists_by_jti(self, db: Session, jti: UUID) -> bool:
        """
        Verifica se um token existe pelo JTI.
        
        Args:
            db: Sessão do banco de dados
            jti: JWT ID do token
            
        Returns:
            bool: True se existir, False caso contrário
        """
        raise NotImplementedError()

    @abstractmethod
    def cleanup_expired(self, db: Session, before_date: datetime) -> int:
        """
        Remove tokens expirados antes de uma data específica.
        
        Args:
            db: Sessão do banco de dados
            before_date: Data limite para remoção
            
        Returns:
            int: Número de tokens removidos
        """
        raise NotImplementedError()
