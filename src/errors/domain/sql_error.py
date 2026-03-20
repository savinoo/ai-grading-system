from __future__ import annotations

from src.errors.domain.base import DomainError
from src.errors.domain.codes import ErrorCode

class SqlError(DomainError):
    """Erro de no SLQ."""
    
    def __init__(self, message: str, *, context: dict | None = None, cause: Exception | None = None):
        super().__init__(
            message=message,
            code=ErrorCode.DATA_BASE,
            context=context or {},
            cause=cause,
            retryable=False,
            severity="error",
        )
