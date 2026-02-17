"""Structured generation with schema enforcement."""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, TypeVar

from pydantic import BaseModel, ValidationError

from src.model_provider import ModelProvider


T = TypeVar("T", bound=BaseModel)


class StructuredGenerationError(ValueError):
    pass


def enforce_schema(payload: Mapping[str, Any], response_model: type[T]) -> Dict[str, Any]:
    try:
        validated = response_model.model_validate(dict(payload))
    except ValidationError as exc:
        raise StructuredGenerationError(str(exc)) from exc
    return validated.model_dump()


class StructuredGenerator:
    """Schema-conformant generation using a model provider."""

    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider

    def generate(
        self,
        *,
        model_name: str,
        prompt: str,
        response_model: type[T],
    ) -> Dict[str, Any]:
        response = self._provider.complete(
            model=model_name,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            payload = json.loads(response.content)
        except json.JSONDecodeError as exc:
            raise StructuredGenerationError(
                "Model response is not valid JSON for structured generation"
            ) from exc
        if not isinstance(payload, dict):
            raise StructuredGenerationError(
                "Model response JSON must be an object for structured generation"
            )
        return enforce_schema(payload, response_model)
