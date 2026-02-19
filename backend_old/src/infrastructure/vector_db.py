# src/infrastructure/vector_db.py
import os
import logging
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config.settings import settings

logger = logging.getLogger(__name__)

_VECTOR_STORE: Chroma | None = None


def get_vector_store() -> Chroma:
    """
    Inicializa e retorna a conexão com o ChromaDB (Persistente).
    
    Técnica: Usamos GoogleGenerativeAIEmbeddings para alinhar a qualidade vetorial 
    com o modelo de raciocínio, usando embeddings gratuitos se possível.
    """
    global _VECTOR_STORE
    if _VECTOR_STORE is not None:
        return _VECTOR_STORE

    # Choose embeddings provider.
    # Prefer Gemini embeddings when available; otherwise fall back to OpenAI.
    embeddings = None
    if settings.GOOGLE_API_KEY:
        try:
            # NOTE: model names vary by account/API version. The most common Gemini embeddings
            # model name is: models/gemini-embedding-001
            embeddings = GoogleGenerativeAIEmbeddings(
                model=os.getenv("EMBEDDINGS_MODEL", "models/gemini-embedding-001"),
                google_api_key=settings.GOOGLE_API_KEY,
            )
            logger.info("VectorDB: using Gemini embeddings")
        except Exception as e:
            logger.warning(f"VectorDB: Gemini embeddings unavailable, falling back. Reason: {e}")

    if embeddings is None:
        from langchain_openai import OpenAIEmbeddings

        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "No embeddings provider available. Set GOOGLE_API_KEY (Gemini) or OPENAI_API_KEY (OpenAI)."
            )
        embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        logger.info("VectorDB: using OpenAI embeddings")

    # Ensure absolute path for persistence
    base_dir = os.getcwd()
    persist_directory = os.path.join(base_dir, "data", "vector_store")

    _VECTOR_STORE = Chroma(
        collection_name="material_didatico_tcc",
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )

    return _VECTOR_STORE
