"""EC2-TASK-000185 — Observability service tests.

Covers the epic's headline acceptance criteria: structured telemetry on 100% of
governed actions (P9), health endpoints live (G1), alerts fire on defined conditions
(G8), append-only audit (P9/PC-16), deterministic evidence, and EC-1 integrity
preservation (P10).
"""

from __future__ import annotations

from platform.foundation.bootstrap import bootstrap_platform
from platform.foundation.events import EventBus
from platform.observability.alerting import AlertRule
from platform.observability.contracts import HealthStatus, Severity
from platform.observability.errors import ObservabilityServiceError
from platform.observability.health import HealthCheck
from platform.observability.metrics import MetricRegistry
from platform.observability.service import (
    GOVERNED_ACTION_METRIC,
    OBSERVABILITY_BOOTSTRAP_EVENT,
    ObservabilityService,
    bootstrap_observability,
    build_observability_service,
)

import pytest


def test_telemetry_covers_100_percent_of_governed_actions():
    bus = EventBus()
    service = build_observability_service(events=bus)
    # Every published governed action must produce metric + log + audit records.
    for i in range(10):
        bus.publish("generation.requested", source="platform.api", subject=f"req-{i}")
    assert service.governed_action_count == 10
    assert service.observed_fraction() == 1.0
    assert len(service.logs) == 10
    assert len(service.audit) == 10
    assert service.metrics.value_of(
        GOVERNED_ACTION_METRIC, event_type="generation.requested"
    ) == 10.0
    assert service.audit.verify() is True


def test_unbound_service_reports_zero_fraction():
    service = build_observability_service()
    assert service.observed_fraction() == 0.0


def test_bind_is_idempotent():
    bus = EventBus()
    service = build_observability_service(events=bus)
    service.bind(bus)  # second bind must not double-subscribe
    bus.publish("e", source="s", subject="x")
    assert service.governed_action_count == 1


def test_health_endpoint_live_through_service():
    service = build_observability_service()
    service.register_health_check(HealthCheck("api-gateway", critical=True))
    endpoint = service.health_endpoint({"api-gateway": HealthStatus.HEALTHY})
    assert endpoint["healthy"] is True


def test_alert_evaluation_through_service():
    service = build_observability_service()
    service.register_alert_rule(
        AlertRule("saturation", lambda o: o.get("cpu", 0) > 0.9, Severity.CRITICAL)
    )
    fired = service.evaluate_alerts({"cpu": 0.99})
    assert len(fired) == 1 and fired[0].severity is Severity.CRITICAL


def test_evidence_is_deterministic_across_identical_runs():
    def run() -> str:
        bus = EventBus()
        svc = build_observability_service(events=bus)
        bus.publish("a", source="s", subject="1")
        bus.publish("b", source="s", subject="2")
        return svc.evidence().fingerprint()

    assert run() == run()


def test_evidence_reports_audit_chain_integrity():
    bus = EventBus()
    service = build_observability_service(events=bus)
    bus.publish("x", source="s", subject="1")
    evidence = service.evidence()
    assert evidence.audit_chain_intact is True
    assert evidence.governed_action_count == 1
    assert evidence.evidence_id.startswith("UCOS-OBEV-")


def test_service_rejects_invalid_components():
    with pytest.raises(ObservabilityServiceError):
        ObservabilityService(
            metrics="nope",  # type: ignore[arg-type]
            logs=None,  # type: ignore[arg-type]
            traces=None,  # type: ignore[arg-type]
            health=None,  # type: ignore[arg-type]
            alerts=None,  # type: ignore[arg-type]
            audit=None,  # type: ignore[arg-type]
        )


def test_bind_requires_event_bus():
    service = build_observability_service()
    with pytest.raises(ObservabilityServiceError):
        service.bind("not-a-bus")  # type: ignore[arg-type]


def test_bootstrap_binds_publishes_contracts_and_emits_event():
    context = bootstrap_platform()
    service = bootstrap_observability(context)
    # Six observability contracts published into the foundation service registry.
    assert "observability.metrics.registry" in context.services
    assert "observability.audit.trail" in context.services
    # A composition event was emitted and observed by the now-bound service.
    assert len(context.events.events_of(OBSERVABILITY_BOOTSTRAP_EVENT)) == 1
    assert service.governed_action_count >= 1
    # Subsequent governed actions are captured at 100%.
    context.events.publish("generation.completed", source="platform.api", subject="req-1")
    assert service.observed_fraction() == 1.0


def test_bootstrap_is_idempotent_on_contracts():
    context = bootstrap_platform()
    bootstrap_observability(context)
    before = len(context.services)
    # Re-binding to the same context must not duplicate contract registrations.
    bootstrap_observability(context)
    assert len(context.services) == before


def test_ec1_integrity_preserved_metric_mirror_is_additive():
    # The observability metric registry mirrors into EC-1 telemetry without
    # modifying EC-1: the reused snapshot API keeps working (P10).
    from engine.foundation.obs import telemetry

    telemetry.reset_metrics()
    reg = MetricRegistry(mirror_to_ec1=True)
    reg.counter("platform.governed_actions", 1.0, event_type="t")
    assert "counters" in telemetry.metrics_snapshot()
    telemetry.reset_metrics()
