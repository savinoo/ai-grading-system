from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.models.entities.auth_refresh_token import AuthRefreshToken

from src.interfaces.repositories.auth_refresh_token_repository_interface import (
    AuthRefreshTokenRepositoryInterface
)

from src.core.logging_config import get_logger


class AuthRefreshTokenRepository(AuthRefreshTokenRepositoryInterface):
    """
    Repositório para operações CRUD da entidade AuthRefreshToken.
    """

    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    # ==================== READ OPERATIONS ====================

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
            SQLAlchemyError: Se ocorrer erro no banco de dados
        """
        try:
            self.__logger.debug("Buscando token por ID: %s", token_id)
            stmt = select(AuthRefreshToken).where(AuthRefreshToken.id == token_id)
            result = db.execute(stmt).scalar_one_or_none()
            
            if not result:
                raise NoResultFound(f"Token com ID {token_id} não encontrado")
            
            return result
        except NoResultFound:
            self.__logger.warning("Token ID %s não encontrado", token_id)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar token ID %s: %s", token_id, e, exc_info=True)
            raise

    def get_by_jti(self, db: Session, jti: UUID) -> Optional[AuthRefreshToken]:
        """
        Busca token por JTI (JWT ID).
        
        Args:
            db: Sessão do banco de dados
            jti: JWT ID único do token
            
        Returns:
            Optional[AuthRefreshToken]: Token encontrado ou None
        """
        try:
            self.__logger.debug("Buscando token por JTI: %s", jti)
            stmt = select(AuthRefreshToken).where(AuthRefreshToken.jti == jti)
            return db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar token por JTI %s: %s", jti, e, exc_info=True)
            raise

    def get_active_by_jti(self, db: Session, jti: UUID) -> Optional[AuthRefreshToken]:
        """
        Busca token ativo (não revogado e não expirado) por JTI.
        
        Args:
            db: Sessão do banco de dados
            jti: JWT ID único do token
            
        Returns:
            Optional[AuthRefreshToken]: Token ativo encontrado ou None
        """
        try:
            self.__logger.debug("Buscando token ativo por JTI: %s", jti)
            now = datetime.now()
            stmt = (
                select(AuthRefreshToken)
                .where(
                    AuthRefreshToken.jti == jti,
                    AuthRefreshToken.key_status == "ACTIVE",
                    AuthRefreshToken.revoked_at.is_(None),
                    AuthRefreshToken.expires_at > now
                )
            )
            return db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar token ativo %s: %s", jti, e, exc_info=True)
            raise

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
        try:
            self.__logger.debug(
                "Listando tokens do usuário %s (skip=%d, limit=%d, only_active=%s)",
                subject, skip, limit, only_active
            )
            
            stmt = select(AuthRefreshToken).where(AuthRefreshToken.subject == subject)
            
            if only_active:
                now = datetime.now()
                stmt = stmt.where(
                    AuthRefreshToken.key_status == "ACTIVE",
                    AuthRefreshToken.revoked_at.is_(None),
                    AuthRefreshToken.expires_at > now
                )
            
            stmt = stmt.order_by(AuthRefreshToken.created_at.desc()).offset(skip).limit(limit)
            
            return db.execute(stmt).scalars().all()
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao listar tokens do usuário %s: %s", subject, e, exc_info=True)
            raise

    def count_active_by_subject(self, db: Session, subject: UUID) -> int:
        """
        Conta quantos tokens ativos o usuário possui.
        
        Args:
            db: Sessão do banco de dados
            subject: UUID do usuário
            
        Returns:
            int: Quantidade de tokens ativos
        """
        try:
            self.__logger.debug("Contando tokens ativos do usuário %s", subject)
            now = datetime.now()
            stmt = (
                select(func.count(AuthRefreshToken.id)) # pylint: disable=not-callable
                .where(
                    AuthRefreshToken.subject == subject,
                    AuthRefreshToken.key_status == "ACTIVE",
                    AuthRefreshToken.revoked_at.is_(None),
                    AuthRefreshToken.expires_at > now
                )
            )
            return db.execute(stmt).scalar() or 0
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao contar tokens do usuário %s: %s", subject, e, exc_info=True)
            raise

    # ==================== WRITE OPERATIONS ====================

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
        try:
            self.__logger.debug("Criando novo refresh token para usuário %s", subject)
            
            token = AuthRefreshToken(
                jti=jti,
                subject=subject,
                token_version=token_version,
                issued_at=issued_at,
                not_before=not_before,
                expires_at=expires_at,
                scopes=scopes,
                issued_ip=issued_ip,
                key_status="ACTIVE",
                created_at=datetime.now()
            )
            
            db.add(token)
            db.flush()
            
            self.__logger.info(
                "Token criado: ID=%s, JTI=%s, subject=%s", 
                token.id, token.jti, token.subject
            )
            
            return token
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao criar token para usuário %s: %s", subject, e, exc_info=True)
            raise

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
            SQLAlchemyError: Se ocorrer erro no banco de dados
        """
        try:
            self.__logger.debug("Revogando token por JTI: %s", jti)
            
            token = self.get_by_jti(db, jti)
            if not token:
                raise NoResultFound(f"Token com JTI {jti} não encontrado")
            
            token.key_status = "REVOKED"
            token.revoked_at = datetime.now()
            
            db.flush()
            
            self.__logger.info("Token revogado: JTI=%s", jti)
            return token
        except NoResultFound:
            self.__logger.warning("Token JTI %s não encontrado para revogação", jti)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao revogar token %s: %s", jti, e, exc_info=True)
            raise

    def revoke_all_by_subject(self, db: Session, subject: UUID) -> int:
        """
        Revoga todos os tokens ativos de um usuário.
        
        Args:
            db: Sessão do banco de dados
            subject: UUID do usuário
            
        Returns:
            int: Número de tokens revogados
        """
        try:
            self.__logger.debug("Revogando todos os tokens do usuário %s", subject)
            now = datetime.now()
            
            stmt = (
                update(AuthRefreshToken)
                .where(
                    AuthRefreshToken.subject == subject,
                    AuthRefreshToken.key_status == "ACTIVE",
                    AuthRefreshToken.revoked_at.is_(None)
                )
                .values(
                    key_status="REVOKED",
                    revoked_at=now
                )
            )
            
            result = db.execute(stmt)
            db.flush()
            
            count = result.rowcount
            self.__logger.info("Revogados %d tokens do usuário %s", count, subject)
            return count
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao revogar tokens do usuário %s: %s", subject, e, exc_info=True)
            raise

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
        try:
            self.__logger.debug("Rotacionando token: old_jti=%s", old_jti)
            
            # Marca o token antigo como ROTATED
            old_token = self.get_by_jti(db, old_jti)
            if not old_token:
                raise NoResultFound(f"Token com JTI {old_jti} não encontrado")
            
            old_token.key_status = "ROTATED"
            
            # Cria o novo token
            db.add(new_token)
            db.flush()
            
            self.__logger.info(
                "Token rotacionado: old_jti=%s -> new_jti=%s", 
                old_jti, new_token.jti
            )
            
            return new_token
        except NoResultFound:
            self.__logger.warning("Token JTI %s não encontrado para rotação", old_jti)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao rotacionar token %s: %s", old_jti, e, exc_info=True)
            raise

    def mark_as_expired(self, db: Session, jti: UUID) -> AuthRefreshToken:
        """
        Marca um token como expirado.
        
        Args:
            db: Sessão do banco de dados
            jti: JWT ID do token
            
        Returns:
            AuthRefreshToken: Token marcado como expirado
        """
        try:
            self.__logger.debug("Marcando token como expirado: %s", jti)
            
            token = self.get_by_jti(db, jti)
            if not token:
                raise NoResultFound(f"Token com JTI {jti} não encontrado")
            
            token.key_status = "EXPIRED"
            db.flush()
            
            self.__logger.info("Token marcado como expirado: JTI=%s", jti)
            return token
        except NoResultFound:
            self.__logger.warning("Token JTI %s não encontrado", jti)
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao marcar token como expirado %s: %s", jti, e, exc_info=True)
            raise

    # ==================== UTILITY OPERATIONS ====================

    def exists_by_jti(self, db: Session, jti: UUID) -> bool:
        """
        Verifica se um token existe pelo JTI.
        
        Args:
            db: Sessão do banco de dados
            jti: JWT ID do token
            
        Returns:
            bool: True se existir, False caso contrário
        """
        try:
            self.__logger.debug("Verificando existência do token JTI: %s", jti)
            stmt = select(func.count(AuthRefreshToken.id)).where(AuthRefreshToken.jti == jti) # pylint: disable=not-callable
            count = db.execute(stmt).scalar()
            return count > 0
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao verificar existência do token %s: %s", jti, e, exc_info=True)
            raise

    def cleanup_expired(self, db: Session, before_date: datetime) -> int:
        """
        Remove tokens expirados antes de uma data específica.
        
        Args:
            db: Sessão do banco de dados
            before_date: Data limite para remoção
            
        Returns:
            int: Número de tokens removidos
        """
        try:
            self.__logger.debug("Limpando tokens expirados antes de %s", before_date)
            
            stmt = (
                delete(AuthRefreshToken)
                .where(AuthRefreshToken.expires_at < before_date)
            )
            
            result = db.execute(stmt)
            db.flush()
            
            count = result.rowcount
            self.__logger.info("Removidos %d tokens expirados", count)
            return count
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao limpar tokens expirados: %s", e, exc_info=True)
            raise
