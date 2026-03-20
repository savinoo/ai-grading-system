from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from fastapi.responses import JSONResponse

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

# Request Models
from src.domain.requests.classes.class_create_request import ClassCreateRequest
from src.domain.requests.classes.add_students_to_class_request import AddStudentsToClassRequest

# Response Models
from src.domain.responses.classes.class_create_response import ClassCreateResponse
from src.domain.responses.classes.class_with_students_response import ClassWithStudentsResponse

from src.core.logging_config import get_logger

from src.main.composer.classes_composer import (
    make_create_class_controller,
    make_add_students_to_class_controller,
    make_get_class_with_students_controller,
    make_get_classes_service_controller,
    make_remove_student_from_class_controller,
    make_deactivate_class_controller
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db

from src.main.dependencies.auth_jwt import auth_jwt_verify

logger = get_logger(__name__)

router = APIRouter(
    prefix="/classes",
    tags=["Classes"],
)

@router.post(
    "",
    response_model=ClassCreateResponse,
    status_code=201,
    summary="Criar uma nova turma",
    description="Endpoint para professores criarem novas turmas. Requer autenticação."
)
def create_class(
    request: Request,
    body: ClassCreateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para criar uma nova turma.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (ClassCreateRequest): Corpo da requisição contendo os dados da turma
        caller (CallerMeta): Metadados do chamador (injetado via dependência)
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com os dados da turma criada
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
    
    controller = make_create_class_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao criar turma: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao criar turma")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.post(
    "/{class_uuid}/students",
    status_code=200,
    summary="Adicionar alunos a uma turma",
    description="Endpoint para adicionar alunos a uma turma existente. Cria novos alunos se não existirem (validando por email)."
)
def add_students_to_class(
    request: Request,
    class_uuid: str,
    body: AddStudentsToClassRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para adicionar alunos a uma turma.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        class_uuid (str): UUID da turma
        body (AddStudentsToClassRequest): Lista de alunos a adicionar
        caller (CallerMeta): Metadados do chamador (injetado via dependência)
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com informações sobre os alunos adicionados
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
        param={"class_uuid": class_uuid},
        token_infos=token_infos
    )
    
    controller = make_add_students_to_class_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao adicionar alunos à turma: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao adicionar alunos")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.get(
    "/class/{class_uuid}",
    response_model=ClassWithStudentsResponse,
    status_code=200,
    summary="Buscar turma com alunos",
    description="Endpoint para buscar uma turma e listar todos os seus alunos matriculados."
)
def get_class_with_students(
    request: Request,
    class_uuid: str,
    skip: int = Query(0, ge=0, description="Número de alunos a pular na paginação"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de alunos a retornar"),
    active_only: bool = Query(True, description="Se deve retornar apenas matrículas ativas"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para buscar uma turma com seus alunos.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        class_uuid (str): UUID da turma
        skip (int): Número de alunos a pular (paginação)
        limit (int): Número máximo de alunos a retornar
        active_only (bool): Se deve retornar apenas matrículas ativas
        caller (CallerMeta): Metadados do chamador (injetado via dependência)
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com os dados da turma e seus alunos
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
        param={"class_uuid": class_uuid, "skip": skip, "limit": limit, "active_only": active_only},
        token_infos=token_infos
    )
    
    controller = make_get_class_with_students_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao buscar turma: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao buscar turma")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e


@router.get(
    "/{teacher_uuid}",
    status_code=200,
    summary="Buscar turmas",
    description="Endpoint para buscar turmas com filtros opcionais."
)
def get_classes(
    request: Request,
    teacher_uuid: str,
    skip: int = Query(0, ge=0, description="Número de alunos a pular na paginação"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de alunos a retornar"),
    active_only: bool = Query(True, description="Se deve retornar apenas matrículas ativas"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db)
):
    """
    Endpoint para buscar turmas com filtros opcionais.
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
        param={
            "teacher_uuid": teacher_uuid,
            "skip": skip,
            "limit": limit,
            "active_only": active_only
        },
        token_infos=token_infos
    )
    
    controller = make_get_classes_service_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao buscar turmas: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao buscar turmas")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.delete(
    "/{class_uuid}/students/{student_uuid}",
    status_code=200,
    summary="Remover aluno de uma turma",
    description="Endpoint para remover um aluno de uma turma específica."
)
def remove_student_from_class(
    request: Request,
    class_uuid: str,
    student_uuid: str,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para remover um aluno de uma turma.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        class_uuid (str): UUID da turma
        student_uuid (str): UUID do aluno
        caller (CallerMeta): Metadados do chamador (injetado via dependência)
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com informações sobre a remoção
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
        param={"class_uuid": class_uuid, "student_uuid": student_uuid},
        token_infos=token_infos
    )
    
    controller = make_remove_student_from_class_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao remover aluno da turma: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao remover aluno")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.patch(
    "/{class_uuid}/deactivate",
    response_model=ClassCreateResponse,
    status_code=200,
    summary="Desativar uma turma",
    description="Endpoint para desativar uma turma. A turma não será deletada, apenas marcada como inativa."
)
def deactivate_class(
    request: Request,
    class_uuid: str,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para desativar uma turma.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        class_uuid (str): UUID da turma
        caller (CallerMeta): Metadados do chamador (injetado via dependência)
        db (Session): Sessão do banco de dados (injetado via dependência)
        
    Returns:
        JSONResponse: Resposta HTTP com os dados da turma desativada
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
        param={"class_uuid": class_uuid},
        token_infos=token_infos
    )
    
    controller = make_deactivate_class_controller()
    
    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao desativar turma: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao desativar turma")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
