"""Evidence readers — the only inputs the engine trusts.

Every fact the engine reports is read here from repository evidence that other
certified/authoritative producers already emit:

  * ``00-BOOK/DATA/*.json``   — ukb.py / ukbx.py generated corpus intelligence
  * ``coverage.xml``          — the pytest+coverage gate output
  * ``git``                   — the version-control eligibility boundary + HEAD

The reader NEVER writes any of these; it composes them (compose-never-duplicate).
Absent evidence is reported as ``available=False`` and degrades gracefully to a
fail-closed ``INDETERMINATE`` rather than an invented value.
"""

from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

from . import __version__
from .canonical import canonical_json, sha256_file, sha256_text
from .config import RepoConfig

_DATA_FILES = (
    "control-tower.json",
    "artifacts.json",
    "certification.json",
    "twin.json",
    "volumes.json",
)


@dataclass(frozen=True)
class Coverage:
    available: bool
    line_pct: float
    branch_pct: float
    lines_covered: int
    lines_valid: int


class EvidenceReader:
    """Reads (never writes) the repository evidence surfaces."""

    def __init__(self, config: RepoConfig) -> None:
        self.config = config
        self._cache: dict[str, Any] = {}

    # -- corpus DATA -----------------------------------------------------
    def data(self, name: str) -> dict[str, Any]:
        if name not in self._cache:
            path = self.config.data_file(name)
            self._cache[name] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        return self._cache[name]

    def control_tower(self) -> dict[str, Any]:
        return self.data("control-tower.json")

    def artifacts(self) -> dict[str, Any]:
        return self.data("artifacts.json")

    def certification(self) -> dict[str, Any]:
        return self.data("certification.json")

    def twin(self) -> dict[str, Any]:
        return self.data("twin.json")

    # -- coverage --------------------------------------------------------
    def coverage(self) -> Coverage:
        path = self.config.coverage_xml
        if not path.exists():
            return Coverage(False, 0.0, 0.0, 0, 0)
        root = ET.parse(path).getroot()  # noqa: S314 - trusted local build artifact
        lr = float(root.get("line-rate", "0") or 0)
        br = float(root.get("branch-rate", "0") or 0)
        lc = int(root.get("lines-covered", "0") or 0)
        lv = int(root.get("lines-valid", "0") or 0)
        return Coverage(True, round(lr * 100, 2), round(br * 100, 2), lc, lv)

    # -- git -------------------------------------------------------------
    def head(self) -> str:
        return self._git("rev-parse", "--short", "HEAD") or "UNKNOWN"

    def head_commit(self) -> str:
        """The full source commit the outputs are derived at."""
        return self._git("rev-parse", "HEAD") or "UNKNOWN"

    def head_committed_at(self) -> str:
        """HEAD's committer date, strict ISO-8601.

        Generation time is taken from the source commit, never from the wall
        clock: the mandated generation timestamp must not make a regeneration of
        an unchanged repository produce different bytes.
        """
        return self._git("show", "-s", "--format=%cI", "HEAD") or "UNKNOWN"

    def branch(self) -> str:
        return self._git("rev-parse", "--abbrev-ref", "HEAD") or "UNKNOWN"

    def tracked(self, pattern: str) -> list[str]:
        out = self._git("ls-files", pattern)
        return sorted(line for line in out.splitlines() if line) if out else []

    def _git(self, *args: str) -> str:
        try:
            res = subprocess.run(  # noqa: S603
                ["git", *args],  # noqa: S607 - fixed argv, no shell
                cwd=self.config.repo_root,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return ""
        return res.stdout.strip() if res.returncode == 0 else ""

    # -- determinism fingerprint ----------------------------------------
    def _coverage_fingerprint(self) -> str:
        """Fingerprint coverage by the measurement consumed, not by the file bytes.

        ``coverage.xml`` embeds a wall-clock ``timestamp`` attribute, so its byte
        hash changes on every test run even when the measurement is identical.
        Hashing the four values the engine actually reads keeps the fingerprint a
        function of repository state, which is what makes regeneration reproducible.
        """
        cov = self.coverage()
        if not cov.available:
            return "absent"
        return sha256_text(
            canonical_json(
                {
                    "branch_pct": cov.branch_pct,
                    "line_pct": cov.line_pct,
                    "lines_covered": cov.lines_covered,
                    "lines_valid": cov.lines_valid,
                }
            )
        )

    def state_fingerprint(self) -> dict[str, Any]:
        """A content fingerprint of all evidence inputs.

        Identical repository state ⇒ identical fingerprint ⇒ identical outputs.

        Repository Fixed-Point Closure (UCOS-RFP-001 RFP-2) — the commit identity
        and branch that this fingerprint previously included are excluded. They made
        every output non-convergent by construction: the outputs are committed, so
        the commit they named was necessarily not the commit that contained them,
        and each regeneration therefore rewrote them without limit. What remains
        pins repository state honestly and without self-reference: the content
        hashes of the generated evidence surfaces and the consumed coverage
        measurement. Both are functions of tracked content, so the fingerprint is
        stable across commits of an unchanged tree.
        """
        files = {
            self.config.rel(self.config.data_file(n)): sha256_file(self.config.data_file(n))
            for n in _DATA_FILES
        }
        return {
            "evidence_files": files,
            "coverage_measurement": {
                "source": self.config.rel(self.config.coverage_xml),
                "fingerprint": self._coverage_fingerprint(),
                "basis": (
                    "the consumed measurement, not the file bytes — coverage.xml embeds a "
                    "wall-clock timestamp, so a byte hash would make every regeneration differ "
                    "with no change in repository state"
                ),
            },
        }

    # -- generation provenance ------------------------------------------
    def generation_state(self) -> dict[str, Any]:
        """The provenance block every generated artefact carries.

        Records the generator, the input hash and where the output hash lives.
        Every field is derived from tracked repository content, so regenerating
        over an unchanged tree reproduces the same bytes — provenance that cannot
        be reproduced is not provenance.

        The source commit, the repository head and the generation timestamp taken
        from the commit's committer date are deliberately ABSENT (UCOS-RFP-001
        RFP-2). Version control already records which commit contains these
        artifacts; restating it inside them duplicated that state and made the
        artifacts unable to reproduce themselves, which is the defect class
        UCOS-RFP-001 abolishes.
        """
        if "generation_state" not in self._cache:
            fingerprint = self.state_fingerprint()
            self._cache["generation_state"] = {
                "generator": "UCOS-RIE-001 Repository Intelligence Engine",
                "generator_version": __version__,
                "anchor": (
                    "the containing commit — owned by version control, never restated here "
                    "(UCOS-RFP-001 RFP-2)"
                ),
                "input_hash": sha256_text(canonical_json(fingerprint)),
                "input_hash_basis": (
                    "sha256 over the canonical evidence fingerprint — every evidence file hash "
                    "and the coverage measurement fingerprint, which together pin the tracked "
                    "state these outputs derive from without naming the commit that carries them"
                ),
                "output_hash_field": "content_hash",
            }
        return dict(self._cache["generation_state"])
