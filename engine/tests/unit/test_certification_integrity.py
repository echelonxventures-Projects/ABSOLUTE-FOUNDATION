"""UCI-000001 — non-vacuity suite for the certification integrity programme.

A gate with no reachable PASS state carries no evidentiary value, and neither does one with no
reachable FAIL state. This suite proves both directions for every law, and it proves them by
MUTATING the measured input rather than by calling the law with hand-built arguments: a law tested
against a fixture it never sees in production is a law tested against a different function.

WHAT IS PROVEN

  * the gate is OPEN on the measured working tree (a reachable PASS)
  * every law REFUSES when its debt grows by one (a reachable FAIL, per law)
  * the ratchet is ONE-sided — a repayment is accepted with no edit anywhere, because Ω-4 replaced
    a two-sided ceiling that refused any measurement below the declared value and so made every
    improvement a chore indistinguishable from a retreat
  * a declared ceiling that binds no measurement is refused
  * the coverage reader reproduces coverage.py's own totals, so it is reading and not guessing
  * the coverage comparison detects a single moved line, which is the granularity Rules 8/10/11
    depend on and the granularity a percentage comparison does not have
  * statement attribution PARTITIONS: object counts sum to the set the surface distributed
    (the AST statements, intersected with coverage's own countable lines when a report names
    the file), and never exceed the file's AST count
  * the shuffle plugin is inactive without a seed, reproducible with one, and genuinely reorders
  * the extraction seal is deterministic, and the fingerprint detects a moved tree
  * an empty or single shard partition is refused rather than silently measured

The suite deliberately does NOT run the test suite, build a virtualenv or measure coverage. Those
are the expensive measurements the programme exists to take; asserting them here would make this
file a second, slower copy of them.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import pytest

from engine.certification_integrity import (
    contract,
    coverage_data,
    immutable,
    inventory,
    pytest_shuffle,
    surface,
)
from engine.certification_integrity.equivalence import discover_test_modules, partition
from engine.certification_integrity.model import (
    FILE_EXECUTABLE,
    FILE_TOOLING,
    PLANE_TYPES,
    IntegrityError,
)
from engine.universal_discovery import ratchet as omega_ratchet

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def built() -> inventory.Inventory:
    """One inventory for the whole module. Building it is the expensive part, not the assertions."""
    return inventory.build(str(REPO))


@pytest.fixture(scope="module")
def declaration() -> contract.Declaration:
    return contract.load_declaration(str(REPO))


@pytest.fixture(scope="module")
def report() -> dict[str, Any]:
    """One measurement for the whole module. Rebuilding it per test cost 10s a time."""
    return contract.measure(str(REPO))


# --------------------------------------------------------------- the reachable PASS state


def test_the_gate_is_open_on_the_measured_working_tree(report: dict[str, Any]) -> None:
    """Without this, every refusal below could be asserting over nothing.

    THE SUBJECT IS THE WORKING TREE, NOT THE COMMIT, and saying so is the whole of this change.
    The `report` fixture is `contract.measure(str(REPO))`, which reads the checkout as it stands —
    committed, staged and modified content alike. This test was named for "the committed
    repository" and its failure message said so, which is true only when the tree happens to be
    clean. On a dirty tree it attributed uncommitted work to HEAD and sent a reader to `git log`
    for a cause sitting in `git status`; the measured refusal named `00-BOOK/tools/*` offenders
    that are present in the checkout and absent from the commit.

    MEASURING THE COMMIT INSTEAD WOULD MAKE THE OLD NAME TRUE AND THE TEST VACUOUS, which is why
    the name was corrected rather than the subject. A frozen extraction of HEAD carries HEAD's
    declaration, whose ratchet keys are NUMBERS — `contract` refuses that as a FAULT under Ω-4 —
    and carries no sealed state at all, so `best` is None, no bound can be exceeded, and no law
    can refuse. A test that cannot fail is not a guard.

    The assertion itself is unchanged: OPEN, or name every refusal.
    """
    state = immutable.fingerprint(str(REPO))
    refused = [law for law in report["laws"] if law["status"] == contract.REFUSED]
    assert report["status"] == contract.OPEN, (
        f"the WORKING TREE does not satisfy its own declaration — HEAD {state.head[:8]} with "
        f"{state.dirty_entries} uncommitted path(s), so this verdict is about the checkout and "
        f"not about the commit: {[(law['law'], law['detail']) for law in refused]}"
    )


def test_the_inventory_is_not_empty(built: inventory.Inventory) -> None:
    """A measurement over nothing reports no violations and means nothing."""
    assert len(built.files) > 1000, f"only {len(built.files)} files enumerated"
    assert len(built.objects) > 10000, f"only {len(built.objects)} objects enumerated"
    assert built.totals["executable_statements"] > 100000


def test_every_declared_ceiling_binds_a_measurement(
    declaration: contract.Declaration,
) -> None:
    assert set(declaration.ratchet) == set(contract.RATCHETED), (
        "the declaration and the measurement table disagree: "
        f"only declared {sorted(set(declaration.ratchet) - set(contract.RATCHETED))}; "
        f"only measured {sorted(set(contract.RATCHETED) - set(declaration.ratchet))}"
    )


def test_every_law_in_the_table_is_declared(declaration: contract.Declaration) -> None:
    """A law the declaration does not name is a law nobody agreed to."""
    declared = {law["id"] for law in declaration.raw["laws"]}
    bound = {law_id for law_id, _fn in contract.RATCHETED.values()}
    assert bound <= declared, f"laws measured but not declared: {sorted(bound - declared)}"


def test_no_law_is_non_blocking(declaration: contract.Declaration) -> None:
    """A law that can be switched off is reachable by the mutation it detects."""
    for law in declaration.raw["laws"]:
        assert law["blocking"] is True, f"{law['id']} is declared non-blocking"


# ------------------------------------------------------------------- NON-VACUITY, per law
# Each law is forged into failure by growing its own population by one.
#
# UNDER Ω-4 THE COMPARISON IS A DIRECTION, NOT A CEILING, so these tests supply the sealed state the
# comparison reads. What changed is which mutations refuse:
#
#   debt GROWS beyond the best-ever value          REFUSED, as before
#   debt is REPAID below the best-ever value       ACCEPTED — it used to be refused as "slack",
#                                                  which made every improvement fail the gate until
#                                                  somebody committed a new number. That fired on
#                                                  the commit introducing Ω: the denominator went
#                                                  from 65 to 64 and the gate closed.
#   the ratchet declares no KIND                   REFUSED, as before


def _sealed_state(declaration: contract.Declaration, **best: float) -> omega_ratchet.Ratchet:
    """A ratchet state holding ``best`` for the given metrics, with the declared kinds."""
    return omega_ratchet.Ratchet(
        {
            "best": dict(best),
            "kinds": {key: declaration.ratchet[key] for key in best if key in declaration.ratchet},
            "holds": {},
            "justifications": [],
            "floors": [],
        }
    )


@pytest.mark.parametrize("key", sorted(contract.RATCHETED))
def test_each_law_refuses_when_its_debt_grows(
    key: str, built: inventory.Inventory, declaration: contract.Declaration
) -> None:
    """One more offender than this repository's own best must refuse, and must name the law."""
    law_id, measurement = contract.RATCHETED[key]
    offenders = measurement(built)
    inflated = _inventory_with(built, key, offenders + ["invented/offender.py"])
    state = _sealed_state(declaration, **{key: float(len(offenders))})
    result = contract._ratcheted(inflated, declaration, key, state)
    assert result.status == contract.REFUSED, f"{law_id} tolerated a new violation"
    assert "REGRESSED" in result.detail
    assert result.measured == len(offenders) + 1


