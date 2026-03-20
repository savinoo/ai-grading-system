from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.exams.update_exam_service_interface import UpdateExamServiceInterface
from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface

from src.domain.requests.exams.exam_update_request import ExamUpdateRequest
from src.domain.responses.exams.exam_response import ExamResponse

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.validate_error import ValidateError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class UpdateExamService(UpdateExamServiceInterface):
    """
    Serviço para atualização de provas.
    """

    def __init__(
        self,
        exam_repository: ExamsRepositoryInterface,
        student_answer_repository: StudentAnswerRepositoryInterface
    ) -> None:
        self.__exam_repository = exam_repository
        self.__student_answer_repository = student_answer_repository
        self.__logger = get_logger(__name__)

    async def update_exam(
        self,
        db: Session,
        exam_uuid: UUID,
        request: ExamUpdateRequest
    ) -> ExamResponse:
        """
        Atualiza uma prova.
        Apenas permite atualização se status = DRAFT.
        Para class_uuid, só permite se não houver respostas de alunos.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova a ser atualizada
            request: Dados a serem atualizados
            
        Returns:
            ExamResponse: Dados da prova atualizada
            
        Raises:
            NotFoundError: Se a prova não for encontrada
            ValidateError: Se a prova não estiver em status DRAFT ou se houver respostas
        """
        try:
            # Valida se pelo menos um campo foi fornecido
            if not request.has_any_field():
                raise ValidateError(
                    message="Nenhum campo fornecido para atualização",
                    context={"exam_uuid": str(exam_uuid)}
                )

            self.__logger.info("Atualizando prova: %s", exam_uuid)

            # Busca a prova
            exam = self.__exam_repository.get_by_uuid(db, exam_uuid)

            # Valida se a prova está em status DRAFT
            if exam.status != "DRAFT":
                raise ValidateError(
                    message="Apenas provas em status DRAFT podem ser editadas",
                    context={
                        "exam_uuid": str(exam_uuid),
                        "current_status": exam.status
                    }
                )

            # Se está tentando atualizar class_uuid, verifica se há respostas
            if request.class_uuid is not None:
                has_answers = self.__student_answer_repository.has_answers_for_exam(db, exam_uuid)
                if has_answers:
                    raise ValidateError(
                        message="Não é possível alterar a turma da prova pois já existem respostas de alunos",
                        context={"exam_uuid": str(exam_uuid)}
                    )

            # Prepara os campos para atualização
            updates = {}
            if request.title is not None:
                updates["title"] = request.title
            if request.description is not None:
                updates["description"] = request.description
            if request.class_uuid is not None:
                updates["class_uuid"] = request.class_uuid

            # Atualiza a prova
            updated_exam = self.__exam_repository.update(db, exam.id, **updates)

            self.__logger.info("Prova atualizada com sucesso: %s", exam_uuid)

            return ExamResponse.model_validate(updated_exam)

        except NoResultFound as e:
            self.__logger.warning("Prova não encontrada: %s", exam_uuid)
            raise NotFoundError(
                message="Prova não encontrada",
                context={"exam_uuid": str(exam_uuid)}
            ) from e
        except ValidateError:
            # Re-raise ValidateError sem wrapping
            raise
        except Exception as e:
            self.__logger.error("Erro ao atualizar prova: %s", str(e), exc_info=True)
            raise SqlError(
                message="Erro ao atualizar prova",
                context={"exam_uuid": str(exam_uuid)}
            ) from e
