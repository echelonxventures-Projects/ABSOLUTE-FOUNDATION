"""EC2-TASK-000182 — Platform health registry tests (go-live G1)."""

from __future__ import annotations

from platform.observability.contracts import HealthStatus
from platform.observability.errors import HealthError
from platform.observability.health import (
    HealthCheck,
    HealthRegistry,
    HealthReport,
    HealthResult,
)

import pytest


def _registry() -> HealthRegistry:
    reg = HealthRegistry()
    reg.register(HealthCheck("api-gateway", critical=True, description="edge"))
    reg.register(HealthCheck("event-bus", critical=True))
    reg.register(HealthCheck("cache", critical=False))
    return reg


def test_all_healthy_report_is_healthy():
    reg = _registry()
    report = reg.report(
        {
            "api-gateway": HealthStatus.HEALTHY,
            "event-bus": HealthStatus.HEALTHY,
            "cache": HealthStatus.HEALTHY,
        }
    )
    assert report.healthy
    assert report.status is HealthStatus.HEALTHY


def test_missing_critical_result_is_unhealthy_fail_closed():
    reg = _registry()
    report = reg.report({"api-gateway": HealthStatus.HEALTHY})  # event-bus missing (critical)
    assert report.status is HealthStatus.UNHEALTHY


def test_missing_noncritical_result_is_degraded():
    reg = _registry()
    report = reg.report(
        {"api-gateway": HealthStatus.HEALTHY, "event-bus": HealthStatus.HEALTHY}
    )  # cache missing (non-critical)
    assert report.status is HealthStatus.DEGRADED


def test_endpoint_is_live_and_serializable():
    reg = _registry()
    endpoint = reg.endpoint(
        {
            "api-gateway": HealthStatus.HEALTHY,
            "event-bus": HealthStatus.HEALTHY,
            "cache": HealthStatus.HEALTHY,
        }
    )
    assert endpoint["healthy"] is True
    assert endpoint["status"] == "healthy"
    assert len(endpoint["checks"]) == 3
    assert endpoint["report_id"].startswith("UCOS-HRPT-")


def test_duplicate_registration_fail_closed():
    reg = HealthRegistry()
    reg.register(HealthCheck("x"))
    with pytest.raises(HealthError):
        reg.register(HealthCheck("x"))


def test_result_for_unregistered_check_rejected():
    reg = _registry()
    with pytest.raises(HealthError):
        reg.report({"nonexistent": HealthStatus.HEALTHY})


def test_report_is_deterministic_and_order_independent():
    reg = _registry()
    r1 = reg.report(
        {"cache": HealthStatus.HEALTHY, "api-gateway": HealthStatus.HEALTHY,
         "event-bus": HealthStatus.DEGRADED}
    )
    r2 = reg.report(
        {"api-gateway": HealthStatus.HEALTHY, "event-bus": HealthStatus.DEGRADED,
         "cache": HealthStatus.HEALTHY}
    )
    assert r1.fingerprint() == r2.fingerprint()


def test_health_result_and_check_validation():
    with pytest.raises(HealthError):
        HealthResult.create("", HealthStatus.HEALTHY)
    with pytest.raises(HealthError):
        HealthResult.create("x", "healthy")  # type: ignore[arg-type]
    with pytest.raises(HealthError):
        HealthCheck("")
    with pytest.raises(HealthError):
        HealthRegistry().register("not-a-check")  # type: ignore[arg-type]


def test_health_report_create_direct():
    report = HealthReport.create(
        (HealthResult.create("b", HealthStatus.HEALTHY),
         HealthResult.create("a", HealthStatus.UNHEALTHY))
    )
    assert report.status is HealthStatus.UNHEALTHY
    # results sorted by name
    assert [r.name for r in report.results] == ["a", "b"]