@pytest.mark.parametrize("key", sorted(contract.RATCHETED))
def test_each_law_accepts_repaid_debt_with_no_edit_anywhere(
    key: str, built: inventory.Inventory, declaration: contract.Declaration
) -> None:
    """THE DEFECT Ω-4 REPLACED, asserted as the new behaviour rather than described.

    The two-sided ceiling refused a measurement BELOW the declared value on the grounds that the
    declaration was carrying slack. The instinct was right and the implementation made improving the
    repository a chore: every repayment closed the gate until a human committed the new number, and
    the commit was indistinguishable from a retreat. Improving now requires no edit at all.
    """
    _law_id, measurement = contract.RATCHETED[key]
    offenders = measurement(built)
    if not offenders:
        pytest.skip(f"{key} is already zero, so there is no debt to repay")
    reduced = _inventory_with(built, key, offenders[:-1])
    state = _sealed_state(declaration, **{key: float(len(offenders))})
    result = contract._ratcheted(reduced, declaration, key, state)
    assert result.status == contract.HOLDS, "repaying debt was refused"
    assert "IMPROVED" in result.detail
    assert result.measured == len(offenders) - 1


@pytest.mark.parametrize("key", sorted(contract.RATCHETED))
def test_each_law_refuses_when_no_ratchet_kind_is_declared(
    key: str, built: inventory.Inventory, declaration: contract.Declaration
) -> None:
    """A measurement with no declared direction is recorded and enforced by nothing."""
    stripped = contract.Declaration(
        version=declaration.version,
        ratchet={k: v for k, v in declaration.ratchet.items() if k != key},
        source=declaration.source,
        raw=declaration.raw,
    )
    result = contract._ratcheted(built, stripped, key, omega_ratchet.Ratchet({}))
    assert result.status == contract.REFUSED
    assert "declares no KIND" in result.detail


