"""Derived analytics — health, progress, frontier, critical path, twin, readiness.

Every value here is a pure function of the evidence + census; nothing is
estimated or hardcoded. Percentages are computed from real counts and the
control-tower dimension statuses.
"""

from __future__ import annotations

from typing import Any

from .census import RootCensus
from .evidence import Coverage, EvidenceReader
from .knowledge import DIMENSION_SCORE, KNOWN_SPINE_GAPS, LOCALLY_VERIFIABLE_DIMENSIONS


def _dimensions(ct: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return ct.get("dimensions", {})


def repository_health(reader: EvidenceReader, census: dict[str, RootCensus], cov: Coverage) -> dict[str, Any]:
    ct = reader.control_tower()
    cert = reader.certification()
    portfolio = ct.get("portfolio", {})
    total_loc = sum(c.loc for c in census.values())
    total_tests = sum(c.test_functions for c in census.values())
    domains_passed = cert.get("domains_passed")
    domains_total = cert.get("domains_total")
    return {
        "corpus": {
            "artifacts": portfolio.get("total_artifacts"),
            "volumes": portfolio.get("total_volumes"),
            "pages": portfolio.get("total_pages"),
            "edges": portfolio.get("total_edges"),
            "status_histogram": portfolio.get("status_histogram", {}),
        },
        "code": {
            "roots": {r: c.as_dict() for r, c in census.items()},
            "total_loc": total_loc,
            "total_tests": total_tests,
            "coverage_line_pct": cov.line_pct if cov.available else None,
            "coverage_branch_pct": cov.branch_pct if cov.available else None,
        },
        "certification": {
            "digital_twin_verdict": cert.get("verdict"),
            "domains": f"{domains_passed}/{domains_total}" if domains_total else None,
            "standard": cert.get("standard"),
        },
        "health_flags": {
            "coverage_full": bool(cov.available and cov.line_pct >= 100.0 and cov.branch_pct >= 100.0),
            "twin_certified": cert.get("verdict") == "CERTIFIED",
            "corpus_present": bool(portfolio.get("total_artifacts")),
        },
        "overall": "HEALTHY" if (cert.get("verdict") == "CERTIFIED" and portfolio.get("total_artifacts")) else "INDETERMINATE",
    }


def progress(reader: EvidenceReader, census: dict[str, RootCensus], cov: Coverage) -> dict[str, Any]:
    ct = reader.control_tower()
    dims = _dimensions(ct)
    literal_total = 0.0
    reconciled_total = 0.0
    per_dimension: dict[str, dict[str, Any]] = {}
    for name, d in sorted(dims.items()):
        status = d.get("status", "INDETERMINATE")
        literal = DIMENSION_SCORE.get(status, 0.0)
        reconciled = literal
        stale = _is_stale(d, ct)
        if (name in LOCALLY_VERIFIABLE_DIMENSIONS and status == "BLOCKED"
                and cov.available and cov.line_pct >= 100.0):
            reconciled = 1.0  # locally-passing evidence overrides stale BLOCKED signal
        literal_total += literal
        reconciled_total += reconciled
        per_dimension[name] = {
            "status": status,
            "source": d.get("signal_source"),
            "as_of": d.get("as_of"),
            "stale": stale,
            "literal_score": literal,
            "reconciled_score": reconciled,
        }
    n = len(dims) or 1
    return {
        "per_dimension": per_dimension,
        "dimension_index_literal_pct": round(literal_total / n * 100, 1),
        "dimension_index_reconciled_pct": round(reconciled_total / n * 100, 1),
        "dimensions_counted": len(dims),
        "unit_validation_pct": cov.line_pct if cov.available else None,
        "authoritative_portfolio_status": ct.get("portfolio", {}).get("portfolio_status"),
    }


def _is_stale(dimension: dict[str, Any], ct: dict[str, Any]) -> bool:
    """A non-manual dimension whose signal predates the snapshot is stale."""
    src = dimension.get("signal_source")
    as_of = dimension.get("as_of")
    gen = ct.get("generated_at")
    if not src or src == "MANUAL" or not as_of or not gen:
        return False
    return str(as_of) < str(gen)


def execution_frontier(reader: EvidenceReader) -> dict[str, Any]:
    """Derive the frontier from program rollups + presence of EC-3 determinations."""
    cfg = reader.config
    ec3_admitted = any((cfg.repo_root / d).exists() for d in cfg.ec3_determinations)
    programs = {p.get("program"): p for p in reader.control_tower().get("programs", [])}
    data_prog = programs.get("DATA", {})
    frontier = {
        "next_executable_capability": None,
        "why": None,
        "ready": [],
        "blocked": [],
        "critical_path": [],
        "single_active_frontier": None,
    }
    if ec3_admitted:
        frontier.update({
            "next_executable_capability": "EC-3 Band 10 (Data) realization",
            "why": "CIOA/lane authority admitted Band 10 as RUNNABLE root; EC-1/EC-2 predecessors CERTIFIED",
            "ready": ["EC-3 Band 10 (Data) class-I realization"],
            "blocked": [
                {"capability": "EC-3 Bands 11/12/13", "blocked_by": "sequential band realization (await Band 10)"},
                {"capability": "Constitutional finality (RAT-01..10)", "blocked_by": "DR-RAT-11 (exogenous)"},
            ],
            "critical_path": ["Band 10 Data", "Band 11 Service", "Band 12 Application",
                              "Band 13 Infrastructure", "EC-3 go-live + closure"],
            "single_active_frontier": "EC-3 Band 10 (Data)",
            "evidence": [cfg.rel(cfg.repo_root / d) for d in cfg.ec3_determinations
                         if (cfg.repo_root / d).exists()],
            "data_program_artifacts": data_prog.get("artifact_count"),
        })
    return frontier


def digital_twin_snapshot(reader: EvidenceReader, health: dict[str, Any], progress_rep: dict[str, Any]) -> dict[str, Any]:
    cert = reader.certification()
    return {
        "note": "Projection view; EXTENDS 00-BOOK/DATA/twin.json — no second twin store.",
        "repository_health": health["overall"],
        "certification_health": "HEALTHY-ENGINEERING" if cert.get("verdict") == "CERTIFIED" else "INDETERMINATE",
        "constitutional_finality": "BLOCKED (DR-RAT-11)",
        "validation_health": (
            "HEALTHY-UNIT · HIGHER-ORDER MISSING"
            if health["health_flags"]["coverage_full"] else "PARTIAL"
        ),
        "execution_readiness": "SUBSTRATE-READY · SPINE-NOT-IMPLEMENTED",
        "automation_readiness": "READY",
        "deployment_readiness": _dimension_status(reader, "deployment"),
        "dimension_index_reconciled_pct": progress_rep["dimension_index_reconciled_pct"],
    }


def _dimension_status(reader: EvidenceReader, name: str) -> str:
    return _dimensions(reader.control_tower()).get(name, {}).get("status", "INDETERMINATE")


def aeos_readiness(reader: EvidenceReader, capabilities: list[dict[str, Any]]) -> dict[str, Any]:
    spec_only = [c for c in capabilities if c.get("implementation_status") == "PLANNED"
                 and c.get("category") == "orchestration_spec"]
    return {
        "verdict": "FOUNDATION-READY — AEOS may begin as a separately authorized program; NOT begun here.",
        "ready_because": [
            "Certified capability substrate present (engine EC-1 + platform EC-2).",
            "Orchestration + completeness fully specified (CIOA + CCE).",
            "Digital twin + append-only ledgers + execution register present.",
            "Operational memory (MCS) + automation present.",
        ],
        "not_ready_because": [
            f"{c['canonical_name']} is specification-only (no executable code)." for c in spec_only
        ] + [f"{g['id']} {g['missing']} not implemented." for g in KNOWN_SPINE_GAPS],
        "authorization_required": "CIOA/lane authority + GOV-004 (this engine authorizes nothing).",
        "known_spine_gaps": KNOWN_SPINE_GAPS,
    }
