from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Index,
    CheckConstraint,
    ForeignKey,
    BigInteger,
    Numeric,
    Boolean,
    DateTime,
    text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.settings.base import Base

class ExamCriteria(Base):
    """
    Entidade que representa os Critérios de Avaliação de uma Prova.
    """
    
    __tablename__ = "exam_criteria"
    __table_args__ = (
        CheckConstraint(
            "weight > 0",
            "chk_exam_criteria_weight",
        ),
        
        Index("idx_exam_criteria_exam_uuid", "exam_uuid"),
        
        {"schema": "public"},
    )
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("gen_random_uuid()"),
        unique=True,
    )
    
    exam_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.exams.uuid", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    
    criteria_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.grading_criteria.uuid", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    
    weight: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False, server_default=text("1.0"))
    max_points: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    
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
    
    # Relacionamentos
    grading_criteria: Mapped["GradingCriteria"] = relationship(
        "GradingCriteria",
        lazy="joined"  # Carrega automaticamente o relacionamento
    )
    
    def __repr__(self) -> str:
        return f"<ExamCriteria(uuid={self.uuid}, exam_uuid={self.exam_uuid}, criteria_uuid={self.criteria_uuid}, weight={self.weight})>"
