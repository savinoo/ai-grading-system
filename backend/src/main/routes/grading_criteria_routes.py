from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.domain.http.caller_domains import CallerMeta

# Response Models
from src.domain.responses.grading_criteria.grading_criteria_response import GradingCriteriaResponse

from src.core.logging_config import get_logger

from src.main.composer.grading_criteria_composer import (
    make_list_grading_criteria_controller
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.auth_jwt import auth_jwt_verify

logger = get_logger(__name__)

router = APIRouter(
    prefix="/grading-criteria",
    tags=["Grading Criteria"],
)

@router.get(
    "",
    response_model=List[GradingCriteriaResponse],
    status_code=200,
    summary="Listar critérios de avaliação disponíveis",
    description="Endpoint para listar todos os critérios de avaliação disponíveis no sistema. Requer autenticação."
)
def list_grading_criteria(
    request: Request,
    active_only: bool = Query(True, description="Retornar apenas critérios ativos"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros a retornar"),
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para listar critérios de avaliação disponíveis.
    
    Args:
        request (Request): Objeto de requisição FastAPI
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
        param={"active_only": active_only, "skip": skip, "limit": limit},
        db=db,
        caller=caller,
        headers=request.headers,
        token_infos=token_infos
    )

    controller = make_list_grading_criteria_controller()

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
        logger.error("Erro ao listar critérios de avaliação: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.exception("Erro inesperado ao listar critérios de avaliação")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
