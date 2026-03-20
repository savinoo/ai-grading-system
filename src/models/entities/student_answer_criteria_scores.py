from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.settings.base import Base


class StudentAnswerCriteriaScore(Base):
    """
    Pontuação atribuída a uma resposta de aluno em um critério específico.
    (Resposta + Critério)
    """

    __tablename__ = "student_answer_criteria_scores"
    __table_args__ = (
        CheckConstraint("raw_score >= 0", name="chk_sacs_raw_score"),

        Index("uq_sacs_uuid", "uuid", unique=True),
        Index(
            "uq_sacs_answer_criteria",
            "student_answer_uuid",
            "criteria_uuid",
            unique=True,
        ),
        Index("idx_sacs_answer", "student_answer_uuid"),
        Index("idx_sacs_criteria", "criteria_uuid"),

        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("gen_random_uuid()"),
        unique=True,
    )

    student_answer_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.student_answers.uuid",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    criteria_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "public.grading_criteria.uuid",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    raw_score: Mapped[float] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        server_default=text("0"),
    )

    weighted_score: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )

    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    def __repr__(self) -> str:
        return (
            f"<StudentAnswerCriteriaScore("
            f"answer={self.student_answer_uuid}, criteria={self.criteria_uuid}, "
            f"raw_score={self.raw_score}, weighted_score={self.weighted_score})>"
        )
