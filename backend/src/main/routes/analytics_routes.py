"""
Rotas do módulo de análise pedagógica.

Endpoints:
  GET /analytics/classes                          — Sumário analítico de todas as turmas do professor
  GET /analytics/classes/{class_uuid}             — Análise completa de uma turma
  GET /analytics/classes/{class_uuid}/students/{student_uuid} — Desempenho individual de um aluno
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta
from src.domain.responses.analytics import (
    ClassAnalyticsSummaryResponse,
    ClassAnalyticsResponse,
    StudentPerformanceResponse,
)

from src.core.logging_config import get_logger

from src.main.composer.analytics_composer import (
    make_list_classes_analytics_controller,
    make_get_class_analytics_controller,
    make_get_student_performance_controller,
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.auth_jwt import auth_jwt_verify

logger = get_logger(__name__)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

# ---------------------------------------------------------------------------
# Helper de autenticação reutilizável
# ---------------------------------------------------------------------------


def _extract_teacher_token(request: Request, db):
    """Extrai e valida o token JWT de professor da requisição."""
    headers = request.headers
    auth_header = headers.get("Authorization") or headers.get("authorization") or ""
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
    token = auth_header.split(" ", 1)[1].strip()
    return auth_jwt_verify(token, db, scope="teacher")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/classes",
    response_model=list[ClassAnalyticsSummaryResponse],
    status_code=200,
    summary="Listar análises de turmas",
    description=(
        "Retorna o sumário analítico de todas as turmas do professor autenticado. "
        "Cada item mostra média da turma, contagem de alunos em dificuldade e top performers."
    ),
)
def list_classes_analytics(
    request: Request,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    try:
        token_infos = _extract_teacher_token(request, db)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e

    http_request = HttpRequest(
        param={},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos,
    )

    controller = make_list_classes_analytics_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        return http_response.body
    except HTTPException as e:
        logger.error("Erro ao listar analytics de turmas: %s", e.detail)
        raise
    except Exception as e:
        logger.exception("Erro inesperado ao listar analytics de turmas")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e


@router.get(
    "/classes/{class_uuid}",
    response_model=ClassAnalyticsResponse,
    status_code=200,
    summary="Análise pedagógica de uma turma",
    description=(
        "Retorna análise pedagógica completa de uma turma: média, mediana, desvio padrão, "
        "distribuição de notas (A/B/C/D/F), alunos em dificuldade, top performers e gaps mais comuns."
    ),
)
def get_class_analytics(
    request: Request,
    class_uuid: str,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    try:
        token_infos = _extract_teacher_token(request, db)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e

    http_request = HttpRequest(
        param={"class_uuid": class_uuid},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos,
    )

    controller = make_get_class_analytics_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body,
        )
    except HTTPException as e:
        logger.error("Erro ao buscar analytics da turma %s: %s", class_uuid, e.detail)
        raise
    except Exception as e:
        logger.exception("Erro inesperado ao buscar analytics da turma")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e


@router.get(
    "/classes/{class_uuid}/students/{student_uuid}",
    response_model=StudentPerformanceResponse,
    status_code=200,
    summary="Desempenho individual de um aluno em uma turma",
    description=(
        "Retorna o perfil analítico completo de um aluno em uma turma: "
        "média, tendência de evolução (regressão linear), gaps de aprendizado e pontos fortes por critério."
    ),
)
def get_student_performance(
    request: Request,
    class_uuid: str,
    student_uuid: str,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    try:
        token_infos = _extract_teacher_token(request, db)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e

    http_request = HttpRequest(
        param={"class_uuid": class_uuid, "student_uuid": student_uuid},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos,
    )

    controller = make_get_student_performance_controller()

    try:
        http_response: HttpResponse = controller.handle(http_request)
        return JSONResponse(
            status_code=http_response.status_code,
            content=http_response.body,
        )
    except HTTPException as e:
        logger.error(
            "Erro ao buscar performance do aluno %s na turma %s: %s",
            student_uuid, class_uuid, e.detail,
        )
        raise
    except Exception as e:
        logger.exception("Erro inesperado ao buscar performance do aluno")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
