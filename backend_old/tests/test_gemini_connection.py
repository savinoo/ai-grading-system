import dspy
import os
import asyncio
from src.config.settings import settings
from src.infrastructure.dspy_config import configure_dspy

# Força configuração para teste
settings.MODEL_NAME = "gemini-2.0-flash"
configure_dspy()

def test_connection():
    print(f"Testing Model: {settings.MODEL_NAME}")
    try:
        # Tenta gerar algo simples
        pred = dspy.Predict("question -> answer")
        res = pred(question="Say 'Hello World' in Portuguese.")
        print(f"Success! Output: {res.answer}")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    # Roda síncrono para simplificar, já que DSPy predict padrão é síncrono (ou via adapter)
    # Mas como configuramos dspy.LM que é async native no v2.5+, vamos ver.
    # O script usa dspy.Predict que é sincrono por cima do LM.
    try:
        pred = dspy.Predict("question -> answer")
        res = pred(question="Say 'Hello World'")
        print(f"Sync Result: {res.answer}")
    except Exception as e:
        print(f"Sync Fail: {e}")
