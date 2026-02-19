"""
Configuração global do DSPy.
Deve ser inicializado no startup da aplicação.
"""

import logging
import dspy
from src.core.settings import settings

logger = logging.getLogger(__name__)

_dspy_configured = False


def configure_dspy() -> None:
    """
    Configura DSPy globalmente. Deve ser chamado na inicialização do app.
    
    Esta função é idempotente - múltiplas chamadas são seguras.
    Configura o DSPy para usar o provider/modelo definido nas settings.
    
    Raises:
        ValueError: Se credenciais necessárias não estiverem configuradas
        
    Examples:
        >>> # No startup do FastAPI
        >>> @app.on_event("startup")
        >>> async def startup_event():
        >>>     configure_dspy()
    """
    global _dspy_configured
    
    if _dspy_configured:
        logger.debug("DSPy já configurado. Pulando...")
        return
    
    logger.info(
        "Configurando DSPy",
        extra={
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL_NAME,
            "temperature": settings.LLM_TEMPERATURE
        }
    )
    
    # Determina a API key baseado no provider
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "gemini":
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY não configurada para DSPy")
        api_key = settings.GOOGLE_API_KEY
        # LiteLLM não aceita prefixos como "models/" ou "google/" no nome do modelo
        clean_model = (
            settings.LLM_MODEL_NAME
            .replace("models/", "")
            .replace("google/", "")
            .replace("gemini/", "")
        )
        model_string = f"gemini/{clean_model}"
    elif provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada para DSPy")
        api_key = settings.OPENAI_API_KEY
        model_string = settings.LLM_MODEL_NAME
    else:
        raise ValueError(f"Provider '{provider}' não suportado pelo DSPy")
    
    # Configurar LM com LiteLLM backend
    lm = dspy.LM(
        model=model_string,
        api_key=api_key,
        temperature=settings.LLM_TEMPERATURE,
        cache=True  # Cache habilitado para reutilizar respostas idênticas (economia de tokens)
    )
    
    dspy.settings.configure(lm=lm)
    _dspy_configured = True
    
    logger.info("DSPy configurado com sucesso")


def is_dspy_configured() -> bool:
    """
    Verifica se o DSPy já foi configurado.
    
    Returns:
        bool: True se configurado, False caso contrário
    """
    return _dspy_configured


def reset_dspy_config() -> None:
    """
    Reseta a configuração do DSPy.
    Útil para testes ou reconfiguração em runtime.
    """
    global _dspy_configured
    _dspy_configured = False
    logger.info("Configuração do DSPy resetada")
