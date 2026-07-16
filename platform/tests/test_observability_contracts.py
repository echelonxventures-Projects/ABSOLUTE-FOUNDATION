"""EC2-TASK-000178 — Observability contract-surface + vocabulary tests."""

from __future__ import annotations

from platform.foundation.contracts import Contract
from platform.observability.contracts import (
    OBSERVABILITY_CONTRACT_VERSION,
    OBSERVABILITY_CONTRACTS,
    HealthStatus,
    MetricKind,
    Severity,
    all_metric_kinds,
    all_severities,
    default_observability_contracts,
    observability_contract,
)
from platform.observability.errors import ObservabilityContractError

import pytest


def test_six_published_contracts_are_versioned():
    assert len(OBSERVABILITY_CONTRACTS) == 6
    assert {c.version for c in OBSERVABILITY_CONTRACTS} == {OBSERVABILITY_CONTRACT_VERSION}
    names = {c.name for c in OBSERVABILITY_CONTRACTS}
    assert "observability.metrics.registry" in names
    assert "observability.audit.trail" in names


def test_default_contracts_are_contract_objects():
    contracts = default_observability_contracts()
    assert len(contracts) == 6
    assert all(isinstance(c, Contract) for c in contracts)


def test_observability_contract_rejects_empty_name():
    with pytest.raises(ObservabilityContractError):
        observability_contract("")


def test_severity_ordering_and_threshold():
    assert Severity.CRITICAL.rank > Severity.ERROR.rank > Severity.WARNING.rank
    assert Severity.ERROR.at_least(Severity.WARNING)
    assert not Severity.INFO.at_least(Severity.WARNING)
    assert all_severities()[0] is Severity.DEBUG
    assert all_severities()[-1] is Severity.CRITICAL


def test_metric_kinds():
    assert set(all_metric_kinds()) == {MetricKind.COUNTER, MetricKind.GAUGE, MetricKind.HISTOGRAM}


def test_health_status_worst_is_fail_closed():
    assert HealthStatus.worst([]) is HealthStatus.HEALTHY
    mixed = [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    assert HealthStatus.worst(mixed) is HealthStatus.DEGRADED
    assert (
        HealthStatus.worst([HealthStatus.DEGRADED, HealthStatus.UNHEALTHY])
        is HealthStatus.UNHEALTHY
    )


def test_health_status_worst_rejects_non_status():
    with pytest.raises(ObservabilityContractError):
        HealthStatus.worst(["healthy"])
