"""URI-000001 — the value types of the realization pipeline.

Every type here is frozen, slotted, wall-clock free, and **content-addressed**: its
``seal`` is the canonical hash of its own core, so a downstream stage can prove which
upstream state it was derived from, and any post-hoc mutation is detectable.

The chain of seals *is* the traceability spine::

    knowledge_seal → plan.seal → composition.seal → manifest.seal → record.seal

Nothing in this module performs I/O, reads a clock, or holds authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from intelligence.realization.canonical import content_hash, sha256_text, short_seal
from intelligence.realization.errors import PlanningError

#: Versioned identity of the realization contract surface (AR-03 / PL-05).
REALIZATION_CONTRACT_NAME = "intelligence.realization"
REALIZATION_CONTRACT_VERSION = "1.0.0"

#: Every artifact records that it derives its content from canonical knowledge and
#: carries no authority of its own.
DERIVED_AUTHORITY = "NONE (derived from canonical knowledge)"


class RealizationStage(str, Enum):
    """The ordered stages of the realization pipeline."""

    INTAKE = "intake"
    PLANNING = "planning"
    COMPOSITION = "composition"
    GENERATION = "generation"
    IMPLEMENTATION = "implementation"
    GOVERNANCE = "governance"
    TRACEABILITY = "traceability"
    EVIDENCE = "evidence"


class ArtifactFamily(str, Enum):
    """The seven artifact families a realization target is realized into."""

    ARCHITECTURE = "architecture"
    API = "api"
    SCHEMA = "schema"
    RUNTIME = "runtime"
    TEST = "test"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"

    @classmethod
    def coerce(cls, value: Any) -> ArtifactFamily:
        """Return the member for ``value`` or fail loudly (no silent defaulting)."""
        try:
            return cls(str(value))
        except ValueError as exc:  # pragma: no cover - defensive
            raise PlanningError("unknown artifact family", value=value) from exc


class MediaKind(str, Enum):
    """The concrete serialization of a generated artifact."""

    JSON = "json"
    MARKDOWN = "markdown"
    PYTHON = "python"
    SQL = "sql"
    YAML = "yaml"


#: The realization dependency order between families. Architecture is derived first
#: because every other family is expressed in terms of its components; tests and
#: documentation come last because they assert/describe everything before them.
FAMILY_DEPENDENCIES: Mapping[ArtifactFamily, tuple[ArtifactFamily, ...]] = {
    ArtifactFamily.ARCHITECTURE: (),
    ArtifactFamily.SCHEMA: (ArtifactFamily.ARCHITECTURE,),
    ArtifactFamily.API: (ArtifactFamily.ARCHITECTURE, ArtifactFamily.SCHEMA),
    ArtifactFamily.RUNTIME: (ArtifactFamily.ARCHITECTURE, ArtifactFamily.SCHEMA),
    ArtifactFamily.DEPLOYMENT: (ArtifactFamily.RUNTIME,),
    ArtifactFamily.TEST: (
        ArtifactFamily.ARCHITECTURE,
        ArtifactFamily.SCHEMA,
        ArtifactFamily.API,
        ArtifactFamily.RUNTIME,
        ArtifactFamily.DEPLOYMENT,
    ),
    ArtifactFamily.DOCUMENTATION: (
        ArtifactFamily.ARCHITECTURE,
        ArtifactFamily.SCHEMA,
        ArtifactFamily.API,
        ArtifactFamily.RUNTIME,
        ArtifactFamily.DEPLOYMENT,
        ArtifactFamily.TEST,
    ),
}

#: Deterministic realization order (a topological sort of FAMILY_DEPENDENCIES,
#: ties broken alphabetically so the order is stable across runs and machines).
FAMILY_ORDER: tuple[ArtifactFamily, ...] = (
    ArtifactFamily.ARCHITECTURE,
    ArtifactFamily.SCHEMA,
    ArtifactFamily.API,
    ArtifactFamily.RUNTIME,
    ArtifactFamily.DEPLOYMENT,
    ArtifactFamily.TEST,
    ArtifactFamily.DOCUMENTATION,
)


def _seal(core: Mapping[str, Any]) -> str:
    """Seal a value type's core with the canonical content hash."""
    return content_hash(dict(core))


def slug(text: str) -> str:
    """Return a deterministic, filesystem-safe, lower-case slug for ``text``."""
    out = []
    prev_dash = False
    for char in str(text).strip().lower():
        if char.isalnum():
            out.append(char)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-") or "unnamed"


