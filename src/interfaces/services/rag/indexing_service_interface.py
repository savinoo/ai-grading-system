from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from langchain_core.documents import Document
from sqlalchemy.orm import Session

class IndexingServiceInterface(ABC):
    """
    Interface para o serviço de indexação de chunks no ChromaDB.
    """
    
    @abstractmethod
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
        
        Args:
            db: Sessão do banco de dados
            chunks: Lista de chunks do PDF (do ChunkingService)
            exam_uuid: UUID da prova (FILTRO PRINCIPAL RAG)
            attachment_uuid: UUID do anexo (para atualizar status)
            discipline: Disciplina (filtro secundário)
            topic: Tópico (metadado informativo)
        
        Returns:
            True se sucesso, False se erro
        """
        raise NotImplementedError()
