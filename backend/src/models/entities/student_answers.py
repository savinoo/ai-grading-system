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
    String,
    Boolean,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.settings.base import Base


class StudentAnswer(Base):
    """
    Entidade que representa a resposta de um aluno para uma questão de uma prova.
    """

    __tablename__ = "student_answers"
    __table_args__ = (
        CheckConstraint(
            "status IN ('SUBMITTED','GRADED','INVALID')",
            name="chk_student_answers_status",
        ),
        CheckConstraint(
            "score IS NULL OR score >= 0",
            name="chk_student_answers_score",
        ),

        Index("uq_student_answers_uuid", "uuid", unique=True),

        Index(
            "uq_student_answers_student_exam_question",
            "student_uuid",
            "exam_uuid",
            "question_uuid",
            unique=True,
        ),

        Index("idx_student_answers_student", "student_uuid"),
        Index("idx_student_answers_exam", "exam_uuid"),
        Index("idx_student_answers_question", "question_uuid"),
        Index("idx_student_answers_status", "status"),

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
        ForeignKey("public.exams.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )

    question_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.exam_questions.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )

    student_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.students.uuid", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )

    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'SUBMITTED'"),
    )

    score: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)

    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    graded_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.uuid", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
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
            f"<StudentAnswer(id={self.id}, student_uuid={self.student_uuid}, "
            f"exam_uuid={self.exam_uuid}, question_uuid={self.question_uuid}, "
            f"status={self.status}, score={self.score})>"
        )
