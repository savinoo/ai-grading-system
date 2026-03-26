
import dspy

from src.config.settings import settings


def configure_dspy():
    """
    Configura o backend do DSPy com o modelo LM definido nas settings.
    Suporta Local (Ollama), Google Gemini e OpenAI via LiteLLM.
    """
    provider = (settings.LLM_PROVIDER or "local").lower()

    if provider == "local":
        # Ollama local via LiteLLM integration
        # Format: ollama_chat/<model_name> for chat models
        # num_ctx e num_predict passados via extra_body para limitar tokens gerados (otimização CPU)
        model_id = f"ollama_chat/{settings.LOCAL_MODEL_NAME}"
        lm = dspy.LM(
            model=model_id,
            api_base=settings.OLLAMA_BASE_URL,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.OLLAMA_NUM_PREDICT,
            extra_body={"num_ctx": settings.OLLAMA_NUM_CTX},
        )

    elif provider == "gemini" or "gemini" in (settings.MODEL_NAME or "").lower():
        model_name = settings.MODEL_NAME.lower()
        clean_name = model_name.replace("models/", "").replace("google/", "").replace("gemini/", "")
        provider_model = f"gemini/{clean_name}"
        lm = dspy.LM(model=provider_model, api_key=settings.GOOGLE_API_KEY, temperature=settings.TEMPERATURE)

    elif provider == "openai" or "gpt" in (settings.MODEL_NAME or "").lower():
        model_name = settings.MODEL_NAME.lower()
        clean_name = model_name.replace("models/", "").replace("openai/", "")
        lm = dspy.LM(model=f"openai/{clean_name}", api_key=settings.OPENAI_API_KEY, temperature=settings.TEMPERATURE)

    else:
        # Fallback generico
        try:
            lm = dspy.LM(model=settings.MODEL_NAME)
        except Exception:
            lm = dspy.LM(model=f"openai/{settings.MODEL_NAME}", api_key=settings.OPENAI_API_KEY)

    try:
        dspy.settings.configure(lm=lm)
    except RuntimeError as e:
        # Streamlit re-run safety:
        # Se o DSPy ja foi configurado em outra thread (execucao anterior),
        # ele bloqueia reconfiguracao. Ignoramos pois a config global persiste.
        if "thread that initially configured it" in str(e):
            pass
        else:
            raise e
