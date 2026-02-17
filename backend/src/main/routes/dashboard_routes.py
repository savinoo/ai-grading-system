"""
Rotas para dashboard do professor.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Query

from src.domain.http.caller_domains import CallerMeta
from src.core.logging_config import get_logger

# Response Models
from src.domain.responses.dashboard.dashboard_stats_response import DashboardStatsResponse

from src.main.composers.dashboard.get_dashboard_stats_composer import make_get_dashboard_stats_controller

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.auth_jwt import auth_jwt_verify


logger = get_logger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/stats/{teacher_uuid}",
    response_model=DashboardStatsResponse,
    status_code=200,
    summary="Obter estatísticas do dashboard",
    description="Retorna estatísticas agregadas para o dashboard do professor: contadores de provas, respostas, provas recentes e ações pendentes. Requer autenticação de professor."
)
def get_dashboard_stats(
    request: Request,
    teacher_uuid: str,
    limit_recent_exams: int = Query(10, ge=1, le=50, description="Limite de provas recentes a retornar"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para obter estatísticas do dashboard do professor.
    
    Args:
        request: Objeto de requisição FastAPI
        teacher_uuid: UUID do professor
        limit_recent_exams: Número de provas recentes a retornar
        caller: Metadados do chamador
        db: Sessão do banco de dados
        
    Returns:
        DashboardStatsResponse com todas as estatísticas
    """
    headers = request.headers
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
        token = auth_header.split(" ", 1)[1].strip()

        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido para dashboard: %s", token_infos)
    except HTTPException as e:
        logger.error("Erro de autenticação: %s", str(e))
        raise

    controller = make_get_dashboard_stats_controller()

    try:
        response = controller.handle(
            db=db,
            teacher_uuid=UUID(teacher_uuid),
            limit_recent_exams=limit_recent_exams,
            token_infos=token_infos,
            caller_meta=caller
        )
        return response
    except HTTPException as e:
        logger.error("Erro ao buscar estatísticas do dashboard: %s", str(e.detail))
        raise
    except ValueError as e:
        logger.error("Valor inválido: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Erro inesperado ao buscar estatísticas do dashboard")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
