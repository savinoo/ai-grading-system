from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Index,
    String,
    Integer,
    Text,
    BigInteger,
    DateTime,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.settings.base import Base

class User(Base):
    """Entidade que representa um Usuário no sistema."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("recovery_code_attempts >= 0", name="chk_users_recovery_code_attempts"),

        Index("idx_users_uuid", "uuid", unique=True),
        Index("idx_users_email", "email"),
        Index("idx_users_active", "active"),
        Index("idx_users_recovery_code_expires_at", "recovery_code_expires_at"),

        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("gen_random_uuid()"),
        unique=True,
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    user_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'teacher'"),
    )

    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)

    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))

    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    recovery_code_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    recovery_code_expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recovery_code_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, user_type={self.user_type}, active={self.active})>"
