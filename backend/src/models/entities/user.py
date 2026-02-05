
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, VARCHAR, BOOLEAN, TIMESTAMP, TEXT, BIGINT

from src.models.settings.base import Base

class User(Base):
    
    """ Entidade que representa um Usuário no sistema. """
    
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    
    
    email: Mapped[str] = mapped_column(VARCHAR(255), unique=True, nullable=False, index=True)
    
    password_hash: Mapped[str] = mapped_column(TEXT, nullable=False)
    
    user_type: Mapped[str] = mapped_column(VARCHAR(50), nullable=False, default="user")
    first_name: Mapped[str] = mapped_column(TEXT, nullable=False)
    last_name: Mapped[str] = mapped_column(TEXT, nullable=False)
    
    active: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=True)
    
    email_verified: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=False)
    
    recovery_code_hash: Mapped[str] = mapped_column(TEXT, nullable=True)
    
    recovery_code_expires_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=True)
    
    recovery_code_attempts: Mapped[int] = mapped_column(BIGINT, nullable=False, default=0)
    
    last_login_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=True)
    
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)
    
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)
    
    deleted_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=True)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, user_type={self.user_type}, active={self.active})>"
