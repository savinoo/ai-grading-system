from __future__ import annotations

from uuid import uuid4
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging_config import set_request_id
from src.core.logging_config import _request_id_ctx  # noqa: PLC0415


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    - Lê X-Request-Id se vier do cliente/gateway
    - Senão gera um UUID4
    - Seta no ContextVar (para logs JSON)
    - Devolve X-Request-Id na resposta
    """

    async def dispatch(self, request: Request, call_next: Callable):
        rid = request.headers.get("X-Request-Id") or str(uuid4())

        token = None
        try:
            token = set_request_id(rid)
        except TypeError:
            set_request_id(rid)

        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = rid

        if token is not None:
            try:
                _request_id_ctx.reset(token)
            except Exception:
                pass

        return response
