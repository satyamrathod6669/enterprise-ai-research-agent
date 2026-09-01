from typing import Optional

from app.llm.base import BaseLLMClient
from app import config


class GeminiClient(BaseLLMClient):
    name = "gemini"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        import google.generativeai as genai
        self.api_key = api_key or config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")
        genai.configure(api_key=self.api_key)
        self.model_name = model or config.GEMINI_MODEL
        self._genai = genai
        self.model = genai.GenerativeModel(self.model_name)

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        resp = self.model.generate_content(
            [system_prompt, user_prompt],
            generation_config=self._genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.2,
            ),
        )
        return resp.text
