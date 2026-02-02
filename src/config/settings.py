import os
from pathlib import Path
from dotenv import load_dotenv

# Define base path
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class Settings:
    """
    Centralized configuration management.
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # Chave do Gemini
    
    # Model Selection
    # Usando gemini-2.0-flash para maior velocidade e eficiência (Tier 1 safe)
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    
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
        # Validation for Google Gemini
        if "gemini" in cls.MODEL_NAME.lower():
            if not cls.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not found. Required for Gemini models.")
        # Legacy validation for OpenAI
        elif "gpt" in cls.MODEL_NAME.lower():
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found. Required for GPT models.")

settings = Settings()
