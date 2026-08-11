"""UCOS-CL-015 — the generated-artifact registry, and the derived views over it.

One fact, one owner, many views
-------------------------------
"This path is generated output" was expressed in three independent places: each
programme's own declaration, ``00-BOOK/tools/config.py::EXCLUDE_DIR_PREFIXES`` for
registration eligibility, and ``.gitignore`` for the version-control boundary. They
drifted. UCOS-RECON-C2 records the consequence: the eleven RIE outputs were admitted to
the Repository Corpus and given permanent identities because ``EXCLUDE_DIR_PREFIXES``
enumerated generated outputs only where they lived under ``00-BOOK/``, and ``intelligence/``
did not exist when that list was authored.

Two producers declared nothing at all — UCOS-AEE-001 and UAIE-000001 emit 33 tracked files
between them and carried no ``outputs`` section.

This module reads the one upstream register and serves the views. It is deliberately
UPSTREAM of every engine it describes: the register is authored, and nothing here consults
an engine's output to decide what that engine produces. That direction is what keeps the
dependency acyclic.

The structural bar
------------------
:func:`validate` refuses a canonical artifact that declares an ENVIRONMENTAL input. That is
the UCOS-CL-005 coverage defect expressed as a rule rather than as a fix: an RIE artifact
naming ``coverage.xml`` in its input closure cannot be declared, so the leak becomes
unrepresentable instead of merely removed once.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REGISTRY_PATH = "00-BOOK/DATA/generated-artifact-registry.json"

#: Every input of every declared artifact carries one of these.
INPUT_CLASSIFICATIONS: frozenset[str] = frozenset(
    {"TRACKED_DETERMINISTIC", "ENVIRONMENTAL", "OPERATIONAL", "EXTERNAL", "UNKNOWN"}
)

#: Classifications a *canonical* artifact may depend on. UNKNOWN is absent by design.
CANONICAL_SAFE_INPUTS: frozenset[str] = frozenset({"TRACKED_DETERMINISTIC"})


@dataclass(frozen=True)
class GeneratedArtifact:
    artifact_id: str
    canonical_path: str
    producer: str
    owner: str
    capability: str
    lifecycle: str
    input_closure: tuple[str, ...]
    input_classification: dict[str, str]
    deterministic: bool
    environmental_dependencies: tuple[str, ...]
    canonical_identity_role: str
    consumers: tuple[str, ...]
    registration_status: str
    validation_owner: str
    regeneration_command: str
    certification_role: str

    @property
    def canonical(self) -> bool:
        return self.canonical_identity_role == "CANONICAL"


def _artifact(raw: dict) -> GeneratedArtifact:
    return GeneratedArtifact(
        artifact_id=str(raw.get("artifact_id", "")),
        canonical_path=str(raw.get("canonical_path", "")),
        producer=str(raw.get("producer", "")),
        owner=str(raw.get("owner", "")),
        capability=str(raw.get("capability", "")),
        lifecycle=str(raw.get("lifecycle", "")),
        input_closure=tuple(raw.get("input_closure", ())),
        input_classification=dict(raw.get("input_classification", {})),
        deterministic=bool(raw.get("deterministic", False)),
        environmental_dependencies=tuple(raw.get("environmental_dependencies", ())),
        canonical_identity_role=str(raw.get("canonical_identity_role", "")),
        consumers=tuple(raw.get("consumers", ())),
        registration_status=str(raw.get("registration_status", "")),
        validation_owner=str(raw.get("validation_owner", "")),
        regeneration_command=str(raw.get("regeneration_command", "")),
        certification_role=str(raw.get("certification_role", "")),
    )


@lru_cache(maxsize=8)
def load(repo: Path) -> tuple[GeneratedArtifact, ...]:
    """Every declared artifact, canonical and environmental alike."""
    doc = json.loads((Path(repo) / REGISTRY_PATH).read_text(encoding="utf-8"))
    return tuple(
        _artifact(raw) for raw in [*doc.get("entries", []), *doc.get("environmental_artifacts", [])]
    )


# --- derived views ----------------------------------------------------------------------


def paths_for_owner(repo: Path, owner: str) -> set[str]:
    """The canonical paths one programme produces.

    This is the view that replaces a hard-coded per-engine list. UCOS-RIB-001 previously
    computed its own from its declaration; it now asks the register, so its answer and the
    registration boundary's answer are the same fact rather than two that can disagree.
    """
    return {a.canonical_path for a in load(Path(repo)) if a.owner == owner}


def producer_of(repo: Path, path: str) -> str | None:
    for a in load(Path(repo)):
        if a.canonical_path == path:
            return a.producer
    return None


def canonical_paths(repo: Path) -> set[str]:
    return {a.canonical_path for a in load(Path(repo)) if a.canonical}


# --- invariants -------------------------------------------------------------------------


def validate(repo: Path) -> list[str]:
    """Every registry invariant, as a list of findings. Empty means the register holds."""
    artifacts = load(Path(repo))
    findings: list[str] = []

    seen: dict[str, str] = {}
    for a in artifacts:
        if not a.canonical_path:
            findings.append(f"{a.artifact_id}: no canonical_path")
            continue
        if a.canonical_path in seen:
            findings.append(
                f"{a.canonical_path}: claimed by two producers "
                f"({seen[a.canonical_path]} and {a.producer})"
            )
        seen[a.canonical_path] = a.producer

        for field, value in (
            ("producer", a.producer),
            ("owner", a.owner),
            ("lifecycle", a.lifecycle),
        ):
            if not value:
                findings.append(f"{a.canonical_path}: no {field}")
        if not a.input_closure:
            findings.append(f"{a.canonical_path}: empty input_closure")

        for inp in a.input_closure:
            klass = a.input_classification.get(inp)
            if klass is None:
                findings.append(f"{a.canonical_path}: input {inp!r} has no classification")
            elif klass not in INPUT_CLASSIFICATIONS:
                findings.append(
                    f"{a.canonical_path}: input {inp!r} has unrecognised class {klass!r}"
                )
            elif klass == "UNKNOWN":
                findings.append(f"{a.canonical_path}: input {inp!r} is UNKNOWN — fails closed")
            elif a.canonical and klass not in CANONICAL_SAFE_INPUTS:
                # THE bar. UCOS-CL-005 as a rule rather than a repair.
                findings.append(
                    f"{a.canonical_path}: CANONICAL artifact declares a {klass} input "
                    f"({inp!r}) — canonical identity may not depend on non-tracked state"
                )
        if a.canonical and a.environmental_dependencies:
            findings.append(
                f"{a.canonical_path}: CANONICAL artifact declares environmental "
                f"dependencies {list(a.environmental_dependencies)}"
            )
        if a.canonical and not a.deterministic:
            findings.append(f"{a.canonical_path}: CANONICAL artifact is not deterministic")
    return findings


def reconcile_owner_view(repo: Path, owner: str, engine_view: Iterable[str]) -> list[str]:
    """Findings where a producer's own idea of its outputs differs from the register."""
    registry = paths_for_owner(repo, owner)
    engine = set(engine_view)
    findings = []
    for missing in sorted(registry - engine):
        findings.append(f"{owner}: registry declares {missing} but the engine does not claim it")
    for extra in sorted(engine - registry):
        findings.append(f"{owner}: engine claims {extra} but the registry does not declare it")
    return findings
