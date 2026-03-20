from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Index,
    CheckConstraint,
    BigInteger,
    ForeignKey,
    text,
    Text,
    Integer,
    DateTime,
    String,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.settings.base import Base

class Attachments(Base):
    """
    Entidade que representa um Anexo de prova.
    """
    
    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint(
            "vector_status IN ('DRAFT', 'SUCCESS', 'FAILED')",
            "chk_attachments_vector_status",
        ),
        Index("idx_attachments_exam_uuid", "exam_uuid"),
        Index("idx_attachments_sha256_hash", "sha256_hash"),
        Index("idx_attachments_vector_status", "vector_status"),
        
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
    
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(Text, nullable=False)
    
    vector_status: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        server_default=text("'DRAFT'")
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    
    def __repr__(self) -> str:
        return f"<Attachment uuid={self.uuid} original_filename={self.original_filename}>"
