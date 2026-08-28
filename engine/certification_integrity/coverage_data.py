"""UCI-000001 Part 2 — reading a coverage measurement without trusting its summary.

WHY THIS READS LINES AND NOT PERCENTAGES.

``coverage.xml`` carries a ``line-rate`` attribute on every element, and using it would make
this package's figures a restatement of coverage.py's arithmetic rather than an independent
computation over the same evidence. The distinction is what makes Rules 10 and 11 provable:
"combined shards == single full execution" is NOT provable from two percentages, because two
different covered-line SETS routinely produce the same ratio. Only the sets can be compared, so
only the sets are read.

The parser therefore takes exactly one thing from the XML — per file, which line numbers were
hit and which were not — and derives every total itself.
"""

from __future__ import annotations

import hashlib
import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from engine.certification_integrity.model import IntegrityError


@dataclass(frozen=True)
class FileCoverage:
    """The measured line status of one file. ``hit``/``missed`` are disjoint by construction."""

    path: str
    hit: frozenset[int]
    missed: frozenset[int]

    @property
    def statements(self) -> int:
        return len(self.hit) + len(self.missed)

    @property
    def percent(self) -> float:
        total = self.statements
        return 100.0 if total == 0 else round(len(self.hit) * 100.0 / total, 4)


@dataclass(frozen=True)
class CoverageReport:
    """A whole coverage measurement, keyed by repository-relative path."""

    files: dict[str, FileCoverage]
    #: Branch totals are carried through for provenance and compared by Rule 11. They are not
    #: used in the line-equality proof: a line-set comparison already detects every difference a
    #: branch comparison would, and reporting both keeps the stronger claim checkable.
    branches_valid: int
    branches_covered: int

    @property
    def statements(self) -> int:
        return sum(f.statements for f in self.files.values())

    @property
    def covered(self) -> int:
        return sum(len(f.hit) for f in self.files.values())

    @property
    def missing(self) -> int:
        return sum(len(f.missed) for f in self.files.values())

    @property
    def percent(self) -> float:
        return 100.0 if self.statements == 0 else round(self.covered * 100.0 / self.statements, 4)

    @property
    def branch_percent(self) -> float | None:
        if not self.branches_valid:
            return None
        return round(self.branches_covered * 100.0 / self.branches_valid, 4)

    def line_signature(self) -> dict[str, tuple[int, ...]]:
        """The exact covered-line set per file, which is what Rules 8, 10 and 11 compare.

        Sorted tuples rather than sets so the structure is directly comparable and directly
        serialisable; a set's iteration order would make an equal signature print differently on
        two runs and invite a false drift finding.
        """
        return {path: tuple(sorted(f.hit)) for path, f in sorted(self.files.items())}

    def digest(self) -> str:
        """A content hash of the whole measurement, for the provenance record.

        Includes the MISSED lines as well as the hit ones, so that a run which stopped measuring
        a file entirely produces a different digest from one that measured it and found it
        uncovered. Those are the two failures Rule 11 separates, and a hit-only digest would
        make them identical.
        """
        payload = {
            path: {"hit": sorted(f.hit), "missed": sorted(f.missed)}
            for path, f in sorted(self.files.items())
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def parse(xml_path: str, *, repository: str | None = None) -> CoverageReport:
    """Read ``coverage.xml`` into per-file line sets.

    Paths are normalised to repository-relative POSIX form. coverage.py writes ``filename``
    relative to a ``<sources>`` root and that root is an absolute machine path, so leaving it
    unresolved would make two runs in two directories produce incomparable reports — and the
    immutable-extraction run of Rule 7 runs in a temporary directory by construction, so every
    comparison it feeds would report drift that is really only a working directory.
    """
    if not os.path.exists(xml_path):
        raise IntegrityError(
            f"no coverage measurement at {xml_path} — refusing to report a coverage figure over "
            "a measurement that was never taken"
        )
    try:
        # noqa justification: the input is this repository's own coverage.xml, written by
        # coverage.py in the same run. defusedxml is not a declared dependency and adding one to
        # parse a file we produced ourselves would widen the dependency surface, not narrow risk.
        root = ET.parse(xml_path).getroot()  # noqa: S314
    except ET.ParseError as exc:
        raise IntegrityError(f"{xml_path} is not parseable coverage XML: {exc}") from exc

    repo = os.path.realpath(repository or os.getcwd())
    sources = [s.text for s in root.findall("./sources/source") if s.text]

    files: dict[str, FileCoverage] = {}
    for element in root.findall(".//class"):
        filename = element.get("filename")
        if not filename:
            continue
        relative = _relative(filename, sources, repo)
        hit: set[int] = set()
        missed: set[int] = set()
        for line in element.findall("./lines/line"):
            number = line.get("number")
            if number is None:
                continue
            (hit if line.get("hits") not in (None, "0") else missed).add(int(number))
        # A path can appear more than once when it is measured under two source roots. Merging
        # by union rather than overwriting keeps a re-measured file from LOSING hits, which
        # would understate coverage and manufacture a drift finding.
        if relative in files:
            previous = files[relative]
            hit |= previous.hit
            missed |= previous.missed
        files[relative] = FileCoverage(relative, frozenset(hit), frozenset(missed - hit))

    if not files:
        raise IntegrityError(
            f"{xml_path} names no measured file — a coverage report over nothing would report "
            "100% forever, so it is refused rather than summarised"
        )

    return CoverageReport(
        files=files,
        branches_valid=int(root.get("branches-valid") or 0),
        branches_covered=int(root.get("branches-covered") or 0),
    )


def _relative(filename: str, sources: list[str], repo: str) -> str:
    """Resolve a coverage ``filename`` to a repository-relative POSIX path."""
    if os.path.isabs(filename):
        candidates = [filename]
    else:
        candidates = [os.path.join(source, filename) for source in sources] or [filename]
        candidates.append(os.path.join(repo, filename))
    for candidate in candidates:
        resolved = os.path.realpath(candidate)
        if resolved.startswith(repo + os.sep) and os.path.exists(resolved):
            return os.path.relpath(resolved, repo).replace(os.sep, "/")
    # Unresolvable: keep the declared name rather than inventing one. A wrong-but-stable key is
    # comparable across runs; a synthesised key is not.
    return filename.replace(os.sep, "/")


def compare(left: CoverageReport, right: CoverageReport) -> dict[str, object]:
    """Diff two measurements at line-set granularity.

    Returns a structure that is empty exactly when the two measurements are identical. This is
    the primitive behind Rule 8 (A == B == C), Rule 10 (shards versus whole) and Rule 11 (two
    independent runs), and it is deliberately the SAME primitive: those rules ask one question
    about three pairs of inputs, and implementing it three times would let the answers diverge.
    """
    left_sig, right_sig = left.line_signature(), right.line_signature()
    only_left = sorted(set(left_sig) - set(right_sig))
    only_right = sorted(set(right_sig) - set(left_sig))
    differing: dict[str, dict[str, list[int]]] = {}
    for path in sorted(set(left_sig) & set(right_sig)):
        a, b = set(left_sig[path]), set(right_sig[path])
        if a != b:
            differing[path] = {
                "covered_only_in_first": sorted(a - b),
                "covered_only_in_second": sorted(b - a),
            }
    return {
        "identical": not (only_left or only_right or differing),
        "files_only_in_first": only_left,
        "files_only_in_second": only_right,
        "files_with_differing_lines": differing,
        "statement_delta": right.statements - left.statements,
        "branch_delta": right.branches_valid - left.branches_valid,
        "first": {
            "statements": left.statements,
            "covered": left.covered,
            "percent": left.percent,
            "branches_valid": left.branches_valid,
            "digest": left.digest(),
        },
        "second": {
            "statements": right.statements,
            "covered": right.covered,
            "percent": right.percent,
            "branches_valid": right.branches_valid,
            "digest": right.digest(),
        },
    }
