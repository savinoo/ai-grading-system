# src/infrastructure/llm_factory.py
import logging

from langchain_core.language_models import BaseChatModel

from src.config.settings import settings

logger = logging.getLogger(__name__)


def get_embeddings():
    """
    Factory para criar instancias de embeddings baseado no provider configurado.

    Providers suportados:
    - local: Ollama (gratuito, recomendado — nomic-embed-text)
    - gemini: Google Gemini Embeddings API
    - openai: OpenAI Embeddings API

    IMPORTANTE: Mudar de provider requer recriar o indice ChromaDB,
    pois embeddings de modelos diferentes sao incompativeis entre si.
    """
    provider = (settings.EMBEDDINGS_PROVIDER or "local").lower()

    if provider == "local":
        model = settings.LOCAL_EMBEDDINGS_MODEL or "nomic-embed-text"
        base_url = settings.OLLAMA_BASE_URL or "http://localhost:11434"
        logger.info(f"[embeddings_factory] Using LOCAL embeddings model={model} via Ollama at {base_url}")

        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=model,
            base_url=base_url,
        )

    if provider == "gemini":
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY nao encontrada no .env. "
                "Necessaria para usar embeddings Gemini."
            )
        import os

        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        emb_model = os.getenv("EMBEDDINGS_MODEL", "models/gemini-embedding-001")
        logger.info(f"[embeddings_factory] Using Gemini embeddings model={emb_model}")
        return GoogleGenerativeAIEmbeddings(
            model=emb_model,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY nao encontrada no .env. "
                "Necessaria para usar embeddings OpenAI."
            )
        from langchain_openai import OpenAIEmbeddings

        logger.info("[embeddings_factory] Using OpenAI embeddings")
        return OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)

    raise ValueError(
        f"EMBEDDINGS_PROVIDER='{provider}' nao suportado. "
        "Use: local, gemini ou openai."
    )


def get_chat_model(
    temperature: float = None,
    model_name: str = None,
    num_predict: int = None,
    num_ctx: int = None,
) -> BaseChatModel:
    """
    Factory para criar instancias de LLM baseado no provider configurado.

    Providers suportados:
    - local: Ollama (gratuito, recomendado para benchmark)
    - gemini: Google Gemini API
    - openai: OpenAI API

    Parâmetros Ollama de otimização (CPU):
    - num_predict: máximo de tokens gerados. Reduzir = mais rápido.
      Padrão: settings.OLLAMA_NUM_PREDICT (450). Use o específico por tarefa via settings.
    - num_ctx: janela de contexto. 1024 é suficiente para nossos prompts.
    """
    if temperature is None:
        temperature = settings.TEMPERATURE

    provider = (settings.LLM_PROVIDER or "local").lower()

    if provider == "local":
        local_model = model_name or settings.LOCAL_MODEL_NAME
        resolved_num_predict = num_predict if num_predict is not None else settings.OLLAMA_NUM_PREDICT
        resolved_num_ctx = num_ctx if num_ctx is not None else settings.OLLAMA_NUM_CTX
        print(f"[llm_factory] Using LOCAL model={local_model} via Ollama at {settings.OLLAMA_BASE_URL} "
              f"[num_ctx={resolved_num_ctx}, num_predict={resolved_num_predict}]")

        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=local_model,
            temperature=temperature,
            base_url=settings.OLLAMA_BASE_URL,
            num_predict=resolved_num_predict,
            num_ctx=resolved_num_ctx,
        )

    if model_name is None:
        model_name = settings.MODEL_NAME

    print(f"[llm_factory] Using model={model_name} temperature={temperature} provider={provider}")

    # Gemini provider
    if provider == "gemini" or "gemini" in model_name.lower():
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY nao encontrada no .env para usar modelo Gemini.")

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=settings.GOOGLE_API_KEY,
            convert_system_message_to_human=True
        )

    # OpenAI provider (fallback)
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=settings.OPENAI_API_KEY
    )
