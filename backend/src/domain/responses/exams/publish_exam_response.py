"""
Response model para publicação de prova.
"""

from pydantic import BaseModel, Field
from typing import List


class PublishExamResponse(BaseModel):
    """
    Resposta da publicação de prova.
    """
    
    message: str = Field(
        ...,
        description="Mensagem de confirmação da publicação"
    )
    
    exam_uuid: str = Field(
        ...,
        description="UUID da prova publicada"
    )
    
    status: str = Field(
        ...,
        description="Status atual da prova após publicação"
    )
    
    next_steps: List[str] = Field(
        default_factory=list,
        description="Próximos passos do processamento em background"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Prova publicada com sucesso. O processamento foi iniciado em background.",
                "exam_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "status": "PUBLISHED",
                "next_steps": [
                    "Os PDFs estão sendo indexados no sistema de vetorização",
                    "Após indexação, a correção automática será executada",
                    "Acompanhe o status da prova para verificar conclusão"
                ]
            }
        }
