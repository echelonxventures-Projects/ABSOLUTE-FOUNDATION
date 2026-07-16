"""EC2-TASK-000184 — Platform audit trail tests (acceptance P9 / PC-16)."""

from __future__ import annotations

from platform.observability.audit import GENESIS_HASH, AuditEvent, AuditTrail
from platform.observability.errors import AuditError

import pytest


def test_trail_is_append_only_and_chained():
    trail = AuditTrail()
    e0 = trail.record("deploy", "operator", "unit-1")
    e1 = trail.record("rollback", "operator", "unit-1")
    assert e0.sequence == 0 and e1.sequence == 1
    assert e0.prev_hash == GENESIS_HASH
    assert e1.prev_hash == e0.event_hash
    assert trail.head_hash == e1.event_hash
    assert len(trail) == 2


def test_chain_verifies_intact():
    trail = AuditTrail()
    for i in range(5):
        trail.record("action", "actor", f"subject-{i}", detail={"i": i})
    assert trail.verify() is True


def test_event_is_content_addressed():
    e = AuditEvent.create("a", "actor", "s", 0, GENESIS_HASH)
    assert e.event_id.startswith("UCOS-AUDIT-")
    assert e.event_hash == AuditEvent.create("a", "actor", "s", 0, GENESIS_HASH).event_hash


def test_event_validation_fail_closed():
    with pytest.raises(AuditError):
        AuditEvent.create("", "actor", "s", 0, GENESIS_HASH)
    with pytest.raises(AuditError):
        AuditEvent.create("a", "", "s", 0, GENESIS_HASH)
    with pytest.raises(AuditError):
        AuditEvent.create("a", "actor", "s", -1, GENESIS_HASH)
    with pytest.raises(AuditError):
        AuditEvent.create("a", "actor", "s", 0, "short-hash")


def test_events_for_filters_by_action():
    trail = AuditTrail()
    trail.record("login", "u", "s")
    trail.record("logout", "u", "s")
    trail.record("login", "u", "s")
    assert len(trail.events_for("login")) == 2


def test_empty_trail_head_is_genesis_and_verifies():
    trail = AuditTrail()
    assert trail.head_hash == GENESIS_HASH
    assert trail.verify() is True


def test_trail_fingerprint_deterministic():
    a = AuditTrail()
    b = AuditTrail()
    for trail in (a, b):
        trail.record("x", "u", "s", detail={"k": "v"})
        trail.record("y", "u", "s")
    assert a.fingerprint() == b.fingerprint()
    assert a.to_dict()["event_count"] == 2


def test_verify_detects_tampering():
    trail = AuditTrail()
    trail.record("a", "u", "s")
    trail.record("b", "u", "s")
    # Tamper with an internal event by replacing it with a divergent-hash event.
    tampered = AuditEvent.create("MUTATED", "u", "s", 0, GENESIS_HASH)
    trail._events[0] = tampered  # noqa: SLF001 — deliberate tamper to prove detection
    assert trail.verify() is False
