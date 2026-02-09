"""
Serviço de publicação de provas.
Orquestra o fluxo completo: indexação de PDFs → correção automática.
"""

import logging
from uuid import UUID
from sqlalchemy.orm import Session

from src.models.repositories.exams_repository import ExamsRepository
from src.models.repositories.attachments_repository import AttachmentsRepository
from src.services.rag.chunking_service import ChunkingService
from src.services.rag.indexing_service import IndexingService
from src.services.grading.grading_workflow_service import GradingWorkflowService
from src.core.file_system_handler import FileSystemHandler

logger = logging.getLogger(__name__)


class PublishExamService:
    """
    Orquestra o fluxo de publicação (indexação + correção).
    
    Fluxo:
    1. Indexar PDFs (DRAFT → INDEXED, ou FAILED em erro)
    2. Executar correção automática (grade_exam)
    3. Atualizar status final (GRADED ou WARNING)
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o serviço de publicação.
        
        Args:
            db: Sessão SQLAlchemy ativa
        """
        self.db = db
        self.exam_repo = ExamsRepository()
        self.attachment_repo = AttachmentsRepository()
        self.chunking_service = ChunkingService()
        self.indexing_service = IndexingService(db)
        self.grading_service = GradingWorkflowService(db)
        self.fs_handler = FileSystemHandler()
    
    async def publish_exam(self, exam_uuid: UUID):
        """
        Fluxo completo de publicação (executado em background).
        
        Etapas:
        1. Buscar prova do DB
        2. Indexar attachments (DRAFT → INDEXED/FAILED)
        3. Chamar correção automática (grade_exam)
        4. Atualizar status final (GRADED/WARNING)
        
        Args:
            exam_uuid: UUID da prova a ser publicada
            
        Raises:
            Exception: Qualquer erro durante o processo (status → WARNING)
        """
        logger.info("🚀 Iniciando publicação da prova %s", exam_uuid)
        
        try:
            # === ETAPA 1: Buscar prova ===
            exam = self.exam_repo.get_by_uuid(self.db, exam_uuid)
            
            if not exam:
                raise ValueError(f"Prova {exam_uuid} não encontrada")
            
            logger.info(
                "📋 Prova encontrada: '%s' (status=%s)",
                exam.title, exam.status
            )
            
            # === ETAPA 2: Indexação de PDFs ===
            attachments = self.attachment_repo.get_by_exam_uuid(
                self.db,
                exam_uuid,
                vector_status='DRAFT'
            )
            
            if not attachments:
                logger.info("📄 Nenhum PDF para indexar. Prosseguindo para correção...")
            else:
                logger.info("📄 Encontrados %d PDFs para indexar", len(attachments))
                
                for attachment in attachments:
                    await self._index_attachment(
                        exam_uuid=exam_uuid,
                        attachment=attachment,
                        discipline=getattr(exam, 'discipline', 'Geral'),
                        topic=getattr(exam, 'topic', 'Geral')
                    )
            
            # === ETAPA 3: Correção automática ===
            logger.info("🤖 Iniciando correção automática...")
            result = await self.grading_service.grade_exam(exam_uuid)
            
            logger.info(
                "✅ Correção concluída: %d/%d respostas corrigidas",
                result['graded_answers'],
                result['total_answers']
            )
            
            # === ETAPA 4: Finalização ===
            if result['failed_answers'] > 0:
                logger.warning(
                    "⚠️ Algumas respostas falharam (%d). Status → WARNING",
                    result['failed_answers']
                )
                self.exam_repo.update_status_by_uuid(self.db, exam_uuid, 'WARNING')
            else:
                logger.info("🎉 Prova publicada e corrigida com sucesso! Status → GRADED")
                self.exam_repo.update_status_by_uuid(self.db, exam_uuid, 'GRADED')
            
            self.db.commit()
            
        except Exception as e:
            logger.error(
                "❌ Erro crítico na publicação da prova %s: %s",
                exam_uuid, str(e),
                exc_info=True
            )
            
            # Rollback + atualizar status para WARNING
            self.db.rollback()
            
            try:
                self.exam_repo.update_status_by_uuid(self.db, exam_uuid, 'WARNING')
                self.db.commit()
                logger.info("Status da prova atualizado para WARNING")
            except Exception as rollback_error:
                logger.error(
                    "Erro ao atualizar status para WARNING: %s",
                    rollback_error,
                    exc_info=True
                )
            
            raise
    
    async def _index_attachment(
        self,
        exam_uuid: UUID,
        attachment,
        discipline: str,
        topic: str
    ):
        """
        Indexa um único attachment (chunking + embedding + ChromaDB).
        
        Args:
            exam_uuid: UUID da prova
            attachment: Entidade Attachments do DB
            discipline: Disciplina da prova
            topic: Tópico da prova
            
        Raises:
            Exception: Se indexação falhar (status → FAILED + WARNING)
        """
        logger.info(
            "📑 Indexando attachment: %s (%s)",
            attachment.uuid, attachment.original_filename
        )
        
        try:
            # 1. Obter path do PDF no filesystem
            file_path = self.fs_handler.get_attachment_path(exam_uuid, attachment.uuid)
            
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {file_path}"
                )
            
            # 2. Chunking do PDF
            logger.debug("Executando chunking de %s", file_path)
            chunks = self.chunking_service.process_pdf(str(file_path))
            
            if not chunks:
                raise ValueError(f"Nenhum chunk gerado para {file_path}")
            
            logger.info("✂️ Gerados %d chunks do PDF", len(chunks))
            
            # 3. Indexação com metadados
            logger.debug("Indexando chunks no ChromaDB...")
            success = self.indexing_service.index_exam_material(
                chunks=chunks,
                exam_uuid=exam_uuid,
                attachment_uuid=attachment.uuid,
                discipline=discipline,
                topic=topic
            )
            
            if not success:
                raise Exception("IndexingService retornou False")
            
            logger.info("✅ Attachment %s indexado com sucesso", attachment.uuid)
            
        except Exception as e:
            logger.error(
                "❌ Falha na indexação do attachment %s: %s",
                attachment.uuid, str(e),
                exc_info=True
            )
            
            # Atualizar status do attachment para FAILED
            # (IndexingService já deve fazer isso, mas garantimos aqui)
            try:
                attachment_entity = self.attachment_repo.get_by_uuid(
                    self.db,
                    attachment.uuid
                )
                attachment_entity.vector_status = 'FAILED'
                self.db.flush()
            except Exception as update_error:
                logger.error(
                    "Erro ao atualizar status do attachment: %s",
                    update_error
                )
            
            # Abortar publicação inteira
            raise Exception(
                f"Indexação falhou para attachment {attachment.uuid}. "
                "Processo de publicação abortado."
            ) from e
