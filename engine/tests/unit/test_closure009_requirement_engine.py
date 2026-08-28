"""UAKOS-CLOSURE-009 — Universal Constitutional Assimilation Programme validation suite.

This suite exists because UCOS-RIB-001 measured the programme's engine as BOTH a dead
engine (``VER-11`` / ``GAP-DEAD-ENGINE``: no declared entry point named it) and an orphan
capability (``VER-09``: unreachable in every declared reachability dimension). REG-AUTO-001
P7 requires enforceability by *tooling gates* rather than author discipline — at least one
Makefile target, at least one workflow and at least one test. This file is the test leg of
that discharge, and it is deliberately not a smoke test: the consequence of the engine being
unreachable was that nothing re-ran it, so its committed registers were left rendered
against a stale HEAD and reported 89 inherited concept gaps that Repository Truth had
already closed. An engine no target names is an engine nobody re-runs, and a register nobody
re-runs is a register that silently stops being true.

What is proven here, in the order the defects actually appeared:

  * committed registers are CURRENT       — they agree with the closure register they measure
  * replay is stable across the commit    — the recorded HEAD is reused, never re-read
  * requirement identity is derived       — RR-<CONCEPT-ID>, total and injective, CREATE = 0
  * measurement is fail-closed            — an absent required input asserts no verdict
  * no wall-clock is emitted              — regeneration is reproducible
  * reachability is mechanized            — the Makefile and workflow legs cannot regress

The suite is read-only over the repository: it never invokes the engine's writing path, so
running it cannot modify a single register.
"""

from __future__ import annotations

import importlib.util
import json
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
PROGRAM_DIR = REPO / "00-MASTER" / "UAKOS-CLOSURE-009"
ENGINE_PATH = PROGRAM_DIR / "requirement_engine.py"
RECORD_PATH = PROGRAM_DIR / "requirements.json"
CLOSURE_PATH = REPO / "00-MASTER" / "UAKOS-CLOSURE-002" / "closure.json"


