"""TASK-000045 — Factory registry tests (TASK-000040)."""

from __future__ import annotations

import pytest

from engine.compiler.ir import BlueprintFamily
from engine.factory import build_default_registry
from engine.factory.classifier import resolve_blueprint_class
from engine.factory.contracts import FactoryCapability, FactoryDescriptor
from engine.factory.errors import FactoryNotFoundError, FactoryRegistrationError
from engine.factory.factories import ApiFactory, DataFactory
from engine.factory.factories.base import BaseFactory
from engine.factory.registry import FactoryRegistry


def test_default_registry_has_four_factories():
    registry = build_default_registry()
    assert len(registry) == 4
    classes = [d.blueprint_class for d in registry.list_factories()]
    assert classes == ["BP-API", "BP-APPLICATION", "BP-DATA", "BP-SERVICE"]  # sorted, deterministic


def test_register_returns_immutable_descriptor():
    registry = FactoryRegistry()
    descriptor = registry.register_factory(DataFactory())
    assert isinstance(descriptor, FactoryDescriptor)
    assert descriptor.name == "data-factory"
    assert descriptor.blueprint_class == "BP-DATA"
    with pytest.raises((AttributeError, TypeError)):
        descriptor.name = "x"  # type: ignore[misc]


def test_duplicate_registration_rejected():
    registry = FactoryRegistry()
    registry.register_factory(DataFactory())
    with pytest.raises(FactoryRegistrationError) as exc:
        registry.register_factory(DataFactory())
    assert "already registered" in exc.value.message


def test_resolve_by_family_classification_and_string():
    registry = build_default_registry()
    by_family = registry.resolve_factory(BlueprintFamily.API)
    by_string = registry.resolve_factory("BP-API")
    by_class = registry.resolve_factory(resolve_blueprint_class({"family": "BP-API"}))
    assert by_family is by_string is by_class
    assert isinstance(by_family, ApiFactory)


def test_resolve_unknown_class_string_rejected():
    registry = build_default_registry()
    with pytest.raises(FactoryNotFoundError):
        registry.resolve_factory("BP-QUANTUM")


def test_resolve_unregistered_family_rejected():
    registry = build_default_registry()
    # CONTRACT has no factory in the default set
    with pytest.raises(FactoryNotFoundError) as exc:
        registry.resolve_factory(BlueprintFamily.CONTRACT)
    assert "no factory is registered" in exc.value.message


def test_has_factory():
    registry = build_default_registry()
    assert registry.has_factory("BP-DATA") is True
    assert registry.has_factory(BlueprintFamily.EVENT) is False


def test_capability_discovery():
    registry = build_default_registry()
    caps = registry.capabilities()
    assert len(caps) == 4
    assert all(isinstance(c, FactoryCapability) for c in caps)
    # every factory shares the same uniform stage set (one execution path)
    uniform = {("classify", "compile", "assemble", "deploy", "evidence")}
    assert {tuple(c.stages) for c in caps} == uniform


def test_factory_exposes_capability_property():
    factory = DataFactory()
    assert factory.capability is factory.descriptor.capability
    assert factory.capability.blueprint_class == "BP-DATA"


def test_resolve_unsupported_key_type_rejected():
    registry = FactoryRegistry()
    with pytest.raises(FactoryNotFoundError):
        registry.resolve_factory(123)  # type: ignore[arg-type]


def test_register_factory_with_unknown_class_rejected():
    class BadFactory(BaseFactory):
        blueprint_class = BlueprintFamily.DATA
        factory_name = "bad"

    factory = BadFactory()
    # forge a descriptor with an unknown class to exercise the guard
    object.__setattr__(
        factory,
        "_descriptor",
        FactoryDescriptor(
            name="bad",
            blueprint_class="BP-QUANTUM",
            capability=FactoryCapability(blueprint_class="BP-QUANTUM", stages=()),
        ),
    )
    with pytest.raises(FactoryRegistrationError):
        FactoryRegistry().register_factory(factory)


def test_base_factory_requires_declarations():
    class NoClass(BaseFactory):
        factory_name = "x"

    with pytest.raises(TypeError):
        NoClass()

    class NoName(BaseFactory):
        blueprint_class = BlueprintFamily.DATA

    with pytest.raises(TypeError):
        NoName()
