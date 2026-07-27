"""Capability discovery — enumerate realized capabilities from the substrate.

Discovery is genuine, not hardcoded. The unit universe is derived from the
version-control eligibility boundary (``git ls-files``), which is the same
Repository Truth the Repository Integration Blueprint discovers over:

  * every tracked ``<root>/__init__.py``   — a code root
  * every tracked ``<root>/<pkg>/__init__.py`` — a package inside a code root

The first line of each package docstring is read as its description and metrics
are derived from the census. Discovery also records the automation tools,
operational memory (MCS), corpus, and the orchestration specifications
(CIOA/CCE) whose presence-without-code marks them PLANNED.

Nothing is filtered out on aesthetic grounds. A test package is a tracked
implementation unit and is catalogued as one; excluding it created a permanent,
uncloseable capability-coverage gap against the repository's own inventory.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path

from .evidence import EvidenceReader
from .knowledge import policy_for


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


def _package_locations(reader: EvidenceReader, root: str) -> list[str]:
    """Tracked package locations inside *root*, repository-relative and sorted.

    Derived from ``git ls-files``; falls back to a deterministic filesystem walk
    so the engine remains usable in a non-git checkout.
    """
    base = reader.config.repo_root / root
    tracked = reader.tracked(f":(glob){root}/*/__init__.py")
    if tracked:
        return sorted({rel.rsplit("/", 1)[0] for rel in tracked})
    if not base.exists():
        return []
    return sorted(
        f"{root}/{d.name}"
        for d in base.iterdir()
        if d.is_dir() and (d / "__init__.py").exists() and not d.name.startswith(".")
    )


def _code_capability(reader: EvidenceReader, seq: int, root: str, location: str) -> Capability:
    """One catalogue record for one tracked Python package."""
    policy = policy_for(root)
    init_py = reader.config.repo_root / location / "__init__.py"
    name = location.replace("/", ".")
    return Capability(
        unique_id=f"RC-{seq:02d}",
        canonical_name=name,
        canonical_location=location,
        category=root,
        authority=str(policy["authority"]),
        reuse=str(policy["reuse"]),
        replacement_prohibited=bool(policy["replacement_prohibited"]),
        implementation_status=str(policy["status"]),
        description=_docline(init_py),
        evidence_present=init_py.exists(),
    )


def discover(reader: EvidenceReader) -> list[Capability]:
    cfg = reader.config
    caps: list[Capability] = []
    seq = 0

    # 1. Every tracked Python code root, and every tracked package inside it.
    for root in cfg.code_roots:
        seq += 1
        caps.append(_code_capability(reader, seq, root, root))
        for location in _package_locations(reader, root):
            seq += 1
            caps.append(_code_capability(reader, seq, root, location))

    # 2. Automation tools (presence-derived).
    tool_dir = cfg.repo_root / cfg.tool_dir
    for tool in ("ukb.py", "ukbx.py", "register.sh"):
        if (tool_dir / tool).exists():
            seq += 1
            pol = policy_for("automation")
            caps.append(Capability(
                unique_id=f"RC-{seq:02d}",
                canonical_name=f"automation/{tool}",
                canonical_location=cfg.rel(tool_dir / tool),
                category="automation",
                authority=str(pol["authority"]),
                reuse=str(pol["reuse"]),
                replacement_prohibited=bool(pol["replacement_prohibited"]),
                implementation_status=str(pol["status"]),
                description=f"Repository automation tool {tool}",
                evidence_present=True,
            ))

    # 3. Operational memory (MCS).
    if (cfg.repo_root / cfg.mcs_dir).exists():
        seq += 1
        pol = policy_for("operational_memory")
        caps.append(Capability(
            unique_id=f"RC-{seq:02d}",
            canonical_name="master-context-system",
            canonical_location=cfg.mcs_dir,
            category="operational_memory",
            authority=str(pol["authority"]),
            reuse=str(pol["reuse"]),
            replacement_prohibited=bool(pol["replacement_prohibited"]),
            implementation_status=str(pol["status"]),
            description="Master Context System (state-driven operational memory)",
            evidence_present=True,
        ))

    # 4. Orchestration specifications (present without code ⇒ PLANNED).
    for spec in cfg.orchestration_specs:
        spec_path = cfg.repo_root / spec
        seq += 1
        pol = policy_for("orchestration_spec")
        name = "CIOA" if "000000" in spec else "CCE"
        caps.append(Capability(
            unique_id=f"SPEC-{name}",
            canonical_name=name,
            canonical_location=spec,
            category="orchestration_spec",
            authority=str(pol["authority"]),
            reuse=str(pol["reuse"]),
            replacement_prohibited=bool(pol["replacement_prohibited"]),
            implementation_status=str(pol["status"]),
            description="Orchestration authority — specification only (no executable code)",
            evidence_present=spec_path.exists(),
        ))

    return caps
