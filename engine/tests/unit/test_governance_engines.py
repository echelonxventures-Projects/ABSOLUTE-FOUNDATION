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
