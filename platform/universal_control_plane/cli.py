"""UCOS-CTRL-000001 — Universal Control Plane CLI.

One-command surface over the Control Plane:

    ucos-ctrl state          # list registered lifecycle states and transitions
    ucos-ctrl registries     # summarise all four registries
    ucos-ctrl plan           # show master plan summary
    ucos-ctrl roadmap        # show roadmap milestone sequence
    ucos-ctrl backlog        # show ordered backlog
    ucos-ctrl schedule       # produce and display a schedule (demo mode)
    ucos-ctrl dashboard      # full unified dashboard snapshot

Exit codes: 0 success, 1 operational error, 2 fatal/argument error.
"""

from __future__ import annotations

import argparse
import json
import sys
from platform.universal_control_plane.errors import ControlPlaneError
from platform.universal_control_plane.execution import AssignmentEngine, Scheduler
from platform.universal_control_plane.intelligence import (
    DashboardEngine,
    MetricsEngine,
    ProgressEngine,
)
from platform.universal_control_plane.ontology import (
    AgentRecord,
    BacklogItem,
    Capability,
    Goal,
    Milestone,
    Objective,
    OwnershipRecord,
    Vision,
)
from platform.universal_control_plane.plan import BacklogEngine, PlanEngine, RoadmapEngine
from platform.universal_control_plane.registry import (
    AgentRegistry,
    CapabilityRegistry,
    DependencyRegistry,
    OwnershipRegistry,
)
from platform.universal_control_plane.state import StateEngine
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ucos-ctrl",
        description="UCOS-CTRL-000001 Universal Control Plane (UCOS Ω∞).",
    )
    parser.add_argument(
        "command",
        choices=("state", "registries", "plan", "roadmap", "backlog", "schedule", "dashboard"),
        help="the operation to perform",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit JSON on stdout")
    parser.add_argument(
        "--universe-id",
        default="UCOS-CTRL-000001",
        help="universe ID for demo data (default: UCOS-CTRL-000001)",
    )
    return parser


def _demo_universe(
    universe_id: str,
) -> tuple[
    CapabilityRegistry,
    OwnershipRegistry,
    DependencyRegistry,
    AgentRegistry,
    PlanEngine,
    RoadmapEngine,
    BacklogEngine,
    StateEngine,
]:
    """Build a minimal demo Control Plane for CLI inspection."""
    cap_reg = CapabilityRegistry()
    own_reg = OwnershipRegistry()
    dep_reg = DependencyRegistry()
    agt_reg = AgentRegistry()
    plan_eng = PlanEngine()
    road_eng = RoadmapEngine()
    back_eng = BacklogEngine()
    state_eng = StateEngine()

    # Register the Control Plane universe as a capability.
    cap_reg.register(
        Capability(
            capability_id="CTRL-CAP-001",
            universe_id=universe_id,
            name="Universal Control Plane",
            description="Engineering operating system",
        )
    )
    cap_reg.register(
        Capability(
            capability_id="CTRL-CAP-002",
            universe_id=universe_id,
            name="Universal State Engine",
            description="Lifecycle governance",
        )
    )
    own_reg.register(
        OwnershipRecord(
            ownership_id="OWN-001",
            capability_id="CTRL-CAP-001",
            owner_id=universe_id,
            owner_kind="Universe",
            rationale="Constitutional ownership",
        )
    )
    agt_reg.register(
        AgentRecord(
            agent_id="AGT-001",
            name="Execution Agent Alpha",
            kind="AUTONOMOUS",
            capabilities=("CTRL-CAP-001",),
        )
    )
    agt_reg.register(
        AgentRecord(
            agent_id="AGT-002",
            name="Execution Agent Beta",
            kind="AUTONOMOUS",
            capabilities=("CTRL-CAP-002",),
        )
    )

    vision = Vision(
        vision_id="VIS-001",
        universe_id=universe_id,
        statement="A universal engineering operating system, infinite by design.",
    )
    plan_eng.register_vision(vision)
    goal = Goal(
        goal_id="GOAL-001",
        vision_id="VIS-001",
        title="Implement the Control Plane",
        priority="CRITICAL",
    )
    plan_eng.register_goal(goal)
    obj = Objective(
        objective_id="OBJ-001",
        goal_id="GOAL-001",
        title="Foundation Layer",
        success_criteria="All engines pass verification",
    )
    plan_eng.register_objective(obj)

    m1 = Milestone(
        milestone_id="MS-001",
        universe_id=universe_id,
        title="Constitutional Foundation",
        sequence=1,
        objective_ids=("OBJ-001",),
    )
    m2 = Milestone(
        milestone_id="MS-002", universe_id=universe_id, title="Execution Layer", sequence=2
    )
    road_eng.register(m1)
    road_eng.register(m2)

    back_eng.add(
        BacklogItem(
            item_id="BLI-001",
            universe_id=universe_id,
            title="Implement ontology",
            priority="CRITICAL",
            milestone_id="MS-001",
            estimate=3,
        )
    )
    back_eng.add(
        BacklogItem(
            item_id="BLI-002",
            universe_id=universe_id,
            title="Implement state engine",
            priority="HIGH",
            milestone_id="MS-001",
            estimate=2,
        )
    )
    back_eng.add(
        BacklogItem(
            item_id="BLI-003",
            universe_id=universe_id,
            title="Implement scheduler",
            priority="MEDIUM",
            milestone_id="MS-002",
            estimate=4,
        )
    )

    return cap_reg, own_reg, dep_reg, agt_reg, plan_eng, road_eng, back_eng, state_eng


def _emit(payload: Any, *, as_json: bool, stream=None) -> None:
    out = stream or sys.stdout
    if as_json:
        print(json.dumps(payload, indent=2, default=str), file=out)
    else:
        _pretty(payload, out)


def _pretty(data: Any, out, indent: int = 0) -> None:
    pad = "  " * indent
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict | list):
                print(f"{pad}{k}:", file=out)
                _pretty(v, out, indent + 1)
            else:
                print(f"{pad}{k}: {v}", file=out)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                _pretty(item, out, indent)
            else:
                print(f"{pad}- {item}", file=out)
    else:
        print(f"{pad}{data}", file=out)


