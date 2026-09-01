from typing import Optional

import requests

from app.llm.base import BaseLLMClient
from app import config


class OllamaClient(BaseLLMClient):
    """Fully offline, zero-cost option. Requires `ollama serve` running locally
    and the model already pulled (e.g. `ollama pull llama3.1`)."""
    name = "ollama"

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or config.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or config.OLLAMA_MODEL

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.2},
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
