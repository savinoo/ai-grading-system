from typing import Optional

from pydantic import BaseModel, Field

class StudentAnswerUpdateRequest(BaseModel):
    """
    Modelo de requisição para atualização de resposta de aluno.
    """

    answer_text: Optional[str] = Field(
        default=None,
        description="Nova resposta do aluno para a questão",
        examples=["Polimorfismo é a capacidade de objetos de classes diferentes responderem à mesma mensagem..."]
    )

