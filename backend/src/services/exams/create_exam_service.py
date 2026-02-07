from __future__ import annotations

from uuid import uuid4, UUID

from sqlalchemy.orm import Session

from src.interfaces.services.exams.create_exam_service_interface import CreateExamServiceInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.domain.requests.exams.exam_create_request import ExamCreateRequest
from src.domain.responses.exams.exam_create_response import ExamCreateResponse

from src.models.entities.exams import Exams

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class CreateExamService(CreateExamServiceInterface):
    """
    Serviço para criação de provas.
    """

    def __init__(self, repository: ExamsRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)

    async def create_exam(
        self,
        db: Session,
        request: ExamCreateRequest,
        teacher_uuid: UUID
    ) -> ExamCreateResponse:
        """
        Cria uma nova prova.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da prova a ser criada
            teacher_uuid: UUID do professor que está criando a prova
            
        Returns:
            ExamCreateResponse: Dados da prova criada
        """
        try:
            self.__logger.info("Criando nova prova: %s", request.title)

            exam_obj = self.__repository.create(
                db,
                uuid=uuid4(),
                title=request.title,
                description=request.description,
                created_by=teacher_uuid,
                class_uuid=request.class_uuid,
                status=request.status,
                starts_at=request.starts_at,
                ends_at=request.ends_at
            )

            self.__logger.info("Prova criada com sucesso: %s", exam_obj.uuid)
            return self.__format_response(exam_obj)

        except Exception as e:
            self.__logger.error("Erro inesperado ao criar prova: %s", e)
            raise SqlError(
                message="Erro ao criar prova no banco de dados",
                context={"title": request.title},
                cause=e
            ) from e

    def __format_response(self, exam_obj: Exams) -> ExamCreateResponse:
        """
        Formata a resposta da prova criada.
        
        Args:
            exam_obj: Entidade Exams
            
        Returns:
            ExamCreateResponse: Resposta formatada
        """
        return ExamCreateResponse.model_validate(exam_obj)
