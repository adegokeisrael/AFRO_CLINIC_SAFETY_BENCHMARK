"""OpenAI model adapter (GPT-4o, GPT-4o-mini, etc.)."""
from __future__ import annotations
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from clinicalsafetybench.models.base import BaseModelAdapter


class OpenAIAdapter(BaseModelAdapter):
    def __init__(self, model_id: str = "gpt-4o", **kwargs):
        super().__init__(model_id=model_id, **kwargs)
        try:
            from openai import OpenAI
            import os
            self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        except ImportError:
            raise ImportError("Run: pip install openai")
        except KeyError:
            raise EnvironmentError("OPENAI_API_KEY not set in environment.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _call_api(self, system_prompt: str, user_prompt: str) -> tuple[str, Optional[int]]:
        resp = self._client.chat.completions.create(
            model=self.model_id,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        )
        text   = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else None
        return text, tokens
