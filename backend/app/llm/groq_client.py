from typing import Optional

from app.llm.base import BaseLLMClient
from app import config


class GroqClient(BaseLLMClient):
    name = "groq"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from groq import Groq  # local import so app still boots without the package installed
        self.api_key = api_key or config.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set. Add it to your .env file.")
        self.model = model or config.GROQ_MODEL
        self.client = Groq(api_key=self.api_key)

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return resp.choices[0].message.content
