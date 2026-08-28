"""UCOS-COV-SCOPE-001 — the coverage denominator is governed, not assumed.

WHY THIS FILE EXISTS, STATED AS THE MEASUREMENT THAT PRODUCED IT.

A coverage percentage is a ratio, and this repository governed only its numerator. The
denominator was declared **twice** — ``addopts`` carries one ``--cov=`` flag per package,
``[tool.coverage.run] source`` carries one path per package — two independent lists reconciled
by nobody. They happened to agree. Nothing required them to, and nothing would have reported it
if they had stopped.

Worse, a package could be absent from *both* and simply not be measured. Three were:

    engine.enforcement_closure      711 statements   ← UEC-000001, the closure programme itself
    engine.constitution           1,976 statements
    engine.uicm                   1,893 statements   ← and zero test files

4,580 statements — 5.2% of the source tree — outside a denominator that was reporting 97%. The
number was not wrong; it was answering a smaller question than it appeared to. UEC-000001 being
one of the three is the sharpest form of it: the programme that refuses "nothing enforces by
existing" was itself outside the measurement it imposes.

WHAT THIS FILE REFUSES, in both directions:

* a package under ``engine/`` or ``platform/`` that is measured by neither list;
* a package in one scope list and not the other;
* a declared exclusion that is stale — naming a package that is now measured, or gone.

THE EXCLUSION LIST IS THE POINT. Excluding ``engine.uicm`` silently is what kept it invisible.
Naming it in ``[tool.ucos.coverage_scope]`` with a reason makes the omission arguable, which is
the only honest form an exclusion can take. An entry that stops being true is itself a refusal,
so the list cannot rot into a blanket exemption — the same construction
``$rules_expected_to_claim_no_tracked_path`` uses in the mutation governance boundary.

WHAT THIS FILE DOES NOT CLAIM. It does not measure coverage and does not assert a percentage.
It governs the SET the percentage is computed over. A partial test run reports a low percentage
against this same scope and that is arithmetic, not regression: measured on one test file the
suite reports 23%, on another 0%, and on the whole suite 97%. Only the whole-suite figure means
anything, which is why ``./verify.sh`` applies the floor after combining every shard and passes
``--cov-fail-under=0`` to each shard individually.
"""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
PYPROJECT = REPO / "pyproject.toml"

#: The trees whose packages are subject to the denominator. Test packages are excluded by
#: ``[tool.coverage.run] omit`` and are not source under measurement.
SOURCE_TREES = ("engine", "platform")
_NOT_A_SOURCE_PACKAGE = frozenset({"tests"})


@pytest.fixture(scope="module")
def config() -> dict[str, Any]:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def _flag_scope(config: dict[str, Any]) -> set[str]:
    """The packages ``addopts`` measures, as dotted names."""
    addopts = config["tool"]["pytest"]["ini_options"]["addopts"]
    return {a.split("=", 1)[1] for a in addopts if a.startswith("--cov=")}


def _source_scope(config: dict[str, Any]) -> set[str]:
    """The packages ``[tool.coverage.run] source`` measures, as dotted names."""
    return {p.replace("/", ".") for p in config["tool"]["coverage"]["run"]["source"]}


def _excluded(config: dict[str, Any]) -> dict[str, str]:
    declared = config["tool"]["ucos"]["coverage_scope"]["excluded_packages"]
    return {entry["package"]: entry["reason"] for entry in declared}


def _packages_present() -> set[str]:
    """Every source package in the measured trees, read from the filesystem.

    ENUMERATION IS BY TRACKED MODULE, NOT BY ``__init__.py``, and that distinction is the
    defect this function was rewritten to close. The original asked ``(child /
    "__init__.py").exists()``, which is not the question "is this a package Python can
    import" — it is the question "is this a package of the *regulated* kind". Since PEP 420
    an implicit namespace directory imports perfectly well without one, so a directory of
    modules with no ``__init__.py`` was invisible to the control, and being invisible to the
    control meant being outside the denominator with nothing saying why. That is the exact
    failure mode the module docstring above describes, reappearing one level up: the guard
    against unmeasured packages had its own unmeasured-package hole.

    Measured consequence: ``engine/recursive_knowledge`` — 16 modules, 2,849 statements,
    URKE-000001, a live gate with a ``verify.sh`` stage, a Makefile target, a workflow and a
    135-test suite — has no ``__init__.py``. It was named by neither scope list and by no
    exclusion, and every test in this file passed. ``verify.sh`` runs it as
    ``-m engine.recursive_knowledge.gate``, so the repository imports as a package precisely
    what this function declined to count as one.

    A directory is therefore a source package if it contains any ``.py`` file at any depth.
    That predicate is strictly wider than the old one and cannot be satisfied by a naming
    convention, which is what makes it unable to miss the namespace case again.

    AND THE POPULATION IS ``git ls-files``, NOT THE FILESYSTEM. Widening the predicate without
    also fixing the boundary immediately produced the mirror-image defect: the wider scan found
    ``engine/certification_integrity`` — one untracked ``__init__.py``, two statements, absent
    from a fresh clone — and failed this control on local debris. A guard that decides
    differently on a working copy than on a clean checkout is not a guard, it is the
    non-reproducibility it was written to eliminate; the same shape as a test asserting a
    gitignored artifact. Every other closure mechanism in this repository quantifies over
    ``git ls-files`` for this reason, and so does this one. Untracked contamination is real and
    is somebody's problem — it is RIB GATE-12's, which surfaces it as working-tree
    contamination, and not the coverage denominator's.
    """
    tracked = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", "ls-files", "-z", *SOURCE_TREES],  # noqa: S607 - git from PATH by design
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8", errors="surrogateescape")

    found: set[str] = set()
    for path in tracked.split("\0"):
        if not path.endswith(".py"):
            continue
        parts = path.split("/")
        if len(parts) < 3 or parts[1] in _NOT_A_SOURCE_PACKAGE:
            continue
        found.add(f"{parts[0]}.{parts[1]}")
    return found


