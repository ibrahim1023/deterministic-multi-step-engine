"""Provider abstraction for deterministic model access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Protocol


class ModelProvider(Protocol):
    def complete(
        self,
        *,
        model: str,
        messages: List[Mapping[str, str]],
        temperature: float = 0.0,
    ) -> "ModelResponse":
        ...


@dataclass(frozen=True)
class ModelResponse:
    model: str
    content: str
    raw: Dict[str, Any]


class LiteLLMProvider:
    """Thin deterministic wrapper over LiteLLM completion."""

    def __init__(self, completion_fn: Callable[..., Any] | None = None) -> None:
        self._completion_fn = completion_fn

    def _resolve_completion(self) -> Callable[..., Any]:
        if self._completion_fn is not None:
            return self._completion_fn
        try:
            from litellm import completion as litellm_completion
        except ImportError as exc:
            raise RuntimeError(
                "litellm is required for LiteLLMProvider. Install litellm first."
            ) from exc
        return litellm_completion

    def complete(
        self,
        *,
        model: str,
        messages: List[Mapping[str, str]],
        temperature: float = 0.0,
    ) -> ModelResponse:
        completion = self._resolve_completion()
        response = completion(
            model=model,
            messages=[dict(message) for message in messages],
            temperature=temperature,
            n=1,
        )

        content = ""
        choices = getattr(response, "choices", None)
        if choices is None and isinstance(response, dict):
            choices = response.get("choices")
        if isinstance(choices, list) and choices:
            choice0 = choices[0]
            message = getattr(choice0, "message", None)
            if message is None and isinstance(choice0, dict):
                message = choice0.get("message")
            if isinstance(message, dict):
                content = str(message.get("content") or "")
            else:
                content = str(getattr(message, "content", "") or "")

        return ModelResponse(
            model=model,
            content=content,
            raw=response if isinstance(response, dict) else {"response": response},
        )