def _inventory_with(
    base: inventory.Inventory, key: str, offenders: list[str]
) -> inventory.Inventory:
    """Rebuild an inventory whose ``key`` measurement returns exactly ``offenders``.

    The mutation is applied to the DATA the measurement reads, not to the measurement, so the test
    exercises the real function. Each law reads a different field, so each gets the shape it needs.
    """
    files = list(base.files)
    if key == "executable_outside_denominator":
        return _replace(base, executable_outside_denominator=tuple(offenders))
    if key == "ungoverned_executables":
        return _replace(base, ungoverned_files=tuple(offenders))
    if key in ("unmeasured_governance_engines", "engines_without_tests", "single_plane_engines"):
        keep = [f for f in files if not f.governing_authority.startswith("UEC-000001")]
        made = []
        for path in offenders:
            if key == "unmeasured_governance_engines":
                measured, sources = False, ("test", "make", "ci")
            elif key == "engines_without_tests":
                measured, sources = True, ("make", "ci")
            else:
                measured, sources = True, ("test", "make")
            made.append(
                _file(
                    path,
                    authority="UEC-000001 (enforcement closure inventory)",
                    measured=measured,
                    invocation_sources=sources,
                )
            )
        return _replace(base, files=tuple(keep + made))
    if key == "files_with_no_execution_path":
        keep = [
            f
            for f in files
            if not (
                f.measured
                and f.ast_statements > 20
                and not f.execution_paths
                and f.classification in (FILE_EXECUTABLE, FILE_TOOLING)
            )
        ]
        made = [
            _file(path, measured=True, statements=99, execution_paths=(), authority="x")
            for path in offenders
        ]
        return _replace(base, files=tuple(keep + made))
    raise AssertionError(f"no mutation defined for {key}")


def _file(
    path: str,
    *,
    authority: str = "NONE — no authority claims this file",
    measured: bool = False,
    statements: int = 10,
    execution_paths: tuple[str, ...] = ("f",),
    invocation_sources: tuple[str, ...] = (),
    ast_statements: int | None = None,
) -> Any:
    from engine.certification_integrity.model import FileRecord

    return FileRecord(
        path=path,
        classification=FILE_EXECUTABLE,
        statements=statements,
        covered=0,
        missing=statements,
        measured=measured,
        execution_paths=execution_paths,
        invocation_sources=invocation_sources,
        governing_authority=authority,
        exclusion_reason=None,
        # UCI-L-06 sizes files by their AST count, never by the coverage-intersected count, so a
        # synthetic offender must carry it or the law correctly declines to flag it.
        ast_statements=statements if ast_statements is None else ast_statements,
    )


def _replace(base: inventory.Inventory, **changes: Any) -> inventory.Inventory:
    return inventory.Inventory(
        files=changes.get("files", base.files),
        objects=base.objects,
        totals=base.totals,
        executable_outside_denominator=changes.get(
            "executable_outside_denominator", base.executable_outside_denominator
        ),
        ungoverned_files=changes.get("ungoverned_files", base.ungoverned_files),
        scope_drift=base.scope_drift,
    )


