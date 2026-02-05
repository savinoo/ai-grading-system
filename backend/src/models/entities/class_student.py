from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, BIGINT, BOOLEAN, TIMESTAMP

from src.models.settings.base import Base

class ClassStudent(Base):
    """ 
    Entidade que representa o relacionamento entre Turma e Estudante.
    """
    
    __tablename__ = "class_students"
    __table_args__ = {"schema": "public"}
    
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    
    class_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.classes.uuid", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True
    )
    
    student_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.students.uuid", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True
    )
    
    enrolled_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.now
    )
    
    active: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=True)
    
    def __repr__(self) -> str:
        return f"<ClassStudent(id={self.id}, class_uuid={self.class_uuid}, student_uuid={self.student_uuid}, active={self.active})>"
