from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Index,
    String,
    BigInteger,
    DateTime,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.models.settings.base import Base

class Student(Base):
    """ 
    Entidade que representa um Estudante no sistema.
    """
    
    __tablename__ = "students"
    __table_args__ = (
        Index("idx_students_active", "active"),
        Index("idx_students_email", "email"),
        
        {"schema": "public"},
    )
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    
    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        unique=True,
        server_default=text("gen_random_uuid()"), 
        nullable=False
    )
    
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, 
        server_default=text("TRUE")
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )
    
    def __repr__(self) -> str:
        return f"<Student(id={self.id}, full_name={self.full_name}, email={self.email}, active={self.active})>"
