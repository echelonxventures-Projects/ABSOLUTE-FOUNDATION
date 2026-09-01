"""Verification purity: the verification plane observes and never mutates.

These are the tests that would have caught the defect on day one. `register.sh --guard`
ran the full registration transaction — Phase 1 is `ukb build --mint`, which allocates
permanent Universal IDs — and only *then* checked for drift. Invoked from
`./verify.sh --full`, it minted 140 permanent identities and emitted ~140 PORTAL pages,
taking `artifacts.json` from 1 233 to 1 373 entries, and then failed because the result
was uncommitted. A verification command performed a migration.

Guards, one per way the boundary can be crossed:

* :func:`test_verification_stage_commands_are_observationally_pure` — behavioural. Runs
  each stage command `verify.sh` invokes and asserts the git tree, the identity ledger
  and the lineage ledger are byte-unchanged.
* :func:`test_no_verification_path_invokes_the_minting_flag` — structural. The `--mint`
  token may appear in exactly one invocation in the repository, and it must be
  `register.sh`'s Phase 1.
* :func:`test_corpus_registration_is_a_governed_mutation_class` — declarative. The
  boundary register must name the class, its owner, and `verify.sh` as excluded.
* :func:`test_observation_build_allocates_nothing` — the mint separation itself.

The behavioural test deliberately does NOT run the pytest stage (it would recurse) or
the prerequisite-generation stage (it writes gitignored generated inputs by design, so
it is pure with respect to version control but not to the filesystem).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
VERIFY = REPO / "verify.sh"
LEDGER = REPO / "00-BOOK" / "DATA" / "id-ledger.json"
LINEAGE = REPO / "00-BOOK" / "DATA" / "change-ledger.json"
ARTIFACTS = REPO / "00-BOOK" / "DATA" / "artifacts.json"
BOUNDARY = REPO / "00-BOOK" / "DATA" / "mutation-governance-boundary.json"


def _git(*args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607 - resolved from PATH by design
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    ).stdout


def _digest(path: Path) -> str:
    """Content digest of a state artifact, or a sentinel when absent."""
    if not path.exists():
        return "<absent>"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot() -> dict[str, str]:
    """The three things a verification run must leave untouched."""
    return {
        "git_status": hashlib.sha256(_git("status", "--porcelain").encode()).hexdigest(),
        "identity_ledger": _digest(LEDGER),
        "lineage_ledger": _digest(LINEAGE),
        "artifact_registry": _digest(ARTIFACTS),
    }


# --- the stage commands verify.sh invokes, minus pytest and prerequisite generation ---
# Derived from verify.sh rather than restated, so a stage added there and not covered
# here is a gap this test can be extended to close deliberately.
OBSERVING_STAGES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ukb enforce --pre", (sys.executable, "00-BOOK/tools/ukb.py", "enforce", "--pre")),
    ("ukb validate", (sys.executable, "00-BOOK/tools/ukb.py", "validate")),
    ("uga gate", (sys.executable, "00-MASTER/UCOS-UGA-001/uga_engine.py", "gate")),
    ("uaue gate", (sys.executable, "-m", "engine.uaue.gate", "--gate", "--quiet")),
    ("uaue replay", (sys.executable, "-m", "engine.uaue.gate", "--replay", "--quiet")),
    ("birth gate", (sys.executable, "-m", "engine.object_birth.gate", "--gate", "--quiet")),
    ("impact engine", (sys.executable, "-m", "engine.verification_impact", "--quiet")),
    ("register.sh --observe", ("bash", "00-BOOK/tools/register.sh", "--observe")),
)


@pytest.mark.parametrize(("label", "argv"), OBSERVING_STAGES, ids=[s[0] for s in OBSERVING_STAGES])
def test_verification_stage_commands_are_observationally_pure(
    label: str, argv: tuple[str, ...]
) -> None:
    """Each verification stage must leave git, identity and lineage byte-identical."""
    before = _snapshot()
    subprocess.run(argv, cwd=REPO, capture_output=True, text=True, check=False)  # noqa: S603
    after = _snapshot()
    for key, was in before.items():
        assert after[key] == was, (
            f"{label} mutated {key}: verification must observe, never change. "
            f"If this stage needs to write, it belongs to the evolution plane "
            f"(REG-AUTO-001 / register.sh), not to verify.sh."
        )


def _invocation_lines(source: str) -> list[str]:
    """Lines that execute something, with comments and blanks removed.

    A guard must judge what a script RUNS, not what it documents. Scanning raw text made
    a stage label mentioning a superseded flag indistinguishable from an invocation of
    it — this guard's own first failure, and a real defect in the guard rather than in
    the script it was guarding.
    """
    out = []
    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def test_no_verification_path_invokes_the_minting_flag() -> None:
    """`build --mint` may be invoked from exactly one file: the REG-AUTO-001 transaction."""
    hits: set[str] = set()
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in {".sh", ".yml", ".yaml"}:
            continue
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith((".ec1-venv/", ".git/")):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if any(re.search(r"\bbuild\s+--mint\b", ln) for ln in _invocation_lines(source)):
            hits.add(rel)
    assert hits == {"00-BOOK/tools/register.sh"}, (
        "`build --mint` must be invoked only by the REG-AUTO-001 transaction; "
        f"found in {sorted(hits)}"
    )


def test_verify_sh_does_not_invoke_the_registration_transaction() -> None:
    """verify.sh must reach register.sh only through its read-only entry."""
    source = "\n".join(_invocation_lines(VERIFY.read_text(encoding="utf-8")))
    invocations = re.findall(r"register\.sh\s+(--[a-z]+)", source)
    assert invocations, "verify.sh no longer invokes register.sh — update this guard"
    for flag in invocations:
        assert flag == "--observe", (
            f"verify.sh invokes register.sh {flag}; only --observe is read-only. "
            "--guard and a bare invocation run the mutating transaction."
        )


def test_corpus_registration_is_a_governed_mutation_class() -> None:
    """The class must exist, name its owner, and exclude the verification plane."""
    doc = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    classes = {m["class"]: m for m in doc["mutation_classes"]}
    assert "CORPUS_REGISTRATION" in classes, (
        "corpus registration must be a declared mutation class — while it was undeclared, "
        "this register's 'no mutation class is ungoverned' invariant was vacuously true "
        "for the one mutation that allocates identity"
    )
    entry = classes["CORPUS_REGISTRATION"]
    assert "REG-AUTO-001" in entry["governed_by"]
    assert "register.sh" in entry["governed_by"]
    excluded = " ".join(entry.get("does_not_govern", []))
    assert "verify.sh" in excluded, "verify.sh must be explicitly excluded from the class"


def test_every_mutation_class_names_exactly_one_owner() -> None:
    """The register's own invariant, re-measured after adding a class."""
    doc = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    for entry in doc["mutation_classes"]:
        owner = entry.get("governed_by", "")
        assert owner, f"{entry['class']} has no governing authority"
    names = [m["class"] for m in doc["mutation_classes"]]
    assert len(names) == len(set(names)), "a mutation class is declared twice"


