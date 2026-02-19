"""
Handler singleton para ChromaDB com embeddings (Google ou OpenAI).
Gerencia conexão persistente ao vector store.
"""

import logging
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from src.core.settings import settings

logger = logging.getLogger(__name__)

_vector_store = None


def get_vector_store() -> Chroma:
    """
    Singleton para ChromaDB com embeddings (Google ou OpenAI).
    Persiste no path configurado via settings.CHROMA_PERSIST_DIRECTORY.

    Auto-detect de provider:
      - Se GOOGLE_API_KEY estiver configurada, usa GoogleGenerativeAIEmbeddings.
      - Caso contrário, faz fallback para OpenAIEmbeddings.
    
    Returns:
        Chroma: Instância singleton do vector store
        
    Raises:
        ValueError: Se as API keys necessárias não estiverem configuradas
    """
    global _vector_store
    
    if _vector_store is not None:
        logger.debug("Reutilizando instância existente do ChromaDB")
        return _vector_store
    
    # --- Auto-detect de provider de embeddings ---
    if settings.GOOGLE_API_KEY:
        embedding_model = settings.EMBEDDING_MODEL or "models/gemini-embedding-001"
        embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=settings.GOOGLE_API_KEY
        )
        logger.info("[ChromaDB] Provider de embeddings: Google (%s)", embedding_model)
    else:
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "Nenhuma API key de embeddings configurada. "
                "Defina GOOGLE_API_KEY ou OPENAI_API_KEY."
            )
        embedding_model = settings.EMBEDDING_MODEL or "text-embedding-3-small"
        embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=settings.OPENAI_API_KEY
        )
        logger.info("[ChromaDB] Provider de embeddings: OpenAI (%s) [fallback]", embedding_model)
    
    logger.info(
        "[ChromaDB] Inicializando",
        extra={
            "persist_dir": settings.CHROMA_PERSIST_DIRECTORY,
            "embedding_model": embedding_model,
        }
    )
    
    # Setup ChromaDB
    _vector_store = Chroma(
        collection_name="exam_materials",
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        client_settings=ChromaSettings(anonymized_telemetry=False)
    )
    
    logger.info("[ChromaDB] Inicializado com sucesso")
    return _vector_store


def reset_vector_store() -> None:
    """
    Reseta o singleton do vector store.
    Útil para testes ou reconfiguramento em runtime.
    """
    global _vector_store
    _vector_store = None
    logger.info("[ChromaDB] Vector store resetado")
