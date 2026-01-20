import os
from pathlib import Path
from dotenv import load_dotenv

# Define base path
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    """
    Centralized configuration management.
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # Trocando para gpt-4o para maior capacidade de raciocínio
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
    DIVERGENCE_THRESHOLD = float(os.getenv("DIVERGENCE_THRESHOLD", "2.0"))

    # Configurações de Retry (Resiliência)
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    INITIAL_RETRY_DELAY = float(os.getenv("INITIAL_RETRY_DELAY", "2.0"))
    MAX_RETRY_DELAY = float(os.getenv("MAX_RETRY_DELAY", "30.0"))
    
    # LangSmith Configuration
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_TRACING_ENABLED = os.getenv("LANGSMITH_TRACING_ENABLED", "false").lower() == "true"
    LANGSMITH_PROJECT_NAME = os.getenv("LANGSMITH_PROJECT_NAME", "ai-grading-system")
    LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    
    # Add other configuration variables here as needed

    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables or .env file.")

settings = Settings()
