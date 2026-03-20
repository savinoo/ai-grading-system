from __future__ import annotations

from src.errors.domain.base import DomainError
from src.errors.domain.codes import ErrorCode

class NotFoundError(DomainError):
    """Erro de recurso não encontrado (ex.: usuário, item, etc)."""
    
    def __init__(self, message: str, *, context: dict | None = None, cause: Exception | None = None):
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            context=context or {},
            cause=cause,
            retryable=False,
            severity="warning",
        )
