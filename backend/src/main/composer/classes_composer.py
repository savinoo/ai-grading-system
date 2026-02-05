from src.models.repositories.classes_repository import ClassesRepository
from src.models.repositories.class_student_repository import ClassStudentRepository
from src.models.repositories.student_repository import StudentRepository

from src.services.classes.create_class_service import CreateClassService
from src.services.classes.add_students_to_class_service import AddStudentsToClassService
from src.services.classes.get_class_with_students_service import GetClassWithStudentsService
from src.services.classes.get_classes_service import GetClassesService
from src.services.classes.remove_student_from_class_service import RemoveStudentFromClassService
from src.services.classes.deactivate_class_service import DeactivateClassService

from src.controllers.classes.create_class_controller import CreateClassController
from src.controllers.classes.add_students_to_class_controller import AddStudentsToClassController
from src.controllers.classes.get_class_with_students_controller import GetClassWithStudentsController
from src.controllers.classes.get_classes_service_controller import GetClassesServiceController
from src.controllers.classes.remove_student_from_class_controller import RemoveStudentFromClassController
from src.controllers.classes.deactivate_class_controller import DeactivateClassController

def make_create_class_controller() -> CreateClassController:
    """
    Factory para criar uma instância de CreateClassController
    com suas dependências injetadas.
    
    Returns:
        CreateClassController: Instância do controlador de criação de turmas
    """
    class_repository = ClassesRepository()
    create_class_service = CreateClassService(class_repository)
    create_class_controller = CreateClassController(create_class_service)
    
    return create_class_controller

def make_add_students_to_class_controller() -> AddStudentsToClassController:
    """
    Factory para criar uma instância de AddStudentsToClassController
    com suas dependências injetadas.
    
    Returns:
        AddStudentsToClassController: Instância do controlador de adição de alunos
    """
    student_repository = StudentRepository()
    class_student_repository = ClassStudentRepository()
    class_repository = ClassesRepository()
    
    add_students_service = AddStudentsToClassService(
        student_repository,
        class_student_repository,
        class_repository
    )
    add_students_controller = AddStudentsToClassController(add_students_service)
    
    return add_students_controller

def make_get_class_with_students_controller() -> GetClassWithStudentsController:
    """
    Factory para criar uma instância de GetClassWithStudentsController
    com suas dependências injetadas.
    
    Returns:
        GetClassWithStudentsController: Instância do controlador de busca de turma com alunos
    """
    class_repository = ClassesRepository()
    class_student_repository = ClassStudentRepository()
    student_repository = StudentRepository()
    
    get_class_service = GetClassWithStudentsService(
        class_repository,
        class_student_repository,
        student_repository
    )
    get_class_controller = GetClassWithStudentsController(get_class_service)
    
    return get_class_controller

def make_get_classes_service_controller() -> GetClassesServiceController:
    """
    Factory para criar uma instância de GetClassesServiceController
    com suas dependências injetadas.
    
    Returns:
        GetClassesServiceController: Instância do controlador de busca de turmas
    """
    class_repository = ClassesRepository()
    
    get_classes_service = GetClassesService(class_repository)
    get_classes_controller = GetClassesServiceController(get_classes_service)
    
    return get_classes_controller

def make_remove_student_from_class_controller() -> RemoveStudentFromClassController:
    """
    Factory para criar uma instância de RemoveStudentFromClassController
    com suas dependências injetadas.
    
    Returns:
        RemoveStudentFromClassController: Instância do controlador de remoção de alunos
    """
    class_student_repository = ClassStudentRepository()
    class_repository = ClassesRepository()
    student_repository = StudentRepository()
    
    remove_student_service = RemoveStudentFromClassService(
        class_student_repository,
        class_repository,
        student_repository
    )
    remove_student_controller = RemoveStudentFromClassController(remove_student_service)
    
    return remove_student_controller

def make_deactivate_class_controller() -> DeactivateClassController:
    """
    Factory para criar uma instância de DeactivateClassController
    com suas dependências injetadas.
    
    Returns:
        DeactivateClassController: Instância do controlador de desativação de turmas
    """
    class_repository = ClassesRepository()
    deactivate_class_service = DeactivateClassService(class_repository)
    deactivate_class_controller = DeactivateClassController(deactivate_class_service)
    
    return deactivate_class_controller
