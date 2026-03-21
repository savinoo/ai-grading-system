from src.models.repositories.exams_repository import ExamsRepository
from src.models.repositories.student_answer_repository import StudentAnswerRepository
from src.models.repositories.attachments_repository import AttachmentsRepository
from src.models.repositories.exam_question_repository import ExamQuestionRepository
from src.models.repositories.grading_criteria_repository import GradingCriteriaRepository
from src.models.repositories.exam_criteria_repository import ExamCriteriaRepository

from src.services.exams.create_exam_service import CreateExamService
from src.services.exams.get_exams_by_teacher_service import GetExamsByTeacherService
from src.services.exams.get_exam_by_uuid_service import GetExamByUuidService
from src.services.exams.update_exam_service import UpdateExamService
from src.services.exams.delete_exam_service import DeleteExamService
from src.services.exams.publish_exam_service import PublishExamService
from src.services.attachments.manage_attachments_service import ManageAttachmentsService
from src.services.rag.chunking_service import ChunkingService
from src.services.rag.indexing_service import IndexingService
from src.services.grading.grading_workflow_service import GradingWorkflowService

from src.controllers.exams.create_exam_controller import CreateExamController
from src.controllers.exams.get_exams_by_teacher_controller import GetExamsByTeacherController
from src.controllers.exams.get_exam_by_uuid_controller import GetExamByUuidController
from src.controllers.exams.update_exam_controller import UpdateExamController
from src.controllers.exams.delete_exam_controller import DeleteExamController
from src.controllers.exams.publish_exam_controller import PublishExamController

def make_create_exam_controller() -> CreateExamController:
    """
    Factory para criar uma instância de CreateExamController
    com suas dependências injetadas.
    
    Returns:
        CreateExamController: Instância do controlador de criação de provas
    """
    exam_repository = ExamsRepository()
    create_exam_service = CreateExamService(exam_repository)
    create_exam_controller = CreateExamController(create_exam_service)

    return create_exam_controller

def make_get_exams_by_teacher_controller() -> GetExamsByTeacherController:
    """
    Factory para criar uma instância de GetExamsByTeacherController
    com suas dependências injetadas.
    
    Returns:
        GetExamsByTeacherController: Instância do controlador de busca de provas por professor
    """
    exam_repository = ExamsRepository()
    get_exams_service = GetExamsByTeacherService(exam_repository)
    get_exams_controller = GetExamsByTeacherController(get_exams_service)

    return get_exams_controller

def make_get_exam_by_uuid_controller() -> GetExamByUuidController:
    """
    Factory para criar uma instância de GetExamByUuidController
    com suas dependências injetadas.
    
    Returns:
        GetExamByUuidController: Instância do controlador de busca de prova por UUID
    """
    exam_repository = ExamsRepository()
    get_exam_service = GetExamByUuidService(exam_repository)
    get_exam_controller = GetExamByUuidController(get_exam_service)

    return get_exam_controller

def make_update_exam_controller() -> UpdateExamController:
    """
    Factory para criar uma instância de UpdateExamController
    com suas dependências injetadas.
    
    Returns:
        UpdateExamController: Instância do controlador de atualização de provas
    """
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()

    update_exam_service = UpdateExamService(
        exam_repository,
        student_answer_repository
    )
    update_exam_controller = UpdateExamController(update_exam_service)

    return update_exam_controller

def make_delete_exam_controller() -> DeleteExamController:
    """
    Factory para criar uma instância de DeleteExamController
    com suas dependências injetadas.
    
    Returns:
        DeleteExamController: Instância do controlador de exclusão de provas
    """
    exam_repository = ExamsRepository()
    attachments_repository = AttachmentsRepository()
    
    # Cria o serviço de anexos para deletar arquivos físicos
    manage_attachments_service = ManageAttachmentsService(attachments_repository)
    
    # Cria o serviço de exclusão de provas com dependência de anexos
    delete_exam_service = DeleteExamService(exam_repository, manage_attachments_service)
    delete_exam_controller = DeleteExamController(delete_exam_service)

    return delete_exam_controller


def make_publish_exam_controller() -> PublishExamController:
    """
    Factory para criar uma instância de PublishExamController
    com suas dependências injetadas.
    
    Returns:
        PublishExamController: Instância do controlador de publicação de provas
    """
    # Repositórios
    exam_repository = ExamsRepository()
    attachments_repository = AttachmentsRepository()
    student_answer_repository = StudentAnswerRepository()
    exam_question_repository = ExamQuestionRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    exam_criteria_repository = ExamCriteriaRepository()
    
    # Serviços de RAG
    chunking_service = ChunkingService()
    indexing_service = IndexingService(attachments_repository)
    
    # Serviço de correção
    grading_service = GradingWorkflowService(
        student_answer_repository,
        exam_question_repository,
        grading_criteria_repository,
        exam_criteria_repository
    )
    
    # Serviço de publicação (com todas as dependências injetadas)
    publish_exam_service = PublishExamService(
        exam_repository,
        attachments_repository,
        exam_question_repository,
        student_answer_repository,
        chunking_service,
        indexing_service,
        grading_service
    )
    
    publish_exam_controller = PublishExamController(publish_exam_service)

    return publish_exam_controller