def _load_engine():
    spec = importlib.util.spec_from_file_location("uakos_closure_009_engine", ENGINE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


re_ = _load_engine()


@pytest.fixture(scope="module")
def record() -> dict:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def closure() -> dict:
    return json.loads(CLOSURE_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------- the registers are still true
def test_committed_register_measures_the_current_closure_register(record, closure):
    """The concrete defect: a register left behind by an engine nobody re-ran.

    Every one of these fields is COPIED from the closure register at render time, so a
    disagreement means the committed register was rendered against a superseded substrate.

    P0-FINAL-CONVERGENCE-001. The commit sha is deliberately NOT compared for equality with
    the live closure register. It cannot be: `closure.json` records `git rev-parse --short
    HEAD` at generation time, so requiring the COMMITTED register to carry it demands that a
    committed artifact carry the sha of the commit that carries it — the exact impossibility
    `_head_commit` exists to prevent, in this module's own words. Git history shows the chase
    it produced, four generations deep: a5ff49a recorded 75166e2, c4a3a10 recorded 89d3baf,
    32a0f36 recorded 05ce974, b71b1e8 recorded d64fbb8 — every register naming its
    predecessor, one commit message reading "the register catches up to the commit that moved
    the corpus". The equality was therefore unsatisfiable at EVERY committed state, and once
    verify.sh regenerates closure.json on every run it fails at every commit rather than
    erroring on an absent file.

    What must agree is the MEASUREMENT the register copied, not the provenance sha. The three
    substantive fields below are what actually detect the original defect (a stale register
    reporting 89 phantom gaps Repository Truth had closed): a register rendered against a
    superseded substrate disagrees on determination, gap_total or concept_total. Detection is
    preserved; only the unsatisfiable provenance equality is dropped, and the sha is still
    required to be present and non-empty.
    """
    baseline = record["baseline"]
    assert str(baseline["closure_baseline_commit"]).strip(), "no closure baseline recorded"
    assert baseline["closure_determination"] == closure["determination"]
    assert baseline["closure_gap_total"] == closure["gap_total"]
    assert baseline["concept_total"] == closure["concept_total"]


def test_no_inherited_concept_gap_is_reported_once_closure_reports_none(record, closure):
    """The 89 phantom gaps. A stale register cannot invent a gap the closure has closed."""
    assert closure["gap_total"] == 0, "closure itself reports gaps — this assertion is void"
    inherited = [
        finding
        for finding in record["systemic_findings"]
        if "inherit" in json.dumps(finding).lower()
    ]
    for finding in inherited:
        assert finding.get("count", 0) == 0, f"stale inherited gap still reported: {finding}"


def test_every_requirement_is_homed_when_the_closure_homes_every_concept(record):
    unhomed = [r["requirement_id"] for r in record["requirements"] if not r["homed"]]
    assert unhomed == [], f"unhomed requirements: {unhomed[:10]}"


# ------------------------------------------------------------------- replay stability
def test_recorded_head_is_replayed_rather_than_re_read():
    """A committed artifact can never carry the sha of the commit that carries it.

    Without this the registers drift by exactly one field on every commit, which is why a
    byte-for-byte drift gate over this programme was previously unenforceable.
    """
    replayed = re_._head_commit({"baseline": {"head_commit": "deadbee"}})
    assert replayed == "deadbee"


def test_live_head_is_used_when_no_record_is_replayed():
    live = re_._head_commit(None)
    assert live and live != "deadbee"


def test_absent_or_blank_recorded_head_falls_back_and_never_yields_empty():
    for degenerate in ({}, {"baseline": {}}, {"baseline": {"head_commit": "  "}}):
        resolved = re_._head_commit(degenerate)
        assert resolved, f"{degenerate} produced an empty head commit"


def test_render_mode_is_declared_by_the_makefile_replay_target():
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    assert "\nclosure009-replay:\n" in makefile
    assert "--render --quiet" in makefile


# ------------------------------------------------------- derived, injective identity
def test_requirement_identity_is_a_derived_function_of_concept_identity(record):
    for requirement in record["requirements"]:
        assert requirement["requirement_id"] == f"RR-{requirement['concept_id']}"


def test_requirement_identity_is_injective_and_total_over_the_concepts(record, closure):
    ids = [r["requirement_id"] for r in record["requirements"]]
    concept_ids = [r["concept_id"] for r in record["requirements"]]
    assert len(set(ids)) == len(ids), "requirement identity is not injective"
    assert len(set(concept_ids)) == len(concept_ids)
    assert len(ids) == record["requirement_total"] == closure["concept_total"]


def test_the_programme_creates_no_concept(record):
    assimilation = record["assimilation"]
    assert assimilation["created_concepts"] == 0
    assert assimilation["reused_concepts"] == record["requirement_total"]


def test_every_requirement_carries_exactly_one_canonical_owner(record):
    for requirement in record["requirements"]:
        owner = requirement["canonical_owner"]
        assert isinstance(owner, str) and owner.strip(), requirement["requirement_id"]


# ------------------------------------------------------------------------ fail-closed
def test_a_required_input_that_is_absent_asserts_no_verdict(monkeypatch, tmp_path):
    """Exit 2, not a verdict. A measurement over an unknown substrate is not a measurement."""
    monkeypatch.setattr(re_, "REPO", tmp_path)
    assert re_.main([]) == 2


def test_gate_flags_are_recognised_by_the_engine():
    source = ENGINE_PATH.read_text(encoding="utf-8")
    for flag in ("--gate", "--baseline-gate", "--render", "--quiet"):
        assert flag in source, f"{flag} is not recognised"


# ------------------------------------------------------------------- reproducibility
def test_no_wall_clock_is_emitted():
    source = ENGINE_PATH.read_text(encoding="utf-8")
    for forbidden in ("datetime", "time.time", "strftime", "import random", "random."):
        assert forbidden not in source, f"{forbidden} would make regeneration irreproducible"


def test_the_record_carries_a_content_seal(record):
    seal = record["seal_sha256"]
    assert isinstance(seal, str) and len(seal) == 64


# ------------------------------------------------ REG-AUTO-001 P7, mechanized
# The dead-engine and orphan findings are only discharged while all three legs exist.
# Asserting them here is what stops the discharge from silently regressing: deleting the
# target or the workflow now breaks a test instead of quietly re-creating a dead engine.
def test_a_makefile_target_names_the_engine():
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    assert "00-MASTER/UAKOS-CLOSURE-009/requirement_engine.py" in makefile
    for target in ("closure009", "closure009-gate", "closure009-baseline-gate"):
        assert f"\n{target}:" in makefile, f"{target} is not declared"


def test_the_engine_targets_depend_on_the_predecessor_model():
    """The engine measures the PHASE-002/003 models; an unregenerated predecessor would
    make it measure a superseded substrate."""
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    for target in ("closure009", "closure009-gate", "closure009-baseline-gate"):
        assert f"\n{target}: closure-phase3\n" in makefile, f"{target} bypasses closure-phase3"
    assert "\nclosure-phase3:" in makefile


def test_a_workflow_names_the_engine():
    workflow = REPO / ".github" / "workflows" / "closure009-gate.yml"
    assert workflow.is_file(), "the CI leg of REG-AUTO-001 P7 is absent"
    body = workflow.read_text(encoding="utf-8")
    assert "00-MASTER/UAKOS-CLOSURE-009/requirement_engine.py" in body
    assert "closure009-replay" in body


def test_this_test_is_collected_by_the_canonical_test_runner():
    """This file sits inside a declared testpath, so `pytest` with no arguments runs it.

    UCOS-CL-008 — the assertion was a literal match on the full testpaths line, which made
    it a change-detector for that string rather than a check of the property it names: a
    legitimate ADDITION to the canonical collection broke it. It now asserts what it means,
    that this file's own root is declared, and additionally that intelligence/tests is
    declared — the omission that left the RIE coverage-isolation regression collected by
    nothing while it claimed to guard canonical identity.

    UCI-000001 — and it broke again, the same way, for the same reason. Reading ``testpaths``
    as a single LINE is still a formatting assertion: when the list grew past one line (four
    more roots were admitted, wiring up 3,995 tests that no runner collected), ``startswith
    ("testpaths")`` matched ``testpaths = [`` and every root moved to a line this check never
    read. Twice is a pattern, so the scrape is replaced by a TOML parse. ``tomllib`` answers
    the question the docstring claims to ask, and no reflow of the file can change its answer.
    """
    with (REPO / "pyproject.toml").open("rb") as handle:
        testpaths = tomllib.load(handle)["tool"]["pytest"]["ini_options"]["testpaths"]
    for root in ("engine/tests", "platform/tests", "intelligence/tests"):
        assert root in testpaths, f"{root} is not a canonical testpath: {testpaths}"
    assert Path(__file__).resolve().is_relative_to(REPO / "engine" / "tests")
