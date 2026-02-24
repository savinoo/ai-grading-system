from __future__ import annotations

from fastapi import Request

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware:
    """
    Middleware ASGI puro para logar requisições HTTP recebidas e suas respostas.

    Implementado como middleware ASGI puro (não herda BaseHTTPMiddleware) para
    evitar o bug do Starlette em que BaseHTTPMiddleware + BackgroundTasks causa
    "Response content longer than Content-Length" ao bufferizar StreamingResponses.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        method = request.method
        path = request.url.path

        if method not in ("OPTIONS", "HEAD"):
            logger.info("Recebendo requisição: %s %s", method, path)

        status_code: int | None = None

        async def send_with_logging(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                if method not in ("OPTIONS", "HEAD"):
                    logger.info(
                        "Respondendo requisição: %s %s -> Status %s",
                        method,
                        path,
                        status_code,
                    )
            await send(message)

        try:
            await self.app(scope, receive, send_with_logging)
        except Exception as e:
            logger.error(
                "Erro não tratado durante a requisição: %s",
                str(e),
                exc_info=True,
            )
            raise