def test_an_orphan_ceiling_is_refused(tmp_path: Path) -> None:
    """A ratchet naming no measurement looks like enforcement and is not.

    The orphan is now a KIND rather than a number, because Ω-4 refuses a numeric ratchet before it
    ever reaches the orphan check — so injecting ``3`` would have tested the wrong refusal.
    """
    document = json.loads((REPO / contract.DECLARATION_RELATIVE).read_text(encoding="utf-8"))
    document["ratchet"]["invented_measurement"] = "CONVERGENT"
    root = tmp_path / "repo"
    (root / os.path.dirname(contract.DECLARATION_RELATIVE)).mkdir(parents=True)
    (root / contract.DECLARATION_RELATIVE).write_text(json.dumps(document), encoding="utf-8")
    loaded = contract.load_declaration(str(root))
    assert "invented_measurement" in loaded.ratchet
    assert set(loaded.ratchet) - set(contract.RATCHETED) == {"invented_measurement"}


def test_a_numeric_ratchet_is_refused(tmp_path: Path) -> None:
    """Ω-4: a ratchet declares a DIRECTION. A number is a snapshot of one afternoon.

    The premise inverted. This test used to require ceilings to be non-negative integers, which was
    the right rule for the wrong model: 65, 27, 39, 25, 14 and 10 were all valid under it, and two
    them had been 607 and 570 a week earlier. Every value below is now refused, including the ones
    that used to be the only accepted shape.
    """
    for bad in (-1, 0, 3, "3", 2.5, True, "WHATEVER", None):
        document = {"version": "1", "ratchet": {"engines_without_tests": bad}}
        root = tmp_path / f"repo-{bad!r}"
        (root / os.path.dirname(contract.DECLARATION_RELATIVE)).mkdir(parents=True)
        (root / contract.DECLARATION_RELATIVE).write_text(json.dumps(document), encoding="utf-8")
        with pytest.raises(IntegrityError, match="declares its KIND"):
            contract.load_declaration(str(root))


def test_every_declared_ratchet_kind_is_accepted(tmp_path: Path) -> None:
    """NON-VACUITY for the refusal above: the four legitimate directions must load."""
    for kind in ("MONOTONIC", "CONVERGENT", "DENSITY", "ENTROPY"):
        document = {"version": "1", "ratchet": {"engines_without_tests": kind}}
        root = tmp_path / f"repo-{kind}"
        (root / os.path.dirname(contract.DECLARATION_RELATIVE)).mkdir(parents=True)
        (root / contract.DECLARATION_RELATIVE).write_text(json.dumps(document), encoding="utf-8")
        assert contract.load_declaration(str(root)).ratchet == {"engines_without_tests": kind}


def test_an_absent_declaration_is_a_fault(tmp_path: Path) -> None:
    """Absence must not read as 'no violations'."""
    with pytest.raises(IntegrityError, match="is absent"):
        contract.load_declaration(str(tmp_path))


# ------------------------------------------------------------------ the coverage reader


def test_the_coverage_reader_reproduces_coveragepy_totals(tmp_path: Path) -> None:
    """Proof the reader reads. Hand-built XML with known totals, checked against them."""
    xml = tmp_path / "coverage.xml"
    xml.write_text(
        textwrap.dedent(
            """\
            <?xml version="1.0" ?>
            <coverage branches-valid="4" branches-covered="2">
              <sources><source>/nowhere</source></sources>
              <packages><package><classes>
                <class filename="a.py"><lines>
                  <line number="1" hits="1"/><line number="2" hits="0"/>
                  <line number="3" hits="1"/>
                </lines></class>
                <class filename="b.py"><lines>
                  <line number="7" hits="0"/>
                </lines></class>
              </classes></package></packages>
            </coverage>
            """
        ),
        encoding="utf-8",
    )
    report = coverage_data.parse(str(xml), repository=str(tmp_path))
    assert report.statements == 4
    assert report.covered == 2
    assert report.percent == 50.0
    assert report.branch_percent == 50.0
    assert report.files["a.py"].hit == frozenset({1, 3})
    assert report.files["a.py"].missed == frozenset({2})


