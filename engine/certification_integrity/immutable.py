"""UCI-000001 Part 5 — certification from an immutable extraction (mandate Rule 7).

WHY A MUTABLE TREE CANNOT BE CERTIFIED, stated as the incident that produced this module.

While this package was being written, a second process in the same working tree ran
``./verify.sh --full``. It rewrote ``coverage.xml``, and a read of that file mid-write raised
``not well-formed (invalid token): line 90558``. HEAD also advanced twice during the same
interval. Neither event was visible to any gate: every gate in the repository reads the working
tree as it finds it, so a run that measures a tree while something else edits it reports a figure
that is attributable to no commit at all. That is a false green of the purest kind — not a wrong
number, but a number that is not ABOUT anything.

``git archive <sha>`` is the remedy the mandate names, and it has a property a ``git clone`` does
not: it emits exactly the tracked content of one commit, with no ``.git``, no untracked files, no
ignored files and no ability to be advanced. A run inside the extraction cannot see the working
tree, so it cannot be contaminated by one.

WHAT IS CHECKED BESIDES THE EXTRACTION.

Extraction alone proves the INPUT was frozen. It does not prove nothing changed while the
measurement ran, because a run can take twenty minutes and read the outer repository through an
absolute path by mistake. So ``run`` samples the outer repository's fingerprint — HEAD, the
porcelain status, and the digest of the tracked file list — before and after, and refuses on any
difference. The two checks answer different questions and neither implies the other.

THE INTERPRETER IS PART OF THE MEASUREMENT. A frozen tree measured by an interpreter whose
site-packages point at the UNfrozen tree is not a frozen measurement: an editable install
resolves ``import engine`` through a meta-path finder that wins over ``sys.path``, so the
extraction would execute the working tree's code while appearing to execute its own. This module
therefore builds a virtualenv INSIDE the extraction and installs the extraction into it. That
cost — roughly one to three minutes with a warm pip cache — buys the only thing that makes the
run citable.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field

from engine.certification_integrity.model import IntegrityError

#: Written into a completed extraction so a second call can reuse it instead of rebuilding the
#: virtualenv. Keyed on the SHA and the dependency declaration, so a changed dependency set
#: invalidates it rather than being silently reused.
READY_MARKER = ".uci-extraction-ready.json"

#: Replaced in a command by the extraction's own interpreter. Named rather than inlined so the
#: substitution is greppable from the call sites that depend on it.
PYTHON_PLACEHOLDER = "{python}"


@dataclass(frozen=True)
class Fingerprint:
    """An outer-repository state sample. Equality is the whole point of the type."""

    head: str
    porcelain_digest: str
    tracked_digest: str
    dirty_entries: int

    def as_record(self) -> dict[str, object]:
        return {
            "head": self.head,
            "porcelain_digest": self.porcelain_digest,
            "tracked_digest": self.tracked_digest,
            "dirty_entries": self.dirty_entries,
        }


@dataclass
class Extraction:
    """A frozen tree and the interpreter that measures it."""

    sha: str
    root: str
    python: str
    reused: bool
    prepare_seconds: float

    def as_record(self) -> dict[str, object]:
        return {
            "sha": self.sha,
            "root": self.root,
            "python": self.python,
            "reused": self.reused,
            "prepare_seconds": round(self.prepare_seconds, 3),
        }


@dataclass
class FrozenRun:
    """One command executed inside one extraction, with the purity evidence around it."""

    sha: str
    command: tuple[str, ...]
    exit_code: int
    duration_seconds: float
    stdout_tail: str
    stderr_tail: str
    before: Fingerprint
    after: Fingerprint
    extraction: Extraction
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def tree_stable(self) -> bool:
        return self.before == self.after

    def as_record(self) -> dict[str, object]:
        return {
            "sha": self.sha,
            "command": list(self.command),
            "exit_code": self.exit_code,
            "duration_seconds": round(self.duration_seconds, 3),
            "tree_stable": self.tree_stable,
            "before": self.before.as_record(),
            "after": self.after.as_record(),
            "extraction": self.extraction.as_record(),
            "artifacts": dict(self.artifacts),
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
        }


def _git(root: str, *args: str) -> str:
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no interpolated input
            ["git", *args],  # noqa: S607 - git from PATH by design
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise IntegrityError(f"git {' '.join(args)} failed in {root}: {exc}") from exc
    return completed.stdout


def resolve_sha(root: str, revision: str = "HEAD") -> str:
    return _git(root, "rev-parse", revision).strip()


def fingerprint(root: str) -> Fingerprint:
    """Sample the outer repository. Cheap enough to take before and after every run."""
    head = resolve_sha(root)
    porcelain = _git(root, "status", "--porcelain")
    tracked = _git(root, "ls-files", "-s")
    return Fingerprint(
        head=head,
        porcelain_digest=hashlib.sha256(porcelain.encode()).hexdigest(),
        tracked_digest=hashlib.sha256(tracked.encode()).hexdigest(),
        dirty_entries=len([line for line in porcelain.splitlines() if line.strip()]),
    )


def _dependency_digest(root: str, sha: str) -> str:
    """Hash the dependency declaration of the COMMIT, not of the working tree."""
    pyproject = _git(root, "show", f"{sha}:pyproject.toml")
    return hashlib.sha256(pyproject.encode()).hexdigest()


def extract(root: str, sha: str, destination: str) -> None:
    """``git archive <sha> | tar -x`` into ``destination``.

    Uses a pipe rather than a temporary archive file so a partially written archive can never be
    extracted as if it were whole — the same failure mode that produced the malformed
    ``coverage.xml`` this module exists to prevent.
    """
    os.makedirs(destination, exist_ok=True)
    archive = subprocess.Popen(  # noqa: S603
        ["git", "archive", "--format=tar", sha],  # noqa: S607
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    untar = subprocess.Popen(  # noqa: S603
        ["tar", "-x", "-f", "-", "-C", destination],  # noqa: S607
        stdin=archive.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if archive.stdout is not None:
        archive.stdout.close()
    _, untar_err = untar.communicate()
    _, archive_err = archive.communicate()
    if archive.returncode != 0:
        raise IntegrityError(
            f"git archive {sha} failed: {archive_err.decode(errors='replace').strip()}"
        )
    if untar.returncode != 0:
        raise IntegrityError(
            f"extracting {sha} failed: {untar_err.decode(errors='replace').strip()}"
        )


def prepare(
    root: str,
    sha: str,
    *,
    workspace: str | None = None,
    build_venv: bool = True,
    reuse: bool = True,
) -> Extraction:
    """Extract ``sha`` and give it an interpreter that resolves imports to the extraction."""
    started = time.monotonic()
    base = workspace or os.path.join(tempfile.gettempdir(), "uci-extractions")
    destination = os.path.join(base, sha)
    dependency = _dependency_digest(root, sha)
    marker = os.path.join(destination, READY_MARKER)

    if reuse and os.path.exists(marker):
        try:
            with open(marker, encoding="utf-8") as handle:
                recorded = json.load(handle)
        except (OSError, json.JSONDecodeError):
            recorded = {}
        if recorded.get("sha") == sha and recorded.get("dependency_digest") == dependency:
            python = recorded.get("python", "")
            if not build_venv or (python and os.path.exists(python)):
                return Extraction(
                    sha=sha,
                    root=destination,
                    python=python or sys.executable,
                    reused=True,
                    prepare_seconds=time.monotonic() - started,
                )

    if os.path.exists(destination):
        shutil.rmtree(destination)
    extract(root, sha, destination)

    python = sys.executable
    if build_venv:
        python = _build_venv(destination)

    with open(marker, "w", encoding="utf-8") as handle:
        json.dump(
            {"sha": sha, "dependency_digest": dependency, "python": python},
            handle,
            indent=1,
            sort_keys=True,
        )
    return Extraction(
        sha=sha,
        root=destination,
        python=python,
        reused=False,
        prepare_seconds=time.monotonic() - started,
    )


def _build_venv(destination: str) -> str:
    """Create a virtualenv inside the extraction and install the extraction into it."""
    venv_dir = os.path.join(destination, ".uci-venv")
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "venv", venv_dir],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise IntegrityError(f"could not create a virtualenv in the extraction: {result.stderr}")
    python = os.path.join(venv_dir, "bin", "python")
    if not os.path.exists(python):  # pragma: no cover - non-POSIX layout
        python = os.path.join(venv_dir, "Scripts", "python.exe")
    install = subprocess.run(  # noqa: S603
        [python, "-m", "pip", "install", "-e", ".[dev]", "-q"],
        cwd=destination,
        capture_output=True,
        text=True,
        check=False,
    )
    if install.returncode != 0:
        raise IntegrityError(
            "the extraction's dependencies could not be installed, so no measurement taken "
            f"inside it would be attributable to {destination}: {install.stderr[-2000:]}"
        )
    return python


def run(
    root: str,
    command: list[str],
    *,
    sha: str | None = None,
    workspace: str | None = None,
    env: dict[str, str] | None = None,
    collect: dict[str, str] | None = None,
    build_venv: bool = True,
    reuse: bool = True,
    timeout: float | None = None,
) -> FrozenRun:
    """Run ``command`` inside a frozen extraction of ``sha``.

    ``command`` may use the token ``PYTHON_PLACEHOLDER``, which is replaced by the extraction's own
    interpreter. ``collect`` names artifacts to copy out of the extraction afterwards, keyed by
    the relative path inside it; a run whose output stayed inside a temporary directory would be
    unciteable for the opposite reason to a mutable one.
    """
    resolved = sha or resolve_sha(root)
    before = fingerprint(root)
    extraction = prepare(root, resolved, workspace=workspace, build_venv=build_venv, reuse=reuse)

    argv = [extraction.python if part == PYTHON_PLACEHOLDER else part for part in command]
    environment = dict(os.environ)
    # The extraction must not inherit a COVERAGE_FILE pointing at the outer tree. The repository
    # has already paid for an inherited value once: engine/verification_intelligence/execution.py
    # records that an ambient COVERAGE_FILE corrupted a parent's data file.
    environment.pop("COVERAGE_FILE", None)
    environment["PYTHONHASHSEED"] = environment.get("PYTHONHASHSEED", "0")
    if env:
        environment.update(env)

    started = time.monotonic()
    completed = subprocess.run(  # noqa: S603
        argv,
        cwd=extraction.root,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        timeout=timeout,
    )
    duration = time.monotonic() - started
    after = fingerprint(root)

    artifacts: dict[str, str] = {}
    for relative, target in (collect or {}).items():
        source = os.path.join(extraction.root, relative)
        if os.path.exists(source):
            os.makedirs(os.path.dirname(os.path.abspath(target)) or ".", exist_ok=True)
            shutil.copy2(source, target)
            artifacts[relative] = target

    return FrozenRun(
        sha=resolved,
        command=tuple(argv),
        exit_code=completed.returncode,
        duration_seconds=duration,
        stdout_tail=completed.stdout[-4000:],
        stderr_tail=completed.stderr[-4000:],
        before=before,
        after=after,
        extraction=extraction,
        artifacts=artifacts,
    )


def require_stable(runs: list[FrozenRun]) -> None:
    """Refuse if the outer repository moved during any run. Rule 7's failure condition."""
    for frozen in runs:
        if not frozen.tree_stable:
            raise IntegrityError(
                f"the repository changed while a certification run was in flight: HEAD "
                f"{frozen.before.head[:12]} -> {frozen.after.head[:12]}, dirty entries "
                f"{frozen.before.dirty_entries} -> {frozen.after.dirty_entries}. The measurement "
                "is not attributable to a commit and is discarded rather than reported."
            )
