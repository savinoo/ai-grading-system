from __future__ import annotations

from fastapi import APIRouter, Depends, Request, HTTPException, Response, Body
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

from src.core.logging_config import get_logger
from src.core.settings import settings

from src.main.composer.auth_composer import (
    make_revoke_by_jti_controller,
    make_refresh_token_controller,
    make_get_me_controller,
    make_user_login_controller
)

from src.domain.auth.auth import RevokeByJti
from src.domain.requests.auth.login import UserLoginRequest

from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.auth_jwt import auth_jwt_verify


logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/revoke/jti", status_code=204, include_in_schema=False)
def revoke_by_jti(
    request: Request,
    body: RevokeByJti,
    db: Session = Depends(get_db),
    meta: CallerMeta = Depends(get_caller_meta),
) -> Response:
    """
    Revoke a token by its JTI.
    """
    try:
        headers = request.headers
        try:
            # Extrai token do header Authorization
            auth_header = headers.get("Authorization") or headers.get("authorization") or ""
            if not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
            token = auth_header.split(" ", 1)[1].strip()
            
            token_infos = auth_jwt_verify(token, db, scope="admin")  # Apenas admin pode revogar tokens
            logger.debug("Token válido: %s", token_infos)
        except HTTPException as e:
            logger.error("Authentication error: %s", str(e), exc_info=True)
            raise HTTPException(status_code=e.status_code, detail=e.detail) from e
        
        http_request = HttpRequest(body=body, caller=meta, db=db, headers=headers, token_infos=token_infos)
        controller = make_revoke_by_jti_controller()
        response: HttpResponse = controller.handle(http_request)
        return Response(status_code=response.status_code)
    
    except HTTPException as http_err:
        logger.error("HTTP error: %s", str(http_err), exc_info=True)
        raise http_err
    
    except Exception as e:
        logger.error("Error processing request: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.") from e

@router.post("/refresh", status_code=200)
def refresh_token(
    request: Request,
    db: Session = Depends(get_db),
    meta: CallerMeta = Depends(get_caller_meta),
) -> JSONResponse:
    """
    Refresh an access token using a valid refresh token stored in HttpOnly cookie.
    """
    try:
        refresh_token_value = request.cookies.get("refresh_token")
        if not refresh_token_value:
            raise HTTPException(status_code=401, detail="Missing refresh token cookie.")

        try:
            token_infos = auth_jwt_verify(
                token=refresh_token_value,
                db=db,
                scope=None
            )
            logger.debug("Refresh token válido: %s", token_infos)
        except HTTPException as e:
            logger.error("Authentication error: %s", str(e.detail), exc_info=True)
            raise HTTPException(status_code=e.status_code, detail=e.detail) from e

        if token_infos.get("typ") != "REFRESH":
            raise HTTPException(status_code=401, detail="Invalid token type for refresh.")

        http_request = HttpRequest(
            body=None,
            caller=meta,
            db=db,
            headers=request.headers,
            token_infos=token_infos
        )

        controller = make_refresh_token_controller()
        response: HttpResponse = controller.handle(http_request)

        return JSONResponse(
            status_code=response.status_code,
            content=jsonable_encoder(response.body)
        )

    except HTTPException as http_err:
        logger.error("HTTP error: %s", str(http_err.detail), exc_info=True)
        raise http_err

    except Exception as e:
        logger.error("Error processing refresh token: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.") from e

