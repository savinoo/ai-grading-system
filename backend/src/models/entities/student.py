from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, VARCHAR, BIGINT, BOOLEAN, TIMESTAMP

from src.models.settings.base import Base

class Student(Base):
    """ 
    Entidade que representa um Estudante no sistema.
    """
    
    __tablename__ = "students"
    __table_args__ = {"schema": "public"}
    
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    
    full_name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    
    email: Mapped[str] = mapped_column(VARCHAR(255), nullable=True, index=True)
    
    active: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=True)
    
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
        return f"<Student(id={self.id}, full_name={self.full_name}, email={self.email}, active={self.active})>"
