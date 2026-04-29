"""Base adapter interface all model adapters must implement."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import time, logging

logger = logging.getLogger(__name__)


@dataclass
class ModelResponse:
    model_id: str
    prompt_id: str
    system_prompt: str
    user_prompt: str
    raw_response: str
    latency_seconds: float
    tokens_used: Optional[int] = None
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None and bool(self.raw_response)


class BaseModelAdapter(ABC):
    def __init__(self, model_id: str, temperature: float = 0.0,
                 max_tokens: int = 1024, request_delay: float = 0.5):
        self.model_id      = model_id
        self.temperature   = temperature
        self.max_tokens    = max_tokens
        self.request_delay = request_delay

    @abstractmethod
    def _call_api(self, system_prompt: str, user_prompt: str) -> tuple[str, Optional[int]]:
        """Return (text_response, token_count_or_None)."""

    def query(self, system_prompt: str, user_prompt: str,
              prompt_id: str = "") -> ModelResponse:
        start = time.monotonic()
        try:
            raw, tokens = self._call_api(system_prompt, user_prompt)
            error = None
        except Exception as exc:
            logger.error("API error for %s [%s]: %s", self.model_id, prompt_id, exc)
            raw, tokens, error = "", None, str(exc)
        latency = time.monotonic() - start
        if self.request_delay:
            time.sleep(self.request_delay)
        return ModelResponse(
            model_id=self.model_id, prompt_id=prompt_id,
            system_prompt=system_prompt, user_prompt=user_prompt,
            raw_response=raw, latency_seconds=latency,
            tokens_used=tokens, error=error,
        )
