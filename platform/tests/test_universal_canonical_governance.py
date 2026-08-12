"""The Universal Canonical Governance Foundation — five invariants, enforced.

What changed, and why these are tests rather than a report
----------------------------------------------------------
Governance here was DISCOVERED. UCOS-CL-005 found a coverage leak in UCOS-RIE-001 and fixed
that one producer; UAKOS-CLOSURE-008 found an execution transcript inside two canonical
artifacts and fixed that one programme; a forensic ablation over all 38 programme engines then
found the same class in five more producers, 263 artifacts governed by nothing at all, and 114
artifacts depending on generated trees whose creation existed only inside one stage of one
shell script. Each discovery arrived after the fact, from a phase gate or an audit.

The five invariants below are the same knowledge stated BEFORE the fact. Each one refuses a
declaration rather than reporting a consequence:

    1  EVERY_CANONICAL_ARTIFACT_REGISTERED
    2  EVERY_INPUT_CLASSIFIED
    3  NO_ENVIRONMENTAL_INPUT_IN_CANONICAL_IDENTITY
    4  EVIDENCE_REFERENCED_ONLY_BY_ID
    5  GENERATED_INPUT_HAS_PRODUCER_AND_BOOTSTRAP

Each has a live half (the repository satisfies it now) and a structural half (a fixture that
violates it is refused). The structural half is the one that matters: it is what makes the
next occurrence unrepresentable instead of discoverable.
"""

from __future__ import annotations

import json
from pathlib import Path
from platform.repository_intelligence import evidence_universe
from platform.repository_intelligence.generated_artifacts import (
    CANONICAL_SAFE_INPUTS,
    EXECUTION_OBSERVATION_CLASSIFICATIONS,
    INPUT_CLASSIFICATIONS,
    REGISTRY_PATH,
    generated_input_for,
    generated_inputs,
    load,
    producer_homes,
    unregistered_paths,
    validate,
)

import pytest

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def artifacts():
    return load(REPO)


def _registry(repo: Path, entries: list[dict], **sections) -> Path:
    (repo / "00-BOOK" / "DATA").mkdir(parents=True, exist_ok=True)
    doc = {"schema": "ucos-generated-artifact-registry", "entries": entries, **sections}
    (repo / REGISTRY_PATH).write_text(json.dumps(doc), encoding="utf-8")
    return repo


def _entry(**overrides) -> dict:
    entry = {
        "artifact_id": "X",
        "canonical_path": "programme/OUT.md",
        "producer": "programme/engine.py",
        "owner": "PROGRAMME",
        "lifecycle": "REGENERATED",
        "input_closure": ["programme/declaration.json"],
        "input_classification": {"programme/declaration.json": "TRACKED_DETERMINISTIC"},
        "deterministic": True,
        "canonical_identity_role": "CANONICAL",
    }
    entry.update(overrides)
    return entry


# --- 1 · every canonical artifact registered ----------------------------------------------


def test_1_live_every_tracked_file_in_a_declared_home_is_declared() -> None:
    findings = unregistered_paths(REPO)
    assert findings == [], (
        "files inside a declared producer home that the register does not know about:\n  "
        + "\n  ".join(findings)
    )


def test_1_the_register_declares_a_home_for_every_producer_it_names(artifacts) -> None:
    homed = {h.owner for h in producer_homes(REPO)}
    owners = {
        a.owner for a in artifacts if a.canonical and a.canonical_path.startswith("00-MASTER/")
    }
    assert owners <= homed, f"artifacts whose owner has no declared home: {sorted(owners - homed)}"


def test_1_structural_an_undeclared_file_in_a_declared_home_is_a_finding(tmp_path: Path) -> None:
    """The property whose absence let 263 artifacts exist ungoverned."""
    import subprocess

    repo = tmp_path / "r"
    (repo / "programme").mkdir(parents=True)
    (repo / "programme" / "engine.py").write_text("", encoding="utf-8")
    (repo / "programme" / "OUT.md").write_text("", encoding="utf-8")
    (repo / "programme" / "SURPRISE.md").write_text("", encoding="utf-8")
    _registry(
        repo,
        [_entry()],
        producer_homes=[
            {
                "owner": "PROGRAMME",
                "home": "programme",
                "producer": "programme/engine.py",
                "authored_inputs": ["declaration.json"],
            }
        ],
    )
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)  # noqa: S603,S607
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)  # noqa: S603,S607
    findings = unregistered_paths(repo)
    assert any("SURPRISE.md" in f for f in findings), findings


# --- 2 · every input classified -----------------------------------------------------------


def test_2_live_every_input_of_every_artifact_carries_a_known_classification(artifacts) -> None:
    for a in artifacts:
        assert a.input_closure, f"{a.canonical_path}: empty input closure"
        for inp in a.input_closure:
            klass = a.input_classification.get(inp)
            assert (
                klass in INPUT_CLASSIFICATIONS
            ), f"{a.canonical_path}: input {inp!r} classified {klass!r}"


def test_2_structural_an_unclassified_input_fails_closed(tmp_path: Path) -> None:
    repo = _registry(
        tmp_path / "r",
        [_entry(input_closure=["mystery"], input_classification={"mystery": "UNKNOWN"})],
    )
    assert any("UNKNOWN" in f for f in validate(repo))


# --- 3 · no environmental input affects canonical identity --------------------------------


def test_3_live_no_canonical_artifact_declares_an_environmental_input(artifacts) -> None:
    unsafe = [
        (a.canonical_path, inp, klass)
        for a in artifacts
        if a.canonical
        for inp, klass in a.input_classification.items()
        if klass not in CANONICAL_SAFE_INPUTS
    ]
    assert unsafe == [], f"canonical artifacts on non-canonical inputs: {unsafe}"


