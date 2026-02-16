from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

# Response Models
from src.domain.responses.results import (
    ExamResultsResponse,
    GradingDetailsResponse,
    ExamResultsSummaryResponse
)

from src.core.logging_config import get_logger

from src.main.composer.results_composer import (
    make_get_exam_results_controller,
    make_get_grading_details_controller,
    make_list_exams_results_controller
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.auth_jwt import auth_jwt_verify

logger = get_logger(__name__)

router = APIRouter(
    prefix="/results",
    tags=["Results"],
)


@router.get(
    "/exams",
    response_model=list[ExamResultsSummaryResponse],
    status_code=200,
    summary="Listar provas com resultados",
    description="Retorna lista de todas as provas do professor que possuem resultados disponíveis. Requer autenticação de professor."
)
def list_exams_results(
    request: Request,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para listar provas com resultados.
    
    Args:
        request: Objeto de requisição FastAPI
        caller: Metadados do chamador
        db: Sessão do banco de dados
        
    Returns:
        JSONResponse com lista de ExamResultsSummaryResponse
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
        param={},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_list_exams_results_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        
        # Retornar diretamente a lista - FastAPI vai serializar usando response_model
        return http_response.body
    except HTTPException as e:
        logger.error("Erro ao listar provas com resultados: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao listar provas com resultados")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e


@router.get(
    "/exams/{exam_uuid}",
    response_model=ExamResultsResponse,
    status_code=200,
    summary="Buscar estatísticas de uma prova corrigida",
    description="Retorna estatísticas completas de uma prova, incluindo média, distribuição de notas e estatísticas por questão. Requer autenticação de professor."
)
def get_exam_results(
    request: Request,
    exam_uuid: str,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para buscar resultados de uma prova.
    
    Args:
        request: Objeto de requisição FastAPI
        exam_uuid: UUID da prova
        caller: Metadados do chamador
        db: Sessão do banco de dados
        
    Returns:
        JSONResponse com ExamResultsResponse
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

    controller = make_get_exam_results_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = (
            http_response.body.model_dump(mode='json')
            if hasattr(http_response.body, 'model_dump')
            else http_response.body
        )
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao buscar resultados da prova: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao buscar resultados da prova")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e


@router.get(
    "/answers/{answer_uuid}/details",
    response_model=GradingDetailsResponse,
    status_code=200,
    summary="Buscar detalhes da correção de uma resposta",
    description="Retorna detalhes completos da correção de uma resposta, incluindo notas por critério, feedback dos agentes e contexto RAG. Requer autenticação de professor."
)
def get_grading_details(
    request: Request,
    answer_uuid: str,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para buscar detalhes de correção de uma resposta.
    
    Args:
        request: Objeto de requisição FastAPI
        answer_uuid: UUID da resposta do aluno
        caller: Metadados do chamador
        db: Sessão do banco de dados
        
    Returns:
        JSONResponse com GradingDetailsResponse
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
        param={"answer_uuid": answer_uuid},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_get_grading_details_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        response_body = (
            http_response.body.model_dump(mode='json')
            if hasattr(http_response.body, 'model_dump')
            else http_response.body
        )
        return JSONResponse(
            status_code=http_response.status_code,
            content=response_body
        )
    except HTTPException as e:
        logger.error("Erro ao buscar detalhes de correção: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao buscar detalhes de correção")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