def test_observation_build_allocates_nothing() -> None:
    """`ukb build` without --mint must not touch the identity ledger."""
    before = _digest(LEDGER)
    result = subprocess.run(  # noqa: S603
        [sys.executable, "00-BOOK/tools/ukb.py", "build"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert _digest(LEDGER) == before, (
        "an observation build wrote the identity ledger; identity is GOVERNED EVOLUTION "
        "STATE and may be allocated only under --mint by the REG-AUTO-001 transaction"
    )
    # Regeneration of derived views is expected and is reverted by the fixture below.


#: The roots this module's tests may cause incidental derived-view regeneration under.
_GUARDED_ROOTS: tuple[str, ...] = ("00-BOOK/DATA/", "00-BOOK/REGISTRIES/", "00-BOOK/CONTROL-TOWER/")


def _dirty_paths(roots: tuple[str, ...]) -> dict[str, str]:
    """``{path: XY status}`` for every dirty entry under ``roots`` (NUL-delimited, rename-aware).

    Porcelain ``-z`` emits ``XY PATH\\0`` for ordinary entries and ``XY ORIG\\0NEW\\0`` for a
    rename/copy (status starting with ``R``/``C``) — the extra field must be consumed or every
    following path shifts by one.
    """
    raw = subprocess.run(  # noqa: S603
        ["git", "status", "--porcelain=v1", "-z", "--", *roots],  # noqa: S607
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    tokens = raw.split("\0")
    out: dict[str, str] = {}
    i = 0
    while i < len(tokens):
        entry = tokens[i]
        i += 1
        if not entry:
            continue
        status, path = entry[:2], entry[3:]
        out[path] = status
        if status[0] in ("R", "C"):  # rename/copy: the new path follows as its own token
            if i < len(tokens) and tokens[i]:
                out[tokens[i]] = status
                i += 1
    return out


def _read_or_none(rel: str) -> bytes | None:
    path = REPO / rel
    return path.read_bytes() if path.is_file() else None


@pytest.fixture(autouse=True)
def _restore_derived_views():
    """Revert only the derived-view regeneration THIS test caused.

    A regeneration may legitimately produce different bytes than the committed views;
    see GOVERNED-EVOLUTION-STATE-DETERMINATION.md §4.1. That drift must not leak out of
    this module as working-tree noise — but a path already dirty *before* this test ran
    (real, governed, uncommitted work — e.g. an identity mint under REG-AUTO-001) must
    survive exactly as it stood, never collapsed into `HEAD` by a directory-wide command
    (ADR-0020, replacing the unconditional `git checkout --` this fixture used to run).
    """
    before = _dirty_paths(_GUARDED_ROOTS)
    before_content = {path: _read_or_none(path) for path in before}
    yield
    after = _dirty_paths(_GUARDED_ROOTS)

    newly_dirty = sorted(set(after) - set(before))
    if newly_dirty:
        tracked = [p for p in newly_dirty if after[p] != "??"]
        untracked = [p for p in newly_dirty if after[p] == "??"]
        if tracked:
            subprocess.run(  # noqa: S603
                ["git", "checkout", "--", *tracked],  # noqa: S607
                cwd=REPO,
                capture_output=True,
                check=False,
            )
        for rel in untracked:
            path = REPO / rel
            if path.is_file():
                path.unlink()

    for rel in sorted(set(after) & set(before)):
        if _read_or_none(rel) != before_content[rel]:
            snapshot = before_content[rel]
            path = REPO / rel
            if snapshot is None:
                if path.is_file():
                    path.unlink()
            else:
                path.write_bytes(snapshot)


def test_ukb_build_declares_the_mint_flag() -> None:
    """The separation must be discoverable, not implicit."""
    helptext = subprocess.run(  # noqa: S603
        [sys.executable, "00-BOOK/tools/ukb.py", "build", "--help"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    assert "--mint" in helptext
    assert "EVOLUTION" in helptext, "the flag must say which plane it belongs to"


# --------------------------------------------------------------------------- guard
# The regression guard proper: a verification execution that changes any of the four
# named state surfaces must FAIL. This is expressed against ./verify.sh itself rather
# than against its stages, because the contract is a property of the entry point.


#: The four surfaces a verification run may never change.
GUARDED_STATE: tuple[tuple[str, Path], ...] = (
    ("id-ledger", LEDGER),
    ("artifact registry", ARTIFACTS),
    ("lineage", LINEAGE),
    ("generated artifacts", REPO / "00-BOOK" / "DATA" / "relationships.json"),
)


def _guarded_digests() -> dict[str, str]:
    return {label: _digest(path) for label, path in GUARDED_STATE}


def test_verify_sh_declares_no_mutating_invocation() -> None:
    """Structural guard over every command ./verify.sh can reach.

    Cheap enough to run in the standard suite, and it catches the reintroduction of a
    mutating call without paying for a full verification run.
    """
    source = "\n".join(_invocation_lines(VERIFY.read_text(encoding="utf-8")))
    forbidden = {
        "register.sh --guard": "runs the REG-AUTO-001 transaction (Phase 1 mints)",
        "register.sh --strict": "runs the transaction",
        "build --mint": "allocates permanent Universal IDs",
        "uga_engine.py run": "mints UGA object identity (use `gate`)",
        "ukbx.py sync": "writes twin state",
        "ukbx.py portal": "regenerates the portal",
        "--render": "writes a generated surface (use --replay)",
    }
    found = [f"{token} — {why}" for token, why in forbidden.items() if token in source]
    assert not found, (
        "verify.sh reaches a mutating operation:\n  "
        + "\n  ".join(found)
        + "\nVerification observes. Evolution changes. Move it to the evolution plane."
    )


def test_verification_leaves_guarded_state_identical() -> None:
    """End-to-end guard: run the observing stages in sequence, then compare.

    Runs the same stage commands ./verify.sh runs, minus pytest (which would recurse)
    and prerequisite generation (which writes only gitignored inputs). If any of the
    four guarded surfaces moves, the verification plane has mutated canonical state.
    """
    before = _guarded_digests()
    before_git = hashlib.sha256(_git("status", "--porcelain").encode()).hexdigest()

    for _label, argv in OBSERVING_STAGES:
        subprocess.run(argv, cwd=REPO, capture_output=True, text=True, check=False)  # noqa: S603

    after = _guarded_digests()
    changed = [k for k in before if after[k] != before[k]]
    assert not changed, (
        f"verification changed {', '.join(changed)}. A verification run must be "
        f"observationally pure — see GOVERNED-EVOLUTION-STATE-DETERMINATION.md §4."
    )
    assert (
        hashlib.sha256(_git("status", "--porcelain").encode()).hexdigest() == before_git
    ), "verification changed the working tree"


def test_observation_is_idempotent_across_consecutive_runs() -> None:
    """Two consecutive observations must produce identical state and identical verdicts."""
    runs = []
    for _ in range(2):
        result = subprocess.run(  # noqa: S603
            ["bash", "00-BOOK/tools/register.sh", "--observe"],  # noqa: S607
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        runs.append((result.returncode, _guarded_digests()))
    assert runs[0][0] == runs[1][0], "observation verdict is not deterministic"
    assert runs[0][1] == runs[1][1], "observation mutated state between runs"


def test_register_sh_remains_the_transaction_owner() -> None:
    """The correction is ownership separation, not replacement."""
    source = (REPO / "00-BOOK" / "tools" / "register.sh").read_text(encoding="utf-8")
    assert "REG-AUTO-001" in source
    assert "build --mint" in source, "register.sh must remain the one minting caller"
    for phase in ("Phase 1/10", "Phase 9/10", "Phase 10/10"):
        assert phase in source, f"the transaction lost {phase} — phases must be preserved"


# ---------------------------------------------------------------------------------------
# UCOS-UCAF-001 — a gate flag that wrote.
#
# `ucaf_engine.py --gate` regenerated every register and `ucaf.json` unconditionally and
# only then evaluated the verdict, so the verdict was computed against a tree the verdict
# run had just rewritten, and a read-only-sounding flag left 00-MASTER/UCOS-UCAF-001/
# dirty. The fix routes the write behind `gate_only`. These two guards hold it there: one
# runs the gate and measures the tree, one proves the write is unreachable without running
# anything. The structural guard is the one that survives a machine where the gate cannot
# be executed.

UCAF_ENGINE = REPO / "00-MASTER" / "UCOS-UCAF-001" / "ucaf_engine.py"
UCAF_HOME = "00-MASTER/UCOS-UCAF-001"


def _ucaf_tree_digest() -> dict[str, str]:
    """Content digest of every file in the UCAF home, tracked or not."""
    root = REPO / UCAF_HOME
    return {
        path.relative_to(REPO).as_posix(): _digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def test_ucaf_gate_writes_nothing() -> None:
    """Behavioural. `--gate` is a verdict, so the bytes it measures must outlive it.

    Asserts on CONTENT, not just `git status`: a write that happens to reproduce the
    committed bytes is still a write, and it is the one that would slip past a
    porcelain-only check on a clean tree.
    """
    before, before_dirty = _ucaf_tree_digest(), _dirty_paths((UCAF_HOME,))
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(UCAF_ENGINE), "--gate"],  # noqa: S607
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    # The verdict itself may be OPEN or CLOSED — that is the corpus's business, not this
    # test's. Only an ABORT (2) means the gate never ran and the assertions are vacuous.
    assert completed.returncode in (
        0,
        1,
    ), f"ucaf gate aborted (rc={completed.returncode}); purity unproven\n{completed.stderr}"
    assert _ucaf_tree_digest() == before, "ucaf_engine.py --gate rewrote its own home"
    assert _dirty_paths((UCAF_HOME,)) == before_dirty, "ucaf_engine.py --gate dirtied the tree"
    assert (
        "nothing written" in completed.stdout
    ), "the gate no longer reports itself read-only — the guard and the engine disagree"


def _gate_reachable_calls() -> tuple[set[str], list[str]]:
    """Callees reachable from ``main()`` when ``gate_only`` is True.

    A recursive descent, NOT ``ast.walk``: walk yields the children of a pruned branch
    anyway, which silently reports the write as reachable and makes the guard useless.
    """
    import ast

    tree = ast.parse(UCAF_ENGINE.read_text(encoding="utf-8"))
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}

    def collect(node: object, out: list[str]) -> None:
        if isinstance(node, ast.IfExp) and ast.unparse(node.test) == "gate_only":
            collect(node.test, out)
            collect(node.body, out)  # taken under gate_only; `orelse` is unreachable
            return
        if isinstance(node, ast.Call):
            func = node.func
            out.append(func.id if isinstance(func, ast.Name) else ast.unparse(func))
        for child in ast.iter_child_nodes(node):  # type: ignore[arg-type]
            collect(child, out)

    seen: set[str] = set()
    calls: list[str] = []
    stack = ["main"]
    while stack:
        name = stack.pop()
        if name in seen or name not in funcs:
            continue
        seen.add(name)
        found: list[str] = []
        collect(funcs[name], found)
        calls.extend(found)
        stack.extend(f for f in found if f in funcs)
    return seen, calls


def test_ucaf_gate_path_cannot_reach_a_write_primitive() -> None:
    """Structural. No execution needed: the write must not be in the gate's call graph."""
    reachable, calls = _gate_reachable_calls()
    assert (
        "measure" in reachable
    ), "the gate path no longer reaches measure() — the walk broke, not the engine"
    assert (
        "write_registers" not in reachable
    ), "write_registers() is reachable from the --gate path; a gate verifies, it does not produce"
    forbidden = sorted(
        {
            call
            for call in calls
            if call.split(".")[-1]
            in {"write_text", "write_bytes", "writelines", "touch", "mkdir", "dump"}
            or call in {"open", "write_registers", "emit"}
        }
    )
    assert not forbidden, f"the --gate path reaches write primitive(s): {forbidden}"
