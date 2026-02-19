import os
from pathlib import Path
from dotenv import load_dotenv


def _get_secret(name: str, default: str | None = None):
    """Fetch secrets from env first, then Streamlit secrets (Cloud).

    Streamlit Cloud exposes secrets via `st.secrets`. Depending on deployment,
    they may not always be present as environment variables.
    """
    v = os.getenv(name)
    if v is not None and v != "":
        return v
    try:
        import streamlit as st  # type: ignore
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default

# Define base path
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class Settings:
    """Centralized configuration management."""

    # Keys
    OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
    GOOGLE_API_KEY = _get_secret("GOOGLE_API_KEY")  # Gemini

    # Model Selection
    # Default: Gemini (cheap/fast). If you deploy without Gemini, set MODEL_NAME=gpt-4o-mini (or similar)
    MODEL_NAME = _get_secret("MODEL_NAME", "gemini-2.0-flash")

    TEMPERATURE = float(_get_secret("TEMPERATURE", "0") or "0")
    DIVERGENCE_THRESHOLD = float(_get_secret("DIVERGENCE_THRESHOLD", "2.0") or "2.0")

    # Retry
    MAX_RETRIES = int(_get_secret("MAX_RETRIES", "3") or "3")
    INITIAL_RETRY_DELAY = float(_get_secret("INITIAL_RETRY_DELAY", "2.0") or "2.0")
    MAX_RETRY_DELAY = float(_get_secret("MAX_RETRY_DELAY", "30.0") or "30.0")

    # LangSmith
    LANGSMITH_API_KEY = _get_secret("LANGSMITH_API_KEY", "") or ""
    LANGSMITH_TRACING_ENABLED = (_get_secret("LANGSMITH_TRACING_ENABLED", "false") or "false").lower() == "true"
    LANGSMITH_PROJECT_NAME = _get_secret("LANGSMITH_PROJECT_NAME", "ai-grading-system") or "ai-grading-system"
    LANGSMITH_ENDPOINT = _get_secret("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com") or "https://api.smith.langchain.com"

    @classmethod
    def validate(cls):
        if "gemini" in (cls.MODEL_NAME or "").lower():
            if not cls.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not found. Required for Gemini models.")
        elif "gpt" in (cls.MODEL_NAME or "").lower():
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found. Required for GPT models.")


settings = Settings()