@pytest.mark.parametrize(
    "classification",
    ["ENVIRONMENTAL", "OPERATIONAL", *sorted(EXECUTION_OBSERVATION_CLASSIFICATIONS)],
)
def test_3_structural_every_environmental_class_is_refused(
    tmp_path: Path, classification: str
) -> None:
    repo = _registry(
        tmp_path / "r",
        [
            _entry(
                input_closure=["coverage.xml"],
                input_classification={"coverage.xml": classification},
            )
        ],
    )
    assert validate(repo), f"{classification} was admitted into canonical identity"


def test_3_the_live_registry_holds_every_invariant() -> None:
    findings = validate(REPO)
    assert findings == [], "generated-artifact registry invariants violated:\n  " + "\n  ".join(
        findings
    )


# --- 4 · evidence referenced only by ID ---------------------------------------------------


def test_4_live_no_canonical_artifact_reads_an_observation_surface(artifacts) -> None:
    """Evidence may support truth. An OBSERVATION may not be read while deciding identity.

    The one class that may cross into canonical identity is VALIDATION — a derived result of
    checking something, computed from tracked sources. That is R-EV-3, and it is why
    `determinism-evidence/` is a legitimate input while `verify.log` and `coverage.xml` are
    not. Every other class is cited by evidence id and never read.
    """
    offenders = []
    for a in artifacts:
        if not a.canonical:
            continue
        for inp in a.input_closure:
            surface = evidence_universe.surface_for(REPO, inp)
            if surface is None:
                continue
            if surface.evidence_class not in evidence_universe.DETERMINISTIC_ELIGIBLE_CLASSES:
                offenders.append(
                    (a.canonical_path, inp, surface.surface_id, surface.evidence_class)
                )
    assert offenders == [], f"canonical artifacts reading observation surfaces: {offenders}"


def test_4_every_evidence_surface_is_non_canonical_and_classified() -> None:
    findings = evidence_universe.validate(REPO)
    assert findings == [], "evidence universe violated:\n  " + "\n  ".join(findings)


def test_4_the_universe_declares_exactly_the_five_classes() -> None:
    doc = evidence_universe.document(REPO)
    assert set(doc["evidence_classes"]) == {
        "AUDIT",
        "DEBUG",
        "IMPROVEMENT",
        "EXECUTION",
        "VALIDATION",
    }
    assert len(doc["constitutional_rules"]) == 4


def test_4_structural_an_execution_input_from_an_undeclared_surface_is_refused(
    tmp_path: Path,
) -> None:
    """A NON_CANONICAL artifact may read evidence — but not evidence nobody declared."""
    repo = tmp_path / "r"
    (repo / "00-BOOK" / "DATA").mkdir(parents=True)
    (repo / evidence_universe.REGISTRY_PATH).write_text(
        json.dumps(
            {
                "schema": evidence_universe.SCHEMA,
                "evidence_classes": dict.fromkeys(evidence_universe.EVIDENCE_CLASSES, "x"),
                "surfaces": [],
            }
        ),
        encoding="utf-8",
    )
    _registry(
        repo,
        [
            _entry(
                canonical_identity_role="NON_CANONICAL",
                deterministic=False,
                input_closure=["some/where/run.log"],
                input_classification={"some/where/run.log": "EXECUTION_TRANSCRIPT"},
            )
        ],
    )
    assert any("no declared evidence surface" in f for f in validate(repo))


# --- 5 · every generated input has a producer and a bootstrap path ------------------------


def test_5_live_every_generated_input_declares_a_producer_and_a_bootstrap_command() -> None:
    declared = generated_inputs(REPO)
    assert declared, "no generated inputs are declared"
    for g in declared:
        assert g.producer, f"{g.path}: no producer"
        assert g.bootstrap_command, f"{g.path}: no bootstrap command"
        assert g.bootstrap_stage, f"{g.path}: no bootstrap stage"


def test_5_live_every_generated_input_a_canonical_artifact_reads_is_reachable(artifacts) -> None:
    """A canonical artifact may only stand on a generated input a pristine clone can create."""
    unreachable = []
    for a in artifacts:
        if not a.canonical:
            continue
        for inp, klass in a.input_classification.items():
            if klass != "GENERATED_DETERMINISTIC":
                continue
            g = generated_input_for(REPO, inp)
            if g is None or not g.bootstrap_complete:
                unreachable.append((a.canonical_path, inp))
    assert unreachable == [], (
        "canonical artifacts standing on generated inputs the declared bootstrap does not "
        f"create: {unreachable}"
    )


def test_5_structural_an_undeclared_generated_input_is_refused(tmp_path: Path) -> None:
    repo = _registry(
        tmp_path / "r",
        [
            _entry(
                input_closure=["knowledge/"],
                input_classification={"knowledge/": "GENERATED_DETERMINISTIC"},
            )
        ],
    )
    assert any("not declared in generated_inputs" in f for f in validate(repo))


def test_5_structural_an_incomplete_bootstrap_path_is_refused(tmp_path: Path) -> None:
    """Declaring a producer is not enough. The clone has to be able to RUN it."""
    repo = _registry(
        tmp_path / "r",
        [
            _entry(
                input_closure=["realization/"],
                input_classification={"realization/": "GENERATED_DETERMINISTIC"},
            )
        ],
        generated_inputs=[
            {
                "path": "realization/",
                "producer": "intelligence/realization/engine.py",
                "bootstrap_command": "python -m intelligence.realization realize",
                "bootstrap_stage": "NOT IN THE BOOTSTRAP — see bootstrap_gaps",
                "tracked": False,
                "deterministic": True,
            }
        ],
    )
    assert any("bootstrap path is incomplete" in f for f in validate(repo))
