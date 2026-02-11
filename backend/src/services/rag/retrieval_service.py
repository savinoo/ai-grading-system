from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.interfaces.services.rag.retrieval_service_interface import RetrievalServiceInterface

from src.core.vector_db_handler import get_vector_store
from src.core.logging_config import get_logger
from src.core.settings import settings

from src.domain.ai.rag_schemas import RetrievedContext

from src.errors.domain.sql_error import SqlError


class RetrievalService(RetrievalServiceInterface):
    """
    Serviço de busca semântica com filtros rígidos de metadados.
    
    CRÍTICO: SEMPRE filtra por exam_uuid para garantir isolamento
    entre provas (RAG de uma prova NÃO retorna material de outra).
    """
    
    def __init__(self) -> None:
        """Inicializa o serviço de retrieval."""
        self.__vector_store = get_vector_store()
        self.__logger = get_logger(__name__)
    
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
        
        Garante que:
        1. Apenas chunks da prova especificada são retornados
        2. Disciplina corresponde exatamente
        3. Tópico é informativo (não filtra)
        
        Args:
            query: Texto da questão ou resposta do aluno
            exam_uuid: FILTRO OBRIGATÓRIO (garante isolamento entre provas)
            discipline: FILTRO OBRIGATÓRIO (garante contexto relevante)
            topic: Informativo (não filtra, apenas metadado)
            k: Top-K resultados (padrão: settings.RAG_TOP_K)
            min_relevance: Score mínimo para incluir resultado (0.0 a 1.0)
        
        Returns:
            Lista de contextos relevantes ordenados por score
            
        Examples:
            >>> retrieval = RetrievalService()
            >>> contexts = retrieval.search_context(
            ...     query="árvore binária de busca propriedades",
            ...     exam_uuid=UUID("..."),
            ...     discipline="Estrutura de Dados",
            ...     k=4
            ... )
            >>> len(contexts)
            4
            >>> contexts[0].relevance_score
            0.87
        """
        k = k or settings.RAG_TOP_K
        
        self.__logger.info(
            "RAG Query",
            extra={
                "exam_uuid": str(exam_uuid),
                "discipline": discipline,
                "topic": topic,
                "k": k,
                "query_length": len(query)
            }
        )
        
        # Validação de entrada
        if not query.strip():
            self.__logger.warning("Query vazia recebida")
            return []
        
        # Filtros de metadados (ChromaDB where clause)
        metadata_filter = {
            "$and": [
                {"exam_uuid": {"$eq": str(exam_uuid)}},
                {"discipline": {"$eq": discipline}}
            ]
        }
        
        try:
            # Busca com score (distância L2)
            results_with_score = self.__vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=metadata_filter
            )
            
            self.__logger.debug(
                "ChromaDB retornou %d resultados antes de filtro de score",
                len(results_with_score)
            )
            
            # Converter para schema e aplicar filtro de relevância
            contexts = []
            for doc, distance in results_with_score:
                # Normalizar distância L2 para score 0-1
                # Distância menor = maior similaridade
                score = 1.0 / (1.0 + distance)
                
                # Filtrar por score mínimo
                if score < min_relevance:
                    self.__logger.debug(
                        "Chunk filtrado por score baixo: %.4f < %.4f",
                        score,
                        min_relevance
                    )
                    continue
                
                contexts.append(RetrievedContext(
                    content=doc.page_content,
                    source_document=doc.metadata.get("source", "unknown"),
                    page_number=doc.metadata.get("page"),
                    relevance_score=score,
                    discipline=doc.metadata.get("discipline", discipline),
                    topic=doc.metadata.get("topic", topic or ""),
                    chunk_index=doc.metadata.get("chunk_index")
                ))
            
            # Ordenar por relevância (descendente)
            contexts.sort(key=lambda x: x.relevance_score, reverse=True)
            
            self.__logger.info(
                "RAG retornou contextos",
                extra={
                    "exam_uuid": str(exam_uuid),
                    "contexts_count": len(contexts),
                    "top_score": contexts[0].relevance_score if contexts else 0.0
                }
            )
            
            return contexts
            
        except Exception as e:
            self.__logger.error(
                "Erro ao buscar contexto RAG: %s",
                str(e),
                exc_info=True
            )
            raise SqlError(
                message="Erro ao buscar contexto RAG",
                context={
                    "exam_uuid": str(exam_uuid),
                    "discipline": discipline
                },
                cause=e
            ) from e
    
    async def _search_by_similarity(
        self,
        reference_text: str,
        exam_uuid: UUID,
        discipline: str,
        k: int = 3
    ) -> List[RetrievedContext]:
        """
        Busca chunks similares a um texto de referência.
        Útil para encontrar exemplos ou gabaritos similares.
        
        Args:
            reference_text: Texto de referência (ex: resposta esperada)
            exam_uuid: UUID da prova
            discipline: Disciplina
            k: Top-K resultados
            
        Returns:
            Lista de contextos similares
        """
        self.__logger.debug(
            "Busca por similaridade: exam=%s, k=%d",
            exam_uuid,
            k
        )
        
        return await self.search_context(
            query=reference_text,
            exam_uuid=exam_uuid,
            discipline=discipline,
            k=k
        )
    
    async def _get_context_for_question(
        self,
        question_text: str,
        student_answer: str,
        exam_uuid: UUID,
        discipline: str,
        topic: Optional[str] = None,
        k: Optional[int] = None
    ) -> List[RetrievedContext]:
        """
        Busca contexto combinando questão + resposta do aluno.
        
        Estratégia: Concatena questão e resposta para capturar
        conceitos mencionados em ambos.
        
        Args:
            question_text: Enunciado da questão
            student_answer: Resposta do aluno
            exam_uuid: UUID da prova
            discipline: Disciplina
            topic: Tópico (opcional)
            k: Top-K resultados
            
        Returns:
            Lista de contextos relevantes
        """
        # Combinar questão + resposta para query mais rica
        combined_query = f"{question_text}\n\n{student_answer}"
        
        self.__logger.debug(
            "Busca contexto para questão+resposta: %d chars",
            len(combined_query)
        )
        
        return await self.search_context(
            query=combined_query,
            exam_uuid=exam_uuid,
            discipline=discipline,
            topic=topic,
            k=k
        )
    
    async def _validate_exam_has_vectors(self, exam_uuid: UUID) -> bool:
        """
        Verifica se uma prova tem vetores indexados.
        Útil antes de tentar fazer retrieval.
        
        Args:
            exam_uuid: UUID da prova
            
        Returns:
            True se a prova tem vetores, False caso contrário
        """
        try:
            # Busca com k=1 apenas para testar existência
            results = self.__vector_store.similarity_search(
                query="test",  # Query dummy
                k=1,
                filter={"exam_uuid": {"$eq": str(exam_uuid)}}
            )
            
            has_vectors = len(results) > 0
            
            self.__logger.debug(
                "Prova %s %s vetores indexados",
                exam_uuid,
                "TEM" if has_vectors else "NÃO TEM"
            )
            
            return has_vectors
            
        except Exception as e:
            self.__logger.error(
                "Erro ao validar vetores da prova %s: %s",
                exam_uuid,
                str(e)
            )
            return False
    
    async def _get_all_sources_for_exam(self, exam_uuid: UUID) -> List[str]:
        """
        Retorna lista de documentos fonte de uma prova.
        Útil para debugging e auditoria.
        
        Args:
            exam_uuid: UUID da prova
            
        Returns:
            Lista de nomes de documentos fonte (ex: ["material_1.pdf", "gabarito.pdf"])
        """
        try:
            # Buscar alguns chunks para extrair metadados
            results = self.__vector_store.similarity_search(
                query="",
                k=100,  # Suficiente para cobrir múltiplos documentos
                filter={"exam_uuid": {"$eq": str(exam_uuid)}}
            )
            
            # Extrair sources únicos
            sources = set()
            for doc in results:
                source = doc.metadata.get("source")
                if source:
                    # Pegar apenas o nome do arquivo
                    source_name = source.split("/")[-1]
                    sources.add(source_name)
            
            sources_list = sorted(list(sources))
            
            self.__logger.debug(
                "Prova %s tem %d documentos fonte: %s",
                exam_uuid,
                len(sources_list),
                sources_list
            )
            
            return sources_list
            
        except Exception as e:
            self.__logger.error(
                "Erro ao buscar sources da prova %s: %s",
                exam_uuid,
                str(e)
            )
            return []
