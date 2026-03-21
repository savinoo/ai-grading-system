from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, TEXT, INET
from sqlalchemy.orm import Mapped, mapped_column

from src.models.settings.base import Base


class AuthRefreshToken(Base):
    """
    Entidade que representa um Refresh Token persistido no banco.
    """

    __tablename__ = "auth_refresh_tokens"
    __table_args__ = (
        CheckConstraint(
            "token_type = 'REFRESH'",
            name="chk_token_type",
        ),
        CheckConstraint(
            "key_status IN ('ACTIVE', 'ROTATED', 'REVOKED', 'EXPIRED')",
            name="chk_key_status",
        ),
        CheckConstraint(
            "issued_at <= not_before AND not_before < expires_at",
            name="chk_token_dates",
        ),

        Index(
            "idx_auth_refresh_tokens_jti",
            "jti",
            unique=True,
        ),
        Index(
            "idx_auth_refresh_tokens_subject",
            "subject",
        ),
        Index(
            "idx_auth_refresh_tokens_valid",
            "subject",
            "expires_at",
            postgresql_where=text(
                "revoked_at IS NULL AND key_status = 'ACTIVE'"
            ),
        ),

        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    jti: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.users.uuid",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    token_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'REFRESH'"),
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    not_before: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    key_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )

    scopes: Mapped[List[str]] = mapped_column(
        ARRAY(TEXT),
        nullable=False,
    )

    issued_ip: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
    )

    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuthRefreshToken(jti={self.jti}, subject={self.subject}, "
            f"status={self.key_status}, expires_at={self.expires_at})>"
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
