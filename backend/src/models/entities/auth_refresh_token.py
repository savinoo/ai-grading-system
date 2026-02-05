from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import (
    UUID, 
    VARCHAR, 
    INTEGER, 
    TIMESTAMP, 
    INET, 
    ARRAY, 
    TEXT,
    BIGINT
)

from src.models.settings.base import Base


class AuthRefreshToken(Base):
    """
    Entidade que representa um token de refresh para autenticação.
    Armazena informações sobre tokens JWT de refresh usados para renovação de sessões.
    """
    
    __tablename__ = "auth_refresh_tokens"
    __table_args__ = (
        CheckConstraint("token_type = 'REFRESH'", name="chk_token_type"),
        CheckConstraint(
            "key_status IN ('ACTIVE', 'ROTATED', 'REVOKED', 'EXPIRED')", 
            name="chk_key_status"
        ),
        CheckConstraint(
            "issued_at <= not_before AND not_before < expires_at",
            name="chk_token_dates"
        ),
        {"schema": "public"}
    )
    
    # Chave primária
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    
    # Identificador único do token (claim jti)
    jti: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    
    # Subject do token (referência ao usuário)
    subject: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("public.users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Versão do token (útil para invalidação em massa)
    token_version: Mapped[int] = mapped_column(INTEGER, nullable=False, default=1)
    
    # Tipo do token (fixo como REFRESH)
    token_type: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, default="REFRESH")
    
    # Claims temporais
    issued_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    
    not_before: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, index=True)
    
    # Estado do token
    key_status: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, default="ACTIVE")
    
    # Escopos associados ao token
    scopes: Mapped[List[str]] = mapped_column(ARRAY(TEXT), nullable=False)
    
    # IP de emissão do token
    issued_ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    
    # Data de revogação (quando aplicável)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # Auditoria
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False,
        default=datetime.now
    )
    
    def __repr__(self) -> str:
        return (
            f"<AuthRefreshToken("
            f"id={self.id}, "
            f"jti={self.jti}, "
            f"subject={self.subject}, "
            f"key_status={self.key_status}, "
            f"expires_at={self.expires_at}"
            f")>"
        )
    
    @property
    def is_valid(self) -> bool:
        """Verifica se o token é válido (ativo e não expirado)."""
        now = datetime.now(timezone.utc)
        return (
            self.key_status == "ACTIVE"
            and self.revoked_at is None
            and self.not_before <= now < self.expires_at
        )
    
    @property
    def is_expired(self) -> bool:
        """Verifica se o token está expirado."""
        return datetime.now(timezone.utc) >= self.expires_at
    
    @property
    def is_revoked(self) -> bool:
        """Verifica se o token foi revogado."""
        return self.revoked_at is not None or self.key_status == "REVOKED"
