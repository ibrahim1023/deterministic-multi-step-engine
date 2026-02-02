import pytest

from src.routing import (
    DEFAULT_POLICY,
    PolicyRegistry,
    RoutingPolicy,
    ensure_steps_known,
    resolve_steps,
    select_policy_name,
)


def test_select_policy_name_defaults() -> None:
    assert select_policy_name({}) == "default"
    assert select_policy_name({"settings": {}}) == "default"


def test_select_policy_name_uses_settings() -> None:
    spec = {"settings": {"policy_profile": "fast"}}
    assert select_policy_name(spec) == "fast"


def test_registry_register_and_get() -> None:
    registry = PolicyRegistry()
    registry.register(DEFAULT_POLICY)
    assert registry.get("default") == DEFAULT_POLICY
    with pytest.raises(ValueError):
        registry.register(DEFAULT_POLICY)
    with pytest.raises(KeyError):
        registry.get("missing")


def test_resolve_steps_uses_registry() -> None:
    registry = PolicyRegistry()
    registry.register(RoutingPolicy(name="fast", steps=["Normalize"]))
    steps = resolve_steps({"settings": {"policy_profile": "fast"}}, registry=registry)
    assert steps == ["Normalize"]


def test_ensure_steps_known() -> None:
    ensure_steps_known(["Normalize", "Verify"], ["Normalize", "Verify"])
    with pytest.raises(ValueError):
        ensure_steps_known(["Normalize", "Unknown"], ["Normalize", "Verify"])
