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
from sqlalchemy.orm import Mapped, mapped_column

from src.models.settings.base import Base

class ExamQuestionCriteriaOverride(Base):
    """
    Entidade que representa as Sobrescritas de Critérios de Avaliação para uma Questão em uma Prova.
    """
    
    __tablename__ = "exam_question_criteria_override"
    __table_args__ = (
        CheckConstraint(
            "weight_override IS NULL OR weight_override > 0",
            "chk_eqco_weight",
        ),
        
        Index("idx_eqco_question_uuid", "question_uuid"),
        
        {"schema": "public"},
    )
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("gen_random_uuid()"),
        unique=True,
    )
        
    question_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.exam_questions.uuid", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    
    criteria_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.grading_criteria.uuid", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    
    weight_override: Mapped[float] = mapped_column(Numeric(8, 4), nullable=True)
    max_points_override: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    
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
    
    def __repr__(self) -> str:
        return f"<ExamQuestionCriteriaOverride(uuid={self.uuid}, question_uuid={self.question_uuid}, criteria_uuid={self.criteria_uuid})>"
