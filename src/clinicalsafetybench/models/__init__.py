from clinicalsafetybench.models.base import BaseModelAdapter
from clinicalsafetybench.models.openai_adapter import OpenAIAdapter
from clinicalsafetybench.models.anthropic_adapter import AnthropicAdapter
from clinicalsafetybench.models.google_adapter import GoogleAdapter

__all__ = ["BaseModelAdapter", "OpenAIAdapter", "AnthropicAdapter", "GoogleAdapter"]

REGISTRY: dict[str, type] = {
    "gpt-4o":             OpenAIAdapter,
    "gpt-4o-mini":        OpenAIAdapter,
    "claude-3-5-sonnet":  AnthropicAdapter,
    "claude-3-opus":      AnthropicAdapter,
    "gemini-1.5-pro":     GoogleAdapter,
    "gemini-1.5-flash":   GoogleAdapter,
}

def get_adapter(model_id: str, **kwargs) -> "BaseModelAdapter":
    key = model_id.lower()
    for pattern, cls in REGISTRY.items():
        if key.startswith(pattern.split("-")[0]):
            return cls(model_id=model_id, **kwargs)
    raise ValueError(f"No adapter for '{model_id}'. Available: {list(REGISTRY.keys())}")
