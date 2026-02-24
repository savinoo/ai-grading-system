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


# Defaults canônicos por provider
_GOOGLE_DEFAULT_MODEL = "models/gemini-embedding-001"
_OPENAI_DEFAULT_MODEL = "text-embedding-3-small"

# Modelos conhecidos de cada provider (para detecção de incompatibilidade)
_OPENAI_MODEL_PREFIXES = ("text-embedding", "ada", "babbage", "curie", "davinci")
_GOOGLE_MODEL_PREFIXES = ("models/", "gemini", "text-multilingual")


def _resolve_provider() -> str:
    """
    Determina o provider de embeddings a ser usado.

    Prioridade:
      1. settings.EMBEDDING_PROVIDER (explícito)
      2. Auto-detect pela presence de API keys
    """
    explicit = (settings.EMBEDDING_PROVIDER or "").strip().lower()
    if explicit in ("google", "openai"):
        return explicit
    # fallback: auto-detect por key disponível
    if settings.GOOGLE_API_KEY:
        return "google"
    if settings.OPENAI_API_KEY:
        return "openai"
    raise ValueError(
        "Nenhuma API key de embeddings configurada. "
        "Defina GOOGLE_API_KEY ou OPENAI_API_KEY."
    )


def _resolve_embedding_model(provider: str) -> str:
    """
    Retorna o modelo de embedding correto para o provider.

    Se EMBEDDING_MODEL estiver configurado e for compatível com o provider,
    usa esse valor; caso contrário usa o default do provider.
    """
    configured = (settings.EMBEDDING_MODEL or "").strip()
    if not configured:
        return _GOOGLE_DEFAULT_MODEL if provider == "google" else _OPENAI_DEFAULT_MODEL

    if provider == "google":
        # Modelos OpenAI não funcionam na API Google
        if configured.startswith(_OPENAI_MODEL_PREFIXES):
            logger.warning(
                "[ChromaDB] EMBEDDING_MODEL='%s' parece ser um modelo OpenAI, "
                "mas EMBEDDING_PROVIDER=google. Usando default Google: %s",
                configured,
                _GOOGLE_DEFAULT_MODEL,
            )
            return _GOOGLE_DEFAULT_MODEL
        return configured
    else:  # openai
        # Modelos Google não funcionam na API OpenAI
        if any(configured.startswith(p) for p in _GOOGLE_MODEL_PREFIXES):
            logger.warning(
                "[ChromaDB] EMBEDDING_MODEL='%s' parece ser um modelo Google, "
                "mas EMBEDDING_PROVIDER=openai. Usando default OpenAI: %s",
                configured,
                _OPENAI_DEFAULT_MODEL,
            )
            return _OPENAI_DEFAULT_MODEL
        return configured


def get_vector_store() -> Chroma:
    """
    Singleton para ChromaDB com embeddings (Google ou OpenAI).
    Persiste no path configurado via settings.CHROMA_PERSIST_DIRECTORY.

    Provider é determinado por settings.EMBEDDING_PROVIDER (google|openai).
    Se não configurado, faz auto-detect pela presence de API keys.
    O modelo de embedding é validado contra o provider escolhido para
    evitar incompatibilidades entre modelos OpenAI e a API Google.

    Returns:
        Chroma: Instância singleton do vector store

    Raises:
        ValueError: Se as API keys necessárias não estiverem configuradas
    """
    global _vector_store

    if _vector_store is not None:
        logger.debug("Reutilizando instância existente do ChromaDB")
        return _vector_store

    provider = _resolve_provider()
    embedding_model = _resolve_embedding_model(provider)

    if provider == "google":
        if not settings.GOOGLE_API_KEY:
            raise ValueError("EMBEDDING_PROVIDER=google mas GOOGLE_API_KEY não está configurada.")
        embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        logger.info("[ChromaDB] Provider de embeddings: Google (%s)", embedding_model)
    else:
        if not settings.OPENAI_API_KEY:
            raise ValueError("EMBEDDING_PROVIDER=openai mas OPENAI_API_KEY não está configurada.")
        embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        logger.info("[ChromaDB] Provider de embeddings: OpenAI (%s)", embedding_model)
    
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
