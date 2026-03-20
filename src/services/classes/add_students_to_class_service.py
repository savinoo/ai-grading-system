from __future__ import annotations

from uuid import uuid4, UUID
from typing import Dict, Any

from sqlalchemy.orm import Session

from src.interfaces.repositories.student_repository_interface import StudentRepositoryInterface
from src.interfaces.repositories.class_student_repository_interface import ClassStudentRepositoryInterface
from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface
from src.interfaces.services.classes.add_students_to_class_service_interface import AddStudentsToClassServiceInterface

from src.domain.requests.classes.add_students_to_class_request import AddStudentsToClassRequest, StudentData

from src.models.entities.student import Student

from src.errors.domain.sql_error import SqlError
from src.errors.domain.not_found import NotFoundError

from src.core.logging_config import get_logger

class AddStudentsToClassService(AddStudentsToClassServiceInterface):
    """ 
    Serviço para adicionar alunos a turmas.
    """
    
    def __init__(
        self,
        student_repository: StudentRepositoryInterface,
        class_student_repository: ClassStudentRepositoryInterface,
        class_repository: ClassesRepositoryInterface
    ) -> None:
        self.__student_repository = student_repository
        self.__class_student_repository = class_student_repository
        self.__class_repository = class_repository
        self.__logger = get_logger(__name__)
        
    async def add_students_to_class(
        self,
        db: Session,
        class_uuid: UUID,
        request: AddStudentsToClassRequest
    ) -> Dict[str, Any]:
        """
        Adiciona alunos a uma turma.
        Cria novos alunos se não existirem (validando por nome e email).
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            request: Lista de alunos a adicionar
            
        Returns:
            dict: Informações sobre os alunos adicionados
        """
        try:
            try:
                class_obj = self.__class_repository.get_by_uuid(db, class_uuid)
            except Exception as e:
                raise NotFoundError(
                    message="Turma não encontrada",
                    context={"class_uuid": str(class_uuid)}
                ) from e
            
            self.__logger.info(
                "Adicionando %d alunos à turma %s",
                len(request.students),
                class_uuid
            )
            
            students_created = []
            students_existing = []
            students_enrolled = []
            students_already_enrolled = []
            errors = []
            
            for student_data in request.students:
                try:
                    student = await self.__get_or_create_student(db, student_data)
                    
                    if student.uuid in [s["uuid"] for s in students_created]:
                        pass
                    elif student_data.full_name not in [s["full_name"] for s in students_existing]:
                        students_existing.append({
                            "uuid": str(student.uuid),
                            "full_name": student.full_name,
                            "email": student.email
                        })
                    
                    # Verifica se já está matriculado
                    if self.__class_student_repository.exists(db, class_uuid, student.uuid):
                        self.__logger.warning(
                            "Aluno %s já está matriculado na turma %s",
                            student.uuid,
                            class_uuid
                        )
                        students_already_enrolled.append({
                            "uuid": str(student.uuid),
                            "full_name": student.full_name,
                            "email": student.email
                        })
                        continue
                    
                    # Matricula o aluno na turma
                    self.__class_student_repository.create(
                        db,
                        class_uuid=class_uuid,
                        student_uuid=student.uuid
                    )
                    
                    students_enrolled.append({
                        "uuid": str(student.uuid),
                        "full_name": student.full_name,
                        "email": student.email
                    })
                    
                except Exception as e:
                    self.__logger.error(
                        "Erro ao processar aluno %s: %s",
                        student_data.full_name,
                        e,
                        exc_info=True
                    )
                    errors.append({
                        "full_name": student_data.full_name,
                        "email": student_data.email,
                        "error": str(e)
                    })
            
            self.__logger.info(
                "Processo concluído: %d matriculados, %d já existiam, %d erros",
                len(students_enrolled),
                len(students_already_enrolled),
                len(errors)
            )
            
            return {
                "class_uuid": str(class_uuid),
                "class_name": class_obj.name,
                "summary": {
                    "total_requested": len(request.students),
                    "students_enrolled": len(students_enrolled),
                    "students_already_enrolled": len(students_already_enrolled),
                    "new_students_created": len(students_created),
                    "errors": len(errors)
                },
                "details": {
                    "enrolled": students_enrolled,
                    "already_enrolled": students_already_enrolled,
                    "created": students_created,
                    "errors": errors
                }
            }
                
        except NotFoundError:
            raise
        except Exception as e:
            self.__logger.error("Erro inesperado ao adicionar alunos: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao adicionar alunos à turma",
                context={"class_uuid": str(class_uuid)},
                cause=e
            ) from e
    
    async def __get_or_create_student(
        self,
        db: Session,
        student_data: StudentData
    ) -> Student:
        """
        Busca um aluno existente ou cria um novo.
        Valida por email (se fornecido) ou por nome completo.
        
        Args:
            db: Sessão do banco de dados
            student_data: Dados do aluno
            
        Returns:
            Student: Aluno encontrado ou criado
        """
        if student_data.email:
            existing_student = self.__student_repository.get_by_email(db, student_data.email)
            if existing_student:
                self.__logger.debug(
                    "Aluno encontrado por email: %s",
                    student_data.email
                )
                return existing_student
        
        self.__logger.info("Criando novo aluno: %s", student_data.full_name)
        new_student = self.__student_repository.create(
            db,
            uuid=uuid4(),
            full_name=student_data.full_name,
            email=student_data.email
        )
        
        return new_student
