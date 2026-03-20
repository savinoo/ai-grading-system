from typing import List

from pydantic import BaseModel, Field

from .exam_response import ExamResponse

class ExamsListResponse(BaseModel):
    """
    Modelo de resposta para lista de provas.
    """

    exams: List[ExamResponse] = Field(
        default_factory=list,
        description="Lista de provas"
    )

    total: int = Field(
        ...,
        description="Total de provas retornadas"
    )
