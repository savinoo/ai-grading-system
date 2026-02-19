"""
Módulo centralizado de configuração do LangSmith tracing.
Deve ser inicializado no startup da aplicação.
"""

from __future__ import annotations

import os
from typing import Optional

from src.core.logging_config import get_logger
from src.core.settings import settings

logger = get_logger(__name__)


def initialize_langsmith() -> bool:
    """
    Inicializa o LangSmith tracing via variáveis de ambiente.

    - Lê ``settings.LANGSMITH_TRACING_ENABLED`` e ``settings.LANGSMITH_API_KEY``.
    - Seta ``LANGCHAIN_TRACING_V2``, ``LANGCHAIN_API_KEY``,
      ``LANGCHAIN_ENDPOINT`` e ``LANGCHAIN_PROJECT`` no ambiente do processo.
    - Nunca lança exceção: erros são logados e retornam ``False``.

    Returns:
        ``True`` se o tracing foi habilitado com sucesso, ``False`` caso contrário.
    """
    try:
        if not settings.LANGSMITH_TRACING_ENABLED:
            logger.info("LangSmith tracing está desabilitado (LANGSMITH_TRACING_ENABLED=false).")
            return False

        if not settings.LANGSMITH_API_KEY:
            logger.warning(
                "LangSmith tracing habilitado, mas LANGSMITH_API_KEY não configurada. "
                "Desabilitando tracing para não bloquear o startup."
            )
            return False

        # Seta as env vars que as libs LangChain/LangSmith consomem
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT_NAME

        project_url = get_trace_url()
        logger.info("LangSmith tracing inicializado com sucesso.")
        logger.info("  Projeto  : %s", settings.LANGSMITH_PROJECT_NAME)
        logger.info("  Endpoint : %s", settings.LANGSMITH_ENDPOINT)
        if project_url:
            logger.info("  Dashboard: %s", project_url)

        return True

    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Erro ao inicializar LangSmith (não crítico): %s", exc, exc_info=True)
        return False


def is_langsmith_enabled() -> bool:
    """
    Verifica se o LangSmith tracing está ativo neste processo.

    Considera habilitado apenas se as settings indicam tracing E a env var
    ``LANGCHAIN_TRACING_V2`` foi efetivamente setada por ``initialize_langsmith()``.

    Returns:
        ``True`` se o tracing está operacional, ``False`` caso contrário.
    """
    return (
        settings.LANGSMITH_TRACING_ENABLED
        and bool(settings.LANGSMITH_API_KEY)
        and os.getenv("LANGCHAIN_TRACING_V2") == "true"
    )


def get_trace_url(run_id: Optional[str] = None) -> Optional[str]:
    """
    Gera a URL do dashboard LangSmith para o projeto ou para um run específico.

    Args:
        run_id: ID de execução (run) opcional. Se fornecido, retorna a URL
                direta do run; caso contrário, retorna a URL do projeto.

    Returns:
        URL como string, ou ``None`` se o LangSmith não estiver habilitado.
    """
    if not is_langsmith_enabled():
        return None

    base_url = "https://smith.langchain.com"
    project = settings.LANGSMITH_PROJECT_NAME

    if run_id:
        return f"{base_url}/projects/p/default/r/{run_id}"

    return f"{base_url}/projects/p/{project}"