# --------------------------------------------------------------- the reachable PASS
# Without these, every refusal below could be asserting over nothing.


def test_the_two_scope_declarations_agree(config: dict[str, Any]) -> None:
    """One denominator, declared twice. Neither copy may drift from the other."""
    flags, source = _flag_scope(config), _source_scope(config)
    assert flags == source, (
        f"the coverage scope disagrees with itself — only in --cov=: {sorted(flags - source)}; "
        f"only in [tool.coverage.run] source: {sorted(source - flags)}"
    )
    assert flags, "the coverage scope is empty, so the percentage is computed over nothing"


def test_every_source_package_is_measured_or_declared_excluded(config: dict[str, Any]) -> None:
    """The whole control. A third possibility is what let 4,580 statements go unmeasured."""
    unaccounted = sorted(_packages_present() - _flag_scope(config) - set(_excluded(config)))
    assert not unaccounted, (
        "these packages are neither measured nor declared excluded, so they are outside the "
        f"coverage denominator and nothing says why: {unaccounted}. Add them to the scope, or "
        "name them in [tool.ucos.coverage_scope] with a reason."
    )


def test_no_declared_exclusion_is_stale(config: dict[str, Any]) -> None:
    """An excuse that stops being true is a refusal, so the list cannot rot."""
    present, measured = _packages_present(), _flag_scope(config)
    for package, reason in _excluded(config).items():
        assert package in present, (
            f"{package} is declared excluded from coverage but is not present in the tree; "
            "the exclusion is stale and must be withdrawn"
        )
        assert package not in measured, (
            f"{package} is declared excluded from coverage AND measured by --cov=; the "
            "exclusion is stale and must be withdrawn"
        )
        assert reason.strip(), f"{package} is excluded with no stated reason"


def test_the_scope_names_only_packages_that_exist(config: dict[str, Any]) -> None:
    """A --cov= flag naming nothing contributes nothing and reads as measurement."""
    ghosts = sorted(_flag_scope(config) - _packages_present())
    assert not ghosts, f"the coverage scope names packages absent from the tree: {ghosts}"


def test_the_enforcement_closure_programme_is_inside_the_denominator(
    config: dict[str, Any],
) -> None:
    """The specific self-exemption this control was written for. Named, so it cannot recur."""
    assert "engine.enforcement_closure" in _flag_scope(config)


def test_a_namespace_package_is_counted_as_present() -> None:
    """The second self-exemption: a package with no ``__init__.py`` must still be seen.

    ``engine.recursive_knowledge`` is the measured instance — 16 modules and no
    ``__init__.py``, which the previous ``__init__.py``-keyed enumeration could not see. It is
    named here rather than described so that deleting the widened predicate in
    ``_packages_present`` fails this test by name instead of silently restoring the hole.
    """
    present = _packages_present()
    assert "engine.recursive_knowledge" in present, (
        "engine/recursive_knowledge is a directory of tracked modules and must be counted as a "
        "source package whether or not it carries an __init__.py; enumeration keyed on "
        "__init__.py is what put 2,849 statements outside the denominator"
    )
    assert not (REPO / "engine" / "recursive_knowledge" / "__init__.py").exists(), (
        "engine/recursive_knowledge has acquired an __init__.py, so it is no longer evidence "
        "that namespace packages are enumerated; point this test at another namespace package "
        "or delete it, but do not let it pass vacuously"
    )


# ------------------------------------------------------------------- NON-VACUITY
# Every guard above is now forged into failure. A control that cannot refuse is decoration,
# and decoration is worse than nothing because it licenses the belief that something was checked.


