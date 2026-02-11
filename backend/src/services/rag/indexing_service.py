from __future__ import annotations

from typing import List
from uuid import UUID

from langchain_core.documents import Document
from sqlalchemy.orm import Session

from src.core.vector_db_handler import get_vector_store
from src.core.logging_config import get_logger

from src.interfaces.services.rag.indexing_service_interface import IndexingServiceInterface
from src.interfaces.repositories.attachments_repository_interfaces import AttachmentsRepositoryInterface

from src.errors.domain.sql_error import SqlError

class IndexingService(IndexingServiceInterface):
    """
    Serviço para indexação de chunks no ChromaDB com metadados da prova.
    
    CRÍTICO: Adiciona exam_uuid a TODOS os chunks para garantir
    isolamento entre provas no retrieval.
    """
    
    def __init__(self, attachment_repository: AttachmentsRepositoryInterface) -> None:
        """
        Inicializa o serviço de indexação.
        
        Args:
            attachment_repository: Repositório de anexos para atualizar status
        """
        self.__attachment_repository = attachment_repository
        self.__vector_store = get_vector_store()
        self.__logger = get_logger(__name__)
    
    async def index_exam_material(
        self,
        db: Session,
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
            db: Sessão do banco de dados
            chunks: Lista de chunks do PDF (do ChunkingService)
            exam_uuid: UUID da prova (FILTRO PRINCIPAL RAG)
            attachment_uuid: UUID do anexo (para atualizar status)
            discipline: Disciplina (filtro secundário)
            topic: Tópico (metadado informativo)
        
        Returns:
            True se sucesso, False se erro
            
        Examples:
            >>> indexing = IndexingService(attachment_repo)
            >>> success = indexing.index_exam_material(
            ...     db=db,
            ...     chunks=chunks,
            ...     exam_uuid=UUID("..."),
            ...     attachment_uuid=UUID("..."),
            ...     discipline="Estrutura de Dados",
            ...     topic="Árvores Binárias"
            ... )
        """
        if not chunks:
            self.__logger.warning("Lista de chunks vazia. Nada a indexar.")
            return False
        
        try:
            self.__logger.info(
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
            
            self.__logger.debug("Metadados enriquecidos em %d chunks", len(chunks))
            
            # Indexar no ChromaDB
            # add_documents retorna lista de IDs dos documentos adicionados
            vector_ids = self.__vector_store.add_documents(chunks)
            
            self.__logger.info(
                "Chunks indexados no ChromaDB",
                extra={
                    "vector_ids_count": len(vector_ids),
                    "exam_uuid": str(exam_uuid)
                }
            )
            
            # Atualizar status no DB
            self.__attachment_repository.update_vector_status(
                db=db,
                uuid=attachment_uuid,
                vector_status="SUCCESS"
            )
            
            db.commit()  # Commit da transação
            
            self.__logger.info(
                "Indexação concluída com sucesso",
                extra={
                    "exam_uuid": str(exam_uuid),
                    "vectors": len(vector_ids)
                }
            )
            
            return True
            
        except Exception as e:
            self.__logger.error(
                "Erro ao indexar material da prova: %s",
                str(e),
                exc_info=True
            )
            
            # Rollback da transação
            db.rollback()
            
            # Marcar como falha no DB
            try:
                self.__attachment_repository.update_vector_status(
                    db=db,
                    uuid=attachment_uuid,
                    vector_status="FAILED"
                )
                db.commit()
            except Exception as update_error:
                self.__logger.error(
                    "Erro ao atualizar status de falha: %s",
                    str(update_error)
                )
                db.rollback()
            
            raise SqlError(
                message="Erro ao indexar material da prova",
                context={
                    "exam_uuid": str(exam_uuid),
                    "attachment_uuid": str(attachment_uuid)
                },
                cause=e
            ) from e
    
    async def _index_multiple_attachments(
        self,
        db: Session,
        attachments_data: List[dict]
    ) -> dict:
        """
        Indexa múltiplos anexos em batch.
        
        Args:
            db: Sessão do banco de dados
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
            try:
                await self.index_exam_material(
                    db=db,
                    chunks=data["chunks"],
                    exam_uuid=data["exam_uuid"],
                    attachment_uuid=data["attachment_uuid"],
                    discipline=data["discipline"],
                    topic=data["topic"]
                )
                results["success"] += 1
            except Exception:
                results["failed"] += 1
                results["failed_uuids"].append(data["attachment_uuid"])
        
        self.__logger.info(
            "Batch indexing concluído: %d/%d sucesso",
            results["success"],
            results["total"]
        )
        
        return results
    
    async def _delete_exam_vectors(self, exam_uuid: UUID) -> bool:
        """
        Remove todos os vetores associados a uma prova.
        Útil ao deletar/reprocessar uma prova.
        
        Args:
            exam_uuid: UUID da prova
            
        Returns:
            True se sucesso, False se erro
        """
        try:
            self.__logger.info("Removendo vetores da prova %s", exam_uuid)
            
            # ChromaDB delete com filtro
            self.__vector_store.delete(
                filter={"exam_uuid": {"$eq": str(exam_uuid)}}
            )
            
            self.__logger.info("Vetores da prova %s removidos", exam_uuid)
            return True
            
        except Exception as e:
            self.__logger.error(
                "Erro ao remover vetores da prova %s: %s",
                exam_uuid,
                str(e),
                exc_info=True
            )
            return False
