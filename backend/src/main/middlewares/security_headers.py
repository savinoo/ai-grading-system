from __future__ import annotations

from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


def build_docs_csp() -> str:
    return (
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'self'; "
        "form-action 'self'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "connect-src 'self' https:; "
        "upgrade-insecure-requests"
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """ 
    Classe de middleware para adicionar cabeçalhos de segurança às respostas HTTP.
    """
    
    def __init__(
        self,
        app,
        csp_policy: Optional[str] = None,
        csp_report_only: bool = True,
    ):
        super().__init__(app)
        self.csp_policy = csp_policy or build_docs_csp()
        self.csp_report_only = csp_report_only

    async def dispatch(self, request: Request, call_next: Callable):
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "0"

        # HSTS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        if request.url.path.startswith("/api/rest/v1/mc/conecta-baby"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"

        # -------- CSP só para HTML --------
        content_type = (response.headers.get("content-type") or "").lower()
        is_html = "text/html" in content_type

        if is_html:
            csp_header = (
                "Content-Security-Policy-Report-Only"
                if self.csp_report_only
                else "Content-Security-Policy"
            )
            response.headers[csp_header] = self.csp_policy

        return response
