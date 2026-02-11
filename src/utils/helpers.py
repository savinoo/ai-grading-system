import asyncio
import os
import streamlit as st
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Concurrency limiter
# NOTE: asyncio primitives are bound to the event loop they were created in.
# Streamlit reruns + our `run_async()` create new event loops, so a module-level
# Semaphore will eventually trigger: "Semaphore ... is bound to a different event loop".
# We therefore create one Semaphore per running loop.
_api_semaphores: dict[int, asyncio.Semaphore] = {}


def get_api_semaphore(limit: int | None = None) -> asyncio.Semaphore:
    """Return a per-event-loop semaphore to avoid cross-loop binding errors.

    Limit can be set via env var API_CONCURRENCY (default 10).
    """
    if limit is None:
        limit = int(os.getenv("API_CONCURRENCY", "10"))

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    key = id(loop)
    sem = _api_semaphores.get(key)
    if sem is None:
        sem = asyncio.Semaphore(int(limit))
        _api_semaphores[key] = sem
    return sem

@contextmanager
def measure_time(operation_name: str):
    """
    Context manager para medir e logar o tempo de execução de operações.
    Útil para debugging de performance de modelos e chamadas externas.
    """
    start_time = time.perf_counter()
    logger.info(f"⏳ Iniciando: {operation_name}...")
    try:
        yield
    finally:
        elapsed_time = time.perf_counter() - start_time
        logger.info(f"✅ Concluído: {operation_name} em {elapsed_time:.4f} segundos.")

def run_async(coro):
    """
    Executa corotinas asyncio de forma segura no thread do Streamlit.
    Força a criação de um novo Call Loop para evitar erros de 'No event loop'.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def safe_gather(*tasks):
    """
    Wrapper seguro para asyncio.gather que respeita o semáforo global.
    Substitui chamadas diretas para garantir controle de taxa.
    """
    sem = get_api_semaphore()

    async def semaphore_wrapper(task):
        async with sem:
            # Optional throttle (avoid fixed 2s latency). If you hit 429s, increase this.
            throttle = float(os.getenv("API_THROTTLE_SLEEP", "0.2"))
            if throttle > 0:
                await asyncio.sleep(throttle)
            return await task

    # Envolve cada task original com o wrapper do semáforo
    wrapped_tasks = [semaphore_wrapper(t) for t in tasks]
    return await asyncio.gather(*wrapped_tasks)

def save_uploaded_file(uploaded_file):
    """Salva o PDF temporariamente para ingestão"""
    if not os.path.exists("data/raw"):
        os.makedirs("data/raw")
    file_path = os.path.join("data/raw", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path
