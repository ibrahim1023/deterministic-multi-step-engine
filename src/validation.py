"""Validation helpers for deterministic schemas."""

from __future__ import annotations

import re
from typing import Any, Mapping


_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def validate_semver(value: str, *, field: str) -> None:
    if not isinstance(value, str) or not _SEMVER_RE.match(value):
        raise ValueError(f"{field} must be a semantic version (MAJOR.MINOR.PATCH)")


def validate_iso8601_utc(value: str, *, field: str) -> None:
    if not isinstance(value, str) or not _ISO_UTC_RE.match(value):
        raise ValueError(f"{field} must be an ISO-8601 UTC timestamp ending with Z")


def validate_non_empty_str(value: Any, *, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def validate_optional_str_list(value: Any, *, field: str) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of strings")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field} must contain non-empty strings")


def validate_problem_spec(problem_spec: Mapping[str, Any]) -> None:
    if not isinstance(problem_spec, Mapping):
        raise ValueError("problem_spec must be an object")

    version = problem_spec.get("version")
    validate_semver(version, field="problem_spec.version")

    major = int(str(version).split(".")[0])
    if major != 1:
        raise ValueError("problem_spec.version major must be 1")

    validate_non_empty_str(problem_spec.get("id"), field="problem_spec.id")
    validate_iso8601_utc(
        problem_spec.get("created_at"), field="problem_spec.created_at")

    inputs = problem_spec.get("inputs")
    if not isinstance(inputs, Mapping):
        raise ValueError("problem_spec.inputs must be an object")
    validate_non_empty_str(inputs.get("prompt"), field="problem_spec.inputs.prompt")
    validate_optional_str_list(
        inputs.get("constraints"), field="problem_spec.inputs.constraints")
    validate_optional_str_list(inputs.get("goals"), field="problem_spec.inputs.goals")
    context = inputs.get("context")
    if context is not None and not isinstance(context, Mapping):
        raise ValueError("problem_spec.inputs.context must be an object")

    settings = problem_spec.get("settings")
    if settings is not None:
        if not isinstance(settings, Mapping):
            raise ValueError("problem_spec.settings must be an object")
        evidence_required = settings.get("evidence_required")
        if evidence_required is not None and not isinstance(evidence_required, bool):
            raise ValueError("problem_spec.settings.evidence_required must be a boolean")
        max_steps = settings.get("max_steps")
        if max_steps is not None:
            if not isinstance(max_steps, int) or max_steps <= 0:
                raise ValueError("problem_spec.settings.max_steps must be > 0")
        policy_profile = settings.get("policy_profile")
        if policy_profile is not None and (not isinstance(policy_profile, str) or not policy_profile.strip()):
            raise ValueError("problem_spec.settings.policy_profile must be a non-empty string")
        model_profile = settings.get("model_profile")
        if model_profile is not None and (not isinstance(model_profile, str) or not model_profile.strip()):
            raise ValueError("problem_spec.settings.model_profile must be a non-empty string")

    provenance = problem_spec.get("provenance")
    if provenance is not None and not isinstance(provenance, Mapping):
        raise ValueError("problem_spec.provenance must be an object")
