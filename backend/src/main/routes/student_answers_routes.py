from fastapi import APIRouter, Depends, HTTPException, Request, Body, Path
from fastapi.responses import JSONResponse

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

# Request Models
from src.domain.requests.student_answers.student_answer_create_request import StudentAnswerCreateRequest
from src.domain.requests.student_answers.student_answer_update_request import StudentAnswerUpdateRequest

# Response Models
from src.domain.responses.student_answers.student_answer_response import StudentAnswerResponse

from src.core.logging_config import get_logger

from src.main.composer.student_answers_composer import (
    make_create_student_answer_controller,
    make_update_student_answer_controller,
    make_delete_student_answer_controller
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.auth_jwt import auth_jwt_verify

logger = get_logger(__name__)

router = APIRouter(
    prefix="/student-answers",
    tags=["Student Answers"],
)

@router.post(
    "",
    response_model=StudentAnswerResponse,
    status_code=201,
    summary="Criar resposta de aluno",
    description="Endpoint para criar uma resposta de aluno para uma questão de prova. A prova deve estar em status DRAFT. Requer autenticação de professor."
)
def create_student_answer(
    request: Request,
    body: StudentAnswerCreateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para criar resposta de aluno.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (StudentAnswerCreateRequest): Corpo da requisição contendo dados da resposta
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com os dados da resposta criada
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

    controller = make_create_student_answer_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao criar resposta de aluno: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao criar resposta de aluno")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.put(
    "/{answer_uuid}",
    response_model=StudentAnswerResponse,
    status_code=200,
    summary="Atualizar resposta de aluno",
    description="Endpoint para atualizar uma resposta de aluno. A prova deve estar em status DRAFT e a resposta não pode estar avaliada. Requer autenticação de professor."
)
def update_student_answer(
    request: Request,
    answer_uuid: str = Path(..., description="UUID da resposta a ser atualizada"),
    body: StudentAnswerUpdateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para atualizar resposta de aluno.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        answer_uuid (str): UUID da resposta a ser atualizada
        body (StudentAnswerUpdateRequest): Corpo da requisição contendo dados da atualização
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com os dados da resposta atualizada
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

    # Merge answer_uuid into body
    body_dict = body.model_dump()
    body_dict["answer_uuid"] = answer_uuid

    http_request = HttpRequest(
        body=body_dict,
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_update_student_answer_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao atualizar resposta de aluno: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao atualizar resposta de aluno")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.delete(
    "/{answer_uuid}",
    status_code=204,
    summary="Remover resposta de aluno",
    description="Endpoint para remover uma resposta de aluno. A prova deve estar em status DRAFT e a resposta não pode estar avaliada. Requer autenticação de professor."
)
def delete_student_answer(
    request: Request,
    answer_uuid: str = Path(..., description="UUID da resposta a ser removida"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para remover resposta de aluno.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        answer_uuid (str): UUID da resposta a ser removida
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
        body={"answer_uuid": answer_uuid},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_delete_student_answer_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=None
        )
    except HTTPException as e:
        logger.error("Erro ao remover resposta de aluno: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao remover resposta de aluno")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
