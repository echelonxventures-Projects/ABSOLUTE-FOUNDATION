"""UCOS-UFC-001 — Constitutional model convergence (UFC-14, UFC-15, UFC-16).

The Constitution forbids two implementations of one constitutional model. This module is the
instrument that *measures* whether that has actually been achieved, rather than a document
asserting it.

A :class:`ConstitutionalModel` declares one constitutional question, the single canonical
implementation that answers it, and every **subordinate surface** that once did or could. Each
subordinate declares the relation it now stands in, and the relation is verified:

    ``DELEGATES``   the surface still exists and must reach the canonical owner. Verified by
                    inspecting its real import graph — a surface that claims to delegate but
                    imports nothing from the owner is a parallel authority.
    ``SUPERSEDED``  the surface must be **gone**. A retired implementation that is still
                    present is still a second answer, whatever a document says about it.
    ``PROJECTION``  the surface is derived output, not an implementation. Verified by proving
                    it holds no executable determination.

The three platform-scoped articles are measured here because they are properties of the
platform, not of any capability: UFC-14 that each model has exactly one owner, UFC-15 that no
subordinate holds a competing definition, UFC-16 that one population yields one measurement.

Zero enumeration: no model, module or capability is named in this file. The population is
``catalog/foundation-convergence.json``.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from platform.foundation.contracts import content_hash
from platform.universal_foundation.conformance import (
    GateResult,
    SymbolRef,
    Verdict,
    imported_modules,
    parse_source,
    string_literals,
)
from platform.universal_foundation.constitution import (
    FoundationConstitution,
    foundation_constitution,
)
from platform.universal_foundation.errors import FoundationConvergenceError
from typing import Any

#: The packaged catalogue directory holding the declared convergence register.
CATALOG_DIRNAME = "catalog"

#: The declared convergence register (data, not code).
DEFAULT_CONVERGENCE_FILENAME = "foundation-convergence.json"

#: The platform gate proving each model has exactly one canonical implementation.
GATE_EXACTLY_ONCE = "FG-14-EXACTLY-ONCE"

#: The platform gate proving no subordinate surface holds a competing definition.
GATE_NO_PARALLEL_AUTHORITY = "FG-15-NO-PARALLEL-AUTHORITY"

#: The platform gate proving one population yields one measurement.
GATE_ONE_MEASUREMENT = "FG-16-ONE-MEASUREMENT"


class ConvergenceRelation(str, Enum):
    """How a subordinate surface now stands to the canonical owner of its model."""

    #: Still present, and must reach the canonical owner rather than answer for itself.
    DELEGATES = "delegates"
    #: Retired. Must be absent — a present implementation is a present second answer.
    SUPERSEDED = "superseded"
    #: Derived output of the canonical owner; must hold no executable determination.
    PROJECTION = "projection"
    #: Holds law over a strictly narrower subject. Must restate none of the canonical law.
    GOVERNED = "governed"

    @classmethod
    def coerce(cls, value: Any, *, subject: str = "convergence relation") -> ConvergenceRelation:
        """Coerce ``value`` to a relation, failing closed (never silently)."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            try:
                return cls(value)
            except ValueError as exc:
                raise FoundationConvergenceError(
                    "unknown convergence relation", subject=subject, value=value
                ) from exc
        raise FoundationConvergenceError("convergence relation must be a string", subject=subject)


