"""Repository-agnostic + storage-agnostic configuration.

The engine never hardcodes an absolute path. It resolves the repository root by
walking upward from the current file until it finds the evidence markers
(``00-BOOK/DATA`` and ``engine``). A caller may override the root explicitly,
making the engine usable against any UCOS-shaped repository.

The code roots are likewise never hardcoded: they are DERIVED from Repository
Truth (see :func:`discover_code_roots`). A caller may still override them.

Storage-agnosticism: outputs are emitted through :class:`OutputSink`. The
default :class:`FileSink` writes JSON files, but any sink (SQL, object store,
in-memory) satisfying the interface may be substituted without touching the
engine.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

_MARKERS = ("00-BOOK/DATA", "engine")


def resolve_repo_root(start: Path | None = None) -> Path:
    """Find the repository root by locating the evidence markers upward."""
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if all((candidate / m).exists() for m in _MARKERS):
            return candidate
    # Fall back to three levels up (intelligence/rie/config.py -> repo root).
    return Path(__file__).resolve().parents[2]


def discover_code_roots(repo_root: Path) -> tuple[str, ...]:
    """Derive every top-level Python code root from Repository Truth.

    A code root is a top-level directory that is a Python package — i.e. a
    tracked ``<root>/__init__.py``. The version-controlled file set is the
    eligibility boundary (``git ls-files``), with a deterministic filesystem
    walk as the fallback for a non-git checkout (repository-agnosticism).

    This is deliberately *derived* rather than declared. A hardcoded root list
    is what let the capability catalogue drift: code roots added after the list
    was written were invisible to discovery, so their packages could never be
    catalogued and capability coverage silently fell behind the repository.
    """
    names: set[str] = set()
    try:
        res = subprocess.run(  # noqa: S603
            ["git", "ls-files", ":(glob)*/__init__.py"],  # noqa: S607 - fixed argv, no shell
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        res = None
    if res is not None and res.returncode == 0 and res.stdout.strip():
        names = {line.split("/", 1)[0] for line in res.stdout.split() if "/" in line}
    else:
        names = {
            child.name
            for child in repo_root.iterdir()
            if child.is_dir()
            and not child.name.startswith(".")
            and (child / "__init__.py").exists()
        }
    return tuple(sorted(names))


@dataclass(frozen=True)
class RepoConfig:
    """Resolved, evidence-source locations. All paths are repository-relative."""

    repo_root: Path
    data_dir: Path
    coverage_xml: Path
    output_dir: Path
    code_roots: tuple[str, ...] = ()
    tool_dir: str = "00-BOOK/tools"
    mcs_dir: str = "00-MASTER"
    orchestration_specs: tuple[str, ...] = (
        "02-MASTER/UCOS-COMP-000000-CONSTITUTIONAL-IMPLEMENTATION-ORCHESTRATION-AUTHORITY.md",
        "02-MASTER/UCOS-COMP-000001-CONSTITUTIONAL-COMPLETENESS-ENGINE-CONSTITUTION.md",
    )
    ec3_determinations: tuple[str, ...] = (
        "02-MASTER/EC-3-AP-2-BAND-10-ADMISSION-DETERMINATION.md",
        "02-MASTER/BANDS-10-13-REALIZATION-LANE-CHARTER.md",
    )

    @classmethod
    def create(
        cls,
        repo_root: Path | None = None,
        output_subdir: str = "intelligence",
        code_roots: tuple[str, ...] | None = None,
    ) -> RepoConfig:
        root = (repo_root or resolve_repo_root()).resolve()
        return cls(
            repo_root=root,
            data_dir=root / "00-BOOK" / "DATA",
            coverage_xml=root / "coverage.xml",
            output_dir=root / output_subdir,
            code_roots=tuple(code_roots) if code_roots else discover_code_roots(root),
        )

    def data_file(self, name: str) -> Path:
        return self.data_dir / name

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)


class OutputSink:
    """Storage-agnostic output interface. Implementations persist a named payload."""

    def emit(self, name: str, canonical_text: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class FileSink(OutputSink):
    """Default sink: write canonical JSON files under a directory."""

    directory: Path

    def emit(self, name: str, canonical_text: str) -> str:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / name
        target.write_text(canonical_text, encoding="utf-8")
        return str(target)


@dataclass
class MemorySink(OutputSink):
    """In-memory sink (used by determinism verification and tests)."""

    store: dict[str, str] = field(default_factory=dict)

    def emit(self, name: str, canonical_text: str) -> str:
        self.store[name] = canonical_text
        return name
