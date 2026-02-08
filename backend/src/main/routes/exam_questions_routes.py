from fastapi import APIRouter, Depends, HTTPException, Request, Body, Path
from fastapi.responses import JSONResponse

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

# Request Models
from src.domain.requests.exam_questions.exam_question_create_request import ExamQuestionCreateRequest

# Response Models
from src.domain.responses.exam_questions.exam_question_response import ExamQuestionResponse

from src.core.logging_config import get_logger

from src.main.composer.exam_questions_composer import (
    make_create_exam_question_controller,
    make_delete_exam_question_controller,
    make_delete_all_question_answers_controller,
    make_list_exam_questions_controller
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.auth_jwt import auth_jwt_verify

logger = get_logger(__name__)

router = APIRouter(
    prefix="/exam-questions",
    tags=["Exam Questions"],
)

@router.post(
    "",
    response_model=ExamQuestionResponse,
    status_code=201,
    summary="Adicionar questão a uma prova",
    description="Endpoint para adicionar uma questão a uma prova em status DRAFT. Requer autenticação de professor."
)
def create_exam_question(
    request: Request,
    body: ExamQuestionCreateRequest = Body(...),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para adicionar questão a uma prova.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        body (ExamQuestionCreateRequest): Corpo da requisição contendo dados da questão
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com os dados da questão criada
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

    controller = make_create_exam_question_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = http_response.body.model_dump(mode='json') if hasattr(http_response.body, 'model_dump') else http_response.body
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao criar questão: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao criar questão")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.delete(
    "/{question_uuid}",
    status_code=204,
    summary="Remover questão de uma prova",
    description="Endpoint para remover uma questão de uma prova em status DRAFT. A questão não pode estar avaliada. Requer autenticação de professor."
)
def delete_exam_question(
    request: Request,
    question_uuid: str = Path(..., description="UUID da questão a ser removida"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para remover questão de uma prova.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        question_uuid (str): UUID da questão a ser removida
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

    controller = make_delete_exam_question_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=None
        )
    except HTTPException as e:
        logger.error("Erro ao remover questão: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao remover questão")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.delete(
    "/{question_uuid}/answers",
    status_code=204,
    summary="Remover todas as respostas de uma questão",
    description="Endpoint para remover todas as respostas de alunos de uma questão específica. A prova deve estar em status DRAFT. Requer autenticação de professor."
)
def delete_all_question_answers(
    request: Request,
    question_uuid: str = Path(..., description="UUID da questão cujas respostas serão removidas"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para remover todas as respostas de uma questão.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        question_uuid (str): UUID da questão cujas respostas serão removidas
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

    controller = make_delete_all_question_answers_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=None
        )
    except HTTPException as e:
        logger.error("Erro ao remover respostas da questão: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao remover respostas da questão")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e

@router.get(
    "/exam/{exam_uuid}",
    response_model=list[ExamQuestionResponse],
    status_code=200,
    summary="Listar questões de uma prova",
    description="Endpoint para listar todas as questões de uma prova específica. Requer autenticação de professor."
)
def list_exam_questions(
    request: Request,
    exam_uuid: str = Path(..., description="UUID da prova"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para listar questões de uma prova.
    
    Args:
        request (Request): Objeto de requisição FastAPI
        exam_uuid (str): UUID da prova
        caller (CallerMeta): Metadados do chamador
        db (Session): Sessão do banco de dados
        
    Returns:
        JSONResponse: Resposta HTTP com lista de questões
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

    controller = make_list_exam_questions_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        questions_list = http_response.body if isinstance(http_response.body, list) else [http_response.body]
        response_data = [
            q.model_dump(mode='json') if hasattr(q, 'model_dump') else q
            for q in questions_list
        ]
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_data
        )
    except HTTPException as e:
        logger.error("Erro ao listar questões: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao listar questões")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
