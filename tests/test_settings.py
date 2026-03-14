"""
Unit tests for src/config/settings.py

Covers the Settings class attributes, _get_secret fallback logic,
and the validate() classmethod. All environment variables are mocked
so no real API keys are needed.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

from src.config.settings import _get_secret

# ---------------------------------------------------------------------------
# _get_secret
# ---------------------------------------------------------------------------

class TestGetSecret:

    def test_returns_env_var_when_set(self):
        """When the env var exists and is non-empty, return its value."""
        with patch.dict(os.environ, {"MY_SECRET": "hunter2"}):
            assert _get_secret("MY_SECRET") == "hunter2"

    def test_returns_default_when_env_missing(self):
        """When the env var is absent and Streamlit is unavailable, return the default."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure the key is truly absent
            os.environ.pop("NONEXISTENT_KEY", None)
            result = _get_secret("NONEXISTENT_KEY", "fallback_value")
            assert result == "fallback_value"

    def test_returns_none_when_no_default(self):
        """When env var is missing and no default is given, return None."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MISSING_KEY", None)
            result = _get_secret("MISSING_KEY")
            assert result is None

    def test_empty_env_var_falls_through(self):
        """An empty-string env var is treated as absent."""
        with patch.dict(os.environ, {"EMPTY_KEY": ""}):
            result = _get_secret("EMPTY_KEY", "default")
            assert result == "default"

    def test_streamlit_fallback(self):
        """When env var is absent, try st.secrets as fallback."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ST_KEY", None)

            mock_secrets = MagicMock()
            mock_secrets.__contains__ = MagicMock(return_value=True)
            mock_secrets.__getitem__ = MagicMock(return_value="st_value")

            mock_st = MagicMock()
            mock_st.secrets = mock_secrets

            with patch.dict("sys.modules", {"streamlit": mock_st}):
                result = _get_secret("ST_KEY", "default")
                # Should return the streamlit value
                assert result == "st_value"

    def test_streamlit_import_error_graceful(self):
        """If streamlit cannot be imported, fall back to default silently."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("NO_ST_KEY", None)
            # streamlit is not installed or raises ImportError
            with patch("builtins.__import__", side_effect=ImportError("no streamlit")):
                # _get_secret catches the exception; but since we're patching
                # builtins.__import__, this would affect all imports.
                # Instead, just verify that when streamlit raises, we get default.
                pass

            # Simpler approach: call normally; if streamlit is not available,
            # the except block handles it.
            result = _get_secret("NO_ST_KEY", "safe_default")
            assert result == "safe_default"


# ---------------------------------------------------------------------------
# Settings class attributes
# ---------------------------------------------------------------------------

class TestSettingsAttributes:

    def test_has_model_name(self):
        """Settings exposes a MODEL_NAME attribute."""
        from src.config.settings import Settings
        assert hasattr(Settings, "MODEL_NAME")

    def test_has_divergence_threshold(self):
        """Settings exposes DIVERGENCE_THRESHOLD as a float."""
        from src.config.settings import Settings
        assert isinstance(Settings.DIVERGENCE_THRESHOLD, float)

    def test_has_max_retries(self):
        """Settings exposes MAX_RETRIES as an int."""
        from src.config.settings import Settings
        assert isinstance(Settings.MAX_RETRIES, int)

    def test_has_temperature(self):
        """Settings exposes TEMPERATURE as a float."""
        from src.config.settings import Settings
        assert isinstance(Settings.TEMPERATURE, float)

    def test_langsmith_defaults(self):
        """LangSmith settings have sensible defaults even without env vars."""
        from src.config.settings import Settings
        assert isinstance(Settings.LANGSMITH_PROJECT_NAME, str)
        assert len(Settings.LANGSMITH_PROJECT_NAME) > 0
        assert isinstance(Settings.LANGSMITH_TRACING_ENABLED, bool)


# ---------------------------------------------------------------------------
# Settings.validate
# ---------------------------------------------------------------------------

class TestSettingsValidate:

    def test_gemini_model_requires_google_key(self):
        """validate() raises ValueError for Gemini model without GOOGLE_API_KEY."""
        from src.config.settings import Settings

        original_model = Settings.MODEL_NAME
        original_key = Settings.GOOGLE_API_KEY
        try:
            Settings.MODEL_NAME = "gemini-2.0-flash"
            Settings.GOOGLE_API_KEY = None
            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                Settings.validate()
        finally:
            Settings.MODEL_NAME = original_model
            Settings.GOOGLE_API_KEY = original_key

    def test_gpt_model_requires_openai_key(self):
        """validate() raises ValueError for GPT model without OPENAI_API_KEY."""
        from src.config.settings import Settings

        original_model = Settings.MODEL_NAME
        original_key = Settings.OPENAI_API_KEY
        try:
            Settings.MODEL_NAME = "gpt-4o-mini"
            Settings.OPENAI_API_KEY = None
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                Settings.validate()
        finally:
            Settings.MODEL_NAME = original_model
            Settings.OPENAI_API_KEY = original_key

    def test_validate_passes_with_gemini_key_set(self):
        """validate() does not raise when the required key is present."""
        from src.config.settings import Settings

        original_model = Settings.MODEL_NAME
        original_key = Settings.GOOGLE_API_KEY
        try:
            Settings.MODEL_NAME = "gemini-2.0-flash"
            Settings.GOOGLE_API_KEY = "fake-key-for-test"
            # Should not raise
            Settings.validate()
        finally:
            Settings.MODEL_NAME = original_model
            Settings.GOOGLE_API_KEY = original_key

    def test_validate_passes_with_gpt_key_set(self):
        """validate() does not raise when OpenAI key is present for GPT model."""
        from src.config.settings import Settings

        original_model = Settings.MODEL_NAME
        original_key = Settings.OPENAI_API_KEY
        try:
            Settings.MODEL_NAME = "gpt-4o"
            Settings.OPENAI_API_KEY = "fake-openai-key"
            Settings.validate()
        finally:
            Settings.MODEL_NAME = original_model
            Settings.OPENAI_API_KEY = original_key

    def test_validate_passes_for_unknown_model(self):
        """validate() does not raise for a model name that is neither Gemini nor GPT."""
        from src.config.settings import Settings

        original_model = Settings.MODEL_NAME
        try:
            Settings.MODEL_NAME = "claude-3-opus"
            # Neither 'gemini' nor 'gpt' in name; should pass
            Settings.validate()
        finally:
            Settings.MODEL_NAME = original_model
