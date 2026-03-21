from datetime import datetime
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    BigInteger,
    DateTime,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.models.settings.base import Base

class ClassStudent(Base):
    """ 
    Entidade que representa o relacionamento entre Turma e Estudante.
    """
    
    __tablename__ = "class_students"
    __table_args__ = (
        Index("idx_class_students_class", "class_uuid"),
        Index("idx_class_students_student", "student_uuid"),
        
        {"schema": "public"},
    )
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    
    class_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.classes.uuid", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    
    student_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.students.uuid", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True
    )
    
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    
    def __repr__(self) -> str:
        return f"<ClassStudent(id={self.id}, class_uuid={self.class_uuid}, student_uuid={self.student_uuid}, active={self.active})>"
