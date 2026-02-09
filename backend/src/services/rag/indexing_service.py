"""
Serviço de Indexação - Indexa chunks no ChromaDB com metadados enriquecidos.
Responsável por adicionar contexto de prova/disciplina e gerenciar status.
"""

import logging
from typing import List
from uuid import UUID
from langchain_core.documents import Document
from sqlalchemy.orm import Session

from src.core.vector_db_handler import get_vector_store
from src.models.repositories.attachments_repository import AttachmentsRepository

logger = logging.getLogger(__name__)


class IndexingService:
    """
    Indexa chunks no ChromaDB com metadados da prova.
    
    CRÍTICO: Adiciona exam_uuid a TODOS os chunks para garantir
    isolamento entre provas no retrieval.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o serviço de indexação.
        
        Args:
            db: Sessão do banco de dados para atualizar status
        """
        self.db = db
        self.vector_store = get_vector_store()
        self.attachment_repo = AttachmentsRepository()
        
        logger.debug("IndexingService inicializado")
    
    def index_exam_material(
        self,
        chunks: List[Document],
        exam_uuid: UUID,
        attachment_uuid: UUID,
        discipline: str,
        topic: str
    ) -> bool:
        """
        Indexa chunks com metadados enriquecidos.
        
        Fluxo:
        1. Enriquece chunks com metadados (exam_uuid, discipline, topic)
        2. Adiciona ao ChromaDB
        3. Atualiza status do attachment no DB
        
        Args:
            chunks: Lista de chunks do PDF (do ChunkingService)
            exam_uuid: UUID da prova (FILTRO PRINCIPAL RAG)
            attachment_uuid: UUID do anexo (para atualizar status)
            discipline: Disciplina (filtro secundário)
            topic: Tópico (metadado informativo)
        
        Returns:
            True se sucesso, False se erro
            
        Examples:
            >>> indexing = IndexingService(db)
            >>> success = indexing.index_exam_material(
            ...     chunks=chunks,
            ...     exam_uuid=UUID("..."),
            ...     attachment_uuid=UUID("..."),
            ...     discipline="Estrutura de Dados",
            ...     topic="Árvores Binárias"
            ... )
        """
        if not chunks:
            logger.warning("Lista de chunks vazia. Nada a indexar.")
            return False
        
        try:
            logger.info(
                "Indexando material da prova",
                extra={
                    "exam_uuid": str(exam_uuid),
                    "attachment_uuid": str(attachment_uuid),
                    "chunks_count": len(chunks),
                    "discipline": discipline,
                    "topic": topic
                }
            )
            
            # Enriquecer metadados (CRUCIAL para filtro RAG)
            for idx, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "exam_uuid": str(exam_uuid),        # CHAVE PRIMÁRIA para filtro
                    "discipline": discipline,           # Filtro secundário
                    "topic": topic,                     # Informativo
                    "attachment_uuid": str(attachment_uuid),
                    "chunk_index": idx                  # Para ordenação
                })
            
            logger.debug("Metadados enriquecidos em %d chunks", len(chunks))
            
            # Indexar no ChromaDB
            # add_documents retorna lista de IDs dos documentos adicionados
            vector_ids = self.vector_store.add_documents(chunks)
            
            logger.info(
                "Chunks indexados no ChromaDB",
                extra={
                    "vector_ids_count": len(vector_ids),
                    "exam_uuid": str(exam_uuid)
                }
            )
            
            # Atualizar status no DB
            self.attachment_repo.update_vector_status(
                db=self.db,
                uuid=attachment_uuid,
                vector_status="SUCCESS"
            )
            
            self.db.commit()  # Commit da transação
            
            logger.info(
                "Indexação concluída com sucesso",
                extra={
                    "exam_uuid": str(exam_uuid),
                    "vectors": len(vector_ids)
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Erro ao indexar material da prova %s: %s",
                exam_uuid,
                str(e),
                exc_info=True
            )
            
            # Rollback da transação
            self.db.rollback()
            
            # Marcar como falha no DB
            try:
                self.attachment_repo.update_vector_status(
                    db=self.db,
                    uuid=attachment_uuid,
                    vector_status="FAILED"
                )
                self.db.commit()
            except Exception as update_error:
                logger.error(
                    "Erro ao atualizar status de falha: %s",
                    str(update_error)
                )
                self.db.rollback()
            
            return False
    
    def index_multiple_attachments(
        self,
        attachments_data: List[dict]
    ) -> dict:
        """
        Indexa múltiplos anexos em batch.
        
        Args:
            attachments_data: Lista de dicts com:
                - chunks: List[Document]
                - exam_uuid: UUID
                - attachment_uuid: UUID
                - discipline: str
                - topic: str
        
        Returns:
            Dict com estatísticas:
                - total: int
                - success: int
                - failed: int
                - failed_uuids: List[UUID]
        """
        results = {
            "total": len(attachments_data),
            "success": 0,
            "failed": 0,
            "failed_uuids": []
        }
        
        for data in attachments_data:
            success = self.index_exam_material(
                chunks=data["chunks"],
                exam_uuid=data["exam_uuid"],
                attachment_uuid=data["attachment_uuid"],
                discipline=data["discipline"],
                topic=data["topic"]
            )
            
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["failed_uuids"].append(data["attachment_uuid"])
        
        logger.info(
            "Batch indexing concluído: %d/%d sucesso",
            results["success"],
            results["total"]
        )
        
        return results
    
    def delete_exam_vectors(self, exam_uuid: UUID) -> bool:
        """
        Remove todos os vetores associados a uma prova.
        Útil ao deletar/reprocessar uma prova.
        
        Args:
            exam_uuid: UUID da prova
            
        Returns:
            True se sucesso, False se erro
        """
        try:
            logger.info("Removendo vetores da prova %s", exam_uuid)
            
            # ChromaDB delete com filtro
            self.vector_store.delete(
                filter={"exam_uuid": {"$eq": str(exam_uuid)}}
            )
            
            logger.info("Vetores da prova %s removidos", exam_uuid)
            return True
            
        except Exception as e:
            logger.error(
                "Erro ao remover vetores da prova %s: %s",
                exam_uuid,
                str(e),
                exc_info=True
            )
            return False