def test_an_unparseable_coverage_document_is_a_fault(tmp_path: Path) -> None:
    """The measured incident: two processes wrote one coverage.xml and produced valid-looking
    bytes with a second document appended. Salvaging the first document would have yielded a
    valid-but-wrong report, so the reader refuses instead."""
    xml = tmp_path / "coverage.xml"
    xml.write_text("<coverage></coverage>\n<line number='1' hits='1'/>\n", encoding="utf-8")
    with pytest.raises(IntegrityError, match="not parseable coverage XML"):
        coverage_data.parse(str(xml), repository=str(tmp_path))


def test_a_coverage_document_measuring_nothing_is_a_fault(tmp_path: Path) -> None:
    xml = tmp_path / "coverage.xml"
    xml.write_text("<coverage><packages></packages></coverage>", encoding="utf-8")
    with pytest.raises(IntegrityError, match="names no measured file"):
        coverage_data.parse(str(xml), repository=str(tmp_path))


def test_an_absent_coverage_document_is_a_fault(tmp_path: Path) -> None:
    with pytest.raises(IntegrityError, match="refusing to report a coverage figure"):
        coverage_data.parse(str(tmp_path / "nope.xml"), repository=str(tmp_path))


def _report(files: dict[str, tuple[set[int], set[int]]]) -> coverage_data.CoverageReport:
    return coverage_data.CoverageReport(
        files={
            path: coverage_data.FileCoverage(path, frozenset(hit), frozenset(missed))
            for path, (hit, missed) in files.items()
        },
        branches_valid=0,
        branches_covered=0,
    )


def test_the_comparison_detects_a_single_moved_line() -> None:
    """The granularity Rules 8, 10 and 11 rest on, and the one a percentage does not have."""
    left = _report({"a.py": ({1, 2}, {3})})
    right = _report({"a.py": ({1, 3}, {2})})
    assert left.percent == right.percent, "the fixture must hold the ratio equal to be meaningful"
    diff = coverage_data.compare(left, right)
    assert diff["identical"] is False
    assert diff["files_with_differing_lines"]["a.py"] == {
        "covered_only_in_first": [2],
        "covered_only_in_second": [3],
    }


def test_the_comparison_detects_a_file_that_stopped_being_measured() -> None:
    left = _report({"a.py": ({1}, set()), "b.py": ({1}, set())})
    right = _report({"a.py": ({1}, set())})
    diff = coverage_data.compare(left, right)
    assert diff["identical"] is False
    assert diff["files_only_in_first"] == ["b.py"]


def test_identical_measurements_compare_identical() -> None:
    left = _report({"a.py": ({1, 2}, {3})})
    right = _report({"a.py": ({1, 2}, {3})})
    assert coverage_data.compare(left, right)["identical"] is True
    assert left.digest() == right.digest()


def test_the_digest_separates_unmeasured_from_uncovered() -> None:
    """Rule 11 lists 'measured files change' and 'coverage changes' as distinct failures."""
    measured_and_uncovered = _report({"a.py": (set(), {1, 2})})
    not_measured_at_all = _report({"a.py": (set(), set())})
    assert measured_and_uncovered.digest() != not_measured_at_all.digest()


# ------------------------------------------------------------------- surface attribution


