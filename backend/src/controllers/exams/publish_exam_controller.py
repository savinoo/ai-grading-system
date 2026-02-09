"""
Controller para publicação de provas.
Endpoint: POST /exams/{exam_uuid}/publish
"""

import logging
from uuid import UUID
from fastapi import Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.domain.http.http_response import HttpResponse
from src.main.dependencies.get_db_session import get_db as get_db_session
from src.services.exams.publish_exam_service import PublishExamService
from src.models.repositories.exams_repository import ExamsRepository

logger = logging.getLogger(__name__)


async def publish_exam_controller(
    exam_uuid: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
) -> HttpResponse:
    """
    Publica uma prova e inicia processamento em background.
    
    Fluxo síncrono (na requisição):
    - Validar que prova existe e está em DRAFT
    - Atualizar status para PUBLISHED
    - Retornar HTTP 202 Accepted
    
    Fluxo assíncrono (background task):
    - Indexar PDFs (attachments com vector_status=DRAFT)
    - Executar correção automática (grade_exam)
    - Atualizar status final (GRADED ou WARNING)
    
    Args:
        exam_uuid: UUID da prova a ser publicada
        background_tasks: FastAPI BackgroundTasks para processamento assíncrono
        db: Sessão do banco de dados (injetada)
    
    Returns:
        HTTPResponse: 
            - 202 Accepted: Publicação iniciada
            - 400 Bad Request: Prova não está em DRAFT
            - 404 Not Found: Prova não existe
    
    Examples:
        POST /exams/123e4567-e89b-12d3-a456-426614174000/publish
        → 202 {"message": "Prova publicada...", "status": "PUBLISHED"}
    """
    logger.info("📥 Requisição de publicação recebida: exam_uuid=%s", exam_uuid)
    
    exam_repo = ExamsRepository()
    
    # === 1. Validar que prova existe ===
    try:
        exam = exam_repo.get_by_uuid(db, exam_uuid)
    except NoResultFound as exc:
        logger.warning("❌ Prova não encontrada: %s", exam_uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prova {exam_uuid} não encontrada"
        ) from exc
    except Exception as e:
        logger.error("Erro ao buscar prova: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar prova"
        ) from e
    
    # === 2. Validar que prova está em DRAFT ===
    if exam.status != 'DRAFT':
        logger.warning(
            "❌ Tentativa de publicar prova com status inválido: %s (atual=%s)",
            exam_uuid, exam.status
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Não é possível publicar prova com status '{exam.status}'. "
                "Apenas provas em DRAFT podem ser publicadas."
            )
        )
    
    # === 3. Atualizar status para PUBLISHED (síncrono) ===
    try:
        exam_repo.update_status_by_uuid(db, exam_uuid, 'PUBLISHED')
        db.commit()
        
        logger.info(
            "✅ Status da prova %s atualizado para PUBLISHED",
            exam_uuid
        )
        
    except Exception as e:
        logger.error(
            "Erro ao atualizar status da prova: %s",
            e,
            exc_info=True
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar status da prova"
        ) from e
    
    # === 4. Agendar processamento em background ===
    publish_service = PublishExamService(db)
    background_tasks.add_task(
        publish_service.publish_exam,
        exam_uuid
    )
    
    logger.info(
        "🚀 Background task agendada para prova %s. "
        "Indexação e correção serão executadas assincronamente.",
        exam_uuid
    )
    
    # === 5. Retornar HTTP 202 Accepted ===
    return HttpResponse(
        status_code=status.HTTP_202_ACCEPTED,
        body={
            "message": (
                "Prova publicada com sucesso. "
                "O processamento de indexação e correção foi iniciado em background."
            ),
            "exam_uuid": str(exam_uuid),
            "status": "PUBLISHED",
            "next_steps": [
                "Os PDFs estão sendo indexados no sistema de vetorização",
                "Após indexação, a correção automática será executada",
                "Acompanhe o status da prova para verificar conclusão"
            ]
        }
    )