def identifier(text: str) -> str:
    """Return a deterministic, valid Python identifier fragment for ``text``."""
    body = slug(text).replace("-", "_")
    return body if body[0].isalpha() or body[0] == "_" else f"u_{body}"


@dataclass(frozen=True, slots=True)
class Invariant:
    """A normative canonical statement a realization must honour at runtime."""

    cko_id: str
    kind: str
    authority: str
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "cko_id": self.cko_id,
            "kind": self.kind,
            "authority": self.authority,
            "statement": self.statement,
        }


@dataclass(frozen=True, slots=True)
class RealizationTarget:
    """One coherent body of canonical knowledge to be realized (a knowledge universe).

    A target is *derived*, never declared: its membership, layers, and invariants are
    read out of the canonical store.
    """

    universe: str
    cko_ids: tuple[str, ...]
    decision_ids: tuple[str, ...]
    kinds: tuple[str, ...]
    authorities: tuple[str, ...]
    lifecycles: tuple[str, ...]
    owners: tuple[str, ...]
    invariants: tuple[Invariant, ...]
    principles: tuple[str, ...]
    patterns: tuple[str, ...]
    conventions: tuple[str, ...]
    anti_patterns: tuple[str, ...]
    edges: tuple[tuple[str, str, str], ...] = ()

    @property
    def target_id(self) -> str:
        """Deterministic identity: ``URI-TGT-<universe-slug>``."""
        return f"URI-TGT-{slug(self.universe).upper()}"

    @property
    def module_name(self) -> str:
        """The Python module-name fragment used by generated code."""
        return identifier(self.universe)

    @property
    def path_slug(self) -> str:
        """The filesystem fragment used by generated artifact paths."""
        return slug(self.universe)

    def _core(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "universe": self.universe,
            "cko_ids": list(self.cko_ids),
            "decision_ids": list(self.decision_ids),
            "kinds": list(self.kinds),
            "authorities": list(self.authorities),
            "lifecycles": list(self.lifecycles),
            "owners": list(self.owners),
            "invariants": [i.to_dict() for i in self.invariants],
            "principles": list(self.principles),
            "patterns": list(self.patterns),
            "conventions": list(self.conventions),
            "anti_patterns": list(self.anti_patterns),
            "edges": [list(e) for e in self.edges],
        }

    @property
    def seal(self) -> str:
        return _seal(self._core())

    def to_dict(self) -> dict[str, Any]:
        payload = self._core()
        payload["seal"] = self.seal
        return payload


@dataclass(frozen=True, slots=True)
class PlanStep:
    """One unit of realization work: realize ``target`` into ``family``."""

    step_id: str
    target_id: str
    universe: str
    family: ArtifactFamily
    depends_on: tuple[str, ...]
    source_ckos: tuple[str, ...]
    wave: int

    def _core(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "target_id": self.target_id,
            "universe": self.universe,
            "family": self.family.value,
            "depends_on": list(self.depends_on),
            "source_ckos": list(self.source_ckos),
            "wave": self.wave,
        }

    @property
    def seal(self) -> str:
        return _seal(self._core())

    def to_dict(self) -> dict[str, Any]:
        payload = self._core()
        payload["seal"] = self.seal
        return payload


@dataclass(frozen=True, slots=True)
class RealizationPlan:
    """The full, ordered, acyclic plan derived from a sealed canonical knowledge state."""

    knowledge_seal: str
    targets: tuple[RealizationTarget, ...]
    steps: tuple[PlanStep, ...]
    waves: tuple[tuple[str, ...], ...]
    coverage_gaps: tuple[str, ...] = ()

    @property
    def plan_id(self) -> str:
        """Deterministic identity derived from the plan's own content."""
        return f"URI-PLAN-{short_seal(self.seal)}"

    def step(self, step_id: str) -> PlanStep:
        for candidate in self.steps:
            if candidate.step_id == step_id:
                return candidate
        raise PlanningError("unknown plan step", step_id=step_id)

    def target(self, target_id: str) -> RealizationTarget:
        for candidate in self.targets:
            if candidate.target_id == target_id:
                return candidate
        raise PlanningError("unknown realization target", target_id=target_id)

    def steps_for(self, target_id: str) -> tuple[PlanStep, ...]:
        return tuple(s for s in self.steps if s.target_id == target_id)

    def _core(self) -> dict[str, Any]:
        return {
            "knowledge_seal": self.knowledge_seal,
            "targets": [t.to_dict() for t in self.targets],
            "steps": [s.to_dict() for s in self.steps],
            "waves": [list(w) for w in self.waves],
            "coverage_gaps": list(self.coverage_gaps),
        }

    @property
    def seal(self) -> str:
        return _seal(self._core())

    def to_dict(self) -> dict[str, Any]:
        payload = self._core()
        payload["plan_id"] = self.plan_id
        payload["step_count"] = len(self.steps)
        payload["target_count"] = len(self.targets)
        payload["seal"] = self.seal
        return payload


