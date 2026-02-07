from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from fastapi.responses import JSONResponse

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

# Request Models
from src.domain.requests.exams.exam_create_request import ExamCreateRequest
from src.domain.requests.exams.exam_update_request import ExamUpdateRequest

# Response Models
from src.domain.responses.exams.exam_create_response import ExamCreateResponse
from src.domain.responses.exams.exam_response import ExamResponse
from src.domain.responses.exams.exams_list_response import ExamsListResponse

from src.core.logging_config import get_logger

from src.main.composer.exams_composer import (
    make_create_exam_controller,
    make_get_exams_by_teacher_controller,
    make_get_exam_by_uuid_controller,
    make_update_exam_controller
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db

from src.main.dependencies.auth_jwt import auth_jwt_verify

logger = get_logger(__name__)

router = APIRouter(
    prefix="/exams",
    tags=["Exams"],
)

@router.post(
    "",
    response_model=ExamCreateResponse,
    status_code=201,
    summary="Criar uma nova prova",
    description="Endpoint para professores criarem novas provas. Requer autenticação."
)
def create_exam(
    request: Request,
    body: ExamCreateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para criar uma nova prova.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (ExamCreateRequest): Corpo da requisição contendo os dados da prova
        caller (CallerMeta): Metadados do chamador (injetado via dependência)
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com os dados da prova criada
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

    controller = make_create_exam_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao criar prova: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao criar prova")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.get(
    "/teacher/{teacher_uuid}",
    response_model=ExamsListResponse,
    status_code=200,
    summary="Listar provas de um professor",
    description="Endpoint para listar todas as provas de um professor. Requer autenticação."
)
def get_exams_by_teacher(
    request: Request,
    teacher_uuid: str,
    active_only: bool = Query(True, description="Retornar apenas provas ativas"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros a retornar"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para listar provas de um professor.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        teacher_uuid (str): UUID do professor
        active_only (bool): Se deve retornar apenas provas ativas
        skip (int): Número de registros a pular
        limit (int): Número máximo de registros a retornar
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com a lista de provas
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
        param={"teacher_uuid": teacher_uuid, "active_only": active_only, "skip": skip, "limit": limit},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_get_exams_by_teacher_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao buscar provas: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao buscar provas")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.get(
    "/{exam_uuid}",
    response_model=ExamResponse,
    status_code=200,
    summary="Buscar prova por UUID",
    description="Endpoint para buscar os dados de uma prova específica. Requer autenticação."
)
def get_exam_by_uuid(
    request: Request,
    exam_uuid: str,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para buscar uma prova por UUID.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        exam_uuid (str): UUID da prova
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com os dados da prova
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
        param={"exam_uuid": exam_uuid},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_get_exam_by_uuid_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao buscar prova: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao buscar prova")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.patch(
    "/{exam_uuid}",
    response_model=ExamResponse,
    status_code=200,
    summary="Atualizar uma prova",
    description="Endpoint para atualizar os dados de uma prova (apenas em status DRAFT). Requer autenticação."
)
def update_exam(
    request: Request,
    exam_uuid: str,
    body: ExamUpdateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para atualizar uma prova.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        exam_uuid (str): UUID da prova
        body (ExamUpdateRequest): Corpo da requisição com os dados a serem atualizados
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com os dados da prova atualizada
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
        param={"exam_uuid": exam_uuid},
        body=body,
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_update_exam_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao atualizar prova: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao atualizar prova")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
