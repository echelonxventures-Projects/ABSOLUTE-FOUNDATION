"""EC-1 Factory implementations (EPIC-006, TASK-000042).

The initial set of factories, all implementing the common contract and reusing the
single orchestrator execution path. :func:`build_default_registry` wires them into
a :class:`~engine.factory.registry.FactoryRegistry` with **explicit** registration
(no dynamic imports).
"""

from __future__ import annotations

from engine.factory.factories.api import ApiFactory
from engine.factory.factories.application import ApplicationFactory
from engine.factory.factories.base import (
    DEFAULT_STAGES,
    BaseFactory,
    ExecutionContext,
    Factory,
    FactoryExecution,
)
from engine.factory.factories.data import DataFactory
from engine.factory.factories.service import ServiceFactory
from engine.factory.registry import FactoryRegistry

#: The initial factory set, in deterministic construction order.
DEFAULT_FACTORIES: tuple[type[BaseFactory], ...] = (
    DataFactory,
    ApiFactory,
    ServiceFactory,
    ApplicationFactory,
)


def build_default_registry() -> FactoryRegistry:
    """Construct a registry with the four initial factories explicitly registered."""
    registry = FactoryRegistry()
    for factory_cls in DEFAULT_FACTORIES:
        registry.register_factory(factory_cls())
    return registry


__all__ = [
    "DEFAULT_STAGES",
    "BaseFactory",
    "Factory",
    "FactoryExecution",
    "ExecutionContext",
    "DataFactory",
    "ApiFactory",
    "ServiceFactory",
    "ApplicationFactory",
    "DEFAULT_FACTORIES",
    "build_default_registry",
]