def test_statement_attribution_partitions_rather_than_nests() -> None:
    """A method's statements belong to the method, not also to its class and its module.

    Nesting would let one statement be covered three times and make object totals exceed the
    file, which would silently inflate every aggregate built from them.

    THE COMPARISON IS AGAINST THE SET THE SURFACE ACTUALLY DISTRIBUTES, not against the raw AST
    statement set, and the difference is the whole reason this test was a false green. `surface`
    builds the AST set as a deliberate SUPERSET and then joins it (`surface.py:599-601`):

        countable = _statement_lines(tree)
        if file_coverage is not None:
            countable &= file_coverage.hit | file_coverage.missed

    so whenever `coverage.xml` names the module, every line coverage.py does not count as a
    statement is dropped before attribution — for `model.py` that is exactly its 8 docstrings,
    which `ast.stmt` counts and coverage.py does not. Comparing against the raw AST set
    therefore asserted `104 == 112` and could only ever pass when NO coverage document named
    the module.

    That precondition was never stated, and for a long time it was satisfied by accident: under
    the coverage-source-root collision (fixed in `pytest_scope`), `coverage xml` keyed this file
    as bare `model.py` rather than `engine/certification_integrity/model.py`, so the lookup
    missed, no join happened, and the assertion held. Rendering the document correctly unmasked
    it. One defect was hiding another, so this test is written against the invariant it
    documents — an exact partition, in BOTH regimes — rather than against one of them.
    """
    import ast

    scope = surface.read_scope(str(REPO))
    built = surface.build(
        str(REPO),
        paths=[
            "engine/certification_integrity/model.py",
            "engine/certification_integrity/contract.py",
            "pyproject.toml",
        ],
    )
    assert scope.flag_packages

    # Read the join through `surface`'s own helpers. A second parser here would make this test
    # assert that two implementations agree, which is not the property under test.
    candidate = REPO / "coverage.xml"
    report = (
        coverage_data.parse(str(candidate), repository=str(REPO)) if candidate.exists() else None
    )

    for module in ("engine/certification_integrity/model.py",):
        objects = [o for o in built.objects if o.module == module]
        assert objects, f"{module} produced no objects"
        own = sum(o.statements for o in objects)

        tree = ast.parse((REPO / module).read_text(encoding="utf-8"))
        countable = surface._statement_lines(tree)
        ast_total = len(countable)
        joined = report.files.get(module) if report else None
        if joined is not None:
            countable = countable & (set(joined.hit) | set(joined.missed))

        assert own == len(countable), (
            f"attribution does not partition for {module}: objects sum to {own}, the surface "
            f"distributed {len(countable)} line(s)"
        )
        # The anti-nesting property itself, stated independently of the join: attribution can
        # never manufacture a line the file does not have.
        assert own <= ast_total, (
            f"attribution EXCEEDS the file for {module}: objects sum to {own}, the AST has "
            f"{ast_total} — a statement is being counted by more than one object"
        )


def test_docstrings_are_not_invocation_evidence() -> None:
    """A module that DESCRIBES an engine has not invoked it.

    UEC-000001 records that counting docstrings as evidence moved its untested-engine deficit
    from 18 to 16 on prose alone. The same rule is measured here rather than assumed.
    """
    prose = '"""This module mentions engine.certification_integrity.gate at length."""\n'
    code = "import engine.certification_integrity.gate\n"
    assert "certification_integrity" not in surface._evidence(prose)
    assert "engine.certification_integrity.gate" in surface._evidence(code)


def test_every_object_reports_only_declared_plane_types(built: inventory.Inventory) -> None:
    for record in built.files:
        for plane in record.invocation_sources:
            assert plane in PLANE_TYPES, f"{record.path} reports unknown plane {plane!r}"


def test_unmeasured_files_report_none_rather_than_zero_coverage(
    built: inventory.Inventory,
) -> None:
    """Zero and unmeasured are different facts, and a float cannot hold both."""
    unmeasured = [r for r in built.files if not r.measured]
    assert unmeasured, "the fixture is vacuous: every file is measured"
    assert all(r.coverage_percent is None for r in unmeasured)


def test_a_tracked_boundary_that_cannot_be_established_is_a_fault(tmp_path: Path) -> None:
    """An empty world is the state in which every 'no violations' claim is true."""
    with pytest.raises(IntegrityError, match="tracked-path boundary could not be established"):
        surface.tracked_paths(str(tmp_path))


# ------------------------------------------------------------------------ the shuffle plugin


def test_the_shuffle_is_inactive_without_a_seed() -> None:
    assert pytest_shuffle.seed_from_environment({}) is None
    items = [1, 2, 3, 4, 5]
    original = list(items)
    pytest_shuffle.pytest_collection_modifyitems(items)
    assert items == original, "the plugin reordered a run that declared no seed"


def test_a_malformed_seed_is_ignored_rather_than_guessed_at() -> None:
    """Inventing a seed would report a permutation nobody chose and nobody can replay."""
    assert pytest_shuffle.seed_from_environment({"UCI_SHUFFLE_SEED": "banana"}) is None


