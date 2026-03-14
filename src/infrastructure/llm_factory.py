# src/infrastructure/llm_factory.py
from langchain_core.language_models import BaseChatModel

from src.config.settings import settings


def get_chat_model(temperature: float = None, model_name: str = None) -> BaseChatModel:
    """
    Factory para criar instancias de LLM baseado no provider configurado.

    Providers suportados:
    - local: Ollama (gratuito, recomendado para benchmark)
    - gemini: Google Gemini API
    - openai: OpenAI API
    """
    if temperature is None:
        temperature = settings.TEMPERATURE

    provider = (settings.LLM_PROVIDER or "local").lower()

    if provider == "local":
        local_model = model_name or settings.LOCAL_MODEL_NAME
        print(f"[llm_factory] Using LOCAL model={local_model} via Ollama at {settings.OLLAMA_BASE_URL}")

        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=local_model,
            temperature=temperature,
            base_url=settings.OLLAMA_BASE_URL,
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
