"""
LangSmith Configuration Module
Gerencia a inicialização e configuração do tracing com LangSmith.
"""

import os
import logging
from typing import Optional
from src.config.settings import settings

logger = logging.getLogger(__name__)


def initialize_langsmith():
    """
    Inicializa o LangSmith tracing com as credenciais e configurações.
    
    Deve ser chamado no início da aplicação (em main.py ou similar).
    
    Exemplo:
        from src.infrastructure.langsmith_config import initialize_langsmith
        initialize_langsmith()
    """
    try:
        if not settings.LANGSMITH_TRACING_ENABLED:
            logger.info("LangSmith tracing está desabilitado")
            return False
        
        if not settings.LANGSMITH_API_KEY:
            logger.warning(
                "LangSmith tracing habilitado, mas LANGSMITH_API_KEY não configurada. "
                "Desabilitando tracing."
            )
            return False
        
        # Configurar variáveis de ambiente para LangSmith
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT_NAME
        
        logger.info(
            f"✓ LangSmith tracing inicializado com sucesso"
        )
        logger.info(
            f"  - Projeto: {settings.LANGSMITH_PROJECT_NAME}"
        )
        logger.info(
            f"  - Endpoint: {settings.LANGSMITH_ENDPOINT}"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao inicializar LangSmith: {str(e)}")
        return False


def is_langsmith_enabled() -> bool:
    """
    Verifica se o LangSmith tracing está habilitado e configurado.
    
    Returns:
        bool: True se LangSmith está ativo, False caso contrário
    """
    return (
        settings.LANGSMITH_TRACING_ENABLED 
        and bool(settings.LANGSMITH_API_KEY)
        and os.getenv("LANGCHAIN_TRACING_V2") == "true"
    )


def get_trace_url(run_id: Optional[str] = None) -> Optional[str]:
    """
    Gera a URL para visualizar traces no dashboard do LangSmith.
    
    Args:
        run_id: ID da execução (run) opcional
        
    Returns:
        str: URL do LangSmith para o projeto ou run específico
    """
    if not is_langsmith_enabled():
        return None
    
    base_url = "https://smith.langchain.com"
    project = settings.LANGSMITH_PROJECT_NAME
    
    if run_id:
        return f"{base_url}/projects/p/default/r/{run_id}"
    
    return f"{base_url}/projects/p/{project}"
