from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface
from src.interfaces.services.classes.deactivate_class_service_interface import DeactivateClassServiceInterface

from src.domain.responses.classes.class_create_response import ClassCreateResponse

from src.models.entities.classes import Classes

from src.errors.domain.sql_error import SqlError
from src.errors.domain.not_found import NotFoundError

from src.core.logging_config import get_logger

class DeactivateClassService(DeactivateClassServiceInterface):
    """ 
    Serviço para desativar turmas.
    """
    
    def __init__(self, repository: ClassesRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)
        
    async def deactivate_class(
        self,
        db: Session,
        class_uuid: UUID
    ) -> ClassCreateResponse:
        """
        Desativa uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            
        Returns:
            ClassCreateResponse: Dados da turma desativada
        """
        try:
            try:
                class_obj = self.__repository.get_by_uuid(db, class_uuid)
            except Exception as e:
                raise NotFoundError(
                    message="Turma não encontrada",
                    context={"class_uuid": str(class_uuid)}
                ) from e
            
            if not class_obj.active:
                self.__logger.warning("Turma %s já está desativada", class_uuid)
                return self._format_response(class_obj)
            
            self.__logger.info("Desativando turma: %s", class_uuid)
            
            updated_class = self.__repository.deactivate(db, class_obj.id)
            
            self.__logger.info("Turma desativada com sucesso: %s", class_uuid)
            return self._format_response(updated_class)
                
        except NotFoundError:
            raise
        except Exception as e:
            self.__logger.error("Erro inesperado ao desativar turma: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao desativar turma no banco de dados",
                context={"class_uuid": str(class_uuid)},
                cause=e
            ) from e

    def _format_response(self, class_obj: Classes) -> ClassCreateResponse:
        """
        Formata a resposta da turma.
        
        Args:
            class_obj: Entidade Classes
            
        Returns:
            ClassCreateResponse: Resposta formatada
        """
        return ClassCreateResponse.model_validate(class_obj)
