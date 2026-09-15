"""Every governance engine under ``00-MASTER/``, loaded and held to one contract.

WHAT THIS CLOSES. Ω-4 measures ``unnameable_exemptions`` — "artifacts no coverage source
could name because their root is not a Python identifier" — and states the condition that
retires it: *"making those engines importable under test rather than only executable as
scripts."* Thirty-nine engines sat behind that measurement; fourteen had a test that
loaded them privately and twenty-five had nothing, so the plane that ENFORCES the
constitution was the plane with the least evidence about it.

THE POPULATION IS DERIVED, NEVER LISTED. ``00-MASTER/*/*_engine.py`` is a glob over the
tree, so an engine added tomorrow is held to this contract on the commit that creates it,
with no edit here. A list would have been the thing this repository has already been
caught by three times — and it would have been a closed enumeration in a file whose whole
subject is refusing them.

WHAT IS ASSERTED, AND WHAT IS DELIBERATELY NOT. These are smoke properties: an engine
loads, it exposes an entry point, and importing it neither writes to the tree nor exits
the process. That is a floor, not a substitute for the behavioural suites the fourteen
already have and the twenty-five still owe. It is worth landing on its own because a
module that cannot be imported cannot be covered, and because import-time side effects in
a governance engine are the specific defect that makes one dangerous to test at all: an
engine that mutates state or calls ``sys.exit`` on import cannot be exercised by anything.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from engine.tests.conftest import load_governance_engine

REPO = Path(__file__).resolve().parents[3]
GOVERNANCE_ROOT = REPO / "00-MASTER"


def _engines() -> list[Path]:
    """Every governance engine, derived from the tree and sorted for a stable report."""
    return sorted(GOVERNANCE_ROOT.glob("*/*_engine.py"))


ENGINES = _engines()
IDS = [f"{p.parent.name}/{p.name}" for p in ENGINES]


def test_the_population_is_not_empty() -> None:
    """A parametrised suite over an empty population passes while asserting nothing."""
    assert ENGINES, (
        "no governance engine was discovered under 00-MASTER/*/*_engine.py; if the layout "
        "changed, this suite is measuring nothing and reporting success"
    )


@pytest.mark.parametrize("engine_path", ENGINES, ids=IDS)
def test_every_governance_engine_loads(engine_path: Path) -> None:
    """The condition Ω-4 names. A module that cannot be imported cannot be covered."""
    module = load_governance_engine(engine_path.parent.name, engine_path.name)
    assert module is not None


SIBLING_LOADERS = tuple(GOVERNANCE_ROOT.glob("*/*.py"))


@pytest.mark.parametrize("engine_path", ENGINES, ids=IDS)
def test_no_governance_engine_is_reachable_by_nothing(engine_path: Path) -> None:
    """Reachable by SOMETHING: a callable entry point, a ``__main__`` block, or a sibling
    that loads it.

    This asserted a callable entry point until three engines refused, and they were right
    to. ``UAKOS-CLOSURE-008/decision_engine.py`` and ``superiority_engine.py`` are function
    libraries with no ``__main__`` at all, loaded by ``assimilation_engine.py`` — for them
    "exposes no entry point" is the correct shape, not a defect, and forcing a ``main()``
    onto a library to satisfy a test would have been the test deforming its subject.

    The property worth holding is weaker and true: nothing here is reachable by NOTHING. An
    engine that no entry point exposes, no ``__main__`` runs and no sibling imports is dead
    code wearing the appearance of enforcement, which is the defect UEC-L-04 names at the
    level of gates and this holds at the level of modules.

    A ``__main__`` block is the weakest passing form and is deliberately still a pass:
    ``UAKOS-PHASE-001B/provenance_engine.py`` carries its logic inline there, so a test can
    load the module but cannot invoke what it does. That is a real limit on what any suite
    can assert about it — recorded here rather than legislated, because extracting a
    ``main()`` from it is a change to a governance engine and belongs in a commit that says
    so.
    """
    module = load_governance_engine(engine_path.parent.name, engine_path.name)
    named = [
        n for n in ("main", "run", "gate", "build", "verify") if callable(getattr(module, n, None))
    ]
    source = engine_path.read_text(encoding="utf-8")
    has_main_block = "__main__" in source
    stem = engine_path.name
    loaded_by_sibling = any(
        other != engine_path and stem in other.read_text(encoding="utf-8", errors="ignore")
        for other in SIBLING_LOADERS
        if other.parent == engine_path.parent
    )
    assert named or has_main_block or loaded_by_sibling, (
        f"{engine_path.relative_to(REPO)} exposes no entry point, runs no __main__ and is "
        f"loaded by no sibling: nothing in this repository can reach it"
    )


@pytest.mark.parametrize("engine_path", ENGINES, ids=IDS)
def test_loading_an_engine_writes_nothing(engine_path: Path) -> None:
    """Import-time side effects are what make a governance engine untestable.

    An engine that mutates the tree on import cannot be exercised by any suite, and — worse
    — would mutate it during the very run that is meant to observe it. That is the
    verification-purity boundary applied one level down, to the engines rather than to the
    entry point that calls them.
    """
    before = subprocess.run(  # noqa: S603
        ["/usr/bin/git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO
    ).stdout
    load_governance_engine(engine_path.parent.name, engine_path.name)
    after = subprocess.run(  # noqa: S603
        ["/usr/bin/git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO
    ).stdout
    assert after == before, (
        f"importing {engine_path.relative_to(REPO)} changed the working tree. A governance "
        f"engine that acts on import cannot be tested and cannot be trusted to observe."
    )


def test_the_loader_refuses_an_ambiguous_program() -> None:
    """Two programs already ship a `closure_engine`, so a bare stem is not an address."""
    ambiguous = [
        d.name
        for d in GOVERNANCE_ROOT.iterdir()
        if d.is_dir() and len(list(d.glob("*_engine.py"))) > 1
    ]
    if not ambiguous:
        pytest.skip("no program currently holds more than one engine")
    with pytest.raises(AssertionError, match="name one explicitly"):
        load_governance_engine(ambiguous[0])


def test_the_loader_refuses_an_absent_program() -> None:
    with pytest.raises(AssertionError, match="no governance program"):
        load_governance_engine("NO-SUCH-PROGRAM-999999")


def test_the_loader_refuses_an_absent_engine() -> None:
    with pytest.raises(AssertionError, match="no engine at"):
        load_governance_engine(ENGINES[0].parent.name, "not_an_engine")


# --- BASELINE-001: the ratification ceiling survives its own vacancy being discharged ---
#
# A REGRESSION THIS SUITE COULD NOT SEE. UCOS-RAT-002 located T1 and retired VAC-01, and
# BLN-CEI-01 read the open-vacancy collection alone: it found nothing, called the ceiling
# unbacked, and took the gate from 20/20 OPEN to 19/20 CLOSED on a corpus that had just
# SATISFIED the obligation. Nothing failed except the engine's own gate, because no test
# here asserted anything about what a measurement concluded.


def _baseline() -> dict:
    return json.loads((GOVERNANCE_ROOT / "BASELINE-001" / "baseline.json").read_text("utf-8"))


def _baseline_declaration() -> dict:
    path = GOVERNANCE_ROOT / "BASELINE-001" / "baseline-declaration.json"
    return json.loads(path.read_text("utf-8"))


def test_the_ceiling_binds_both_recorded_dispositions_of_its_vacancy() -> None:
    """Open under `vacancies`, or discharged by a located closing act. Either backs it."""
    ceiling = _baseline_declaration()["ceiling"]
    assert ceiling["vacancy_pointer"], "the open disposition must stay declared"
    assert ceiling["discharge_pointer"], "the discharged disposition must be declared too"
    assert ceiling["discharge_field"], "the field carrying the closing act must be named"


def test_a_discharged_vacancy_still_backs_the_ratification_ceiling() -> None:
    """The measured state after UCOS-RAT-002: no vacancy is OPEN, and the cap still holds."""
    measured = _baseline()
    ceiling = measured["ceiling"]
    assert ceiling["vacancies_located"] == 0, "VAC-01 was retired; an open one would be news"
    assert ceiling["vacancies_discharged"] >= 1, "the closing act must be located"
    assert ceiling["bound"] is True
    assert measured["gate"] == "OPEN"
    assert measured["blocking_failures"] == []


def test_the_ceiling_is_disclosed_and_no_baseline_is_elevated() -> None:
    """What the fix must NOT have relaxed: the cap itself, and the prohibition under it."""
    ceiling = _baseline()["ceiling"]
    assert ceiling["disclosure_token"] == "CERTIFIED-PROVISIONAL"
    assert ceiling["terminal_token"] == "FINALIZED"
    assert ceiling["elevated"] == [], "an elevated baseline would be a finality this corpus lacks"


# --- no governance gate closes unnoticed --------------------------------------------
#
# THE FAILURE THIS REFUSES IS SILENCE, NOT CLOSURE. A programme is entitled to close its
# gate; what it is not entitled to do is close it and have nobody know. Measured twice in
# one span: BASELINE-001 fell from 20/20 OPEN to 19/20 CLOSED inside a commit titled "the
# ratification reconciled at its claim owners" and stayed closed for five days, and UFEP
# was re-measured into a CLOSED gate under the subject line "eligibility TRUE, 5/5,
# drift 0". Both messages read as success. Neither was checked by anything, because a
# closed gate is a value in a generated file and no test read it.
#
# The table below is the whole mechanism: a programme measuring CLOSED must be named here
# with a reason, so closing a gate costs a reviewable diff instead of nothing. It is
# checked in BOTH directions — an entry naming a programme that has since reopened is a
# stale permission, and a stale permission is how the next silent closure would pass.

ACKNOWLEDGED_CLOSED: dict[str, str] = {
    "UCOS-UFEP-001": (
        "CORRECT AND NOT STALE. UFEP-VAL-11 requires every valid record of the located "
        "ratification registry to be a declared freeze subject. URAT carries six records "
        "and UFEP declares five, and the sixth CANNOT become the missing subject: "
        "URAT-REC-06 records UCOS-RAT-002, which states in its own text that it 'does not "
        "certify anything (certification has its own owners)' and 'does not freeze "
        "anything (CEP-007 reserves that to Freeze Authority)', and the record carries no "
        "admits_freeze. A freeze subject requires located validation AND certification "
        "evidence; the certification evidence does not exist because the act declined to "
        "produce it. The gate is therefore reporting a true incompleteness, and closing "
        "it would require either the Freeze Authority to act or a declared exclusion — "
        "both determinations this repository does not hold."
    ),
}


def _programme_states() -> dict[str, tuple[Path, object, object]]:
    """Every programme publishing a gate STATE, keyed by programme.

    `gate` is not one vocabulary. UCOS-UGA-001 publishes `gate: FAIL_CLOSED` as a POLICY
    descriptor — how the gate behaves — while reporting `result: PASS` at 30/30, so a
    reading that treated the string as a state would refuse a passing programme. Only the
    exact value CLOSED, or a non-zero gate_exit, is read as closure here.
    """
    found: dict[str, tuple[Path, object, object]] = {}
    for path in sorted(GOVERNANCE_ROOT.glob("*/*.json")):
        if "declaration" in path.name or "manifest" in path.name:
            continue
        try:
            document = json.loads(path.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(document, dict):
            continue
        gate, exit_code = document.get("gate"), document.get("gate_exit")
        closed = (isinstance(gate, str) and gate.upper() == "CLOSED") or (
            isinstance(exit_code, int) and not isinstance(exit_code, bool) and exit_code != 0
        )
        if closed:
            found[path.parent.name] = (path, gate, exit_code)
    return found


def test_no_governance_gate_is_closed_without_an_acknowledgement() -> None:
    """A gate may close. It may not close silently."""
    closed = _programme_states()
    unacknowledged = sorted(set(closed) - set(ACKNOWLEDGED_CLOSED))
    assert not unacknowledged, (
        "governance gate(s) measured CLOSED with no acknowledgement: "
        + ", ".join(
            f"{p} ({closed[p][0].relative_to(REPO)}: gate={closed[p][1]!r}, "
            f"gate_exit={closed[p][2]!r})"
            for p in unacknowledged
        )
        + " — record why in ACKNOWLEDGED_CLOSED, or reopen the gate."
    )


def test_no_acknowledgement_outlives_the_closure_it_explains() -> None:
    """The other direction. A permission nobody needs is a permission nobody notices."""
    stale = sorted(set(ACKNOWLEDGED_CLOSED) - set(_programme_states()))
    assert not stale, (
        "ACKNOWLEDGED_CLOSED names programme(s) whose gate is no longer closed: "
        + ", ".join(stale)
        + " — delete the entry; it would silently admit the next closure."
    )


def test_every_acknowledgement_states_a_reason() -> None:
    """An entry that says nothing is an exemption wearing a table's clothes."""
    for programme, reason in ACKNOWLEDGED_CLOSED.items():
        assert len(reason.split()) >= 25, f"{programme}: acknowledgement is not a reason"
