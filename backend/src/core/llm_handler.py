"""
Factory para criação de instâncias LLM.
Suporta múltiplos provedores (OpenAI, Gemini).
"""

import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.settings import settings

logger = logging.getLogger(__name__)


def get_chat_model(
    temperature: Optional[float] = None,
    model_name: Optional[str] = None,
    max_retries: Optional[int] = None
) -> BaseChatModel:
    """
    Factory para LLM. Suporta OpenAI e Gemini.
    
    Args:
        temperature: Override de temperatura (padrão: settings.LLM_TEMPERATURE)
        model_name: Override de modelo (padrão: settings.LLM_MODEL_NAME)
        max_retries: Override de max retries (padrão: settings.LLM_MAX_RETRIES)
        
    Returns:
        BaseChatModel: Instância do modelo de chat configurado
        
    Raises:
        ValueError: Se o provider não for suportado ou credenciais ausentes
        
    Examples:
        >>> # Usa configurações padrão
        >>> llm = get_chat_model()
        >>> 
        >>> # Override específico para tarefa determinística
        >>> llm = get_chat_model(temperature=0.0)
        >>> 
        >>> # Usa modelo diferente
        >>> llm = get_chat_model(model_name="gpt-4")
    """
    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
    model = model_name or settings.LLM_MODEL_NAME
    retries = max_retries if max_retries is not None else settings.LLM_MAX_RETRIES
    
    provider = settings.LLM_PROVIDER.lower()
    
    logger.info(
        "Criando instância LLM",
        extra={
            "provider": provider,
            "model": model,
            "temperature": temp,
            "max_retries": retries
        }
    )
    
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada")
        
        return ChatOpenAI(
            model=model,
            temperature=temp,
            api_key=settings.OPENAI_API_KEY,
            max_retries=retries
        )
    
    elif provider == "gemini":
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY não configurada")
        
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temp,
            google_api_key=settings.GOOGLE_API_KEY,
            max_retries=retries
        )
    
    else:
        raise ValueError(
            f"Provider '{provider}' não suportado. "
            f"Use 'openai' ou 'gemini'."
        )
