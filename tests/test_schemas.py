import pytest

from src.schemas import parse_problem_spec


def _base_problem_spec() -> dict:
    return {
        "version": "1.0.0",
        "id": "req-schema-1",
        "created_at": "2026-02-02T00:00:00Z",
        "inputs": {"prompt": "hello"},
    }


def test_parse_problem_spec_valid() -> None:
    model = parse_problem_spec(_base_problem_spec())
    assert model.id == "req-schema-1"


def test_parse_problem_spec_rejects_major_version() -> None:
    spec = _base_problem_spec()
    spec["version"] = "2.0.0"
    with pytest.raises(ValueError):
        parse_problem_spec(spec)


def test_parse_problem_spec_rejects_blank_prompt() -> None:
    spec = _base_problem_spec()
    spec["inputs"] = {"prompt": "   "}
    with pytest.raises(ValueError):
        parse_problem_spec(spec)
