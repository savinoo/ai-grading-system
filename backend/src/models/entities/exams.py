from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Index,
    CheckConstraint,
    BigInteger,
    ForeignKey,
    text,
    String,
    DateTime,
    Text,
    Boolean
)   
    
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.settings.base import Base

class Exams(Base):
    """
    Entidade que representa uma Prova no sistema.
    """
    
    __tablename__ = "exams"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT','ACTIVE','GRADING','GRADED','FINALIZED','PUBLISHED','ARCHIVED')",
            "chk_exams_status",
        ), 
        CheckConstraint(
            "starts_at IS NULL OR ends_at IS NULL OR starts_at < ends_at",
            "chk_exams_window",
        ),
        
        Index("idx_exams_active", "active"),
        Index("idx_exams_created_by", "created_by"),
        Index("idx_exams_class_uuid", "class_uuid"),
        Index("idx_exams_status", "status"),
        
        {"schema": "public"},
    )
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("gen_random_uuid()"),
        unique=True,
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.uuid", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    
    class_uuid: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.classes.uuid", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'DRAFT'"))
    
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
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
        return f"<Exams(id={self.id}, uuid={self.uuid}, title={self.title}, status={self.status})>"
