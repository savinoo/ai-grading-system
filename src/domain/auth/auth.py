from __future__ import annotations

from datetime import datetime 
from typing import Optional, Literal, List
from pydantic import BaseModel

class CreateToken (BaseModel):
    """
    Dados necessários para criação de um token JWT.
    """
    sub: str
    application_name: str
    scope: List[str] = []
    token_type: Literal["ACCESS", "REFRESH"] = "ACCESS"
    non_expiring: bool = True
    expires_in_seconds: Optional[int] = None
    not_before_seconds: Optional[int] = None
    
class TokenResponse (BaseModel):
    """
    Resposta ao criar um token JWT.
    """
    token: str
    jti: str
    expires_at: Optional[datetime] = None
    non_expiring: bool

    
class RevokeByJti (BaseModel):
    """
    Dados para revogação de um token JWT pelo jti.
    """
    jti: str
    reason: Optional[str] = None

class RevokeBySub (BaseModel):
    """
    Dados para revogação de tokens JWT pelo sub.
    """
    sub: str
    reason: Optional[str] = None
