from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.settings.base import Base


class ExamQuestion(Base):
    """
    Entidade que representa uma questão de uma prova.
    """

    __tablename__ = "exam_questions"
    __table_args__ = (
        CheckConstraint("points >= 0", name="chk_exam_questions_points"),
        CheckConstraint("question_order >= 1", name="chk_exam_questions_order"),

        Index("uq_exam_questions_uuid", "uuid", unique=True),
        Index(
            "uq_exam_questions_exam_order",
            "exam_uuid",
            "question_order",
            unique=True,
        ),
        Index("idx_exam_questions_exam_uuid", "exam_uuid"),
        Index("idx_exam_questions_active", "active"),

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
        ForeignKey(
            "public.exams.uuid",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    question_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    points: Mapped[float] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        server_default=text("1.00"),
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    is_graded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
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
        return (
            f"<ExamQuestion(id={self.id}, exam_uuid={self.exam_uuid}, "
            f"order={self.question_order}, points={self.points}, active={self.active})>"
        )
