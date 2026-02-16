"""
Request models para ações de revisão.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AcceptSuggestionRequest(BaseModel):
    """Request para aceitar uma sugestão da IA."""
    
    answer_uuid: UUID = Field(..., description="UUID da resposta")
    suggestion_id: str = Field(..., description="ID da sugestão", examples=["sug_1"])


class RejectSuggestionRequest(BaseModel):
    """Request para rejeitar uma sugestão da IA."""
    
    answer_uuid: UUID = Field(..., description="UUID da resposta")
    suggestion_id: str = Field(..., description="ID da sugestão", examples=["sug_1"])
    reason: Optional[str] = Field(None, description="Motivo da rejeição")


class AdjustGradeRequest(BaseModel):
    """Request para ajustar nota manualmente."""
    
    answer_uuid: UUID = Field(..., description="UUID da resposta")
    new_score: float = Field(..., description="Nova nota", examples=[9.5])
    feedback: Optional[str] = Field(None, description="Feedback atualizado")
    
    # Ajustes por critério (opcional)
    criteria_adjustments: Optional[dict[str, float]] = Field(
        None,
        description="Ajustes por critério (criterion_uuid: new_score)"
    )


class FinalizeReviewRequest(BaseModel):
    """Request para finalizar revisão e gerar relatório."""
    
    exam_uuid: UUID = Field(..., description="UUID da prova")
    send_notifications: bool = Field(
        True,
        description="Se deve enviar notificações aos alunos"
    )
    generate_pdf: bool = Field(
        True,
        description="Se deve gerar relatório em PDF"
    )
