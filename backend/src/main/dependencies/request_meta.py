from typing import Optional
from fastapi import Request, Header
from src.domain.http.caller_domains import CallerMeta

async def get_caller_meta(
    request: Request,
    x_app_name: Optional[str] = Header(default=None, alias="X-App-Name"),
) -> CallerMeta:
    ua = request.headers.get("user-agent", "")[:255]
    
    ip = ""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        ip = xff.split(",")[0].strip()
    if not ip:
        ip = request.headers.get("x-real-ip", "") or (request.client.host if request.client else "")

    caller_app = (x_app_name or "api")[:80]
    caller_user = (ua or "unknown")[:255]

    return CallerMeta(ip=ip, user_agent=ua, caller_app=caller_app, caller_user=caller_user)
