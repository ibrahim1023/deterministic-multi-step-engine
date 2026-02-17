import pytest

from src.model_provider import ModelResponse
from src.schemas import SynthesisOutputModel
from src.structured_generation import StructuredGenerationError, StructuredGenerator, enforce_schema


class FakeProvider:
    def __init__(self, content: str) -> None:
        self._content = content

    def complete(self, *, model, messages, temperature=0.0):  # noqa: ANN001
        return ModelResponse(model=model, content=self._content, raw={})


def test_enforce_schema_validates_payload() -> None:
    payload = enforce_schema({"summary": "hello"}, SynthesisOutputModel)
    assert payload == {"summary": "hello"}


def test_structured_generator_rejects_non_json() -> None:
    generator = StructuredGenerator(FakeProvider("not-json"))
    with pytest.raises(StructuredGenerationError):
        generator.generate(
            model_name="gpt-test",
            prompt="hello",
            response_model=SynthesisOutputModel,
        )


def test_structured_generator_validates_schema() -> None:
    generator = StructuredGenerator(FakeProvider('{"summary":"done"}'))
    payload = generator.generate(
        model_name="gpt-test",
        prompt="hello",
        response_model=SynthesisOutputModel,
    )
    assert payload["summary"] == "done"
