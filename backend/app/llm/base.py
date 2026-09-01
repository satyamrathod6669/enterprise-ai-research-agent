"""
Abstract LLM interface. Every concrete client (Groq, Gemini, Ollama) implements
`complete_json`, which asks the model to return structured JSON matching a
schema description. This is the seam that lets us hot-swap providers with a
single environment variable (LLM_PROVIDER) and zero code changes elsewhere
in the pipeline.
"""
from abc import ABC, abstractmethod
import json
import re


class BaseLLMClient(ABC):
    name: str = "base"

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        """Return raw text completion from the model."""
        raise NotImplementedError

    def complete_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 1536):
        """
        Ask the model for JSON and parse it defensively. LLMs sometimes wrap
        JSON in prose or markdown fences, so we extract the first {...} or [...]
        block before parsing rather than trusting raw output.
        """
        strict_system = (
            system_prompt
            + "\n\nYou must respond with ONLY valid JSON. No prose, no markdown "
              "fences, no explanation before or after the JSON."
        )
        raw = self.complete(strict_system, user_prompt, max_tokens=max_tokens)
        return self._extract_json(raw)

    @staticmethod
    def _extract_json(raw: str):
        raw = raw.strip()
        raw = re.sub(r"^```(json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Fallback: find the earliest-opening {...} or [...] span (whichever
        # bracket type actually opens first in the text is the real outer
        # container — checking a fixed order caused arrays like `[{...}]` to
        # be mis-parsed as just the inner object).
        candidates = []
        for open_c, close_c in [("{", "}"), ("[", "]")]:
            start = raw.find(open_c)
            end = raw.rfind(close_c)
            if start != -1 and end != -1 and end > start:
                candidates.append((start, raw[start:end + 1]))
        for _, candidate in sorted(candidates, key=lambda x: x[0]):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        raise ValueError(f"Could not parse JSON from LLM response: {raw[:300]}")
