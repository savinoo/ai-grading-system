from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import JSONResponse

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

# Request Models
from src.domain.requests.users.user_create_request import UserCreateRequest

# Response Models
from src.domain.responses.users.user_response import UserResponse

from src.core.logging_config import get_logger

from src.main.composer.users_composer import (
    make_create_user_controller,
    make_verify_email_controller,
    make_resend_verification_email_controller,
    make_generate_recovery_code_controller,
    make_validate_recovery_code_controller,
    make_reset_password_controller,
    make_change_password_controller,
)
from src.main.dependencies.auth_jwt import auth_jwt_verify

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db

logger = get_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register_user(
    request: Request,
    body: UserCreateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para registrar um novo usuário.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (UserCreateRequest): Corpo da requisição contendo os dados do usuário
        caller (CallerMeta): Metadados do chamador (injetado via dependência)
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com os dados do usuário criado
    """
    http_request = HttpRequest(
        body=body,
        db=db,
        caller=caller,
        headers=request.headers,
    )
    
    controller = make_create_user_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body
        )
    except HTTPException as e:
        logger.error("Erro ao registrar usuário: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao registrar usuário")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.put(
    "/verify-email/{uuid}",
    status_code=200
)
def verify_email(
    request: Request,
    uuid: str,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para verificar o email de um usuário e realizar login automático.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        uuid (str): UUID do usuário a ter o email verificado
        caller (CallerMeta): Metadados do chamador (injetado via dependência)
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com tokens de autenticação
    """
    http_request = HttpRequest(
        db=db,
        caller=caller,
        headers=request.headers,
        param={"uuid": uuid}
    )
    
    controller = make_verify_email_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        
        # Extrai o refresh_token do body
        refresh_token = http_response.body.get("refresh_token")
        
        # Remove refresh_token do body da resposta
        response_body = {k: v for k, v in http_response.body.items() if k != "refresh_token"}
        
        # Cria resposta JSON
        response = JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
        
        # Define cookie com refresh_token
        if refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="none",
                path="/auth",
                max_age=604800
            )
        
        return response
        
    except HTTPException as e:
        logger.error("Erro ao verificar email: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao verificar email")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.post(
    "/resend-verification",
    status_code=200
)
def resend_verification_email(
    request: Request,
    body: dict = Body(..., examples={"email": "usuario@exemplo.com"}),
    db=Depends(get_db),
):
    """
    Endpoint para reenviar email de verificação.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (dict): Corpo contendo o email do usuário
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com confirmação de envio
    """
    http_request = HttpRequest(
        db=db,
        headers=request.headers,
        body=body
    )
    
    controller = make_resend_verification_email_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body
        )
    except HTTPException as e:
        logger.error("Erro ao reenviar email: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao reenviar email")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.post(
    "/generate-recovery-code",
    status_code=200
)
def generate_recovery_code(
    request: Request,
    body: dict = Body(..., examples={"email": "usuario@exemplo.com"}),
    db=Depends(get_db),
):
    """
    Endpoint para gerar código de recuperação e enviar por email.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (dict): Corpo contendo o email do usuário
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com confirmação de envio
    """
    http_request = HttpRequest(
        db=db,
        headers=request.headers,
        body=body
    )
    
    controller = make_generate_recovery_code_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body
        )
    except HTTPException as e:
        logger.error("Erro ao gerar código de recuperação: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao gerar código de recuperação")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.post(
    "/validate-recovery-code",
    status_code=200
)
def validate_recovery_code(
    request: Request,
    body: dict = Body(..., examples={"email": "usuario@exemplo.com", "code": "123456"}),
    db=Depends(get_db),
):
    """
    Endpoint para validar código de recuperação.
    
    Valida se o código é válido sem limpar (incrementa tentativas se inválido).
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (dict): Corpo contendo email e code
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com confirmação de validação
    """
    http_request = HttpRequest(
        db=db,
        headers=request.headers,
        body=body
    )
    
    controller = make_validate_recovery_code_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body
        )
    except HTTPException as e:
        logger.error("Erro ao validar código de recuperação: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao validar código de recuperação")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.post(
    "/password/reset",
    status_code=200
)
def reset_password(
    request: Request,
    body: dict = Body(..., examples={"email": "usuario@exemplo.com", "code": "123456", "new_password": "novaSenha123"}),
    db=Depends(get_db),
):
    """
    Endpoint para resetar senha usando código de recuperação.
    
    Valida o código, atualiza a senha e limpa o código.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (dict): Corpo contendo email, code e new_password
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com confirmação de reset
    """
    http_request = HttpRequest(
        db=db,
        headers=request.headers,
        body=body
    )
    
    controller = make_reset_password_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body
        )
    except HTTPException as e:
        logger.error("Erro ao resetar senha: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao resetar senha")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.patch(
    "/me/password",
    status_code=200,
    summary="Trocar senha",
    description="Troca a senha do usuário autenticado verificando a senha atual."
)
def change_password(
    request: Request,
    body: dict = Body(..., examples={"current_password": "senhaAtual123", "new_password": "novaSenha456"}),
    db=Depends(get_db),
    meta: CallerMeta = Depends(get_caller_meta),
):
    """
    Endpoint para trocar a senha do usuário logado.

    Requer autenticação via Bearer token.
    Valida a senha atual antes de atualizar.
    """
    try:
        auth_header = request.headers.get("Authorization") or ""
        token = auth_header.split(" ", 1)[1].strip() if auth_header.startswith("Bearer ") else ""
        token_infos = auth_jwt_verify(token, db, scope=None)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token inválido") from e

    http_request = HttpRequest(
        db=db,
        headers=request.headers,
        body=body,
        caller=meta,
        token_infos=token_infos,
    )

    controller = make_change_password_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body
        )
    except HTTPException as e:
        logger.error("Erro ao trocar senha: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao trocar senha")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
