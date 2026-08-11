"""UCOS-CL-001 — an ignore rule must not be able to buy repository cleanliness.

The regression these tests exist for is specific and was real. At ``be46a300`` two lines
were added to ``.gitignore``:

    * [2-9]
    * [2-9].*

45 duplicate files were physically present. 41 of them left ``git status --porcelain``,
which is the command UCOS-RIB-001 counts for ``dirty_entries_outside_generated``. Nothing
was deleted. But the metric fell to zero, and that flipped RIB ``GATE-12`` and ``GATE-04``,
opened ``rib.json:gate``, satisfied AEE ``OBS-BLUEPRINT-GATE`` and cleared ``CONV-02``.

No test in the repository failed, because no test asserted the property that matters:
*exclusion must not be able to reduce the measured contamination on its own.*

``test_adding_an_ignore_rule_does_not_reduce_contamination`` is that assertion. It builds a
throwaway repository, plants a contaminating file, measures, then adds an ignore rule for
it and measures again — and requires the count to hold. It fails against the pre-fix
design by construction, because under that design the count is the porcelain line count.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from platform.repository_intelligence.contamination import (
    DECLARED_CLASSES,
    ContaminationReport,
    load_register,
    measure,
)

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607 - fixed argv, no shell
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    """A minimal repository carrying a valid exclusion register."""
    repo = tmp_path / "repo"
    (repo / "00-BOOK" / "DATA").mkdir(parents=True)
    _git(repo.parent, "init", "--quiet", str(repo))
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "test")

    (repo / "00-BOOK" / "DATA" / "exclusion-register.json").write_text(
        json.dumps(
            {
                "schema": "ucos-exclusion-register",
                "entries": [
                    {"rule": "__pycache__/", "class": "CACHE", "rationale": "bytecode"},
                ],
            }
        ),
        encoding="utf-8",
    )
    (repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (repo / "source.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "--quiet", "-m", "baseline")
    return repo


def test_baseline_sandbox_is_clean(sandbox: Path) -> None:
    report = measure(sandbox)
    assert report.clean, report.as_dict()
    assert report.contamination_entries == 0


def test_adding_an_ignore_rule_does_not_reduce_contamination(sandbox: Path) -> None:
    """THE regression. Exclusion without declaration must not lower the count.

    This is the property whose absence let a two-line .gitignore edit clear a blocking
    convergence criterion on a repository that still held every contaminating file.
    """
    (sandbox / "debris 2.py").write_text("y = 2\n", encoding="utf-8")

    before = measure(sandbox)
    assert before.contamination_entries == 1, before.as_dict()
    assert "debris 2.py" in before.untracked_entries

    # Exclude it — the exact move that manufactured cleanliness at be46a300. The rule is
    # COMMITTED, as it was there, so the only thing left to measure is the debris itself.
    (sandbox / ".gitignore").write_text("__pycache__/\n* [2-9].*\n", encoding="utf-8")
    _git(sandbox, "add", ".gitignore")
    _git(sandbox, "commit", "--quiet", "-m", "exclude the debris")

    after = measure(sandbox)
    assert after.contamination_entries == 1, (
        "adding an ignore rule reduced the contamination count without any declaration — "
        "the exclusion authority is again an input to the gate that polices exclusion.\n"
        f"before={before.as_dict()}\nafter={after.as_dict()}"
    )
    # It moved from 'untracked' to 'ignored but undeclared'. Still counted, now named.
    assert after.ignored_unclassified == 1
    assert "debris 2.py" in after.unclassified_paths


def test_declaring_the_class_is_what_clears_it(sandbox: Path) -> None:
    """The count falls only when a tracked, reviewable declaration accounts for the path.

    This is the other half of the invariant: exclusion is not forbidden, it is made to cost
    a declaration. A reviewer sees the class and can disagree with it.
    """
    (sandbox / "scratch.tmp").write_text("t\n", encoding="utf-8")
    (sandbox / ".gitignore").write_text("__pycache__/\n*.tmp\n", encoding="utf-8")
    _git(sandbox, "add", ".gitignore")
    _git(sandbox, "commit", "--quiet", "-m", "exclude scratch files")

    assert measure(sandbox).ignored_unclassified == 1

    register = sandbox / "00-BOOK" / "DATA" / "exclusion-register.json"
    doc = json.loads(register.read_text(encoding="utf-8"))
    doc["entries"].append({"rule": "*.tmp", "class": "TEMPORARY", "rationale": "scratch"})
    register.write_text(json.dumps(doc), encoding="utf-8")
    _git(sandbox, "add", "-A")
    _git(sandbox, "commit", "--quiet", "-m", "declare the class")

    after = measure(sandbox)
    assert after.ignored_unclassified == 0, after.as_dict()
    assert after.clean, after.as_dict()


def test_a_tracked_path_shadowed_by_an_ignore_rule_is_counted(sandbox: Path) -> None:
    """A tracked file matched by an ignore rule is contamination-in-waiting.

    It survives only because git does not apply ignore rules to indexed files. The moment
    it leaves the index it disappears from governance silently. `00-SOURCE/VISION/Missing
    2.docx` and `Missing 3.docx` were in exactly this state under the withdrawn rule, while
    the rule's own comment claimed numbered originals were not suppressed.
    """
    (sandbox / "Chapter 2.md").write_text("# two\n", encoding="utf-8")
    _git(sandbox, "add", "-A")
    _git(sandbox, "commit", "--quiet", "-m", "authored numbered document")
    assert measure(sandbox).clean

    (sandbox / ".gitignore").write_text("__pycache__/\n* [2-9].*\n", encoding="utf-8")

    after = measure(sandbox)
    assert "Chapter 2.md" in after.shadowed_tracked, after.as_dict()
    assert not after.clean


def test_undeclared_class_in_register_is_a_register_error(sandbox: Path) -> None:
    """A register entry carrying an unrecognised class declares nothing, and fails closed."""
    register = sandbox / "00-BOOK" / "DATA" / "exclusion-register.json"
    doc = json.loads(register.read_text(encoding="utf-8"))
    doc["entries"].append({"rule": "*.tmp", "class": "PROBABLY_FINE", "rationale": "no"})
    register.write_text(json.dumps(doc), encoding="utf-8")

    mapping, errors = load_register(sandbox)
    assert "*.tmp" not in mapping
    assert any("PROBABLY_FINE" in e for e in errors)
    assert not measure(sandbox).clean


def test_missing_register_fails_closed(tmp_path: Path) -> None:
    """No register is not 'nothing to check'. It is an unmeasurable repository."""
    repo = tmp_path / "bare"
    repo.mkdir()
    _git(tmp_path, "init", "--quiet", str(repo))
    mapping, errors = load_register(repo)
    assert mapping == {}
    assert errors and "missing" in errors[0]


# --- the live repository ----------------------------------------------------------------


def test_live_repository_has_no_unclassified_exclusion() -> None:
    """Every ignored path in THIS repository resolves to a declared class."""
    report = measure(REPO_ROOT)
    assert report.register_errors == [] or not report.register_errors, report.register_errors
    assert report.ignored_unclassified == 0, (
        "ignored paths with no declared class in the exclusion register:\n  "
        + "\n  ".join(report.unclassified_paths)
    )


def test_live_repository_shadows_no_tracked_path() -> None:
    """No tracked path in THIS repository is matched by an ignore rule."""
    report = measure(REPO_ROOT)
    assert report.shadowed_tracked == (), (
        "tracked paths matched by an ignore rule — they survive only by being indexed:\n  "
        + "\n  ".join(report.shadowed_tracked)
    )


def test_every_declared_class_is_recognised() -> None:
    """The live register uses only classes the classifier recognises."""
    mapping, errors = load_register(REPO_ROOT)
    assert errors == (), errors
    assert mapping, "live exclusion register declares no rules"
    assert set(mapping.values()) <= DECLARED_CLASSES


def test_report_counts_are_consistent() -> None:
    """contamination_entries is the sum of its parts — no double counting, no omission."""
    r = ContaminationReport(
        dirty_entries=("a",),
        untracked_entries=("b", "c"),
        excluded=(),
        shadowed_tracked=("d",),
    )
    assert r.contamination_entries == 4
    assert not r.clean
