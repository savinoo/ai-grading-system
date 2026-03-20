from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class ClassInClasses(BaseModel):
    """ 
    Modelo de resposta para listagem de turmas.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    uuid: UUID = Field(
        ...,
        description="UUID da turma"
    )
    
    name: str = Field(
        ...,
        description="Nome da turma"
    )
    
    description: str | None = Field(
        default=None,
        description="Descrição da turma"
    )
    
    year: int | None = Field(
        default=None,
        description="Ano letivo"
    )
    
    semester: int | None = Field(
        default=None,
        description="Semestre"
    )

class ClassesResponse(BaseModel):
    """
    Modelo de resposta para listagem de turmas.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "classes": [
                    {
                        "uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Matemática Avançada - Turma A",
                        "description": "Turma de matemática avançada",
                        "year": 2026,
                        "semester": 1
                    }
                ],
                "total_classes": 1
            }
        }
    )
    
    classes: list[ClassInClasses] = Field(
        ...,
        description="Lista de turmas"
    )
    
    total_classes: int = Field(
        ...,
        description="Total de turmas"
    )
