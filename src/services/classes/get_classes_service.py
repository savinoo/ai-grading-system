from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface

from src.domain.responses.classes.classes_response import ClassesResponse, ClassInClasses

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class GetClassesService():
    """ 
    Serviço para buscar turma com seus alunos.
    """
    
    def __init__(
        self,
        class_repository: ClassesRepositoryInterface
    ) -> None:
        self.__class_repository = class_repository
        self.__logger = get_logger(__name__)
        
    async def get_classes(
        self,
        db: Session,
        teacher_uuid: UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> ClassesResponse:
        """
        Busca todas as turmas de um professor.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            active_only: Se deve retornar apenas alunos ativos
            skip: Número de alunos a pular na paginação
            limit: Número máximo de alunos a retornar
            
        Returns:
            ClassesResponse: Lista de turmas do professor
        """
        class_data = []
        try:
            self.__logger.info("Buscando turmas para o professor: %s", teacher_uuid)
            
            classes = self.__class_repository.get_by_teacher(
                db,
                teacher_uuid,
                skip=skip,
                limit=limit,
                active_only=active_only
            )
            
        except Exception as e:
            self.__logger.error("Erro ao buscar turmas: %s", str(e), exc_info=True)
            raise SqlError(
                message="Erro ao buscar turmas",
                context={"teacher_uuid": str(teacher_uuid)}
            ) from e
        
        for class_obj in classes:
            class_data.append(
                ClassInClasses(
                    uuid=class_obj.uuid,
                    name=class_obj.name,
                    description=class_obj.description,
                    year=class_obj.year,
                    semester=class_obj.semester,
                    active=class_obj.active,
                    created_at=class_obj.created_at,
                    updated_at=class_obj.updated_at
                )
            )
        
        return ClassesResponse(
            classes=class_data,
            total_classes=len(class_data)
        )