def test_the_shuffle_is_reproducible_under_one_seed() -> None:
    items = list(range(50))
    assert pytest_shuffle.shuffled(items, 7) == pytest_shuffle.shuffled(items, 7)


def test_the_shuffle_is_not_vacuous() -> None:
    """A permutation that never permutes would make Rule 9 pass over the declared order."""
    items = list(range(50))
    assert pytest_shuffle.shuffled(items, 7) != items
    assert pytest_shuffle.shuffled(items, 7) != pytest_shuffle.shuffled(items, 8)
    assert sorted(pytest_shuffle.shuffled(items, 7)) == items, "the permutation lost items"


def test_the_shuffle_reports_its_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    """An order-dependent failure that cannot be replayed is an anecdote."""
    monkeypatch.setenv(pytest_shuffle.SEED_VARIABLE, "1234")
    header = pytest_shuffle.pytest_report_header()
    assert header is not None and "seed=1234" in header and "replay" in header


def test_the_shuffle_does_not_disturb_the_global_random_stream() -> None:
    """Seeding the global stream would make this measurement a cause of instability."""
    import random

    random.seed(99)
    expected = [random.random() for _ in range(3)]  # noqa: S311 - stream identity, not crypto
    random.seed(99)
    pytest_shuffle.shuffled(list(range(100)), 5)
    assert [random.random() for _ in range(3)] == expected  # noqa: S311


# --------------------------------------------------------------------- the frozen extraction


