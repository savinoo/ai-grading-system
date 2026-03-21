from __future__ import annotations

from src.errors.domain.base import DomainError
from src.errors.domain.codes import ErrorCode

class AlreadyExistingError(DomainError):
    
    """Erro de item ja existente."""
    
    def __init__(self, message: str, *, context: dict | None = None, cause: Exception | None = None):
        super().__init__(
            message=message,
            code=ErrorCode.CONFLICT,
            context=context or {},
            cause=cause,
            retryable=True,
            severity="error",
        )
