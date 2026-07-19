"""Capability discovery — enumerate realized capabilities from the substrate.

Discovery is genuine, not hardcoded: the engine scans the code roots for Python
sub-packages (each ``<root>/<name>/`` with an ``__init__.py`` is a capability),
reads the first line of the package docstring as its description, and derives
metrics from the census. It also records the automation tools, operational
memory (MCS), corpus, and the orchestration specifications (CIOA/CCE) whose
presence-without-code marks them PLANNED.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path

from .evidence import EvidenceReader
from .knowledge import CATEGORY_POLICY


@dataclass(frozen=True)
class Capability:
    unique_id: str
    canonical_name: str
    canonical_location: str
    category: str
    authority: str
    reuse: str
    replacement_prohibited: bool
    implementation_status: str
    description: str
    evidence_present: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _docline(init_py: Path) -> str:
    try:
        mod = ast.parse(init_py.read_text(encoding="utf-8", errors="ignore"))
        doc = ast.get_docstring(mod) or ""
    except (OSError, SyntaxError):
        return ""
    first = doc.strip().splitlines()[0] if doc.strip() else ""
    return first[:160]


def _subpackages(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return sorted(
        d for d in base.iterdir()
        if d.is_dir()
        and (d / "__init__.py").exists()
        and not d.name.startswith("_")
        and d.name != "tests"
    )


def discover(reader: EvidenceReader) -> list[Capability]:
    cfg = reader.config
    caps: list[Capability] = []
    seq = 0

    # 1. Realized code sub-packages under each code root.
    for root in cfg.code_roots:
        policy = CATEGORY_POLICY.get(root, CATEGORY_POLICY["engine"])
        for pkg in _subpackages(cfg.repo_root / root):
            seq += 1
            caps.append(Capability(
                unique_id=f"RC-{seq:02d}",
                canonical_name=f"{root}.{pkg.name}",
                canonical_location=cfg.rel(pkg),
                category=root,
                authority=str(policy["authority"]),
                reuse=str(policy["reuse"]),
                replacement_prohibited=bool(policy["replacement_prohibited"]),
                implementation_status="CERTIFIED" if root == "engine" else "IMPLEMENTED",
                description=_docline(pkg / "__init__.py"),
                evidence_present=True,
            ))

    # 2. Automation tools (presence-derived).
    tool_dir = cfg.repo_root / cfg.tool_dir
    for tool in ("ukb.py", "ukbx.py", "register.sh"):
        if (tool_dir / tool).exists():
            seq += 1
            pol = CATEGORY_POLICY["automation"]
            caps.append(Capability(
                unique_id=f"RC-{seq:02d}",
                canonical_name=f"automation/{tool}",
                canonical_location=cfg.rel(tool_dir / tool),
                category="automation",
                authority=str(pol["authority"]),
                reuse=str(pol["reuse"]),
                replacement_prohibited=bool(pol["replacement_prohibited"]),
                implementation_status="IMPLEMENTED",
                description=f"Repository automation tool {tool}",
                evidence_present=True,
            ))

    # 3. Operational memory (MCS).
    if (cfg.repo_root / cfg.mcs_dir).exists():
        seq += 1
        pol = CATEGORY_POLICY["operational_memory"]
        caps.append(Capability(
            unique_id=f"RC-{seq:02d}",
            canonical_name="master-context-system",
            canonical_location=cfg.mcs_dir,
            category="operational_memory",
            authority=str(pol["authority"]),
            reuse=str(pol["reuse"]),
            replacement_prohibited=bool(pol["replacement_prohibited"]),
            implementation_status="IMPLEMENTED",
            description="Master Context System (state-driven operational memory)",
            evidence_present=True,
        ))

    # 4. Orchestration specifications (present without code ⇒ PLANNED).
    for spec in cfg.orchestration_specs:
        spec_path = cfg.repo_root / spec
        seq += 1
        pol = CATEGORY_POLICY["orchestration_spec"]
        name = "CIOA" if "000000" in spec else "CCE"
        caps.append(Capability(
            unique_id=f"SPEC-{name}",
            canonical_name=name,
            canonical_location=spec,
            category="orchestration_spec",
            authority=str(pol["authority"]),
            reuse=str(pol["reuse"]),
            replacement_prohibited=bool(pol["replacement_prohibited"]),
            implementation_status="PLANNED",
            description="Orchestration authority — specification only (no executable code)",
            evidence_present=spec_path.exists(),
        ))

    return caps