def run(argv: list[str] | None = None, *, out=None, err=None) -> int:
    out = out or sys.stdout
    err = err or sys.stderr
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        uid = args.universe_id
        cap_reg, own_reg, dep_reg, agt_reg, plan_eng, road_eng, back_eng, state_eng = (
            _demo_universe(uid)
        )

        if args.command == "state":
            payload = state_eng.to_dict()

        elif args.command == "registries":
            payload = {
                "registries": [
                    cap_reg.to_dict(),
                    own_reg.to_dict(),
                    dep_reg.to_dict(),
                    agt_reg.to_dict(),
                ]
            }

        elif args.command == "plan":
            payload = plan_eng.to_dict()

        elif args.command == "roadmap":
            payload = road_eng.to_dict()

        elif args.command == "backlog":
            payload = back_eng.to_dict()

        elif args.command == "schedule":
            scheduler = Scheduler()
            schedule = scheduler.schedule(back_eng.ready(), dep_reg, agt_reg, tick=0)
            payload = schedule.to_dict()

        elif args.command == "dashboard":
            scheduler = Scheduler()
            schedule = scheduler.schedule(back_eng.ready(), dep_reg, agt_reg, tick=0)
            assign_eng = AssignmentEngine()
            prog_eng = ProgressEngine()
            prog_eng.measure(uid, back_eng.ordered(), tick=0)
            met_eng = MetricsEngine()
            met_eng.record(uid, "backlog.count", float(back_eng.count()), tick=0)
            met_eng.record(uid, "milestone.count", float(road_eng.count()), tick=0)
            dash = DashboardEngine()
            payload = dash.snapshot(
                plan_dict=plan_eng.to_dict(),
                roadmap_dict=road_eng.to_dict(),
                backlog_dict=back_eng.to_dict(),
                schedule_dict=schedule.to_dict(),
                assignment_dict=assign_eng.to_dict(),
                progress_dict=prog_eng.to_dict(),
                metrics_dict=met_eng.to_dict(),
                registry_dicts=[
                    cap_reg.to_dict(),
                    own_reg.to_dict(),
                    dep_reg.to_dict(),
                    agt_reg.to_dict(),
                ],
                tick=0,
            )

        else:  # pragma: no cover — argparse guards this
            print(f"unknown command: {args.command}", file=err)
            return 2

        _emit(payload, as_json=args.as_json, stream=out)
        return 0

    except ControlPlaneError as exc:
        print(f"error: {exc}", file=err)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"fatal: {exc}", file=err)
        return 2


def main(argv: list[str] | None = None) -> None:
    sys.exit(run(argv))


if __name__ == "__main__":
    main()
