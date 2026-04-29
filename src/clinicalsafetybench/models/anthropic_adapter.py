"""Anthropic model adapter (Claude 3.5 Sonnet, Claude 3 Opus, etc.)."""
from __future__ import annotations
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from clinicalsafetybench.models.base import BaseModelAdapter


class AnthropicAdapter(BaseModelAdapter):
    def __init__(self, model_id: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(model_id=model_id, **kwargs)
        try:
            import anthropic, os
            self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        except ImportError:
            raise ImportError("Run: pip install anthropic")
        except KeyError:
            raise EnvironmentError("ANTHROPIC_API_KEY not set in environment.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _call_api(self, system_prompt: str, user_prompt: str) -> tuple[str, Optional[int]]:
        resp = self._client.messages.create(
            model=self.model_id,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text   = resp.content[0].text if resp.content else ""
        tokens = resp.usage.input_tokens + resp.usage.output_tokens if resp.usage else None
        return text, tokens