@dataclass(frozen=True, slots=True)
class SubordinateSurface:
    """A surface that once did, or could, answer a constitutional question independently."""

    locator: str
    relation: ConvergenceRelation
    rationale: str = ""
    module: str = ""

    @classmethod
    def from_document(cls, payload: Mapping[str, Any]) -> SubordinateSurface:
        """Build from a declared mapping (fail-closed)."""
        if not isinstance(payload, Mapping):
            raise FoundationConvergenceError("subordinate declaration must be a mapping")
        missing = [key for key in ("locator", "relation") if key not in payload]
        if missing:
            raise FoundationConvergenceError(
                "subordinate declaration is incomplete", missing=",".join(missing)
            )
        locator = str(payload["locator"]).strip()
        if not locator:
            raise FoundationConvergenceError("subordinate declaration requires a locator")
        return cls(
            locator=locator,
            relation=ConvergenceRelation.coerce(payload["relation"], subject=locator),
            rationale=str(payload.get("rationale", "")),
            module=str(payload.get("module", "")).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        """A JSON-serialisable projection."""
        return {
            "locator": self.locator,
            "relation": self.relation.value,
            "module": self.module,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class ConstitutionalModel:
    """One constitutional question, its single canonical answer, and every subordinate."""

    model_id: str
    name: str
    question: str
    canonical_package: str
    canonical_contracts: SymbolRef
    subordinates: tuple[SubordinateSurface, ...] = ()
    measurement: SymbolRef | None = None
    rationale: str = ""

    @classmethod
    def from_document(cls, payload: Mapping[str, Any]) -> ConstitutionalModel:
        """Build a validated model declaration (fail-closed)."""
        if not isinstance(payload, Mapping):
            raise FoundationConvergenceError("model declaration must be a mapping")
        required = ("model_id", "name", "question", "canonical_package", "canonical_contracts")
        missing = [key for key in required if key not in payload]
        if missing:
            raise FoundationConvergenceError(
                "model declaration is incomplete",
                model_id=str(payload.get("model_id", "")),
                missing=",".join(missing),
            )
        model_id = str(payload["model_id"]).strip()
        measurement = payload.get("measurement")
        return cls(
            model_id=model_id,
            name=str(payload["name"]),
            question=str(payload["question"]),
            canonical_package=str(payload["canonical_package"]).strip(),
            canonical_contracts=SymbolRef.parse(payload["canonical_contracts"], context=model_id),
            subordinates=tuple(
                SubordinateSurface.from_document(item) for item in payload.get("subordinates", ())
            ),
            measurement=SymbolRef.parse(measurement, context=model_id) if measurement else None,
            rationale=str(payload.get("rationale", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        """A JSON-serialisable projection."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "question": self.question,
            "canonical_package": self.canonical_package,
            "canonical_contracts": str(self.canonical_contracts),
            "measurement": str(self.measurement) if self.measurement else "",
            "subordinates": [item.to_dict() for item in self.subordinates],
            "rationale": self.rationale,
        }

    def fingerprint(self) -> str:
        """The deterministic content fingerprint of this declaration."""
        return content_hash(self.to_dict())


@dataclass(frozen=True, slots=True)
class SubordinateFinding:
    """The measured standing of one subordinate surface against its declared relation."""

    model_id: str
    locator: str
    relation: ConvergenceRelation
    satisfied: bool
    observed: str

    def to_dict(self) -> dict[str, Any]:
        """A JSON-serialisable projection."""
        return {
            "model_id": self.model_id,
            "locator": self.locator,
            "relation": self.relation.value,
            "satisfied": self.satisfied,
            "observed": self.observed,
        }


@dataclass(frozen=True, slots=True)
class ModelConvergence:
    """The measured convergence of one constitutional model."""

    model_id: str
    name: str
    canonical_package: str
    owner_resolved: bool
    contract_count: int
    findings: tuple[SubordinateFinding, ...]
    measurement_fingerprint: str = ""
    measurement_stable: bool | None = None
    detail: str = ""

    @property
    def competing(self) -> tuple[SubordinateFinding, ...]:
        """Every subordinate that does not stand in its declared relation."""
        return tuple(item for item in self.findings if not item.satisfied)

    @property
    def converged(self) -> bool:
        """Whether this model has exactly one live answer."""
        return (
            self.owner_resolved
            and self.contract_count > 0
            and not self.competing
            and self.measurement_stable is not False
        )

    @property
    def live_implementations(self) -> int:
        """How many surfaces currently answer this model's question independently."""
        return 1 + len(self.competing) if self.owner_resolved else len(self.competing)

    def to_dict(self) -> dict[str, Any]:
        """A JSON-serialisable projection."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "canonical_package": self.canonical_package,
            "owner_resolved": self.owner_resolved,
            "contract_count": self.contract_count,
            "converged": self.converged,
            "live_implementations": self.live_implementations,
            "measurement_fingerprint": self.measurement_fingerprint,
            "measurement_stable": self.measurement_stable,
            "detail": self.detail,
            "findings": [item.to_dict() for item in self.findings],
        }


@dataclass(frozen=True, slots=True)
class ConvergenceDetermination:
    """The immutable determination of constitutional convergence across every model."""

    models: tuple[ModelConvergence, ...]
    gate_results: tuple[GateResult, ...]
    determination_id: str = ""

    @classmethod
    def create(
        cls,
        models: Iterable[ModelConvergence],
        gate_results: Iterable[GateResult],
    ) -> ConvergenceDetermination:
        """Build a content-addressed determination."""
        ordered = tuple(sorted(models, key=lambda item: item.model_id))
        gates = tuple(sorted(gate_results, key=lambda item: item.gate))
        core = {
            "models": [item.to_dict() for item in ordered],
            "gates": [item.result_id for item in gates],
        }
        return cls(
            models=ordered,
            gate_results=gates,
            determination_id=f"UCOS-UFCV-{content_hash(core)[:16]}",
        )

    @property
    def total(self) -> int:
        """How many constitutional models were measured."""
        return len(self.models)

    @property
    def converged(self) -> bool:
        """Whether every model has exactly one live answer and every gate passed."""
        return all(item.converged for item in self.models) and all(
            item.satisfied for item in self.gate_results
        )

    @property
    def duplicates(self) -> int:
        """How many surplus live implementations exist across every model.

        Zero is the freeze condition: one model, one implementation, no exceptions.
        """
        return sum(max(0, item.live_implementations - 1) for item in self.models)

    def competing(self) -> tuple[SubordinateFinding, ...]:
        """Every surface holding a competing constitutional definition."""
        found: list[SubordinateFinding] = []
        for model in self.models:
            found.extend(model.competing)
        return tuple(sorted(found, key=lambda item: (item.model_id, item.locator)))

    def model(self, model_id: str) -> ModelConvergence:
        """The measured convergence of ``model_id`` (fail-closed)."""
        for item in self.models:
            if item.model_id == model_id:
                return item
        raise FoundationConvergenceError("unknown constitutional model", model_id=str(model_id))

    def counts(self) -> dict[str, int]:
        """Headline counts of the convergence determination."""
        return {
            "models": self.total,
            "converged": sum(1 for item in self.models if item.converged),
            "unconverged": sum(1 for item in self.models if not item.converged),
            "duplicate_implementations": self.duplicates,
            "competing_surfaces": len(self.competing()),
        }

    def blockers(self) -> tuple[str, ...]:
        """``model/locator`` identities of every competing surface, plus failed gates."""
        found = [f"{item.model_id}/{item.locator}" for item in self.competing()]
        found.extend(item.gate for item in self.gate_results if not item.satisfied)
        return tuple(sorted(found))

    def to_dict(self) -> dict[str, Any]:
        """A JSON-serialisable projection of this determination."""
        return {
            "determination_id": self.determination_id,
            "converged": self.converged,
            "counts": self.counts(),
            "blockers": list(self.blockers()),
            "models": [item.to_dict() for item in self.models],
            "gate_results": [item.to_dict() for item in self.gate_results],
        }

    def summary(self) -> dict[str, Any]:
        """A compact projection without the per-subordinate detail."""
        return {
            "determination_id": self.determination_id,
            "converged": self.converged,
            "counts": self.counts(),
            "blockers": list(self.blockers()),
            "models": [
                {
                    "model_id": item.model_id,
                    "name": item.name,
                    "canonical_package": item.canonical_package,
                    "converged": item.converged,
                    "live_implementations": item.live_implementations,
                }
                for item in self.models
            ],
            "gate_results": [
                {"gate": item.gate, "verdict": item.verdict.value, "summary": item.summary}
                for item in self.gate_results
            ],
        }

    def fingerprint(self) -> str:
        """The deterministic content fingerprint of this determination."""
        return content_hash(self.to_dict())


class ConvergenceRegister:
    """A deterministic, fail-closed registry of declared constitutional models."""

    __slots__ = ("_models", "_register_id")

    def __init__(
        self,
        models: Iterable[ConstitutionalModel] = (),
        *,
        register_id: str = "foundation.convergence",
    ) -> None:
        self._models: dict[str, ConstitutionalModel] = {}
        self._register_id = register_id.strip() or "foundation.convergence"
        for model in models:
            self.add(model)

    def add(self, model: ConstitutionalModel) -> ConstitutionalModel:
        """Declare ``model``; fail-closed on an identity collision."""
        if not isinstance(model, ConstitutionalModel):
            raise FoundationConvergenceError("register accepts only ConstitutionalModel values")
        existing = self._models.get(model.model_id)
        if existing is not None:
            if existing.fingerprint() == model.fingerprint():
                return existing
            raise FoundationConvergenceError(
                "model already declared with a different body", model_id=model.model_id
            )
        self._models[model.model_id] = model
        return model

    def get(self, model_id: str) -> ConstitutionalModel | None:
        """The declared model ``model_id``, or ``None``."""
        return self._models.get(model_id)

    def require(self, model_id: str) -> ConstitutionalModel:
        """The declared model ``model_id`` (fail-closed)."""
        model = self.get(model_id)
        if model is None:
            raise FoundationConvergenceError("unknown constitutional model", model_id=str(model_id))
        return model

    @property
    def register_id(self) -> str:
        """The declared identity of this register."""
        return self._register_id

    @property
    def count(self) -> int:
        """How many models are declared."""
        return len(self._models)

    def ordered(self) -> tuple[ConstitutionalModel, ...]:
        """Every model in deterministic identity order."""
        return tuple(sorted(self._models.values(), key=lambda item: item.model_id))

    def ids(self) -> tuple[str, ...]:
        """Every declared model identity, in order."""
        return tuple(item.model_id for item in self.ordered())

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> ConvergenceRegister:
        """Build a register from the declared convergence document (fail-closed)."""
        if not isinstance(document, Mapping):
            raise FoundationConvergenceError("convergence document must be a mapping")
        models = document.get("models")
        if not isinstance(models, Sequence) or isinstance(models, str | bytes):
            raise FoundationConvergenceError("convergence document requires a 'models' sequence")
        register = cls(register_id=str(document.get("register_id", "")))
        for model in models:
            register.add(ConstitutionalModel.from_document(model))
        if register.count == 0:
            raise FoundationConvergenceError("convergence register declares no model")
        return register

    def to_dict(self) -> dict[str, Any]:
        """A JSON-serialisable projection of this register."""
        return {
            "register_id": self._register_id,
            "model_count": self.count,
            "models": [item.to_dict() for item in self.ordered()],
        }

    def fingerprint(self) -> str:
        """The deterministic content fingerprint of this register."""
        return content_hash(self.to_dict())


def catalog_path(filename: str = DEFAULT_CONVERGENCE_FILENAME) -> Path:
    """The packaged catalogue path for ``filename``."""
    return Path(__file__).resolve().parent / CATALOG_DIRNAME / filename


def load_convergence_register(path: Path | str) -> ConvergenceRegister:
    """Load a declared convergence register from ``path`` (fail-closed)."""
    target = Path(path)
    try:
        document = json.loads(target.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FoundationConvergenceError(
            "convergence register could not be read", path=str(target), detail=str(exc)
        ) from exc
    return ConvergenceRegister.from_document(document)


def default_convergence_register(
    filename: str = DEFAULT_CONVERGENCE_FILENAME,
) -> ConvergenceRegister:
    """The convergence register shipped in the packaged catalogue."""
    return load_convergence_register(catalog_path(filename))


class ConvergenceEngine:
    """Measures whether every declared constitutional model has exactly one live answer."""

    __slots__ = ("_register", "_constitution", "_project_root")

    def __init__(
        self,
        register: ConvergenceRegister,
        *,
        constitution: FoundationConstitution | None = None,
        project_root: Path | str = ".",
    ) -> None:
        if not isinstance(register, ConvergenceRegister):
            raise FoundationConvergenceError("convergence requires a ConvergenceRegister")
        self._register = register
        self._constitution = constitution or foundation_constitution()
        self._project_root = Path(project_root)

    @property
    def register(self) -> ConvergenceRegister:
        """The declared model population this engine measures."""
        return self._register

    @property
    def constitution(self) -> FoundationConstitution:
        """The law whose platform-scoped articles this engine proves."""
        return self._constitution

    def _measure_subordinate(
        self, model: ConstitutionalModel, subordinate: SubordinateSurface
    ) -> SubordinateFinding:
        """Verify one subordinate stands in the relation it declares."""
        path = self._project_root / subordinate.locator
        exists = path.exists()

        if subordinate.relation is ConvergenceRelation.SUPERSEDED:
            return SubordinateFinding(
                model.model_id,
                subordinate.locator,
                subordinate.relation,
                not exists,
                "absent — the retired implementation is gone"
                if not exists
                else (
                    "PRESENT — a retired implementation that still exists is still a "
                    "second answer"
                ),
            )

        if subordinate.relation is ConvergenceRelation.PROJECTION:
            executable = path.suffix == ".py"
            return SubordinateFinding(
                model.model_id,
                subordinate.locator,
                subordinate.relation,
                exists and not executable,
                "derived output holding no executable determination"
                if exists and not executable
                else (
                    "EXECUTABLE — a projection may not hold a determination"
                    if executable
                    else "absent — the declared projection does not exist"
                ),
            )

        if not exists:
            return SubordinateFinding(
                model.model_id,
                subordinate.locator,
                subordinate.relation,
                False,
                "absent — a surface declared to delegate must exist to be verified",
            )
        module_name = subordinate.module
        if not module_name:
            return SubordinateFinding(
                model.model_id,
                subordinate.locator,
                subordinate.relation,
                False,
                "no module declared — delegation cannot be verified without one",
            )
        try:
            location = getattr(importlib.import_module(module_name), "__file__", None)
        except Exception as exc:  # noqa: BLE001 - contained by design (fail-closed)
            return SubordinateFinding(
                model.model_id,
                subordinate.locator,
                subordinate.relation,
                False,
                f"module could not be imported: {type(exc).__name__}: {exc}",
            )
        if not location:
            return SubordinateFinding(
                model.model_id,
                subordinate.locator,
                subordinate.relation,
                False,
                "module has no filesystem location; delegation cannot be verified",
            )

        if subordinate.relation is ConvergenceRelation.GOVERNED:
            # A narrower authority is legitimate precisely while it restates none of the
            # canonical law. Proving that mechanically is what separates "a second authority
            # over a smaller subject" from "a second copy of the same law".
            reserved = {
                *self._constitution.article_ids(),
                *self._constitution.gates(),
                self._constitution.constitution_id,
            }
            literals = set(string_literals(parse_source(Path(location))))
            restated = sorted(reserved & literals)
            return SubordinateFinding(
                model.model_id,
                subordinate.locator,
                subordinate.relation,
                not restated,
                "holds law over a narrower subject and restates no article, gate or identity "
                "of the canonical law"
                if not restated
                else f"RESTATES CANONICAL LAW: {','.join(restated)}",
            )

        imported = imported_modules(parse_source(Path(location)))
        package = model.canonical_package
        delegates = any(name == package or name.startswith(f"{package}.") for name in imported)
        return SubordinateFinding(
            model.model_id,
            subordinate.locator,
            subordinate.relation,
            delegates,
            f"imports the canonical owner ({package})"
            if delegates
            else f"PARALLEL AUTHORITY — never reaches the canonical owner ({package})",
        )

    def measure_model(self, model: ConstitutionalModel) -> ModelConvergence:
        """Measure one constitutional model against its declaration."""
        owner_resolved = True
        contract_count = 0
        detail = ""
        try:
            importlib.import_module(model.canonical_package)
            contracts = model.canonical_contracts.resolve()
            contract_count = len(contracts) if isinstance(contracts, tuple) else 0
            if contract_count == 0:
                detail = "the canonical owner publishes no contract surface"
        except Exception as exc:  # noqa: BLE001 - contained by design (fail-closed)
            owner_resolved = False
            detail = f"canonical owner does not resolve: {type(exc).__name__}: {exc}"

        fingerprint = ""
        stable: bool | None = None
        if model.measurement is not None:
            try:
                build = model.measurement.resolve()
                first, second = build(), build()
                fingerprint = first.fingerprint()
                stable = fingerprint == second.fingerprint()
                if not stable:
                    detail = "the canonical measurement is not reproducible"
            except Exception as exc:  # noqa: BLE001 - contained by design (fail-closed)
                stable = False
                detail = f"the canonical measurement could not be taken: {exc}"

        return ModelConvergence(
            model_id=model.model_id,
            name=model.name,
            canonical_package=model.canonical_package,
            owner_resolved=owner_resolved,
            contract_count=contract_count,
            findings=tuple(
                self._measure_subordinate(model, subordinate) for subordinate in model.subordinates
            ),
            measurement_fingerprint=fingerprint,
            measurement_stable=stable,
            detail=detail,
        )

    def _gate(
        self, gate: str, verdict: Verdict, summary: str, findings: Iterable[str] = ()
    ) -> GateResult:
        article = next(item for item in self._constitution.platform_articles() if item.gate == gate)
        return GateResult.create(
            gate,
            article.article_id,
            "PLATFORM",
            verdict,
            summary=summary,
            findings=findings,
        )

    def measure(self) -> ConvergenceDetermination:
        """Measure every declared model and prove the three platform-scoped articles."""
        models = tuple(self.measure_model(model) for model in self._register.ordered())

        unowned = [item.model_id for item in models if not item.owner_resolved]
        uncontracted = [
            item.model_id for item in models if item.owner_resolved and item.contract_count == 0
        ]
        exactly_once = self._gate(
            GATE_EXACTLY_ONCE,
            Verdict.PASS if not unowned and not uncontracted else Verdict.FAIL,
            f"{len(models)} constitutional models, each with exactly one canonical owner "
            "publishing a contract surface"
            if not unowned and not uncontracted
            else "a constitutional model has no resolvable, contracted owner",
            findings=[*unowned, *uncontracted],
        )

        competing = [
            f"{item.model_id}/{item.locator}: {item.observed}"
            for model in models
            for item in model.competing
        ]
        no_parallel = self._gate(
            GATE_NO_PARALLEL_AUTHORITY,
            Verdict.PASS if not competing else Verdict.FAIL,
            f"every declared subordinate surface across {len(models)} models stands in its "
            "declared relation"
            if not competing
            else f"{len(competing)} surfaces hold a competing constitutional definition",
            findings=competing,
        )

        measured = [item for item in models if item.measurement_stable is not None]
        unstable = [
            f"{item.model_id}: {item.detail}" for item in measured if not item.measurement_stable
        ]
        unmeasured = [item.model_id for item in models if item.measurement_stable is None]
        one_measurement = self._gate(
            GATE_ONE_MEASUREMENT,
            Verdict.PASS if measured and not unstable and not unmeasured else Verdict.FAIL,
            f"{len(measured)} canonical measurements are reproducible and no model declares a "
            "second measuring surface"
            if measured and not unstable and not unmeasured
            else "a constitutional model has no reproducible canonical measurement",
            findings=[
                *unstable,
                *(f"{item}: declares no canonical measurement" for item in unmeasured),
            ],
        )

        return ConvergenceDetermination.create(models, (exactly_once, no_parallel, one_measurement))

    def to_dict(self) -> dict[str, Any]:
        """A JSON-serialisable projection of this engine's composition."""
        return {"register": self._register.to_dict()}

    def fingerprint(self) -> str:
        """The deterministic content fingerprint of this engine's composition."""
        return content_hash(self.to_dict())


def bootstrap_convergence(
    register: ConvergenceRegister | Path | str | None = None,
    *,
    project_root: Path | str = ".",
) -> ConvergenceEngine:
    """Compose the convergence engine over a declared convergence register."""
    if register is None:
        resolved = default_convergence_register()
    elif isinstance(register, ConvergenceRegister):
        resolved = register
    else:
        resolved = load_convergence_register(register)
    return ConvergenceEngine(resolved, project_root=project_root)


__all__ = [
    "CATALOG_DIRNAME",
    "DEFAULT_CONVERGENCE_FILENAME",
    "GATE_EXACTLY_ONCE",
    "GATE_NO_PARALLEL_AUTHORITY",
    "GATE_ONE_MEASUREMENT",
    "ConstitutionalModel",
    "ConvergenceDetermination",
    "ConvergenceEngine",
    "ConvergenceRegister",
    "ConvergenceRelation",
    "ModelConvergence",
    "SubordinateFinding",
    "SubordinateSurface",
    "bootstrap_convergence",
    "catalog_path",
    "default_convergence_register",
    "load_convergence_register",
]