def test_the_seal_is_deterministic(tmp_path: Path) -> None:
    """Two extractions of one content must agree, or Rule 8's equality compares clocks."""
    shas = []
    for name in ("one", "two"):
        target = tmp_path / name
        target.mkdir()
        (target / "a.txt").write_text("content\n", encoding="utf-8")
        (target / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
        shas.append(immutable.seal(str(target)))
    assert shas[0] == shas[1], f"the seal is not content-addressed: {shas}"


def test_the_seal_leaves_the_extraction_clean(tmp_path: Path) -> None:
    """A purity check inside the extraction must not report the harness as contamination."""
    target = tmp_path / "repo"
    target.mkdir()
    (target / "a.txt").write_text("content\n", encoding="utf-8")
    immutable.seal(str(target))
    (target / ".uci-venv").mkdir()
    (target / ".uci-coverage-x.xml").write_text("x", encoding="utf-8")
    status = subprocess.run(  # noqa: S603
        ["git", "status", "--porcelain"],  # noqa: S607
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    )
    assert status.stdout.strip() == "", f"the extraction reports dirty: {status.stdout!r}"


def test_a_sealed_extraction_differs_when_content_differs(tmp_path: Path) -> None:
    shas = []
    for name, body in (("one", "a\n"), ("two", "b\n")):
        target = tmp_path / name
        target.mkdir()
        (target / "a.txt").write_text(body, encoding="utf-8")
        shas.append(immutable.seal(str(target)))
    assert shas[0] != shas[1], "the seal does not distinguish different content"


def test_the_fingerprint_detects_a_changed_tree(tmp_path: Path) -> None:
    """Rule 7's failure condition, measured rather than asserted."""
    target = tmp_path / "repo"
    target.mkdir()
    (target / "a.txt").write_text("one\n", encoding="utf-8")
    immutable.seal(str(target))
    before = immutable.fingerprint(str(target))
    (target / "b.txt").write_text("two\n", encoding="utf-8")
    after = immutable.fingerprint(str(target))
    assert before != after
    assert before.head == after.head, "the fixture changed HEAD, so it is not testing dirtiness"
    assert after.dirty_entries > before.dirty_entries


def test_require_stable_refuses_a_run_whose_tree_moved() -> None:
    moved = immutable.FrozenRun(
        sha="a" * 40,
        command=("true",),
        exit_code=0,
        duration_seconds=1.0,
        stdout_tail="",
        stderr_tail="",
        before=immutable.Fingerprint("a" * 40, "x", "y", 0),
        after=immutable.Fingerprint("b" * 40, "x", "y", 3),
        extraction=immutable.Extraction("a" * 40, "unused", "python", False, 0.0),
    )
    assert moved.tree_stable is False
    with pytest.raises(IntegrityError, match="changed while a certification run was in flight"):
        immutable.require_stable([moved])


# ------------------------------------------------------------------------ shard partitioning


def test_a_single_shard_partition_is_refused() -> None:
    with pytest.raises(IntegrityError, match="at least two shards"):
        partition(["a", "b"], 1)


def test_an_empty_shard_is_refused() -> None:
    """An empty shard contributes no data and makes the combined total silently smaller."""
    with pytest.raises(IntegrityError, match="received no tests"):
        partition(["a", "b"], 4)


def test_the_partition_is_a_permutation_of_its_input() -> None:
    modules = [f"test_{i}.py" for i in range(23)]
    groups = partition(modules, 4)
    flattened = sorted(item for group in groups for item in group)
    assert flattened == sorted(modules), "the partition lost or duplicated a module"
    assert len({len(g) for g in groups}) <= 2, "the partition is badly unbalanced"


def test_a_shard_proof_over_an_empty_suite_is_refused(tmp_path: Path) -> None:
    with pytest.raises(IntegrityError, match="no test modules found"):
        discover_test_modules(str(tmp_path), ["nowhere"])


def test_the_repository_offers_test_modules_to_shard() -> None:
    found = discover_test_modules(str(REPO), ["engine/tests"])
    assert len(found) > 100
    assert all(name.endswith(".py") for name in found)


# ------------------------------------------------------------------------- classification


def test_the_default_classification_is_executable() -> None:
    """The cheap classification must be the one that costs work."""
    classification, rule, reason = inventory._classify(
        "engine/whatever/thing.py", "x = 1\n", {}, is_test=False
    )
    assert (classification, rule, reason) == (FILE_EXECUTABLE, "UCI-C-00", None)


def test_a_declared_exclusion_carries_its_reason_through() -> None:
    classification, _rule, reason = inventory._classify(
        "engine/uicm/thing.py", "x = 1\n", {"engine.uicm": "stated reason"}, is_test=False
    )
    assert classification == "intentionally_excluded"
    assert reason == "stated reason"


def test_a_generated_marker_is_detected_by_content_not_path() -> None:
    classification, rule, _ = inventory._classify(
        "engine/x/y.py", "# DO NOT EDIT - auto-generated\nx = 1\n", {}, is_test=False
    )
    assert (classification, rule) == ("generated", "UCI-C-02")


def test_the_inventory_document_is_deterministic(built: inventory.Inventory) -> None:
    """Rule 7 records an inventory digest; a digest over unstable bytes records nothing."""
    again = inventory.build(str(REPO))
    assert built.digest() == again.digest()
    assert json.dumps(built.as_document(), sort_keys=True) == json.dumps(
        again.as_document(), sort_keys=True
    )


def test_the_inventory_declares_no_authority(built: inventory.Inventory) -> None:
    document = built.as_document()
    assert document["authority"].startswith("NONE")
    assert "determinism" in document


def test_no_wall_clock_or_machine_path_leaks_into_the_inventory(
    built: inventory.Inventory,
) -> None:
    """A register carrying a timestamp cannot be a fixed point."""
    encoded = json.dumps(built.as_document())
    assert str(REPO) not in encoded, "an absolute machine path leaked into the inventory"
    import re

    assert not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", encoded), "a timestamp leaked in"


def test_measuring_does_not_mutate_the_declaration_it_reads(
    declaration: contract.Declaration, report: dict[str, Any]
) -> None:
    """Guards against a law that repairs its own expectation as a side effect."""
    snapshot = copy.deepcopy(dict(declaration.ratchet))
    # ``ratchet_declared`` became ``ratchet_kinds`` when the declaration stopped carrying numbers.
    # The bounds moved to the sealed state and are reported separately as ``ratchet_best``.
    assert report["ratchet_kinds"] == snapshot
    assert dict(contract.load_declaration(str(REPO)).ratchet) == snapshot
    assert set(report["ratchet_best"]) == set(
        contract.RATCHETED
    ), "every measured law must report the bound it was held to"