def test_a_package_in_neither_list_is_refused(config: dict[str, Any]) -> None:
    """Drop a measured package from the scope without excluding it: the guard must fire."""
    mutated = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    ini = mutated["tool"]["pytest"]["ini_options"]
    ini["addopts"] = [a for a in ini["addopts"] if a != "--cov=engine.enforcement_closure"]
    with pytest.raises(AssertionError, match="neither measured nor declared excluded"):
        test_every_source_package_is_measured_or_declared_excluded(mutated)


def test_scope_lists_that_disagree_are_refused(config: dict[str, Any]) -> None:
    """Remove one package from one copy only — the exact drift two lists invite."""
    mutated = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    run = mutated["tool"]["coverage"]["run"]
    run["source"] = [p for p in run["source"] if p != "engine/enforcement_closure"]
    with pytest.raises(AssertionError, match="disagrees with itself"):
        test_the_two_scope_declarations_agree(mutated)


def test_an_exclusion_for_a_measured_package_is_refused() -> None:
    """Excluding something that is also measured is a claim about the past, not the present."""
    mutated = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    mutated["tool"]["ucos"]["coverage_scope"]["excluded_packages"].append(
        {"package": "engine.construct", "reason": "stale"}
    )
    with pytest.raises(AssertionError, match="stale"):
        test_no_declared_exclusion_is_stale(mutated)


def test_an_exclusion_for_an_absent_package_is_refused() -> None:
    mutated = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    mutated["tool"]["ucos"]["coverage_scope"]["excluded_packages"].append(
        {"package": "engine.no_such_package", "reason": "invented"}
    )
    with pytest.raises(AssertionError, match="not present in the tree"):
        test_no_declared_exclusion_is_stale(mutated)


def test_an_exclusion_with_no_reason_is_refused() -> None:
    """A reason is what makes an exclusion arguable rather than merely present."""
    mutated = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    mutated["tool"]["ucos"]["coverage_scope"]["excluded_packages"] = [
        {"package": "engine.uicm", "reason": "   "}
    ]
    with pytest.raises(AssertionError, match="no stated reason"):
        test_no_declared_exclusion_is_stale(mutated)


def test_a_scope_entry_naming_a_missing_package_is_refused() -> None:
    """A flag that measures nothing must not read as measurement."""
    mutated = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    mutated["tool"]["pytest"]["ini_options"]["addopts"].append("--cov=engine.does_not_exist")
    with pytest.raises(AssertionError, match="absent from the tree"):
        test_the_scope_names_only_packages_that_exist(mutated)


def test_an_empty_scope_is_refused() -> None:
    """The degenerate case: a denominator over nothing would report 100% forever."""
    mutated = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    ini = mutated["tool"]["pytest"]["ini_options"]
    ini["addopts"] = [a for a in ini["addopts"] if not a.startswith("--cov=")]
    mutated["tool"]["coverage"]["run"]["source"] = []
    with pytest.raises(AssertionError, match="computed over nothing"):
        test_the_two_scope_declarations_agree(mutated)


def test_untracked_debris_does_not_enter_the_denominator() -> None:
    """NON-VACUITY for the tracked boundary, and a regression pin for how it was found.

    Widening the package predicate to catch PEP 420 namespace directories immediately caught
    something else: ``engine/certification_integrity``, an untracked ``__init__.py`` present on
    one working copy and in no clone. Enumerating the filesystem made this control's verdict a
    function of local state, which is the precise failure it exists to eliminate — a guard that
    is green on a clean checkout and red on a developer's machine gets suppressed, and a
    suppressed guard measures nothing.

    So: a directory carrying a ``.py`` file that git does not track is not a source package.
    """
    present = _packages_present()
    tracked_dirs = {
        f"{p.split('/')[0]}.{p.split('/')[1]}"
        for p in subprocess.run(  # noqa: S603
            ["git", "ls-files", *SOURCE_TREES],  # noqa: S607
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        if p.endswith(".py") and len(p.split("/")) >= 3
    }
    assert present <= tracked_dirs, (
        "the coverage-scope control counted a package git does not track, so its verdict "
        f"depends on local state: {sorted(present - tracked_dirs)}"
    )


def test_a_namespace_package_is_still_a_source_package() -> None:
    """NON-VACUITY for the widened predicate. The specific miss, pinned by name.

    ``engine/recursive_knowledge`` has no ``__init__.py`` — it is an implicit namespace package
    (PEP 420) that ``verify.sh`` runs as ``-m engine.recursive_knowledge.gate``. The original
    predicate asked whether ``__init__.py`` existed and therefore did not see 2,849 statements
    across sixteen modules, while every test in this file passed.
    """
    assert not (REPO / "engine" / "recursive_knowledge" / "__init__.py").exists(), (
        "engine/recursive_knowledge now has an __init__.py; this test pins the NAMESPACE case "
        "and must be repointed at a package that still has none, or withdrawn"
    )
    assert "engine.recursive_knowledge" in _packages_present()
