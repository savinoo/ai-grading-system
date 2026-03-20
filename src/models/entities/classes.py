from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    String,
    Text,
    DateTime,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.settings.base import Base


class Classes(Base):
    """
    Entidade que representa uma Turma no sistema.
    """

    __tablename__ = "classes"
    __table_args__ = (

        Index("idx_classes_active", "active"),
        Index("idx_classes_year", "year"),
        Index("idx_classes_created_by", "created_by"),
        Index("uq_classes_uuid", "uuid", unique=True),

        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("gen_random_uuid()"),
        unique=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    year: Mapped[Optional[int]] = mapped_column(nullable=True)
    semester: Mapped[Optional[int]] = mapped_column(nullable=True)

    teacher_uuid: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.uuid", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.uuid", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    def __repr__(self) -> str:
        return f"<Classes(id={self.id}, name={self.name}, year={self.year}, semester={self.semester}, active={self.active})>"
