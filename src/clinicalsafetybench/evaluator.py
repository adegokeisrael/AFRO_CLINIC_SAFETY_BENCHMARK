"""
evaluator.py
------------
Orchestrates running the benchmark: loads prompts, queries the model,
scores each response, and returns structured results.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import List, Optional

from tqdm import tqdm

from clinicalsafetybench.benchmark import Prompt
from clinicalsafetybench.models.base import BaseModelAdapter
from clinicalsafetybench.scoring.rubric import Rubric, PromptScore

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    """Flat record wrapping PromptScore for JSON serialisation and reporting."""
    prompt_id:    str
    country:      str
    condition:    str
    model_id:     str
    raw_response: str
    overall_pass: bool
    failures:     List[str]
    notes:        str = ""

    def to_dict(self) -> dict:
        return {
            "prompt_id":    self.prompt_id,
            "country":      self.country,
            "condition":    self.condition,
            "model_id":     self.model_id,
            "overall_pass": self.overall_pass,
            "failure_count":len(self.failures),
            "failures":     self.failures,
            "raw_response": self.raw_response,
            "notes":        self.notes,
        }


class Evaluator:
    """
    Run ClinicalSafetyBench against a model adapter.

    Parameters
    ----------
    adapter  : configured BaseModelAdapter instance
    rubric   : Rubric instance (auto-created if not provided)
    """

    def __init__(self, adapter: BaseModelAdapter, rubric: Optional[Rubric] = None):
        self.adapter = adapter
        self.rubric  = rubric or Rubric()

    def run(self, prompts: List[Prompt], show_progress: bool = True) -> List[EvalResult]:
        """Evaluate all prompts. Returns a list of EvalResult objects."""
        results: List[EvalResult] = []
        iterator = tqdm(prompts, desc=self.adapter.model_id) if show_progress else prompts

        for prompt in iterator:
            # Query the model — returns a ModelResponse object
            response = self.adapter.query(
                system_prompt=prompt.build_system_prompt(),
                user_prompt=prompt.build_user_prompt(),
                prompt_id=prompt.id,
            )

            # Pass ModelResponse to rubric (rubric handles failed responses internally)
            score = self.rubric.score(prompt=prompt, response=response)

            results.append(EvalResult(
                prompt_id=prompt.id,
                country=prompt.country,
                condition=prompt.condition,
                model_id=self.adapter.model_id,
                raw_response=response.raw_response,
                overall_pass=score.overall_pass,
                failures=score.triggered_failure_modes,
                notes=score.scorer_notes,
            ))

        total  = len(results)
        passed = sum(1 for r in results if r.overall_pass)
        logger.info("%s: %d/%d passed (GAR=%.1f%%)",
                    self.adapter.model_id, passed, total,
                    100 * passed / total if total else 0)
        return results

    @classmethod
    def from_model_id(cls, model_id: str, **adapter_kwargs) -> "Evaluator":
        from clinicalsafetybench.models import get_adapter
        return cls(adapter=get_adapter(model_id, **adapter_kwargs))
