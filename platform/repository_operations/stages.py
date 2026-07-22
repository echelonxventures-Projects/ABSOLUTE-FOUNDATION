"""EPIC-PLAT-003 — Pipeline stage executors (Terminal T5).

Each stage kind is a **thin adapter over existing canonical machinery** — a canonical
script/target, the certified EC-1 Acceptance / Validation / Certification engines, the
certified frozen-corpus guard, or the canonical coverage report. No stage re-implements
a check or invents a verdict (TP-01): it delegates and records the outcome.

A legitimate fail-closed outcome (a rejected repository, a below-threshold coverage
report, a frozen-corpus write) is reported as a FAILED
:class:`~platform.repository_operations.contracts.StageResult`; only a malformed stage
definition raises :class:`~platform.repository_operations.errors.StageExecutionError`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from platform.foundation.contracts import content_hash
from platform.repository_operations.commands import CommandRunner, resolve_command
from platform.repository_operations.contracts import (
    CoverageSummary,
    StageKind,
    StageOutcome,
    StageResult,
    StageSpec,
)
from platform.repository_operations.coverage import load_coverage_summary
from platform.repository_operations.errors import StageExecutionError
from platform.repository_operations.subjects import build_validation_subject
from typing import Any

from engine.acceptance.contracts import RepositorySubject
from engine.acceptance.engine import AcceptanceEngine
from engine.acceptance.errors import RepositorySubjectError
from engine.acceptance.readiness import build_repository_readiness
from engine.certification.engine import certify_validation
from engine.foundation.guards.frozen_paths import FROZEN_PREFIXES, find_frozen_writes
from engine.validation.evidence import build_validation_evidence
from engine.validation.executor import ValidationEngine


def execute_stage(
    spec: StageSpec,
    *,
    command_runner: CommandRunner,
    repo_root: str | Path,
) -> tuple[StageResult, CoverageSummary | None]:
    """Execute one stage, returning its result and (for COVERAGE) the parsed summary."""
    if spec.kind is StageKind.COMMAND:
        return _run_command(spec, command_runner), None
    if spec.kind is StageKind.ACCEPTANCE:
        return _run_acceptance(spec), None
    if spec.kind is StageKind.VALIDATION:
        return _run_validation(spec), None
    if spec.kind is StageKind.CERTIFICATION:
        return _run_certification(spec), None
    if spec.kind is StageKind.FREEZE:
        return _run_freeze(spec), None
    return _run_coverage(spec, repo_root)


def _require_mapping(spec: StageSpec, key: str) -> Mapping[str, Any]:
    value = spec.params.get(key)
    if not isinstance(value, Mapping):
        raise StageExecutionError(
            f"{spec.kind.value} stage requires a '{key}' mapping",
            stage_id=spec.stage_id,
        )
    return value


def _run_command(spec: StageSpec, command_runner: CommandRunner) -> StageResult:
    name = spec.params.get("command")
    if not name or not isinstance(name, str):
        raise StageExecutionError("command stage requires a 'command' name", stage_id=spec.stage_id)
    argv = resolve_command(name)
    returncode = command_runner(argv)
    outcome = StageOutcome.PASSED if returncode == 0 else StageOutcome.FAILED
    return StageResult.create(
        spec,
        outcome,
        f"canonical command '{name}' exited {returncode}",
        detail={"command": name, "argv": list(argv), "returncode": returncode},
    )


def _run_acceptance(spec: StageSpec) -> StageResult:
    facts = _require_mapping(spec, "facts")
    try:
        subject = RepositorySubject.from_mapping(facts)
    except RepositorySubjectError as exc:
        raise StageExecutionError(
            "acceptance facts could not be assimilated",
            stage_id=spec.stage_id,
            detail=str(exc),
        ) from exc
    decision = AcceptanceEngine().accept(subject)
    readiness = build_repository_readiness(decision)
    outcome = StageOutcome.PASSED if decision.accepted else StageOutcome.FAILED
    return StageResult.create(
        spec,
        outcome,
        f"repository acceptance {decision.status.value} (readiness {readiness.verdict})",
        evidence_ref=decision.acceptance_id,
        detail={
            "acceptance_id": decision.acceptance_id,
            "status": decision.status.value,
            "readiness_verdict": readiness.verdict,
            "freeze_ready": readiness.freeze_ready,
            "blocking_failures": list(decision.blocking_failures),
            "counts": decision.counts(),
        },
    )


def _run_validation(spec: StageSpec) -> StageResult:
    subject = build_validation_subject(_require_mapping(spec, "subject"))
    report = ValidationEngine().validate(subject)
    outcome = StageOutcome.PASSED if report.accepted else StageOutcome.FAILED
    return StageResult.create(
        spec,
        outcome,
        f"validation {report.verdict.value}",
        evidence_ref=content_hash(report.to_dict()),
        detail={
            "target_id": report.target_id,
            "verdict": report.verdict.value,
            "counts": report.counts(),
            "blocking_failures": [f.check_id for f in report.blocking_failures],
        },
    )


def _run_certification(spec: StageSpec) -> StageResult:
    subject = build_validation_subject(_require_mapping(spec, "subject"))
    version = str(spec.params.get("version", "1.0.0"))
    report = ValidationEngine().validate(subject)
    evidence = build_validation_evidence(report)
    decision = certify_validation(report, evidence, version=version)
    outcome = StageOutcome.PASSED if decision.certified else StageOutcome.FAILED
    return StageResult.create(
        spec,
        outcome,
        f"certification {decision.status.value}",
        evidence_ref=decision.certification_id,
        detail={
            "certification_id": decision.certification_id,
            "status": decision.status.value,
            "blocking_failures": list(decision.blocking_failures),
            "counts": decision.counts(),
        },
    )


def _run_freeze(spec: StageSpec) -> StageResult:
    paths_raw = spec.params.get("paths", [])
    if not isinstance(paths_raw, Sequence) or isinstance(paths_raw, str | bytes):
        raise StageExecutionError("freeze stage 'paths' must be a list", stage_id=spec.stage_id)
    paths = [str(p) for p in paths_raw]
    violations = find_frozen_writes(paths)
    outcome = StageOutcome.FAILED if violations else StageOutcome.PASSED
    summary = (
        f"{len(violations)} frozen-corpus write(s) detected"
        if violations
        else f"no frozen-corpus writes across {len(paths)} path(s)"
    )
    return StageResult.create(
        spec,
        outcome,
        summary,
        detail={
            "checked": len(paths),
            "violations": violations,
            "frozen_prefixes": list(FROZEN_PREFIXES),
        },
    )


def _run_coverage(
    spec: StageSpec, repo_root: str | Path
) -> tuple[StageResult, CoverageSummary | None]:
    try:
        min_percent = float(spec.params.get("min_percent", 90.0))
    except (TypeError, ValueError) as exc:
        raise StageExecutionError(
            "coverage stage 'min_percent' must be numeric",
            stage_id=spec.stage_id,
            detail=str(exc),
        ) from exc

    coverage_path = Path(spec.params.get("path", "coverage.xml"))
    if not coverage_path.is_absolute():
        coverage_path = Path(repo_root) / coverage_path

    if not coverage_path.is_file():
        result = StageResult.create(
            spec,
            StageOutcome.FAILED,
            f"coverage report not found at {coverage_path}",
            detail={"path": str(coverage_path), "min_percent": min_percent},
        )
        return result, None

    summary = load_coverage_summary(coverage_path)
    outcome = StageOutcome.PASSED if summary.meets(min_percent) else StageOutcome.FAILED
    result = StageResult.create(
        spec,
        outcome,
        f"line coverage {summary.line_percent}% (minimum {min_percent}%)",
        evidence_ref=content_hash(summary.to_dict()),
        detail={"path": str(coverage_path), "min_percent": min_percent, **summary.to_dict()},
    )
    return result, summary


__all__ = ["execute_stage"]
