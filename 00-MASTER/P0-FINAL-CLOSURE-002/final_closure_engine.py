#!/usr/bin/env python3
"""P0-FINAL-CLOSURE-002 — Phase 8 fixed-point and Phase 9 pristine-clone measurement.

AUTHORITY = NONE (DERIVED TRUTH). This engine legislates nothing, registers nothing,
certifies nothing and owns no capability. It runs the located regeneration chain, measures
what changed, and records the result. It cannot make a state converge and cannot make a
clone agree; where either fails it emits the failure.

Phase 8 — the fixed point
-------------------------
A *round* is one execution of the located regeneration chain. Zero drift means the round
changed nothing: the repository regenerated itself and produced byte-identical output.
Eight variance dimensions are measured separately rather than as one digest, because
"something moved" is not an actionable finding — *which* identity moved is.

The measurement is only valid with **no concurrent writer**. The prior attempt at this
phase was contaminated by exactly that and correctly refused to derive a claim from it, so
this engine takes a working-tree fingerprint before and after every round and fails closed
if anything it did not run has written into the tree.

Phase 9 — the pristine clones
-----------------------------
Each clone is an independent ``git clone`` of the canonical repository at HEAD, verified on
its own and then compared against the canonical identities. A clone that regenerates to a
different digest means the output depends on something outside version control, which is
the defect this phase exists to detect.

    python3 00-MASTER/P0-FINAL-CLOSURE-002/final_closure_engine.py
    python3 00-MASTER/P0-FINAL-CLOSURE-002/final_closure_engine.py --rounds 5 --clones 3
    python3 00-MASTER/P0-FINAL-CLOSURE-002/final_closure_engine.py --phase 8
    python3 00-MASTER/P0-FINAL-CLOSURE-002/final_closure_engine.py --gate

Exit semantics:
    0  both phases measured and every requirement met (or --gate not requested)
    1  --gate requested and a requirement was not met
    2  fail-closed abort — a concurrent writer, or a phase that could not be measured

No timestamp, no duration, no commit identity and no absolute path is emitted, so the
artifact set is byte-identical for an unchanged repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROGRAMME = "P0-FINAL-CLOSURE-002"
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "00-MASTER" / PROGRAMME

#: The located regeneration chain, in the order the repository declares it. Each entry is
#: run as a subprocess exactly as its Makefile target runs it, so this engine measures the
#: real chain rather than a reimplementation of it.
CHAIN: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("rib", ("00-MASTER/UCOS-RIB-001/rib_engine.py",)),
    ("aee", ("00-MASTER/UCOS-AEE-001/aee_engine.py", "--tier", "standard")),
)

#: The eight variance dimensions Phase 8 requires, each bound to the artifact whose digest
#: carries it. DATA — a ninth dimension is one appended entry.
DIMENSIONS: Mapping[str, str] = {
    "registry_variance": "00-MASTER/UCOS-RIB-001/rib.json",
    "authority_variance": "00-MASTER/UCCEP-000000/uccep.json",
    "certification_variance": "00-MASTER/UCOS-AEE-001/aee.json",
    "bookkeeping_variance": "00-MASTER/UCL-000001/ucl.json",
    "lineage_variance": "00-MASTER/ACEE-000001/acee.json",
    "dictionary_variance": "intelligence/UCOS-RIE-CAPABILITY-CATALOG.json",
    "ordering_variance": "00-MASTER/UCOS-RIB-001/10-IMPLEMENTATION-QUEUE.md",
    "replay_variance": "00-MASTER/P0-LIFECYCLE-CLOSURE-001/UCOS-LIFECYCLE-REPLAY.json",
}

#: What Phase 9 compares between a clone and the canonical repository.
CLONE_IDENTITIES: Mapping[str, str] = dict(DIMENSIONS)


class Abort(Exception):
    """A phase could not be measured, so no verdict may be asserted."""


def rel(path: Path | str) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO))
    except (ValueError, OSError):
        return str(path)


def sha256(path: Path) -> str:
    """The content digest of one artifact, or ``"absent"`` when it does not exist."""
    if not path.is_file():
        return "absent"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identities(root: Path, mapping: Mapping[str, str] = DIMENSIONS) -> dict[str, str]:
    """The digest of every measured artifact under ``root``."""
    return {name: sha256(root / target) for name, target in sorted(mapping.items())}


def porcelain(root: Path) -> list[str]:
    """The working-tree state as git reports it, sorted."""
    run = subprocess.run(  # noqa: S603 - literal argv
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return sorted(line for line in run.stdout.splitlines() if line.strip())


def run_chain(root: Path, chain: Sequence[tuple[str, tuple[str, ...]]] = CHAIN) -> dict[str, int]:
    """Execute the located regeneration chain once. Returns each actuator's exit code."""
    codes: dict[str, int] = {}
    for name, argv in chain:
        run = subprocess.run(  # noqa: S603 - argv is literal; root is a repository path
            [sys.executable, *argv],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        codes[name] = run.returncode
    return codes


# --------------------------------------------------------------------------- phase 8


def phase8(rounds: int) -> dict[str, Any]:
    """Run the chain ``rounds`` times and measure drift across every dimension.

    Fails closed on a concurrent writer: if the tree changes between the end of one round
    and the start of the next, something other than this engine wrote, and drift measured
    under concurrent mutation is not attributable to the regeneration pipeline.
    """
    before_tree = porcelain(REPO)
    if before_tree:
        raise Abort(
            "the working tree is not clean; a fixed point measured over uncommitted state "
            f"would certify an arbitrary snapshot ({len(before_tree)} dirty entries)"
        )

    baseline = identities(REPO)
    observed: list[dict[str, Any]] = []
    previous_tree = before_tree

    for index in range(1, rounds + 1):
        if porcelain(REPO) != previous_tree:
            raise Abort(f"a concurrent writer mutated the tree before round {index}")
        codes = run_chain(REPO)
        tree = porcelain(REPO)
        current = identities(REPO)
        drifted = sorted(k for k, v in current.items() if v != baseline[k])
        observed.append(
            {
                "round": index,
                "actuators": codes,
                "actuator_failures": sorted(k for k, v in codes.items() if v not in (0, 1)),
                "mutation": len(tree),
                "mutated_paths": [line[3:] for line in tree][:20],
                "drift": len(drifted),
                "drifted_dimensions": drifted,
                "identities": current,
            }
        )
        previous_tree = tree

    zero_drift = [r for r in observed if r["drift"] == 0 and r["mutation"] == 0]
    consecutive = 0
    best = 0
    for record in observed:
        if record["drift"] == 0 and record["mutation"] == 0:
            consecutive += 1
            best = max(best, consecutive)
        else:
            consecutive = 0

    variance = {
        name: sum(1 for r in observed if name in r["drifted_dimensions"]) for name in DIMENSIONS
    }
    met = best >= rounds and not any(r["actuator_failures"] for r in observed)
    return {
        "phase": 8,
        "title": "Five-Round Fixed-Point Certification",
        "authority": "NONE — DERIVED TRUTH. Measurement only.",
        "requirement": f"{rounds} consecutive rounds, 0 drift, 0 mutation, 0 variance",
        "verdict": "FIXED POINT CERTIFIED" if met else "NOT PROVEN",
        "met": met,
        "rounds_executed": len(observed),
        "consecutive_zero_drift_rounds": best,
        "zero_drift_rounds": len(zero_drift),
        "concurrent_writer_detected": False,
        "chain": [{"actuator": n, "argv": list(a)} for n, a in CHAIN],
        "variance": variance,
        "dimensions": dict(sorted(DIMENSIONS.items())),
        "baseline_identities": baseline,
        "rounds": observed,
    }


# --------------------------------------------------------------------------- phase 9


def _clone(index: int, workdir: Path) -> Path:
    target = workdir / f"clone-{index}"
    run = subprocess.run(  # noqa: S603 - literal argv
        ["git", "clone", "--quiet", "--local", "--no-hardlinks", str(REPO), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode != 0 or not target.exists():
        raise Abort(f"clone {index} could not be created: {run.stderr[-300:]}")
    return target


def phase9(clones: int, cycles: int) -> dict[str, Any]:
    """Create ``clones`` pristine clones, run ``cycles`` verification cycles in each.

    Each cycle runs the same located chain the canonical repository runs. A clone is
    byte-identical when every measured identity matches the canonical one after every
    cycle — which is what proves the output depends on version-controlled content and
    nothing else.
    """
    canonical = identities(REPO, CLONE_IDENTITIES)
    results: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="ucos-pristine-") as tmp:
        workdir = Path(tmp)
        for index in range(1, clones + 1):
            target = _clone(index, workdir)
            cycle_records: list[dict[str, Any]] = []
            for cycle in range(1, cycles + 1):
                codes = run_chain(target)
                observed = identities(target, CLONE_IDENTITIES)
                mismatched = sorted(k for k, v in observed.items() if v != canonical[k])
                cycle_records.append(
                    {
                        "cycle": cycle,
                        "actuators": codes,
                        "actuator_failures": sorted(
                            k for k, v in codes.items() if v not in (0, 1)
                        ),
                        "mismatched_identities": mismatched,
                        "byte_identical": not mismatched,
                        "mutation": len(porcelain(target)),
                    }
                )
            identical = all(c["byte_identical"] for c in cycle_records)
            results.append(
                {
                    "clone": index,
                    "cycles_executed": len(cycle_records),
                    "byte_identical_every_cycle": identical,
                    "cycles": cycle_records,
                }
            )
            shutil.rmtree(target, ignore_errors=True)

    met = bool(results) and all(c["byte_identical_every_cycle"] for c in results)
    return {
        "phase": 9,
        "title": "Pristine Clone Certification",
        "authority": "NONE — DERIVED TRUTH. Measurement only.",
        "requirement": f"{clones} independent clones, {cycles} verification cycles each",
        "verdict": "REPRODUCIBILITY CERTIFIED" if met else "NOT PROVEN",
        "met": met,
        "clones": len(results),
        "cycles_per_clone": cycles,
        "total_cycles": sum(c["cycles_executed"] for c in results),
        "identities_compared": sorted(CLONE_IDENTITIES),
        "canonical_identities": canonical,
        "results": results,
    }


# --------------------------------------------------------------------------- driver


def emit(name: str, payload: dict[str, Any]) -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"programme": PROGRAMME, **payload}
    payload["digest"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    target = OUT / name
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return rel(target)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="final_closure_engine",
        description=(
            "Phase 8 fixed-point and Phase 9 pristine-clone measurement. "
            "AUTHORITY = NONE; executable evidence only."
        ),
    )
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--clones", type=int, default=3)
    parser.add_argument("--cycles", type=int, default=5)
    parser.add_argument("--phase", type=int, choices=(8, 9), default=0)
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args(argv)

    written: list[str] = []
    verdicts: dict[str, bool] = {}
    try:
        if args.phase in (0, 8):
            result = phase8(args.rounds)
            written.append(emit("UCOS-FIXED-POINT-CERTIFICATION.json", result))
            verdicts["phase8"] = result["met"]
        if args.phase in (0, 9):
            result = phase9(args.clones, args.cycles)
            written.append(emit("UCOS-PRISTINE-CLONE-CERTIFICATION.json", result))
            verdicts["phase9"] = result["met"]
    except Abort as exc:
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {"programme": PROGRAMME, "artifacts": written, "verdicts": verdicts},
            indent=2,
            sort_keys=True,
        )
    )
    if args.gate and not all(verdicts.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
