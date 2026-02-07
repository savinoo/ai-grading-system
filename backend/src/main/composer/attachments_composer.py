from src.models.repositories.attachments_repository import AttachmentsRepository

from src.services.attachments.upload_attachment_service import UploadAttachmentService
from src.services.attachments.manage_attachments_service import ManageAttachmentsService

from src.controllers.attachments.upload_attachment_controller import UploadAttachmentController
from src.controllers.attachments.get_attachments_by_exam_controller import GetAttachmentsByExamController
from src.controllers.attachments.get_attachment_by_uuid_controller import GetAttachmentByUuidController
from src.controllers.attachments.delete_attachment_controller import DeleteAttachmentController
from src.controllers.attachments.download_attachment_controller import DownloadAttachmentController


def make_upload_attachment_controller() -> UploadAttachmentController:
    """
    Factory para criar uma instância de UploadAttachmentController
    com suas dependências injetadas.
    
    Returns:
        UploadAttachmentController: Instância do controlador de upload de anexos
    """
    repository = AttachmentsRepository()
    service = UploadAttachmentService(repository)
    controller = UploadAttachmentController(service)

    return controller


def make_get_attachments_by_exam_controller() -> GetAttachmentsByExamController:
    """
    Factory para criar uma instância de GetAttachmentsByExamController
    com suas dependências injetadas.
    
    Returns:
        GetAttachmentsByExamController: Instância do controlador de listagem de anexos
    """
    repository = AttachmentsRepository()
    service = ManageAttachmentsService(repository)
    controller = GetAttachmentsByExamController(service)

    return controller


def make_get_attachment_by_uuid_controller() -> GetAttachmentByUuidController:
    """
    Factory para criar uma instância de GetAttachmentByUuidController
    com suas dependências injetadas.
    
    Returns:
        GetAttachmentByUuidController: Instância do controlador de busca de anexo
    """
    repository = AttachmentsRepository()
    service = ManageAttachmentsService(repository)
    controller = GetAttachmentByUuidController(service)

    return controller


def make_delete_attachment_controller() -> DeleteAttachmentController:
    """
    Factory para criar uma instância de DeleteAttachmentController
    com suas dependências injetadas.
    
    Returns:
        DeleteAttachmentController: Instância do controlador de deleção de anexos
    """
    repository = AttachmentsRepository()
    service = ManageAttachmentsService(repository)
    controller = DeleteAttachmentController(service)

    return controller


def make_download_attachment_controller() -> DownloadAttachmentController:
    """
    Factory para criar uma instância de DownloadAttachmentController
    com suas dependências injetadas.
    
    Returns:
        DownloadAttachmentController: Instância do controlador de download de anexos
    """
    repository = AttachmentsRepository()
    service = ManageAttachmentsService(repository)
    controller = DownloadAttachmentController(service)

    return controller
