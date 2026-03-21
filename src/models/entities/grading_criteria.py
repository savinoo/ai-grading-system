from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Index,
    BigInteger,
    String,
    DateTime,
    Text,
    Boolean,
    text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.settings.base import Base

class GradingCriteria(Base):
    """
    Entidade que representa um Critério de Avaliação no sistema.
    """
    
    __tablename__ = "grading_criteria"
    __table_args__ = (
        Index("uq_grading_criteria_uuid", "uuid", unique=True),
        {"schema": "public"},
    )
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("gen_random_uuid()"),
        unique=True,
    )
    
    
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    
    def __repr__(self) -> str:
        return f"<GradingCriteria(uuid={self.uuid}, code={self.code}, name={self.name})>"
