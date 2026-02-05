from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, VARCHAR, INTEGER, BOOLEAN, TIMESTAMP, TEXT

from src.models.settings.base import Base

class Classes(Base):
    """ 
    Entidade que representa uma Turma no sistema.
    """
    
    __tablename__ = "classes"
    __table_args__ = {"schema": "public"}
    
    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, index=True)
    
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    
    description: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    
    year: Mapped[Optional[int]] = mapped_column(INTEGER, nullable=True, index=True)
    
    semester: Mapped[Optional[int]] = mapped_column(INTEGER, nullable=True)
    
    teacher_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.uuid", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=False
    )
    
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.uuid", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True
    )
    
    active: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.now
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )
    
    def __repr__(self) -> str:
        return f"<Classes(id={self.id}, name={self.name}, year={self.year}, semester={self.semester}, active={self.active})>"
