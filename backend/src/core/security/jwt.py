from __future__ import annotations
from typing import Dict
from datetime import datetime, timedelta
from uuid import uuid4
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError #pylint: disable=unused-import

from src.core.settings import settings
from src.core.logging_config import get_logger

class JWTHandler:
    """Cria e valida JWTs (tanto API Key quanto Access Token)."""
    
    def __init__(self) -> None:
        self.__log = get_logger(__name__)
    

    def encode_jwt_token(self, payload: Dict) -> str:
        """Cria token JWT."""
        self.__log.debug("Codificando token JWT")
        token = jwt.encode(payload=payload, key=settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token

    def decode_jwt_token(self, token: str) -> Dict:
        """
        Valida assinatura e, se 'exp' existir, valida expiração.
        (Em PyJWT 2.x, 'exp' é verificado automaticamente quando presente.)
        """
        try:
            return jwt.decode(token, key=settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except ExpiredSignatureError:
            self.__log.warning("Token JWT expirado")
            raise
        except InvalidTokenError as e:
            self.__log.warning("Token JWT inválido: %s", str(e))
            raise
    
    def create_access_token(self, subject: str, scopes: list[str] = None) -> str:
        """Cria um access token JWT."""
        now = datetime.now()
        payload = {
            "sub": subject,
            "typ": "ACCESS",  # Padronizado como 'typ' (padrão JWT)
            "scope": scopes or [],  # Padronizado como 'scope' (singular, padrão OAuth)
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(seconds=settings.JWT_ACCESS_TOKEN_TTL),
        }
        return self.encode_jwt_token(payload)
    
    def create_refresh_token(self, subject: str, scopes: list[str] = None) -> str:
        """Cria um refresh token JWT."""
        now = datetime.now()
        payload = {
            "sub": subject,
            "typ": "REFRESH",  # Padronizado como 'typ' (padrão JWT)
            "scope": scopes or [],  # Padronizado como 'scope' (singular, padrão OAuth)
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(seconds=settings.JWT_REFRESH_TOKEN_TTL),
        }
        return self.encode_jwt_token(payload)
