import asyncio
import os
import streamlit as st
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

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

def save_uploaded_file(uploaded_file):
    """Salva o PDF temporariamente para ingestão"""
    if not os.path.exists("data/raw"):
        os.makedirs("data/raw")
    file_path = os.path.join("data/raw", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path
