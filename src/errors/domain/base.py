from __future__ import annotations
from typing import Any, Optional
from src.errors.domain.codes import ErrorCode

class DomainError(Exception):
    """Base para erros de domínio/serviços (sem acoplamento a HTTP)."""
    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: dict[str, Any] | None = None,
        cause: Optional[BaseException] = None,
        retryable: bool = False,
        severity: str = "error",
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
        self.retryable = retryable
        self.severity = severity
        if cause is not None:
            self.__cause__ = cause

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

    def to_problem_details(self, status: int, type_: str = "about:blank") -> dict[str, Any]:
        return {
            "type": type_,
            "title": self.code.replace("_", " ").title(),
            "status": status,
            "detail": self.message,
            "code": self.code,
            "retryable": self.retryable,
            **({"context": self.context} if self.context else {}),
        }
