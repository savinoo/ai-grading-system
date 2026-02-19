"""
Utilitários de controle de concorrência para chamadas à API externa (Gemini).
"""

from __future__ import annotations

import asyncio
from typing import Any, Coroutine, Dict

from src.core.logging_config import get_logger
from src.core.settings import settings

logger = get_logger(__name__)

# Mapeamento loop-id → semáforo para evitar conflitos entre event-loops
_api_semaphores: Dict[int, asyncio.Semaphore] = {}


def get_api_semaphore(limit: int | None = None) -> asyncio.Semaphore:
    """
    Retorna um semáforo compartilhado para o event-loop atual.

    O semáforo é criado uma única vez por event-loop, garantindo que
    **todas** as chamadas paralelas ao Gemini compartilhem o mesmo limite.

    Args:
        limit: Número máximo de chamadas simultâneas. Se ``None``, usa
            ``settings.API_CONCURRENCY`` (default 10).

    Returns:
        Semáforo asyncio configurado.
    """
    if limit is None:
        limit = settings.API_CONCURRENCY

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Nenhum event-loop ativo (chamada fora de contexto async) — retorna
        # um semáforo descartável. Situação improvável em FastAPI.
        logger.warning("get_api_semaphore chamado fora de event-loop ativo.")
        return asyncio.Semaphore(limit)

    key = id(loop)
    if key not in _api_semaphores:
        _api_semaphores[key] = asyncio.Semaphore(limit)
        logger.debug(
            "Semáforo de API criado: loop=%d, limite=%d", key, limit
        )

    return _api_semaphores[key]


async def safe_gather(
    *tasks: Coroutine[Any, Any, Any],
    throttle: float | None = None,
) -> list[Any]:
    """
    ``asyncio.gather`` com semáforo global e throttle opcional.

    Usa o semáforo retornado por :func:`get_api_semaphore` para limitar
    quantas corotinas executam simultaneamente. Útil para processar
    múltiplas respostas de alunos em paralelo sem sobrecarregar a API.

    Args:
        *tasks: Corotinas a executar.
        throttle: Segundos de espera após adquirir o semáforo antes de
                chamar a corotina. Se ``None``, usa
                ``settings.API_THROTTLE_SLEEP`` (default 0.2 s).
                Passe ``0`` para desativar.

    Returns:
        Lista de resultados na mesma ordem das tarefas.

    Exemplo::

        results = await safe_gather(
            grade_answer(q, a1),
            grade_answer(q, a2),
            grade_answer(q, a3),
        )
    """
    sem = get_api_semaphore()

    if throttle is None:
        throttle = settings.API_THROTTLE_SLEEP

    async def _wrapped(task: Coroutine[Any, Any, Any]) -> Any:
        async with sem:
            if throttle > 0:
                await asyncio.sleep(throttle)
            return await task

    return list(await asyncio.gather(*[_wrapped(t) for t in tasks]))
