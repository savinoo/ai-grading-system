from __future__ import annotations

from uuid import UUID
from typing import Dict, Any

from sqlalchemy.orm import Session

from src.interfaces.repositories.class_student_repository_interface import ClassStudentRepositoryInterface
from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface
from src.interfaces.repositories.student_repository_interface import StudentRepositoryInterface
from src.interfaces.services.classes.remove_student_from_class_service_interface import RemoveStudentFromClassServiceInterface

from src.errors.domain.sql_error import SqlError
from src.errors.domain.not_found import NotFoundError

from src.core.logging_config import get_logger

class RemoveStudentFromClassService(RemoveStudentFromClassServiceInterface):
    """ 
    Serviço para remover aluno de uma turma.
    """
    
    def __init__(
        self,
        class_student_repository: ClassStudentRepositoryInterface,
        class_repository: ClassesRepositoryInterface,
        student_repository: StudentRepositoryInterface
    ) -> None:
        self.__class_student_repository = class_student_repository
        self.__class_repository = class_repository
        self.__student_repository = student_repository
        self.__logger = get_logger(__name__)
        
    async def remove_student_from_class(
        self,
        db: Session,
        class_uuid: UUID,
        student_uuid: UUID
    ) -> Dict[str, Any]:
        """
        Remove um aluno de uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            student_uuid: UUID do aluno
            
        Returns:
            dict: Informações sobre a remoção
        """
        try:
            try:
                class_obj = self.__class_repository.get_by_uuid(db, class_uuid)
            except Exception as e:
                raise NotFoundError(
                    message="Turma não encontrada",
                    context={"class_uuid": str(class_uuid)}
                ) from e
            
            try:
                student = self.__student_repository.get_by_uuid(db, student_uuid)
            except Exception as e:
                raise NotFoundError(
                    message="Aluno não encontrado",
                    context={"student_uuid": str(student_uuid)}
                ) from e
            
            if not self.__class_student_repository.exists(db, class_uuid, student_uuid):
                raise NotFoundError(
                    message="Aluno não está matriculado nesta turma",
                    context={
                        "class_uuid": str(class_uuid),
                        "student_uuid": str(student_uuid)
                    }
                )
            
            self.__logger.info(
                "Removendo aluno %s da turma %s",
                student_uuid,
                class_uuid
            )
            
            self.__class_student_repository.remove_student_from_class(
                db,
                class_uuid,
                student_uuid
            )
            
            self.__logger.info(
                "Aluno %s removido da turma %s com sucesso",
                student_uuid,
                class_uuid
            )
            
            return {
                "message": "Aluno removido da turma com sucesso",
                "class_uuid": str(class_uuid),
                "class_name": class_obj.name,
                "student_uuid": str(student_uuid),
                "student_name": student.full_name
            }
                
        except NotFoundError:
            raise
        except Exception as e:
            self.__logger.error("Erro inesperado ao remover aluno da turma: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao remover aluno da turma",
                context={
                    "class_uuid": str(class_uuid),
                    "student_uuid": str(student_uuid)
                },
                cause=e
            ) from e
