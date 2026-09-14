"""URI-000001 — the generator registry.

Seven generators, one per artifact family, resolved through a single frozen registry. The
registry is the only place a family is bound to an implementation, so the Generation
Engine stays a single execution path: it never branches on family, it looks the strategy
up and invokes the same contract.

The registry is validated at import time: every family declared in
:data:`~intelligence.realization.contracts.FAMILY_ORDER` must have exactly one generator,
and no generator may claim a family twice. A partially wired registry fails loudly at
import rather than silently skipping an artifact family at generation time.
"""

from __future__ import annotations

from intelligence.realization.contracts import FAMILY_ORDER, ArtifactFamily
from intelligence.realization.errors import GenerationError
from intelligence.realization.generators.api import ApiGenerator
from intelligence.realization.generators.architecture import ArchitectureGenerator
from intelligence.realization.generators.base import GenerationContext, Generator
from intelligence.realization.generators.deployment import DeploymentGenerator
from intelligence.realization.generators.documentation import DocumentationGenerator
from intelligence.realization.generators.runtime import RuntimeGenerator
from intelligence.realization.generators.schema import SchemaGenerator
from intelligence.realization.generators.tests import TestGenerator

#: Every realization generator, in family realization order.
GENERATORS: tuple[Generator, ...] = (
    ArchitectureGenerator(),
    SchemaGenerator(),
    ApiGenerator(),
    RuntimeGenerator(),
    DeploymentGenerator(),
    TestGenerator(),
    DocumentationGenerator(),
)


def _build_registry() -> dict[ArtifactFamily, Generator]:
    registry: dict[ArtifactFamily, Generator] = {}
    for generator in GENERATORS:
        if generator.family in registry:
            raise GenerationError(
                "artifact family claimed by more than one generator",
                family=generator.family.value,
                generator=generator.name,
            )
        registry[generator.family] = generator
    missing = [family.value for family in FAMILY_ORDER if family not in registry]
    if missing:
        raise GenerationError("artifact family has no generator", missing=missing)
    return registry


#: Family → generator. Complete and unambiguous by construction.
REGISTRY: dict[ArtifactFamily, Generator] = _build_registry()


def generator_for(family: ArtifactFamily) -> Generator:
    """Return the single generator bound to ``family``."""
    generator = REGISTRY.get(family)
    if generator is None:  # pragma: no cover - _build_registry guarantees completeness
        raise GenerationError("no generator for artifact family", family=family.value)
    return generator


def registry_manifest() -> list[dict[str, str]]:
    """A deterministic description of the wired generators (recorded in evidence)."""
    return [
        {
            "family": family.value,
            "generator": REGISTRY[family].name,
            "version": REGISTRY[family].version,
            "implementation": type(REGISTRY[family]).__name__,
        }
        for family in FAMILY_ORDER
    ]


__all__ = [
    "GENERATORS",
    "REGISTRY",
    "ApiGenerator",
    "ArchitectureGenerator",
    "DeploymentGenerator",
    "DocumentationGenerator",
    "GenerationContext",
    "Generator",
    "RuntimeGenerator",
    "SchemaGenerator",
    "TestGenerator",
    "generator_for",
    "registry_manifest",
]
