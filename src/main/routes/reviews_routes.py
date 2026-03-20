from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.domain.http.caller_domains import CallerMeta
from src.core.logging_config import get_logger

# Response Models
from src.domain.responses.reviews import ExamReviewResponse

# Request Models
from src.domain.requests.reviews import (
    AdjustGradeRequest,
    FinalizeReviewRequest
)

from src.main.composer.reviews_composer import (
    make_get_exam_review_controller,
    make_adjust_grade_controller,
    make_approve_answer_controller,
    make_finalize_review_controller,
    make_download_exam_report_controller
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
    "/approve-answer/{answer_uuid}",
    status_code=200,
    summary="Aprovar resposta individual",
    description="Aprova uma resposta individual, marcando-a como finalizada. Requer autenticação de professor."
)
def approve_answer(
    answer_uuid: str,
    request: Request,
    caller: CallerMeta = Depends(get_caller_meta),
    db=Depends(get_db),
):
    """
    Endpoint para aprovar uma resposta individual.
    
    Args:
        answer_uuid: UUID da resposta a ser aprovada
        request: Objeto de requisição FastAPI
        caller: Metadados do chamador
        db: Sessão do banco de dados
        
    Returns:
        Dict com mensagem de sucesso e dados da resposta
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

    controller = make_approve_answer_controller()

    try:
        response = controller.handle(
            db=db,
            answer_uuid=answer_uuid,
            token_infos=token_infos,
            caller_meta=caller
        )
        return response
    except HTTPException as e:
        logger.error("Erro ao aprovar resposta: %s", str(e.detail))
        raise
    except ValueError as e:
        logger.error("UUID inválido: %s", str(e))
        raise HTTPException(status_code=400, detail="UUID inválido") from e
    except Exception as e:
        logger.exception("Erro inesperado ao aprovar resposta")
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


@router.get(
    "/exams/{exam_uuid}/report",
    status_code=200,
    summary="Download de relatório de notas por prova",
    description="Faz download do relatório Excel mais recente de uma prova específica."
)
def download_exam_report(exam_uuid: str):
    """
    Endpoint para download de relatório por prova.
    
    Args:
        exam_uuid: UUID da prova
        
    Returns:
        FileResponse com arquivo Excel
    """
    controller = make_download_exam_report_controller()
    
    try:
        return controller.handle(exam_uuid=exam_uuid)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro inesperado ao fazer download de relatório da prova")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
