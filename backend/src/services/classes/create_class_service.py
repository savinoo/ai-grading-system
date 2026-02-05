from __future__ import annotations

from uuid import uuid4, UUID

from sqlalchemy.orm import Session

from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface
from src.interfaces.services.classes.create_class_service_interface import CreateClassServiceInterface

from src.domain.requests.classes.class_create_request import ClassCreateRequest
from src.domain.responses.classes.class_create_response import ClassCreateResponse

from src.models.entities.classes import Classes

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class CreateClassService(CreateClassServiceInterface):
    """ 
    Serviço para criação de turmas.
    """
    
    def __init__(self, repository: ClassesRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)
        
    async def create_class(
        self,
        db: Session,
        request: ClassCreateRequest,
        teacher_uuid: UUID
    ) -> ClassCreateResponse:
        """
        Cria uma nova turma.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da turma a ser criada
            teacher_uuid: UUID do professor que está criando a turma
            
        Returns:
            ClassCreateResponse: Dados da turma criada
        """
        try:
            self.__logger.info("Criando nova turma: %s", request.name)
            
            class_obj = self.__repository.create(
                db,
                uuid=uuid4(),
                name=request.name,
                description=request.description,
                year=request.year,
                semester=request.semester,
                teacher_uuid=teacher_uuid,
                created_by=teacher_uuid
            )
            
            self.__logger.info("Turma criada com sucesso: %s", class_obj.uuid)
            return self._format_response(class_obj)
                
        except Exception as e:
            self.__logger.error("Erro inesperado ao criar turma: %s", e)
            raise SqlError(
                message="Erro ao criar turma no banco de dados",
                context={"name": request.name},
                cause=e
            ) from e

    def _format_response(self, class_obj: Classes) -> ClassCreateResponse:
        """
        Formata a resposta da turma criada.
        
        Args:
            class_obj: Entidade Classes
            
        Returns:
            ClassCreateResponse: Resposta formatada
        """
        return ClassCreateResponse.model_validate(class_obj)
