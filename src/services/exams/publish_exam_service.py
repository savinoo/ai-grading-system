"""
Serviço de publicação de provas.
Orquestra o fluxo completo: indexação de PDFs → correção automática.
"""

from __future__ import annotations

from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.attachments_repository_interfaces import AttachmentsRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface

from src.interfaces.services.exams.publish_exam_service_interface import PublishExamServiceInterface
from src.interfaces.services.rag.chunking_service_interface import ChunkingServiceInterface
from src.interfaces.services.rag.indexing_service_interface import IndexingServiceInterface
from src.interfaces.services.grading.grading_workflow_service_interface import GradingWorkflowServiceInterface

from src.domain.responses.exams.publish_exam_response import PublishExamResponse
from src.domain.ai.schemas import StudentAnswer

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.validate_error import ValidateError

from src.core.file_system_handler import FileSystemHandler
from src.core.logging_config import get_logger

from src.main.dependencies.get_db_session import get_db

class PublishExamService(PublishExamServiceInterface):
    """
    Orquestra o fluxo de publicação (indexação + correção).
    
    Fluxo:
    1. Validar prova (existe e está em DRAFT)
    2. Atualizar status para PUBLISHED
    3. Agendar background task para indexação + correção
    """
    
    def __init__(
        self,
        exam_repository: ExamsRepositoryInterface,
        attachment_repository: AttachmentsRepositoryInterface,
        exam_question_repository: ExamQuestionRepositoryInterface,
        student_answer_repository: StudentAnswerRepositoryInterface,
        chunking_service: ChunkingServiceInterface,
        indexing_service: IndexingServiceInterface,
        grading_service: GradingWorkflowServiceInterface
    ) -> None:
        """
        Inicializa o serviço de publicação.
        
        Args:
            exam_repository: Repositório de provas
            attachment_repository: Repositório de anexos
            exam_question_repository: Repositório de questões
            student_answer_repository: Repositório de respostas de alunos
            chunking_service: Serviço de chunking de PDFs
            indexing_service: Serviço de indexação de vetores
            grading_service: Serviço de workflow de correção automática
        """
        self.__exam_repo = exam_repository
        self.__attachment_repo = attachment_repository
        self.__exam_question_repo = exam_question_repository
        self.__student_answer_repo = student_answer_repository
        self.__chunking_service = chunking_service
        self.__indexing_service = indexing_service
        self.__grading_service = grading_service
        
        self.__logger = get_logger("services")
    
    async def publish_exam(
        self,
        db: Session,
        exam_uuid: UUID,
        background_tasks: BackgroundTasks
    ) -> PublishExamResponse:
        """
        Publica uma prova e agenda processamento em background.
        
        Etapas síncronas:
        1. Buscar prova do DB
        2. Validar que está em DRAFT
        3. Atualizar status para PUBLISHED
        4. Agendar background task
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova a ser publicada
            background_tasks: FastAPI BackgroundTasks para processamento assíncrono
            
        Returns:
            PublishExamResponse: Resposta com detalhes da publicação
            
        Raises:
            NotFoundError: Se prova não existir
            ValidationError: Se prova não estiver em DRAFT
        """
        self.__logger.info("📥 Iniciando publicação da prova %s", exam_uuid)
        
        # === ETAPA 1: Buscar prova ===
        exam = self.__exam_repo.get_by_uuid(db, exam_uuid)
        
        if not exam:
            self.__logger.warning("❌ Prova não encontrada: %s", exam_uuid)
            raise NotFoundError(
                message=f"Prova {exam_uuid} não encontrada",
                context={"exam_uuid": str(exam_uuid)}
            )
        
        self.__logger.info(
            "📋 Prova encontrada: '%s' (status=%s)",
            exam.title, exam.status
        )
        
        # === ETAPA 2: Validar status ===
        if exam.status != 'DRAFT':
            self.__logger.warning(
                "❌ Tentativa de publicar prova com status inválido: %s (atual=%s)",
                exam_uuid, exam.status
            )
            raise ValidateError(
                message=f"Não é possível publicar prova com status '{exam.status}'",
                context={"exam_uuid": str(exam_uuid), "current_status": exam.status}
            )
        
        # === ETAPA 2.5: Validar dados da prova (questões e respostas) ===
        self._validate_exam_data(db, exam_uuid)
        
        # === ETAPA 3: Atualizar status para PUBLISHED ===
        self.__exam_repo.update_status_by_uuid(db, exam_uuid, 'PUBLISHED')
        db.commit()
        
        self.__logger.info("✅ Status da prova %s atualizado para PUBLISHED", exam_uuid)
        
        # === ETAPA 4: Agendar background task ===
        background_tasks.add_task(
            self._background_process_exam,
            exam_uuid
        )
        
        self.__logger.info(
            "🚀 Background task agendada para prova %s. "
            "Indexação e correção serão executadas assincronamente.",
            exam_uuid
        )
        
        # === ETAPA 5: Retornar resposta ===
        return PublishExamResponse(
            message=(
                "Prova publicada com sucesso. "
                "O processamento de indexação e correção foi iniciado em background."
            ),
            exam_uuid=str(exam_uuid),
            status="PUBLISHED",
            next_steps=[
                "Os PDFs estão sendo indexados no sistema de vetorização",
                "Após indexação, a correção automática será executada",
                "Acompanhe o status da prova para verificar conclusão"
            ]
        )
    
    def _validate_exam_data(self, db: Session, exam_uuid: UUID) -> None:
        """
        Valida os dados da prova antes de publicar.
        
        Verifica:
        1. Se há pelo menos uma questão na prova
        2. Se todas as respostas dos alunos são válidas (não vazias)
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova a ser validada
            
        Raises:
            ValidateError: Se houver dados inválidos
        """
        self.__logger.info("🔍 Validando dados da prova %s antes de publicar...", exam_uuid)
        
        # Buscar todas as questões da prova
        questions = self.__exam_question_repo.get_by_exam(db, exam_uuid, active_only=True)
        
        if not questions:
            self.__logger.warning("❌ Prova sem questões: %s", exam_uuid)
            raise ValidateError(
                message="Não é possível publicar prova sem questões",
                context={"exam_uuid": str(exam_uuid)}
            )
        
        self.__logger.info("✓ Prova possui %d questão(ões)", len(questions))
        
        # Validar respostas de cada questão
        invalid_answers = []
        
        for question in questions:
            # Buscar todas as respostas desta questão
            answers = self.__student_answer_repo.get_by_question(
                db,
                question.uuid,
                limit=1000
            )
            
            if not answers:
                self.__logger.info("⚠️ Questão %s não possui respostas ainda", question.uuid)
                continue
            
            # Tentar validar cada resposta usando o schema Pydantic
            for answer_entity in answers:
                try:
                    # Tentar criar o schema - vai falhar se a resposta for inválida
                    StudentAnswer(
                        id=answer_entity.uuid,
                        student_id=answer_entity.student_uuid,
                        question_id=answer_entity.question_uuid,
                        text=answer_entity.answer or ""
                    )
                except Exception as e:
                    # Se falhar a validação, registrar o erro
                    invalid_answers.append({
                        "answer_uuid": str(answer_entity.uuid),
                        "student_uuid": str(answer_entity.student_uuid),
                        "question_uuid": str(answer_entity.question_uuid),
                        "error": str(e)
                    })
        
        # Se houver respostas inválidas, impedir a publicação
        if invalid_answers:
            self.__logger.warning(
                "❌ Encontradas %d resposta(s) inválida(s): %s",
                len(invalid_answers),
                invalid_answers
            )
            
            error_details = []
            for invalid in invalid_answers:
                error_details.append(
                    f"Aluno {invalid['student_uuid'][:8]}... tem resposta vazia ou inválida"
                )
            
            raise ValidateError(
                message=(
                    f"Não é possível publicar prova com {len(invalid_answers)} "
                    f"resposta(s) vazia(s) ou inválida(s). "
                    f"Por favor, peça aos alunos para preencher suas respostas antes de publicar."
                ),
                context={
                    "exam_uuid": str(exam_uuid),
                    "invalid_count": len(invalid_answers),
                    "details": error_details[:5]  # Limitar a 5 exemplos
                }
            )
        
        self.__logger.info("✅ Validação concluída: todos os dados estão válidos")
    
    async def _background_process_exam(self, exam_uuid: UUID):
        """
        Fluxo completo de processamento em background.
        
        Etapas:
        1. Buscar prova do DB
        2. Indexar attachments (DRAFT → INDEXED/FAILED)
        3. Chamar correção automática (grade_exam)
        4. Atualizar status final (GRADED/WARNING)
        
        Args:
            exam_uuid: UUID da prova a ser processada
        """
        
        
        self.__logger.info("🚀 Iniciando processamento em background da prova %s", exam_uuid)
        
        db = next(get_db())
        
        try:
            # === ETAPA 1: Buscar prova ===
            exam = self.__exam_repo.get_by_uuid(db, exam_uuid)
            
            if not exam:
                raise ValueError(f"Prova {exam_uuid} não encontrada")
            
            # === ETAPA 2: Indexação de PDFs ===
            attachments = self.__attachment_repo.get_by_exam_uuid(
                db,
                exam_uuid,
                vector_status='DRAFT'
            )
            
            if not attachments:
                self.__logger.info("📄 Nenhum PDF para indexar. Prosseguindo para correção...")
            else:
                self.__logger.info("📄 Encontrados %d PDFs para indexar", len(attachments))
                                
                for attachment in attachments:
                    # Usar class_name se disponível, caso contrário "Geral"
                    discipline = getattr(exam, 'class_name', None) or "Geral"
                    
                    await self.__index_attachment(
                        db=db,
                        exam_uuid=exam_uuid,
                        attachment=attachment,
                        discipline=discipline,
                        topic=exam.description or "Sem tópico"
                    )
            
            # === ETAPA 3: Correção automática ===
            self.__logger.info("🤖 Iniciando correção automática...")
            result = await self.__grading_service.grade_exam(db, exam_uuid)
            
            self.__logger.info(
                "✅ Correção concluída: %d/%d respostas corrigidas",
                result['graded_answers'],
                result['total_answers']
            )
            
            # === ETAPA 4: Finalização ===
            if result['failed_answers'] > 0:
                self.__logger.warning(
                    "⚠️ Algumas respostas falharam (%d). Status → WARNING",
                    result['failed_answers']
                )
                self.__exam_repo.update_status_by_uuid(db, exam_uuid, 'WARNING')
            else:
                self.__logger.info("🎉 Prova publicada e corrigida com sucesso! Status → GRADED")
                self.__exam_repo.update_status_by_uuid(db, exam_uuid, 'GRADED')
            
            db.commit()
            
        except Exception as e:
            self.__logger.error(
                "❌ Erro crítico no processamento da prova %s: %s",
                exam_uuid, str(e),
                exc_info=True
            )
            
            # Rollback + atualizar status para WARNING
            db.rollback()
            
            try:
                self.__exam_repo.update_status_by_uuid(db, exam_uuid, 'WARNING')
                db.commit()
                self.__logger.info("Status da prova atualizado para WARNING")
            except Exception as rollback_error:
                self.__logger.error(
                    "Erro ao atualizar status para WARNING: %s",
                    rollback_error,
                    exc_info=True
                )
        finally:
            db.close()
    
    async def __index_attachment(
        self,
        db: Session,
        exam_uuid: UUID,
        attachment,
        discipline: str,
        topic: str
    ) -> None:
        """
        Indexa um único attachment (chunking + embedding + ChromaDB).
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            attachment: Entidade Attachments do DB
            discipline: Disciplina da prova
            topic: Tópico da prova
            
        Raises:
            Exception: Se indexação falhar (status → FAILED + WARNING)
        """
        self.__logger.info(
            "📑 Indexando attachment: %s (%s)",
            attachment.uuid, attachment.original_filename
        )
        
        try:
            # 1. Obter path do PDF no filesystem
            fs_handler = FileSystemHandler()
            file_path = fs_handler.get_attachment_path(exam_uuid, attachment.uuid)
            
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {file_path}"
                )
            
            # 2. Chunking do PDF
            self.__logger.debug("Executando chunking de %s", file_path)
            chunks = await self.__chunking_service.process_pdf(str(file_path))
            
            if not chunks:
                raise ValueError(f"Nenhum chunk gerado para {file_path}")
            
            self.__logger.info("✂️ Gerados %d chunks do PDF", len(chunks))
            
            # 3. Indexação com metadados
            self.__logger.debug("Indexando chunks no ChromaDB...")
            success = await self.__indexing_service.index_exam_material(
                db=db,
                chunks=chunks,
                exam_uuid=exam_uuid,
                attachment_uuid=attachment.uuid,
                discipline=discipline,
                topic=topic
            )
            
            if not success:
                raise Exception("IndexingService retornou False")
            
            self.__logger.info("✅ Attachment %s indexado com sucesso", attachment.uuid)
            
        except Exception as e:
            self.__logger.error(
                "❌ Falha na indexação do attachment %s: %s",
                attachment.uuid, str(e),
                exc_info=True
            )
            
            # Atualizar status do attachment para FAILED
            # (IndexingService já deve fazer isso, mas garantimos aqui)
            try:
                attachment.vector_status = 'FAILED'
                attachment.updated_at = datetime.utcnow()
                db.flush()
                db.commit()
            except Exception as update_error:
                self.__logger.error(
                    "Erro ao atualizar status do attachment para FAILED: %s",
                    update_error
                )
            
            # Abortar publicação inteira
            raise Exception(
                f"Indexação falhou para attachment {attachment.uuid}. "
                "Processo de publicação abortado."
            ) from e
