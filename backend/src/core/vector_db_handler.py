"""
Handler singleton para ChromaDB com embeddings (Google ou OpenAI).
Gerencia conexão persistente ao vector store.
"""

import logging
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from src.core.settings import settings

logger = logging.getLogger(__name__)

_vector_store = None


def get_vector_store() -> Chroma:
    """
    Singleton para ChromaDB com embeddings (Google ou OpenAI).
    Persiste no path configurado via settings.CHROMA_PERSIST_DIRECTORY.
    
    Returns:
        Chroma: Instância singleton do vector store
        
    Raises:
        ValueError: Se as API keys necessárias não estiverem configuradas
    """
    global _vector_store
    
    if _vector_store is not None:
        logger.debug("Reutilizando instância existente do ChromaDB")
        return _vector_store
    
    logger.info(
        "Inicializando ChromaDB",
        extra={
            "persist_dir": settings.CHROMA_PERSIST_DIRECTORY,
            "embedding_model": settings.EMBEDDING_MODEL,
            "provider": settings.EMBEDDING_PROVIDER
        }
    )
    
    # Setup embeddings baseado no provider
    if settings.EMBEDDING_PROVIDER.lower() == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada para embeddings")
        embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        logger.info(f"Usando OpenAI embeddings: {settings.EMBEDDING_MODEL}")
    else:
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY não configurada para embeddings")
        embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )
        logger.info(f"Usando Google embeddings: {settings.EMBEDDING_MODEL}")
    
    # Setup ChromaDB
    _vector_store = Chroma(
        collection_name="exam_materials",
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        client_settings=ChromaSettings(anonymized_telemetry=False)
    )
    
    logger.info("ChromaDB inicializado com sucesso")
    return _vector_store


def reset_vector_store() -> None:
    """
    Reseta o singleton do vector store.
    Útil para testes ou reconfiguração em runtime.
    """
    global _vector_store
    _vector_store = None
    logger.info("Vector store resetado")
