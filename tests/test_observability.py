"""Tests for the observability module -- tracing configuration and client wrapping."""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _clean_tracing_env():
    """Remove LangSmith/LangChain env vars before and after each test."""
    keys = [
        "LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT",
        "LANGCHAIN_TRACING_V2", "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT",
    ]
    saved = {k: os.environ.pop(k, None) for k in keys}
    yield
    for k in keys:
        os.environ.pop(k, None)
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v


def _mock_settings(**overrides):
    defaults = {
        "tracing_enabled": False,
        "tracing_backend": "langsmith",
        "langsmith_api_key": "",
        "langsmith_project": "emiglio",
    }
    defaults.update(overrides)
    s = MagicMock()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


# --- configure_tracing tests ---


class TestConfigureTracing:
    def test_disabled_by_default(self):
        from emiglio.observability import configure_tracing

        with patch("emiglio.config.settings", _mock_settings(tracing_enabled=False)):
            assert configure_tracing() is False
        assert os.environ.get("LANGSMITH_TRACING") != "true"

    def test_enabled_sets_env_vars(self):
        from emiglio.observability import configure_tracing

        s = _mock_settings(
            tracing_enabled=True,
            langsmith_api_key="lsv2_test_key_123",
            langsmith_project="test-project",
        )
        with patch("emiglio.config.settings", s):
            assert configure_tracing() is True

        assert os.environ["LANGSMITH_TRACING"] == "true"
        assert os.environ["LANGSMITH_API_KEY"] == "lsv2_test_key_123"
        assert os.environ["LANGSMITH_PROJECT"] == "test-project"
        assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
        assert os.environ["LANGCHAIN_API_KEY"] == "lsv2_test_key_123"
        assert os.environ["LANGCHAIN_PROJECT"] == "test-project"

    def test_empty_api_key_disables(self):
        from emiglio.observability import configure_tracing

        s = _mock_settings(tracing_enabled=True, langsmith_api_key="")
        with patch("emiglio.config.settings", s):
            assert configure_tracing() is False

    def test_unknown_backend_disables(self):
        from emiglio.observability import configure_tracing

        s = _mock_settings(tracing_enabled=True, tracing_backend="custom", langsmith_api_key="key")
        with patch("emiglio.config.settings", s):
            assert configure_tracing() is False


# --- Config fields test ---


class TestTracingConfig:
    def test_default_settings(self):
        """Tracing fields have correct defaults."""
        from emiglio.config import Settings

        s = Settings(_env_file=None)
        assert s.tracing_enabled is False
        assert s.tracing_backend == "langsmith"
        assert s.langsmith_api_key == ""
        assert s.langsmith_project == "emiglio"

    def test_env_var_override(self):
        """Tracing fields can be set via EMIGLIO_ env vars."""
        env = {
            "EMIGLIO_TRACING_ENABLED": "true",
            "EMIGLIO_LANGSMITH_API_KEY": "lsv2_test",
            "EMIGLIO_LANGSMITH_PROJECT": "my-project",
        }
        with patch.dict(os.environ, env):
            from emiglio.config import Settings
            s = Settings(_env_file=None)
            assert s.tracing_enabled is True
            assert s.langsmith_api_key == "lsv2_test"
            assert s.langsmith_project == "my-project"