@dataclass(frozen=True, slots=True)
class CompositionUnit:
    """A plan step bound to the exact canonical objects and upstream units it consumes."""

    unit_id: str
    step_id: str
    target_id: str
    universe: str
    family: ArtifactFamily
    bound_ckos: tuple[str, ...]
    bound_decisions: tuple[str, ...]
    upstream_units: tuple[str, ...]
    consumed_families: tuple[str, ...]

    def _core(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "step_id": self.step_id,
            "target_id": self.target_id,
            "universe": self.universe,
            "family": self.family.value,
            "bound_ckos": list(self.bound_ckos),
            "bound_decisions": list(self.bound_decisions),
            "upstream_units": list(self.upstream_units),
            "consumed_families": list(self.consumed_families),
        }

    @property
    def seal(self) -> str:
        return _seal(self._core())

    def to_dict(self) -> dict[str, Any]:
        payload = self._core()
        payload["seal"] = self.seal
        return payload


@dataclass(frozen=True, slots=True)
class RealizationComposition:
    """The composed, topologically ordered realization graph ready for generation."""

    plan_id: str
    plan_seal: str
    knowledge_seal: str
    units: tuple[CompositionUnit, ...]
    order: tuple[str, ...]
    conflicts: tuple[tuple[str, str], ...] = ()

    @property
    def composition_id(self) -> str:
        return f"URI-COMP-{short_seal(self.seal)}"

    def unit(self, unit_id: str) -> CompositionUnit:
        for candidate in self.units:
            if candidate.unit_id == unit_id:
                return candidate
        raise PlanningError("unknown composition unit", unit_id=unit_id)

    def ordered_units(self) -> tuple[CompositionUnit, ...]:
        by_id = {u.unit_id: u for u in self.units}
        return tuple(by_id[uid] for uid in self.order)

    def _core(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plan_seal": self.plan_seal,
            "knowledge_seal": self.knowledge_seal,
            "units": [u.to_dict() for u in self.units],
            "order": list(self.order),
            "conflicts": [list(c) for c in self.conflicts],
        }

    @property
    def seal(self) -> str:
        return _seal(self._core())

    def to_dict(self) -> dict[str, Any]:
        payload = self._core()
        payload["composition_id"] = self.composition_id
        payload["unit_count"] = len(self.units)
        payload["seal"] = self.seal
        return payload


@dataclass(frozen=True, slots=True)
class Provenance:
    """The traceability block every generated artifact carries in its own body."""

    generator: str
    generator_version: str
    capability: str
    plan_id: str
    step_id: str
    unit_id: str
    target_id: str
    knowledge_seal: str
    source_ckos: tuple[str, ...]
    source_decisions: tuple[str, ...] = ()
    authority: str = DERIVED_AUTHORITY

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "capability": self.capability,
            "generator": self.generator,
            "generator_version": self.generator_version,
            "knowledge_seal": self.knowledge_seal,
            "plan_id": self.plan_id,
            "source_ckos": list(self.source_ckos),
            "source_decisions": list(self.source_decisions),
            "step_id": self.step_id,
            "target_id": self.target_id,
            "unit_id": self.unit_id,
        }


