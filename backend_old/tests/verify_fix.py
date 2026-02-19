import sys
import os
import asyncio
from tenacity import retry, wait_exponential

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.dspy_config import configure_dspy
from src.agents.mock_generator import MockDataGeneratorAgent
from src.infrastructure.llm_factory import get_chat_model
from src.config.settings import settings

# Configure
configure_dspy()

async def test_generation():
    print(f"🚀 Iniciando Teste de Verificação")
    print(f"🔧 Modelo Configurado: {settings.MODEL_NAME}")
    
    try:
        llm = get_chat_model(temperature=1)
        agent = MockDataGeneratorAgent(llm)
        
        print("⚡ Tentando gerar 1 questão (com Retry ativo)...")
        q = await agent.generate_exam_question("Teste de Conexão", "TI", "Easy")
        
        print(f"✅ Sucesso! Questão gerada ID: {q.id}")
        print(f"📜 Enunciado: {q.statement[:50]}...")
        
    except Exception as e:
        print(f"❌ Falha: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generation())
