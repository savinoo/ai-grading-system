from fastapi import APIRouter, Depends, HTTPException, Request, Body, Path
from fastapi.responses import JSONResponse

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

# Request Models
from src.domain.requests.exam_question_criteria_override.criteria_override_create_request import ExamQuestionCriteriaOverrideCreateRequest
from src.domain.requests.exam_question_criteria_override.criteria_override_update_request import ExamQuestionCriteriaOverrideUpdateRequest

# Response Models
from src.domain.responses.exam_question_criteria_override.criteria_override_response import ExamQuestionCriteriaOverrideResponse

from src.core.logging_config import get_logger

from src.main.composer.exam_question_criteria_override_composer import (
    make_create_question_criteria_override_controller,
    make_reset_question_criteria_controller,
    make_update_question_criteria_override_controller,
    make_delete_question_criteria_override_controller
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.auth_jwt import auth_jwt_verify

logger = get_logger(__name__)

router = APIRouter(
    prefix="/question-criteria-override",
    tags=["Question Criteria Override"],
)

@router.post(
    "",
    response_model=ExamQuestionCriteriaOverrideResponse,
    status_code=201,
    summary="Criar critério customizado para questão",
    description="Endpoint para criar ou atualizar um critério de avaliação customizado para uma questão específica. A prova deve estar em status DRAFT. Requer autenticação de professor."
)
def create_question_criteria_override(
    request: Request,
    body: ExamQuestionCriteriaOverrideCreateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para criar critério customizado para questão.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (ExamQuestionCriteriaOverrideCreateRequest): Corpo da requisição contendo dados do critério customizado
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com os dados do critério customizado criado
    """
    headers = request.headers
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
        token = auth_header.split(" ", 1)[1].strip()

        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido: %s", token_infos)
    except HTTPException as e:
        logger.error("Authentication error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e

    http_request = HttpRequest(
        body=body,
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_create_question_criteria_override_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao criar critério customizado: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao criar critério customizado")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.put(
    "/{override_uuid}",
    response_model=ExamQuestionCriteriaOverrideResponse,
    status_code=200,
    summary="Atualizar sobrescrita de critério",
    description="Endpoint para atualizar uma sobrescrita específica (peso, pontos ou status). A prova deve estar em status DRAFT. Requer autenticação de professor."
)
def update_question_criteria_override(
    request: Request,
    override_uuid: str = Path(..., description="UUID da sobrescrita a ser atualizada"),
    body: ExamQuestionCriteriaOverrideUpdateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para atualizar sobrescrita de critério.
    """
    headers = request.headers
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
        token = auth_header.split(" ", 1)[1].strip()

        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido: %s", token_infos)
    except HTTPException as e:
        logger.error("Authentication error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e

    http_request = HttpRequest(
        body=body,
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos,
        path_params={"override_uuid": override_uuid}
    )

    controller = make_update_question_criteria_override_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao atualizar sobrescrita: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao atualizar sobrescrita")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.delete(
    "/{override_uuid}",
    status_code=204,
    summary="Remover sobrescrita de critério",
    description="Endpoint para remover uma sobrescrita específica. A prova deve estar em status DRAFT. Requer autenticação de professor."
)
def delete_question_criteria_override(
    request: Request,
    override_uuid: str = Path(..., description="UUID da sobrescrita a ser removida"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para remover sobrescrita de critério.
    """
    headers = request.headers
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
        token = auth_header.split(" ", 1)[1].strip()

        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido: %s", token_infos)
    except HTTPException as e:
        logger.error("Authentication error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e

    http_request = HttpRequest(
        body=None,
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos,
        path_params={"override_uuid": override_uuid}
    )

    controller = make_delete_question_criteria_override_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=None
        )
    except HTTPException as e:
        logger.error("Erro ao remover sobrescrita: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao remover sobrescrita")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.delete(
    "/question/{question_uuid}/reset",
    status_code=204,
    summary="Resetar critérios de uma questão",
    description="Endpoint para remover todas as customizações de critérios de uma questão, voltando aos critérios originais da prova. A prova deve estar em status DRAFT. Requer autenticação de professor."
)
def reset_question_criteria(
    request: Request,
    question_uuid: str = Path(..., description="UUID da questão cujos critérios serão resetados"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para resetar critérios de uma questão.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        question_uuid (str): UUID da questão cujos critérios serão resetados
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP sem conteúdo (204)
    """
    headers = request.headers
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
        token = auth_header.split(" ", 1)[1].strip()

        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido: %s", token_infos)
    except HTTPException as e:
        logger.error("Authentication error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e

    http_request = HttpRequest(
        body={"question_uuid": question_uuid},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_reset_question_criteria_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=None
        )
    except HTTPException as e:
        logger.error("Erro ao resetar critérios: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao resetar critérios")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
