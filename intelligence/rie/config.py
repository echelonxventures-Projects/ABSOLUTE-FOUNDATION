"""Repository-agnostic + storage-agnostic configuration.

The engine never hardcodes an absolute path. It resolves the repository root by
walking upward from the current file until it finds the evidence markers
(``00-BOOK/DATA`` and ``engine``). A caller may override the root explicitly,
making the engine usable against any UCOS-shaped repository.

Storage-agnosticism: outputs are emitted through :class:`OutputSink`. The
default :class:`FileSink` writes JSON files, but any sink (SQL, object store,
in-memory) satisfying the interface may be substituted without touching the
engine.
"""

from __future__ import annotations

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


@dataclass(frozen=True)
class RepoConfig:
    """Resolved, evidence-source locations. All paths are repository-relative."""

    repo_root: Path
    data_dir: Path
    coverage_xml: Path
    output_dir: Path
    code_roots: tuple[str, ...] = ("engine", "platform")
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
    def create(cls, repo_root: Path | None = None, output_subdir: str = "intelligence") -> RepoConfig:
        root = (repo_root or resolve_repo_root()).resolve()
        return cls(
            repo_root=root,
            data_dir=root / "00-BOOK" / "DATA",
            coverage_xml=root / "coverage.xml",
            output_dir=root / output_subdir,
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
