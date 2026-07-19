"""RIE command-line interface (AI-agnostic, head-less).

    python -m intelligence.rie build     # regenerate all machine-readable outputs
    python -m intelligence.rie verify     # prove deterministic regeneration
    python -m intelligence.rie snapshot   # print the compact intelligence snapshot
    python -m intelligence.rie answer      # answer the success-criteria questions
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .canonical import canonical_json
from .config import RepoConfig
from .engine import RepositoryIntelligenceEngine


def _engine(args: argparse.Namespace) -> RepositoryIntelligenceEngine:
    root = Path(args.repo).resolve() if args.repo else None
    return RepositoryIntelligenceEngine(RepoConfig.create(root) if root else None)


def _cmd_build(args: argparse.Namespace) -> int:
    eng = _engine(args)
    written = eng.write()
    print(f"RIE: regenerated {len(written)} intelligence outputs under {eng.config.output_dir}:")
    for w in written:
        print(f"  - {Path(w).name}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    eng = _engine(args)
    result = eng.verify_determinism()
    print(canonical_json(result), end="")
    return 0 if result["deterministic"] else 1


def _cmd_snapshot(args: argparse.Namespace) -> int:
    eng = _engine(args)
    print(canonical_json(eng.outputs()["UCOS-RIE-SNAPSHOT.json"]), end="")
    return 0


def _cmd_answer(args: argparse.Namespace) -> int:
    eng = _engine(args)
    m = eng.model()
    f = m["execution_frontier"]
    answers = {
        "what_exists": f"{m['capability_count']} realized/spec capabilities; "
                       f"{m['health']['corpus']['artifacts']} corpus artifacts",
        "what_is_implemented": f"engine EC-1 + platform EC-2 "
                               f"({m['health']['code']['total_loc']} LOC, "
                               f"{m['health']['code']['total_tests']} tests, "
                               f"{m['health']['code']['coverage_line_pct']}% coverage)",
        "what_remains": [g["missing"] for g in m["aeos_readiness"]["known_spine_gaps"]],
        "what_is_blocked": f.get("blocked", []),
        "what_is_executable": f.get("next_executable_capability"),
        "critical_path": f.get("critical_path", []),
        "current_repository_state": m["digital_twin"],
        "is_aeos_ready": m["aeos_readiness"]["verdict"],
    }
    print(canonical_json(answers), end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="intelligence.rie", description="Repository Intelligence Engine")
    parser.add_argument("--repo", help="repository root (default: auto-resolve)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in (("build", _cmd_build), ("verify", _cmd_verify),
                     ("snapshot", _cmd_snapshot), ("answer", _cmd_answer)):
        p = sub.add_parser(name)
        p.set_defaults(func=fn)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
