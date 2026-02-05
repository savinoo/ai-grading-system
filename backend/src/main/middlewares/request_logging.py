from __future__ import annotations

from typing import Callable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logar requisições HTTP recebidas e suas respostas.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        if request.method not in ("OPTIONS", "HEAD"):
            logger.info(
                "Recebendo requisição: %s %s",
                request.method,
                request.url.path,
            )

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "Erro não tratado durante a requisição: %s",
                str(e),
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal Server Error"
            ) from e

        if request.method not in ("OPTIONS", "HEAD"):
            logger.info(
                "Respondendo requisição: %s %s -> Status %s",
                request.method,
                request.url.path,
                response.status_code,
            )

        return response
