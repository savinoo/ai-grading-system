from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query, Path
from fastapi.responses import JSONResponse

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

# Request Models
from src.domain.requests.exam_criteria.exam_criteria_create_request import ExamCriteriaCreateRequest
from src.domain.requests.exam_criteria.exam_criteria_update_request import ExamCriteriaUpdateRequest

# Response Models
from src.domain.responses.exam_criteria.exam_criteria_response import ExamCriteriaResponse

from src.core.logging_config import get_logger

from src.main.composer.exam_criteria_composer import (
    make_create_exam_criteria_controller,
    make_list_exam_criteria_controller,
    make_update_exam_criteria_controller,
    make_delete_exam_criteria_controller
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.auth_jwt import auth_jwt_verify

logger = get_logger(__name__)

router = APIRouter(
    prefix="/exam-criteria",
    tags=["Exam Criteria"],
)

@router.post(
    "",
    response_model=ExamCriteriaResponse,
    status_code=201,
    summary="Adicionar critério a uma prova",
    description="Endpoint para adicionar um critério de avaliação a uma prova em status DRAFT. Requer autenticação."
)
def create_exam_criteria(
    request: Request,
    body: ExamCriteriaCreateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para adicionar critério a uma prova.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (ExamCriteriaCreateRequest): Corpo da requisição contendo dados do critério
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com os dados do critério criado
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

    controller = make_create_exam_criteria_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao criar critério de prova: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao criar critério de prova")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.get(
    "/exam/{exam_uuid}",
    response_model=List[ExamCriteriaResponse],
    status_code=200,
    summary="Listar critérios de uma prova",
    description="Endpoint para listar todos os critérios de uma prova específica. Requer autenticação."
)
def list_exam_criteria(
    request: Request,
    exam_uuid: str = Path(..., description="UUID da prova"),
    active_only: bool = Query(True, description="Retornar apenas critérios ativos"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros a retornar"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para listar critérios de uma prova.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        exam_uuid (str): UUID da prova
        active_only (bool): Se deve retornar apenas critérios ativos
        skip (int): Número de registros a pular
        limit (int): Número máximo de registros a retornar
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com a lista de critérios
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
        param={"exam_uuid": exam_uuid, "active_only": active_only, "skip": skip, "limit": limit},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_list_exam_criteria_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body
        
        # Extrai apenas a lista de critérios do body
        if isinstance(response_body, dict) and "data" in response_body:
            criteria_list = response_body["data"]
            # Converte para dicionário se necessário
            if criteria_list and hasattr(criteria_list[0], 'model_dump'):
                response_data = [item.model_dump(mode='json') for item in criteria_list]
            else:
                response_data = criteria_list
        else:
            response_data = response_body
            
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_data
        )
    except HTTPException as e:
        logger.error("Erro ao listar critérios da prova: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao listar critérios da prova")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.patch(
    "/{exam_criteria_uuid}",
    response_model=ExamCriteriaResponse,
    status_code=200,
    summary="Atualizar critério de prova",
    description="Endpoint para atualizar peso e/ou pontos máximos de um critério. Apenas para provas em DRAFT. Requer autenticação."
)
def update_exam_criteria(
    request: Request,
    exam_criteria_uuid: str = Path(..., description="UUID do critério de prova"),
    body: ExamCriteriaUpdateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para atualizar critério de prova.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        exam_criteria_uuid (str): UUID do critério de prova
        body (ExamCriteriaUpdateRequest): Corpo da requisição com dados a atualizar
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com os dados atualizados
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
        param={"exam_criteria_uuid": exam_criteria_uuid},
        body=body,
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_update_exam_criteria_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao atualizar critério de prova: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao atualizar critério de prova")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.delete(
    "/{exam_criteria_uuid}",
    status_code=204,
    summary="Remover critério de prova",
    description="Endpoint para remover um critério de uma prova. Apenas para provas em DRAFT. Requer autenticação."
)
def delete_exam_criteria(
    request: Request,
    exam_criteria_uuid: str = Path(..., description="UUID do critério de prova"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para remover critério de prova.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        exam_criteria_uuid (str): UUID do critério de prova
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        Response: Resposta HTTP 204 (No Content)
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
        param={"exam_criteria_uuid": exam_criteria_uuid},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_delete_exam_criteria_controller()

    try:
        controller.handle(http_request)
        return JSONResponse(status_code=204, content=None)
    except HTTPException as e:
        logger.error("Erro ao remover critério de prova: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao remover critério de prova")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
