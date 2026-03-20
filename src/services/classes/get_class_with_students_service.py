from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface
from src.interfaces.repositories.class_student_repository_interface import ClassStudentRepositoryInterface
from src.interfaces.repositories.student_repository_interface import StudentRepositoryInterface
from src.interfaces.services.classes.get_class_with_students_service_interface import GetClassWithStudentsServiceInterface

from src.domain.responses.classes.class_with_students_response import ClassWithStudentsResponse, StudentInClass

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class GetClassWithStudentsService(GetClassWithStudentsServiceInterface):
    """ 
    Serviço para buscar turma com seus alunos.
    """
    
    def __init__(
        self,
        class_repository: ClassesRepositoryInterface,
        class_student_repository: ClassStudentRepositoryInterface,
        student_repository: StudentRepositoryInterface
    ) -> None:
        self.__class_repository = class_repository
        self.__class_student_repository = class_student_repository
        self.__student_repository = student_repository
        self.__logger = get_logger(__name__)
        
    async def get_class_with_students(
        self,
        db: Session,
        class_uuid: UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> ClassWithStudentsResponse:
        """
        Busca uma turma e seus alunos.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            active_only: Se deve retornar apenas alunos ativos
            skip: Número de alunos a pular na paginação
            limit: Número máximo de alunos a retornar
            
        Returns:
            ClassWithStudentsResponse: Turma com lista de alunos
        """
        try:
            try:
                class_obj = self.__class_repository.get_by_uuid(db, class_uuid)
            except Exception as e:
                raise NotFoundError(
                    message="Turma não encontrada",
                    context={"class_uuid": str(class_uuid)}
                ) from e
            
            self.__logger.debug("Buscando alunos da turma %s", class_uuid)
            
            enrollments = self.__class_student_repository.get_students_by_class(
                db,
                class_uuid,
                active_only=active_only,
                skip=skip,
                limit=limit
            )
            
            students_data = []
            for enrollment in enrollments:
                try:
                    student = self.__student_repository.get_by_uuid(db, enrollment.student_uuid)
                    students_data.append(
                        StudentInClass(
                            uuid=student.uuid,
                            full_name=student.full_name,
                            email=student.email,
                            enrolled_at=enrollment.enrolled_at,
                            active=enrollment.active
                        )
                    )
                except Exception as e:
                    self.__logger.error(
                        "Erro ao buscar dados do aluno %s: %s",
                        enrollment.student_uuid,
                        e,
                        exc_info=True
                    )
            
            total_students = self.__class_student_repository.count_students_in_class(
                db,
                class_uuid,
                active_only=active_only
            )
            
            self.__logger.info(
                "Turma %s possui %d alunos",
                class_uuid,
                total_students
            )
            
            return ClassWithStudentsResponse(
                uuid=class_obj.uuid,
                name=class_obj.name,
                description=class_obj.description,
                year=class_obj.year,
                semester=class_obj.semester,
                total_students=total_students,
                students=students_data
            )
                
        except NotFoundError:
            raise
        except Exception as e:
            self.__logger.error("Erro inesperado ao buscar turma com alunos: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao buscar turma com alunos",
                context={"class_uuid": str(class_uuid)},
                cause=e
            ) from e
