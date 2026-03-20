from __future__ import annotations

from typing import Any, Dict
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError, InvalidTokenError  # pylint: disable=import-error

from src.models.repositories.auth_refresh_token_repository import AuthRefreshTokenRepository

from src.core.security.jwt import JWTHandler
from src.core.settings import settings
from src.core.logging_config import get_logger

_jwt = JWTHandler()
_refresh_token_repo = AuthRefreshTokenRepository()
_logger = get_logger(__name__)

def _now () -> int:
    """Retorna o timestamp atual (segundos desde epoch)."""
    tz = ZoneInfo(settings.TIME_ZONE)
    return int(datetime.now(tz=tz).timestamp())


def _match_scope(required_scope: str, token_scope: str) -> bool:
    """Verifica se um scope do token atende ao scope requerido.
    
    Hierarquia de user_type:
    - admin: Acesso total (super_user/dev)
    - teacher: Acesso apenas a recursos de teacher
    - student: Acesso apenas a recursos de student (futuro)
    
    Regras:
    - admin tem acesso a tudo
    - teacher tem acesso apenas a recursos que exigem teacher
    - student tem acesso apenas a recursos que exigem student
    
    Args:
        required_scope: Scope requerido pela rota (user_type necessário)
        token_scope: Scope presente no token (user_type do usuário)
    
    Returns:
        True se o token_scope atende ao required_scope
    """
    # Match exato
    if required_scope == token_scope:
        return True
    
    # Admin tem acesso a tudo
    if token_scope == "admin":
        return True
    
    return False


def _validate_access_token_stateless(token: str, scope: str | None) -> Dict[str, Any]:
    """Valida token ACCESS de forma stateless (sem acessar banco de dados).
    Verifica apenas assinatura, expiração e claims básicas.
    """
    try:
        claims = _jwt.decode_jwt_token(token)
    except ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token expirado.") from e
    except (InvalidSignatureError, InvalidTokenError) as e:
        raise HTTPException(status_code=401, detail="Token inválido.") from e
    except Exception as e:  # pylint: disable=broad-except
        raise HTTPException(status_code=401, detail="Não foi possível validar o token.") from e

    _logger.debug("Claims do token ACCESS: %s", claims)
    
    # Validar expiração
    now = _now()
    exp = int(claims.get("exp") or 0)
    if now > exp > 0:
        _logger.error("Token expirado: exp=%d (agora é %d)", exp, now)
        raise HTTPException(status_code=401, detail="Token expirado.")
    _logger.debug("Token não expirado: expira em %d (agora é %d)", exp, now)
    
    nbf = int(claims.get("nbf") or 0)
    if nbf > 0 and nbf > now:
        _logger.error("Token não é válido ainda: nbf=%d (agora é %d)", nbf, now)
        raise HTTPException(status_code=401, detail="Token não é válido ainda.")
    _logger.debug("Token já é válido: nbf=%d (agora é %d)", nbf, now)
    
    sub = (claims.get("sub") or "").strip()
    if not sub:
        _logger.error("Token sem 'sub': %s", claims)
        raise HTTPException(status_code=401, detail="Usuário não autorizado.")
    _logger.debug("Token pertence ao usuário: %s", sub)
    
    if scope:
        token_scopes = claims.get("scope", [])
        if not isinstance(token_scopes, list):
            token_scopes = []
        
        has_permission = any(_match_scope(scope, ts) for ts in token_scopes)
        
        if not has_permission:
            _logger.error("Escopo '%s' requerido, mas não presente no token: %s", scope, token_scopes)
            raise HTTPException(status_code=403, detail="Acesso negado para o recurso solicitado.")
        _logger.debug("Escopos do token: %s (requerido: %s)", token_scopes, scope)
    
    return claims


def _validate_refresh_token_stateful(token: str, db: Session) -> Dict[str, Any]:
    """Valida token REFRESH de forma stateful (acessando banco de dados).
    Verifica assinatura, expiração, JTI e status no banco.
    """
    try:
        claims = _jwt.decode_jwt_token(token)
    except ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token expirado.") from e
    except (InvalidSignatureError, InvalidTokenError) as e:
        raise HTTPException(status_code=401, detail="Token inválido.") from e
    except Exception as e:  # pylint: disable=broad-except
        raise HTTPException(status_code=401, detail="Não foi possível validar o token.") from e

    _logger.debug("Claims do token REFRESH: %s", claims)
    
    # Validações básicas de tempo
    now = _now()
    exp = int(claims.get("exp") or 0)
    if now > exp > 0:
        _logger.error("Token expirado: exp=%d (agora é %d)", exp, now)
        raise HTTPException(status_code=401, detail="Token expirado.")
    _logger.debug("Token não expirado: expira em %d (agora é %d)", exp, now)
    
    nbf = int(claims.get("nbf") or 0)
    if nbf > 0 and nbf > now:
        _logger.error("Token não é válido ainda: nbf=%d (agora é %d)", nbf, now)
        raise HTTPException(status_code=401, detail="Token não é válido ainda.")
    _logger.debug("Token já é válido: nbf=%d (agora é %d)", nbf, now)
    
    # Validação de subject
    sub = (claims.get("sub") or "").strip()
    if not sub:
        _logger.error("Token sem 'sub': %s", claims)
        raise HTTPException(status_code=401, detail="Usuário não autorizado.")
    _logger.debug("Token pertence ao usuário: %s", sub)
    
    # Validação de JTI
    jti = (claims.get("jti") or "").strip()
    if not jti:
        _logger.error("Token sem 'jti': %s", claims)
        raise HTTPException(status_code=401, detail="Token inválido.")
    _logger.debug("JTI do token: %s", jti)
    
    # Busca token no banco
    token_record = _refresh_token_repo.get_active_by_jti(db, jti=jti)
    if not token_record:
        _logger.error("Token JTI não encontrado ou inativo na base: %s", jti)
        raise HTTPException(status_code=401, detail="Token revogado ou inválido.")
    
    _logger.debug("Token encontrado no banco: %s", token_record)
    
    # Usa a propriedade is_valid da entidade
    if not token_record.is_valid:
        _logger.error("Token não é válido: revoked=%s, expired=%s", 
                    token_record.is_revoked, token_record.is_expired)
        raise HTTPException(status_code=401, detail="Token revogado ou expirado.")
    
    _logger.debug("Token válido para o usuário: %s", sub)
    
    return claims

def auth_jwt_verify(token: str, db: Session, scope: str | None) -> Dict[str, Any]:
    """Valida token JWT recebido diretamente.
    Detecta automaticamente se é ACCESS (stateless) ou REFRESH (stateful).
    
    Args:
        token: Token JWT a ser validado
        db: Sessão do banco de dados (usada apenas para REFRESH tokens)
        scope: Escopo requerido (verificado apenas para ACCESS tokens)
    
    Returns:
        Claims do token decodificado
    """
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente.")

    try:
        claims = _jwt.decode_jwt_token(token)
        token_type = claims.get("typ", "ACCESS")
    except ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Token expirado.") from e
    except (InvalidSignatureError, InvalidTokenError) as e:
        raise HTTPException(status_code=401, detail="Token inválido.") from e
    except Exception as e:  # pylint: disable=broad-except
        raise HTTPException(status_code=401, detail="Não foi possível validar o token.") from e
    
    _logger.debug("Token type detectado: %s", token_type)
    
    if token_type == "ACCESS":
        return _validate_access_token_stateless(token, scope)
    if token_type == "REFRESH":
        return _validate_refresh_token_stateful(token, db)
    
    raise HTTPException(status_code=401, detail="Tipo de token inválido.")
