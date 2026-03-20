from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.ai.rag_schemas import RetrievedContext

class RetrievalServiceInterface(ABC):
    """
    Interface para o serviço de busca semântica com filtros de metadados.
    """
    
    @abstractmethod
    async def search_context(
        self,
        query: str,
        exam_uuid: UUID,
        discipline: str,
        topic: Optional[str] = None,
        k: Optional[int] = None,
        min_relevance: float = 0.0
    ) -> List[RetrievedContext]:
        """
        Busca RAG com filtros rígidos.
        
        Args:
            query: Texto da questão ou resposta do aluno
            exam_uuid: FILTRO OBRIGATÓRIO (garante isolamento entre provas)
            discipline: FILTRO OBRIGATÓRIO (garante contexto relevante)
            topic: Informativo (não filtra, apenas metadado)
            k: Top-K resultados
            min_relevance: Score mínimo para incluir resultado (0.0 a 1.0)
        
        Returns:
            Lista de contextos relevantes ordenados por score
        """
        raise NotImplementedError()
