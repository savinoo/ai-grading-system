"""
Utilitários de medição de tempo para monitoramento de performance.
"""

import time
from contextlib import contextmanager

from src.core.logging_config import get_logger

logger = get_logger(__name__)


@contextmanager
def measure_time(operation_name: str):
    """
    Context manager para medir e logar o tempo de execução de uma operação.

    Exemplo de uso::

        with measure_time("DSPy Examiner - Question 123"):
            result = module(...)

    Args:
        operation_name: Descrição legível da operação sendo medida.
    """
    start = time.perf_counter()
    logger.info("Iniciando: %s...", operation_name)
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("Concluído: %s em %.4f segundos.", operation_name, elapsed)
