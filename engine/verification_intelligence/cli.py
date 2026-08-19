"""UVI-000001 Part 09 — the surface ``./verify.sh`` consumes.

Four subcommands, each one thing:

    plan        compute the plan for a mode and emit it (tsv for the shell, json for a reader)
    run-tests   execute the pytest stage of a mode — select, shard, run, combine, evaluate
    record      store one stage result in the evidence registry
    report      the human-readable account of what a mode would do and why

``plan`` and ``report`` write nothing. ``run-tests`` writes only coverage data and
reports, all gitignored. ``record`` writes only into the evidence store, which is
untracked by design.

Exit codes are chosen so the shell can branch without parsing: 0 succeeded, 1 a
verification failed, 2 the intelligence itself faulted. A FAULT never means "skip" — the
shell's fail-safe on 2 is to run the stage the ordinary way.
"""

from __future__ import annotations

import argparse
import os
import sys

from engine.verification_intelligence.constitution import load_constitution, repo_root
from engine.verification_intelligence.evidence import record as record_evidence
from engine.verification_intelligence.evidence import store_home
from engine.verification_intelligence.execution import run_tests
from engine.verification_intelligence.model import VerificationIntelligenceError
from engine.verification_intelligence.plan import (
    build_plan,
    plan_digest,
    plan_json,
    plan_tsv,
)

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_FAULT = 2


def _render_plan(plan) -> str:
    selection = plan.selection
    lines = [
        "VERIFICATION PLAN",
        "-" * 72,
        f"  mode                  : --{plan.mode.mode_id}",
        f"  claim                 : {plan.mode.claim}",
        f"  does NOT claim        : {', '.join(plan.mode.claims_not) or '-'}",
        f"  coverage              : {plan.coverage.value}"
        + ("  (escalated)" if plan.escalated_coverage else ""),
        f"  changed files         : {len(selection.changed)}",
        f"  affected objects      : {len(selection.affected_objects)}",
        f"  affected owners       : {len(selection.affected_owners)}",
        f"  affected capabilities : {len(selection.affected_capabilities)}",
        f"  selection             : {selection.selection.value}",
        f"  test objects selected : {len(selection.test_paths)}",
        f"  shards                : {len(plan.shards)} across {plan.workers} worker(s)",
        f"  plan digest           : {plan_digest(plan)[:16]}",
        "-" * 72,
    ]
    if selection.layers:
        lines.append("  selection layers:")
        for name, reached in selection.layers:
            lines.append(f"    {name:<14} reached {reached}")
    if selection.escalations:
        lines.append("  escalations:")
        for reason in selection.escalations[:8]:
            lines.append(f"    - {reason}")
        remaining = len(selection.escalations) - 8
        if remaining > 0:
            lines.append(f"    ... +{remaining} more")
    lines.append("  stages:")
    for entry in plan.stages:
        lines.append(f"    {entry.action.value:<5} {entry.stage.phase:<9} {entry.stage.label}")
    for note in plan.notes:
        lines.append(f"  note: {note}")
    lines.append("-" * 72)
    return "\n".join(lines)


def _plan_for(args) -> object:
    return build_plan(
        args.mode,
        changed=tuple(args.path) if getattr(args, "path", None) else None,
        base=getattr(args, "base", None),
        workers_override=os.environ.get("UVI_WORKERS"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m engine.verification_intelligence",
        description="Universal Verification Intelligence — plan and execute verification.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("plan", "compute the plan for a mode"),
        ("report", "explain what a mode would do and why"),
        ("run-tests", "execute the pytest stage of a mode"),
    ):
        node = sub.add_parser(name, help=help_text)
        node.add_argument(
            "--mode", default=None, help="declared mode id (default: the declared default)"
        )
        node.add_argument("--base", default=None, help="explicit diff base")
        node.add_argument("--path", action="append", default=None, help="treat PATH as changed")
        if name == "plan":
            node.add_argument("--tsv", action="store_true", help="emit action/phase/label rows")
            node.add_argument("--json", action="store_true", help="emit the plan as JSON")
            node.add_argument("--out", default=None, help="write to this file instead of stdout")

    node = sub.add_parser("record", help="store one stage result in the evidence registry")
    node.add_argument("--stage-label", required=True, help="the declared stage label")
    node.add_argument("--result", required=True, choices=["PASS", "FAIL"])
    node.add_argument("--digest", required=True, help="the input digest the plan computed")

    args = parser.parse_args(argv)

    try:
        if args.command == "record":
            constitution = load_constitution()
            match = [stage for stage in constitution.stages if stage.label == args.stage_label]
            if not match:
                print(
                    f"UVI: no declared stage carries that label: {args.stage_label}",
                    file=sys.stderr,
                )
                return EXIT_FAULT
            record_evidence(
                store_home(None, constitution.evidence_home),
                match[0].stage_id,
                args.digest,
                args.result,
            )
            return EXIT_OK

        plan = _plan_for(args)
        if args.command == "report":
            print(_render_plan(plan))
            return EXIT_OK
        if args.command == "plan":
            if args.json:
                text = plan_json(plan)
            elif args.tsv:
                text = plan_tsv(plan)
            else:
                text = _render_plan(plan)
            if getattr(args, "out", None):
                with open(args.out, "w", encoding="utf-8") as handle:
                    handle.write(text if text.endswith("\n") else text + "\n")
            else:
                print(text)
            return EXIT_OK

        # run-tests
        print(_render_plan(plan), file=sys.stderr)
        return run_tests(
            plan.shards,
            plan.coverage,
            root=repo_root(),
            python=sys.executable,
            selection=plan.selection.test_paths,
        )
    except VerificationIntelligenceError as exc:
        print(f"UVI FAULT: {exc}", file=sys.stderr)
        return EXIT_FAULT


if __name__ == "__main__":  # pragma: no cover - CLI dispatch
    raise SystemExit(main())
