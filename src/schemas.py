"""Pydantic schemas for deterministic engine contracts."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _is_semver(value: str) -> bool:
    return bool(SEMVER_RE.match(value))


class VerificationPathConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    evidence_required: bool | None = None


class LoopStopCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    operator: Literal[
        "equals",
        "not_equals",
        "contains",
        "not_contains",
        "in",
        "not_in",
        "gt",
        "gte",
        "lt",
        "lte",
    ]
    value: Any


class LoopConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    start_step: str = Field(min_length=1)
    end_step: str = Field(min_length=1)
    max_iterations: int = Field(ge=1)
    stop_condition: LoopStopCondition


class ProblemInputsModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    prompt: str = Field(min_length=1)
    constraints: List[str] | None = None
    goals: List[str] | None = None
    context: Dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_trimmed(self) -> "ProblemInputsModel":
        if not self.prompt.strip():
            raise ValueError("problem_spec.inputs.prompt must be a non-empty string")
        if self.constraints is not None:
            for item in self.constraints:
                if not item or not item.strip():
                    raise ValueError(
                        "problem_spec.inputs.constraints must contain non-empty strings"
                    )
        if self.goals is not None:
            for item in self.goals:
                if not item or not item.strip():
                    raise ValueError(
                        "problem_spec.inputs.goals must contain non-empty strings"
                    )
        return self


class ProblemSettingsModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    evidence_required: bool | None = None
    max_steps: int | None = Field(default=None, gt=0)
    policy_profile: str | None = None
    model_profile: str | None = None
    model_provider: Literal["litellm"] | None = None
    model_name: str | None = None
    orchestration_framework: Literal["native", "langgraph"] | None = None
    structured_generation: bool | None = None
    verification_paths: List[VerificationPathConfig] | None = None
    loop: LoopConfigModel | None = None

    @model_validator(mode="after")
    def _validate_strings(self) -> "ProblemSettingsModel":
        if self.policy_profile is not None and not self.policy_profile.strip():
            raise ValueError(
                "problem_spec.settings.policy_profile must be a non-empty string"
            )
        if self.model_profile is not None and not self.model_profile.strip():
            raise ValueError(
                "problem_spec.settings.model_profile must be a non-empty string"
            )
        if self.model_name is not None and not self.model_name.strip():
            raise ValueError(
                "problem_spec.settings.model_name must be a non-empty string"
            )
        return self


class ProblemSpecModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: str
    id: str = Field(min_length=1)
    created_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    inputs: ProblemInputsModel
    settings: ProblemSettingsModel | None = None
    provenance: Dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_version(self) -> "ProblemSpecModel":
        if not _is_semver(self.version):
            raise ValueError(
                "problem_spec.version must be a semantic version (MAJOR.MINOR.PATCH)"
            )
        major = int(self.version.split(".", 1)[0])
        if major != 1:
            raise ValueError("problem_spec.version major must be 1")
        return self


class ReasoningStateModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    step_index: int = Field(ge=0)
    status: Literal["pending", "running", "failed", "completed"]
    artifacts: Dict[str, Any] | None = None
    metadata: Dict[str, Any] | None = None


class StepErrorModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)


class StepResultModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: str
    step: str = Field(min_length=1)
    status: Literal["success", "failed", "skipped"]
    input_hash: str = Field(min_length=1)
    output_hash: str = Field(min_length=1)
    started_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    finished_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    output: Dict[str, Any] | None = None
    errors: List[StepErrorModel] | None = None

    @model_validator(mode="after")
    def _validate_contract(self) -> "StepResultModel":
        if not _is_semver(self.version):
            raise ValueError(
                "StepResult.version must be a semantic version (MAJOR.MINOR.PATCH)"
            )
        if self.status == "success" and self.output is None:
            raise ValueError("StepResult.success requires output")
        if self.status == "failed" and not self.errors:
            raise ValueError("StepResult.failed requires errors")
        if self.status == "skipped" and (self.output is not None or self.errors):
            raise ValueError("StepResult.skipped must not include output or errors")
        return self


class SynthesisOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)


def _as_value_error(exc: ValidationError, *, fallback_prefix: str) -> ValueError:
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first.get("loc") or [])
    message = first.get("msg", "invalid value")
    if location:
        return ValueError(f"{fallback_prefix}.{location}: {message}")
    return ValueError(f"{fallback_prefix}: {message}")


def parse_problem_spec(problem_spec: Mapping[str, Any]) -> ProblemSpecModel:
    try:
        return ProblemSpecModel.model_validate(problem_spec)
    except ValidationError as exc:
        raise _as_value_error(exc, fallback_prefix="problem_spec") from exc


def parse_reasoning_state(state: Mapping[str, Any]) -> ReasoningStateModel:
    try:
        return ReasoningStateModel.model_validate(state)
    except ValidationError as exc:
        raise _as_value_error(exc, fallback_prefix="ReasoningState") from exc


def parse_step_result(result: Mapping[str, Any]) -> StepResultModel:
    try:
        return StepResultModel.model_validate(result)
    except ValidationError as exc:
        raise _as_value_error(exc, fallback_prefix="StepResult") from exc