@router.get(
    "/me",
    summary="Obter informações do usuário logado",
    description="Esse endpoint retorna as informações do usuário atualmente logado.",
    status_code=200
)
def get_me(
    request: Request,
    db=Depends(get_db),
    meta: CallerMeta = Depends(get_caller_meta)
) -> JSONResponse:
    """
    Endpoint para obter as informações do usuário atualmente logado.
    """
    try:
        try:
            auth_header = request.headers.get("Authorization") or ""
            token = auth_header.split(" ", 1)[1].strip() if auth_header.startswith("Bearer ") else ""
            token_infos = auth_jwt_verify(token, db, scope=None)
            logger.debug("Token Valido")
        except HTTPException as e:
            logger.error("Erro de autenticação: %s",  str(e.detail))
            raise HTTPException(status_code=e.status_code, detail=e.detail) from e
        except Exception as e:
            logger.error("Erro inesperado de autenticação: %s", str(e))
            raise HTTPException(status_code=500, detail="Erro interno de autenticação") from e
        
        http_request = HttpRequest(
            caller=meta,
            headers=request.headers,
            db=db,
            token_infos=token_infos        
        )
        
        controller = make_get_me_controller()
        http_response: HttpResponse = controller.handle(http_request)

        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body
        )
        
    except HTTPException as e:
        logger.error("Erro HTTP: %s", str(e.detail))
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except Exception as e:
        logger.error("Erro inesperado: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.post(
    "/login",
    summary="Login de Usuário",
    description="Autentica um usuário e retorna um token JWT."
)
def user_login(
    request: Request,
    db = Depends(get_db),
    meta: CallerMeta = Depends(get_caller_meta),
    body: UserLoginRequest = Body(
        ...,
        description="Dados de login do usuário",
    )
) -> JSONResponse:
    """
    Endpoint para autenticar um usuário e retornar um token JWT.
    """
    
    try:
        http_request = HttpRequest(
            body=body,
            db=db,
            headers=request.headers,
            caller=meta
        )
        controller = make_user_login_controller()
        http_response: HttpResponse = controller.handle(http_request)
        
        body = http_response.body or {}
        refresh_token_value = body.pop("refresh_token", None)
        
        response = JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body
        )
        
        if refresh_token_value:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token_value, 
                httponly=True,
                secure=True,
                samesite="none",
                path="/auth",
                max_age=settings.JWT_REFRESH_TOKEN_TTL,
            )
        
        return response
    except HTTPException as http_exc:
        logger.error("HTTPException during user login: %s", repr(http_exc))
        raise http_exc
    except Exception as exc:
        logger.error("Unexpected error during user login: %s", repr(exc))
        raise HTTPException(status_code=500, detail={"error": "Internal server error"}) from exc



@router.post(
    "/logout",
    summary="Logout de Usuário",
    description="Revoga o token de refresh e realiza o logout do usuário."
)
def logout(
    request: Request,
    db=Depends(get_db),
    meta: CallerMeta = Depends(get_caller_meta)
) -> Response:
    """
    Endpoint para realizar logout do usuário revogando o refresh token.
    """
    try:
        refresh_token_value = request.cookies.get("refresh_token")
        
        if not refresh_token_value:
            logger.error("Token de refresh ausente no cookie")
            raise HTTPException(status_code=401, detail="Token de refresh ausente.")
        
        try:
            token_infos = auth_jwt_verify(refresh_token_value, db, scope=None)
            jti = token_infos.get("jti")
            
            if not jti:
                logger.error("JTI ausente no token")
                raise HTTPException(status_code=401, detail="Token inválido.")
                
        except HTTPException as e:
            logger.error("Erro de autenticação: %s", str(e.detail))
            raise HTTPException(status_code=e.status_code, detail=e.detail) from e
        except Exception as e:
            logger.error("Erro inesperado de autenticação: %s", str(e))
            raise HTTPException(status_code=401, detail="Token inválido.") from e
        
        
        http_request = HttpRequest(
            body=RevokeByJti(jti=jti, reason="logout"),
            db=db,
            headers=request.headers,
            caller=meta,
            token_infos=token_infos
        )
        
        controller = make_revoke_by_jti_controller()
        http_response: HttpResponse = controller.handle(http_request)
        
        response = Response(status_code=http_response.status_code)
        response.delete_cookie(
            key="refresh_token",
            path="/auth",
            samesite="none"
        )
        
        return response
        
    except HTTPException as e:
        logger.error("Erro HTTP durante logout: %s", str(e.detail))
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except Exception as e:
        logger.error("Erro inesperado durante logout: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
