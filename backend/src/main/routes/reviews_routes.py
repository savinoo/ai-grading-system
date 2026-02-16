"""
Rotas para revisão de provas corrigidas.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request

from src.domain.http.caller_domains import CallerMeta
from src.core.logging_config import get_logger

# Response Models
from src.domain.responses.reviews import ExamReviewResponse

# Request Models
from src.domain.requests.reviews import (
    AcceptSuggestionRequest,
    RejectSuggestionRequest,
    AdjustGradeRequest,
    FinalizeReviewRequest
)

from src.main.composer.reviews_composer import (
    make_get_exam_review_controller,
    make_accept_suggestion_controller,
    make_reject_suggestion_controller,
    make_adjust_grade_controller,
    make_finalize_review_controller
)

from src.main.dependencies.request_meta import get_caller_meta
from src.main.dependencies.get_db_session import get_db
from src.main.dependencies.auth_jwt import auth_jwt_verify


logger = get_logger(__name__)

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


@router.get(
    "/exams/{exam_uuid}",
    response_model=ExamReviewResponse,
    status_code=200,
    summary="Buscar dados para revisão de prova",
    description="Retorna todos os dados necessários para revisão de uma prova: questões, respostas dos alunos, sugestões da IA e scores por critério. Requer autenticação de professor."
)
def get_exam_review(
    request: Request,
    exam_uuid: str,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para buscar dados de revisão de uma prova.
    
    Args:
        request: Objeto de requisição FastAPI
        exam_uuid: UUID da prova
        caller: Metadados do chamador
        db: Sessão do banco de dados
        
    Returns:
        ExamReviewResponse com dados de revisão
    """
    headers = request.headers
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
        token = auth_header.split(" ", 1)[1].strip()

        token_infos = auth_jwt_verify(token, db, scope="teacher")
        logger.debug("Token válido para revisão: %s", token_infos)
    except HTTPException as e:
        logger.error("Erro de autenticação: %s", str(e))
        raise

    controller = make_get_exam_review_controller()

    try:
        response = controller.handle(
            db=db,
            exam_uuid=UUID(exam_uuid),
            token_infos=token_infos,
            caller_meta=caller
        )
        return response
    except HTTPException as e:
        logger.error("Erro ao buscar dados de revisão: %s", str(e.detail))
        raise
    except ValueError as e:
        logger.error("UUID inválido: %s", str(e))
        raise HTTPException(status_code=400, detail="UUID inválido") from e
    except Exception as e:
        logger.exception("Erro inesperado ao buscar dados de revisão")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e


@router.post(
    "/suggestions/accept",
    status_code=200,
    summary="Aceitar sugestão da IA",
    description="Aceita uma sugestão da IA para uma resposta específica. Requer autenticação de professor."
)
def accept_suggestion(
    request_body: AcceptSuggestionRequest,
    request: Request,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para aceitar uma sugestão da IA.
    
    Args:
        request_body: Dados da solicitação
        request: Objeto de requisição FastAPI
        caller: Metadados do chamador
        db: Sessão do banco de dados
        
    Returns:
        Dict com mensagem de sucesso
    """
    headers = request.headers
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
        token = auth_header.split(" ", 1)[1].strip()

        token_infos = auth_jwt_verify(token, db, scope="teacher")
    except HTTPException as e:
        logger.error("Erro de autenticação: %s", str(e))
        raise

    controller = make_accept_suggestion_controller()

    try:
        response = controller.handle(
            db=db,
            request=request_body,
            token_infos=token_infos,
            caller_meta=caller
        )
        return response
    except HTTPException as e:
        logger.error("Erro ao aceitar sugestão: %s", str(e.detail))
        raise
    except Exception as e:
        logger.exception("Erro inesperado ao aceitar sugestão")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e


@router.post(
    "/suggestions/reject",
    status_code=200,
    summary="Rejeitar sugestão da IA",
    description="Rejeita uma sugestão da IA para uma resposta específica. Requer autenticação de professor."
)
def reject_suggestion(
    request_body: RejectSuggestionRequest,
    request: Request,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para rejeitar uma sugestão da IA.
    
    Args:
        request_body: Dados da solicitação
        request: Objeto de requisição FastAPI
        caller: Metadados do chamador
        db: Sessão do banco de dados
        
    Returns:
        Dict com mensagem de sucesso
    """
    headers = request.headers
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
        token = auth_header.split(" ", 1)[1].strip()

        token_infos = auth_jwt_verify(token, db, scope="teacher")
    except HTTPException as e:
        logger.error("Erro de autenticação: %s", str(e))
        raise

    controller = make_reject_suggestion_controller()

    try:
        response = controller.handle(
            db=db,
            request=request_body,
            token_infos=token_infos,
            caller_meta=caller
        )
        return response
    except HTTPException as e:
        logger.error("Erro ao rejeitar sugestão: %s", str(e.detail))
        raise
    except Exception as e:
        logger.exception("Erro inesperado ao rejeitar sugestão")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e


@router.put(
    "/grades/adjust",
    status_code=200,
    summary="Ajustar nota manualmente",
    description="Permite ao professor ajustar manualmente a nota de uma resposta. Requer autenticação de professor."
)
def adjust_grade(
    request_body: AdjustGradeRequest,
    request: Request,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para ajustar nota manualmente.
    
    Args:
        request_body: Dados da solicitação
        request: Objeto de requisição FastAPI
        caller: Metadados do chamador
        db: Sessão do banco de dados
        
    Returns:
        Dict com mensagem de sucesso e nova nota
    """
    headers = request.headers
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
        token = auth_header.split(" ", 1)[1].strip()

        token_infos = auth_jwt_verify(token, db, scope="teacher")
    except HTTPException as e:
        logger.error("Erro de autenticação: %s", str(e))
        raise

    controller = make_adjust_grade_controller()

    try:
        response = controller.handle(
            db=db,
            request=request_body,
            token_infos=token_infos,
            caller_meta=caller
        )
        return response
    except HTTPException as e:
        logger.error("Erro ao ajustar nota: %s", str(e.detail))
        raise
    except Exception as e:
        logger.exception("Erro inesperado ao ajustar nota")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e


@router.post(
    "/finalize",
    status_code=200,
    summary="Finalizar revisão",
    description="Finaliza a revisão de uma prova, gerando relatório e enviando notificações aos alunos (se solicitado). Requer autenticação de professor."
)
def finalize_review(
    request_body: FinalizeReviewRequest,
    request: Request,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para finalizar revisão.
    
    Args:
        request_body: Dados da solicitação
        request: Objeto de requisição FastAPI
        caller: Metadados do chamador
        db: Sessão do banco de dados
        
    Returns:
        Dict com mensagem de sucesso
    """
    headers = request.headers
    try:
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Credenciais ausentes ou inválidas.")
        token = auth_header.split(" ", 1)[1].strip()

        token_infos = auth_jwt_verify(token, db, scope="teacher")
    except HTTPException as e:
        logger.error("Erro de autenticação: %s", str(e))
        raise

    controller = make_finalize_review_controller()

    try:
        response = controller.handle(
            db=db,
            request=request_body,
            token_infos=token_infos,
            caller_meta=caller
        )
        return response
    except HTTPException as e:
        logger.error("Erro ao finalizar revisão: %s", str(e.detail))
        raise
    except Exception as e:
        logger.exception("Erro inesperado ao finalizar revisão")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
