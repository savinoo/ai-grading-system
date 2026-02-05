# src/rag/retriever.py
from typing import List
from src.infrastructure.vector_db import get_vector_store
from src.domain.schemas import RetrievedContext
from src.utils.helpers import measure_time

import logging

logger = logging.getLogger(__name__)

def search_context(query: str, discipline: str, topic: str, k: int = 4) -> List[RetrievedContext]:
    """
    Executa a busca RAG com 'Metadata Filtering' (TCC Seção 2.2).
    
    Args:
        query: O texto da questão ou resposta do aluno.
        discipline: Filtro rígido de disciplina.
        topic: Filtro rígido de tópico (Ignorado na busca semântica para aumentar recall).
    
    Returns:
        Lista de contextos estruturados para o LLM.
    """
    with measure_time("RAG Retrieval (Similarity Search)"):
        vector_store = get_vector_store()
        
        logger.info(f"RAG Search: Query='{query[:50]}...' | Discipline='{discipline}' | Topic='{topic}'")
        
        # Filtro de Metadados: 
        # O usuário solicitou que o match seja pela PERGUNTA (semântico) e não pelo Tópico (metadado rígido).
        # Mantemos apenas o filtro de Disciplina para evitar colisão entre matérias distintas.
        
        # 1. Busca por Disciplina (Ignorando Tópico)
        search_kwargs = {
            "k": k,
            "filter": {"discipline": {"$eq": discipline}}
        }
        
        # Busca por similaridade usando score bruto (distância) para evitar filtragem silenciosa
        # O Chroma retorna distância L2 (menor é melhor) por padrão
        results_with_score = vector_store.similarity_search_with_score(
            query, 
            **search_kwargs
        )
        
        docs = []
        for doc, distance in results_with_score:
            # Converte distância em relevância (0 a 1)
            score = 1.0 / (1.0 + distance)
            docs.append((doc, score))
            
        # 2. Fallback Final: Busca Global (sem filtros)
        if not docs:
            logger.warning(f"RAG: Nenhum documento encontrado para disciplina '{discipline}'. Tentando busca global.")
            search_kwargs = {"k": k} # Remove filters
            results_with_score = vector_store.similarity_search_with_score(query, **search_kwargs)
            for doc, distance in results_with_score:
                score = 1.0 / (1.0 + distance)
                docs.append((doc, score))
        
        logger.info(f"RAG Results: Found {len(docs)} documents.")
        
        results = []
        for doc, score in docs:
            results.append(RetrievedContext(
                content=doc.page_content,
                source_document=doc.metadata.get("source", "unknown"),
                page_number=doc.metadata.get("page", 0),
                relevance_score=score
            ))
        
        if not results:
            logger.warning("No relevant context found after filtering and thresholding.")
            
        return results
