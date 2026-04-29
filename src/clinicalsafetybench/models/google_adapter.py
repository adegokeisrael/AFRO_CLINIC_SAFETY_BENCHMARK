"""Google Generative AI adapter (Gemini 1.5 Pro, Flash, etc.)."""
from __future__ import annotations
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from clinicalsafetybench.models.base import BaseModelAdapter


class GoogleAdapter(BaseModelAdapter):
    def __init__(self, model_id: str = "gemini-1.5-pro", **kwargs):
        super().__init__(model_id=model_id, **kwargs)
        try:
            import google.generativeai as genai
            import os
            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
            self._genai = genai
            self._model_id = model_id
        except ImportError:
            raise ImportError("Run: pip install google-generativeai")
        except KeyError:
            raise EnvironmentError("GOOGLE_API_KEY not set in environment.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _call_api(self, system_prompt: str, user_prompt: str) -> tuple[str, Optional[int]]:
        model = self._genai.GenerativeModel(
            model_name=self._model_id,
            system_instruction=system_prompt,
            generation_config=self._genai.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            ),
        )
        resp   = model.generate_content(user_prompt)
        text   = resp.text or ""
        tokens = None
        if hasattr(resp, "usage_metadata"):
            tokens = (resp.usage_metadata.prompt_token_count or 0) + \
                     (resp.usage_metadata.candidates_token_count or 0)
        return text, tokens
