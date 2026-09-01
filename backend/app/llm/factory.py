from app import config
from app.llm.base import BaseLLMClient


def get_llm_client() -> BaseLLMClient:
    """
    Single point of provider selection. Change LLM_PROVIDER in .env to swap
    Groq <-> Gemini <-> Ollama with NO code changes anywhere else in the app —
    this satisfies the challenge's "free-tier service becomes unavailable"
    resilience requirement.
    """
    provider = config.LLM_PROVIDER
    if provider == "groq":
        from app.llm.groq_client import GroqClient
        return GroqClient()
    if provider == "gemini":
        from app.llm.gemini_client import GeminiClient
        return GeminiClient()
    if provider == "ollama":
        from app.llm.ollama_client import OllamaClient
        return OllamaClient()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
