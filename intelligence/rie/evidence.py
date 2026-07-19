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

from .canonical import sha256_file
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
    def state_fingerprint(self) -> dict[str, Any]:
        """A content fingerprint of all evidence inputs + HEAD.

        Identical repository state ⇒ identical fingerprint ⇒ identical outputs.
        """
        files = {
            self.config.rel(self.config.data_file(n)): sha256_file(self.config.data_file(n))
            for n in _DATA_FILES
        }
        files[self.config.rel(self.config.coverage_xml)] = sha256_file(self.config.coverage_xml)
        return {
            "head": self.head(),
            "branch": self.branch(),
            "evidence_files": files,
        }
