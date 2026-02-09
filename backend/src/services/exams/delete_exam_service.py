from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exams.delete_exam_service_interface import DeleteExamServiceInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface

from src.errors.domain.validate_error import ValidateError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class DeleteExamService(DeleteExamServiceInterface):
    """
    Serviço para deletar uma prova e todos os seus dados relacionados.
    """

    def __init__(self, repository: ExamsRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)

    async def delete_exam(
        self,
        db: Session,
        exam_uuid: UUID,
        teacher_uuid: UUID
    ) -> None:
        """
        Deleta uma prova e todos os seus dados relacionados.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova a ser deletada
            teacher_uuid: UUID do professor (para validação de permissão)
            
        Raises:
            ValidateError: Se a prova não for encontrada ou o professor não tiver permissão
            SqlError: Se houver erro ao deletar
        """
        try:
            self.__logger.info("Deletando prova: %s", exam_uuid)

            # Busca a prova para validar existência e permissão
            exam = self.__repository.get_by_uuid(db, exam_uuid)

            # Valida se o professor é o criador da prova
            if str(exam.created_by) != str(teacher_uuid):
                self.__logger.warning(
                    "Professor %s tentou deletar prova de outro professor: %s",
                    teacher_uuid,
                    exam_uuid
                )
                raise ValidateError(
                    message="Você não tem permissão para deletar esta prova",
                    context={
                        "exam_uuid": str(exam_uuid),
                        "teacher_uuid": str(teacher_uuid)
                    }
                )

            # Deleta a prova (cascade irá deletar os relacionados)
            self.__repository.delete(db, exam.id)
            db.commit()

            self.__logger.info("Prova deletada com sucesso: %s", exam_uuid)

        except NoResultFound as e:
            self.__logger.warning("Prova não encontrada para deletar: %s", exam_uuid)
            raise ValidateError(
                message="Prova não encontrada",
                context={"exam_uuid": str(exam_uuid)}
            ) from e
        except ValidateError:
            raise
        except Exception as e:
            self.__logger.error("Erro ao deletar prova: %s", str(e), exc_info=True)
            db.rollback()
            raise SqlError(
                message="Erro ao deletar prova",
                context={"exam_uuid": str(exam_uuid)}
            ) from e
