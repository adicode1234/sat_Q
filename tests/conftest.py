"""Keep disposable test directories inside the workspace on restricted Windows hosts."""
from pathlib import Path
import uuid
import os
import pytest


def pytest_configure(config):
    if config.option.basetemp is None:
        # Unique per run: pytest never clears a pre-existing user directory.
        parent = Path(__file__).resolve().parents[1]/'.test-runs'
        parent.mkdir(exist_ok=True)
        config.option.basetemp = str(parent/uuid.uuid4().hex)


@pytest.fixture(autouse=True, scope='session')
def disable_cloud_vision_in_tests():
    """Disable cloud vision for all tests — prevents .env API keys from
    triggering real network calls in a sandboxed / offline test environment."""
    os.environ.pop('SATQUERY_CLOUD_VISION', None)
    os.environ.pop('SATQUERY_VISION_PROVIDER', None)
    os.environ.pop('OPENROUTER_API_KEY', None)
    os.environ.pop('OPENROUTER_MODEL', None)
    os.environ.pop('GEMINI_API_KEY', None)
    os.environ.pop('GEMINI_MODEL', None)
    os.environ.pop('OPENAI_API_KEY', None)
    os.environ.pop('NOVITA_API_KEY', None)
    os.environ.pop('NOVITA_MODEL', None)
    os.environ.pop('OLLAMA_MODEL', None)
    # Reset module-level state in cloud_vision
    try:
        from models import cloud_vision
        cloud_vision.configure(None, False)
        # PROVIDERS defaults are evaluated at import time — reset to hardcoded defaults
        # so tests don't pick up any model names from .env that was loaded by the server
        cloud_vision.PROVIDERS['openrouter'] = ('OpenRouter', 'google/gemini-2.5-flash', 'OPENROUTER_API_KEY')
        cloud_vision.PROVIDERS['gemini']     = ('Google Gemini', 'gemini-2.5-flash', 'GEMINI_API_KEY')
        cloud_vision.PROVIDERS['openai']     = ('OpenAI', 'gpt-4.1', 'OPENAI_API_KEY')
        cloud_vision.PROVIDERS['novita']     = ('Novita AI', 'meta-llama/llama-3.2-11b-vision-instruct', 'NOVITA_API_KEY')
        cloud_vision.PROVIDERS['ollama']     = ('Local Ollama', '', 'OLLAMA_API_KEY')
    except Exception:
        pass
    yield
    # Nothing to restore — tests are isolated


