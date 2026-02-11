"""
Interface para serviço de publicação de provas.
Define contrato para orquestração de indexação e correção automática.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from src.domain.responses.exams.publish_exam_response import PublishExamResponse


class PublishExamServiceInterface(ABC):
    """
    Interface para serviço de publicação de provas.
    
    Responsabilidades:
    - Validar status da prova (DRAFT → PUBLISHED)
    - Orquestrar indexação de PDFs em background
    - Disparar correção automática após indexação
    - Gerenciar transições de status (PUBLISHED → GRADED/WARNING)
    """
    
    @abstractmethod
    async def publish_exam(
        self,
        db: Session,
        exam_uuid: UUID,
        background_tasks: BackgroundTasks
    ) -> PublishExamResponse:
        """
        Publica uma prova e agenda processamento em background.
        
        Fluxo:
        1. Validar que prova existe e está em DRAFT
        2. Atualizar status para PUBLISHED
        3. Agendar background task (indexação + correção)
        4. Retornar resposta de confirmação
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova a ser publicada
            background_tasks: FastAPI BackgroundTasks para processamento assíncrono
            
        Returns:
            PublishExamResponse: Detalhes da publicação iniciada
            
        Raises:
            NotFoundError: Se prova não existir
            ValidateError: Se prova não estiver em DRAFT
        """
        pass