@dataclass(frozen=True, slots=True)
class GeneratedArtifact:
    """A fully generated artifact held in memory. Generation never touches disk."""

    relative_path: str
    family: ArtifactFamily
    media: MediaKind
    content: str
    provenance: Provenance

    @property
    def content_sha256(self) -> str:
        return sha256_text(self.content)

    @property
    def artifact_id(self) -> str:
        return f"URI-ART-{short_seal(self.content_sha256, width=16)}"

    @property
    def size(self) -> int:
        return len(self.content.encode("utf-8"))

    def to_record(self) -> dict[str, Any]:
        """The manifest record for this artifact (content excluded; hash included)."""
        return {
            "artifact_id": self.artifact_id,
            "relative_path": self.relative_path,
            "family": self.family.value,
            "media": self.media.value,
            "content_sha256": self.content_sha256,
            "size": self.size,
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class GenerationManifest:
    """The sealed inventory of everything a generation run produced."""

    composition_id: str
    composition_seal: str
    plan_id: str
    knowledge_seal: str
    artifacts: tuple[GeneratedArtifact, ...]

    @property
    def generation_id(self) -> str:
        return f"URI-GEN-{short_seal(self.seal)}"

    def by_family(self) -> dict[str, tuple[str, ...]]:
        grouped: dict[str, list[str]] = {}
        for art in self.artifacts:
            grouped.setdefault(art.family.value, []).append(art.relative_path)
        return {k: tuple(sorted(v)) for k, v in sorted(grouped.items())}

    def paths(self) -> tuple[str, ...]:
        return tuple(sorted(a.relative_path for a in self.artifacts))

    def _core(self) -> dict[str, Any]:
        return {
            "composition_id": self.composition_id,
            "composition_seal": self.composition_seal,
            "plan_id": self.plan_id,
            "knowledge_seal": self.knowledge_seal,
            "artifacts": [a.to_record() for a in self.artifacts],
        }

    @property
    def seal(self) -> str:
        return _seal(self._core())

    def to_dict(self) -> dict[str, Any]:
        payload = self._core()
        payload["generation_id"] = self.generation_id
        payload["artifact_count"] = len(self.artifacts)
        payload["families"] = {k: list(v) for k, v in self.by_family().items()}
        payload["seal"] = self.seal
        return payload


@dataclass(frozen=True, slots=True)
class MaterializedFile:
    """The outcome of materializing one generated artifact onto a writable surface."""

    relative_path: str
    artifact_id: str
    content_sha256: str
    size: int
    action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "artifact_id": self.artifact_id,
            "content_sha256": self.content_sha256,
            "size": self.size,
            "action": self.action,
        }


@dataclass(frozen=True, slots=True)
class ImplementationRecord:
    """The sealed record of a materialization pass (or a dry run that wrote nothing)."""

    generation_id: str
    generation_seal: str
    knowledge_seal: str
    artifact_root: str
    files: tuple[MaterializedFile, ...]
    dry_run: bool
    verified: bool

    @property
    def implementation_id(self) -> str:
        return f"URI-IMP-{short_seal(self.seal)}"

    def actions(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.files:
            counts[item.action] = counts.get(item.action, 0) + 1
        return dict(sorted(counts.items()))

    def _core(self) -> dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "generation_seal": self.generation_seal,
            "knowledge_seal": self.knowledge_seal,
            "artifact_root": self.artifact_root,
            "files": [f.to_dict() for f in self.files],
            "dry_run": self.dry_run,
            "verified": self.verified,
        }

    @property
    def seal(self) -> str:
        return _seal(self._core())

    def to_dict(self) -> dict[str, Any]:
        payload = self._core()
        payload["implementation_id"] = self.implementation_id
        payload["file_count"] = len(self.files)
        payload["actions"] = self.actions()
        payload["seal"] = self.seal
        return payload


@dataclass(frozen=True, slots=True)
class TraceEdge:
    """One directed traceability edge in the realization spine."""

    source: str
    relation: str
    target: str
    stage: RealizationStage = RealizationStage.TRACEABILITY

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "relation": self.relation,
            "target": self.target,
            "stage": self.stage.value,
        }


@dataclass(frozen=True, slots=True)
class Envelope:
    """The common, deterministic header every URI output document carries."""

    artifact_id: str
    title: str
    document_format: str
    knowledge_seal: str
    extra: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "artifact_id": self.artifact_id,
            "title": self.title,
            "document_format": self.document_format,
            "producer": (
                f"{REALIZATION_CONTRACT_NAME} v{REALIZATION_CONTRACT_VERSION} "
                "(URI-000001 Universal Realization Intelligence)"
            ),
            "authority": DERIVED_AUTHORITY,
            "capability": "URI-000001",
            "knowledge_seal": self.knowledge_seal,
        }
        payload.update(dict(self.extra))
        return payload


def dedupe(values: Iterable[str]) -> tuple[str, ...]:
    """Return ``values`` de-duplicated and sorted (deterministic set semantics)."""
    return tuple(sorted(set(values)))


__all__ = [
    "DERIVED_AUTHORITY",
    "FAMILY_DEPENDENCIES",
    "FAMILY_ORDER",
    "REALIZATION_CONTRACT_NAME",
    "REALIZATION_CONTRACT_VERSION",
    "ArtifactFamily",
    "CompositionUnit",
    "Envelope",
    "GeneratedArtifact",
    "GenerationManifest",
    "ImplementationRecord",
    "Invariant",
    "MaterializedFile",
    "MediaKind",
    "PlanStep",
    "Provenance",
    "RealizationComposition",
    "RealizationPlan",
    "RealizationStage",
    "RealizationTarget",
    "TraceEdge",
    "dedupe",
    "identifier",
    "slug",
]
