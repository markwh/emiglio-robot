"""Observability module -- opt-in LangSmith tracing for LLM calls."""

import logging
import os

logger = logging.getLogger(__name__)


def configure_tracing() -> bool:
    """Configure LangSmith tracing from Emiglio settings.

    Sets the environment variables that LangSmith and LangChain SDKs read.
    Returns True if tracing was enabled, False otherwise.

    Call early in startup, before creating LangChain/Anthropic clients.
    """
    from emiglio.config import settings

    if not settings.tracing_enabled:
        logger.debug("Tracing disabled")
        return False

    if settings.tracing_backend != "langsmith":
        logger.warning("Unknown tracing backend %r -- only 'langsmith' is supported", settings.tracing_backend)
        return False

    if not settings.langsmith_api_key:
        logger.warning("Tracing enabled but EMIGLIO_LANGSMITH_API_KEY is empty -- disabling")
        return False

    # LangSmith SDK env vars
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project

    # LangChain auto-tracing env vars (for server-side LangGraph agent)
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    logger.info("LangSmith tracing enabled (project=%s)", settings.langsmith_project)
    return True


def wrap_anthropic_client(client):
    """Wrap an Anthropic client with LangSmith tracing if active.

    Returns the client unmodified when tracing is disabled.
    """
    if os.environ.get("LANGSMITH_TRACING") != "true":
        return client

    try:
        from langsmith.wrappers import wrap_anthropic

        wrapped = wrap_anthropic(client)
        logger.info("Anthropic client wrapped with LangSmith tracing")
        return wrapped
    except Exception as e:
        logger.warning("Failed to wrap Anthropic client: %s", e)
        return client
