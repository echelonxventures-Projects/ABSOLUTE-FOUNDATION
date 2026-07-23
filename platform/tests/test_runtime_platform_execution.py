"""EPIC-007 (T7) — Execution engine tests."""

from __future__ import annotations

from platform.runtime_platform.contracts import WorkloadAttestation
from platform.runtime_platform.errors import ExecutionEngineError, ExecutionRequestError
from platform.runtime_platform.execution import ExecutionEngine, ExecutionRequest
from platform.runtime_platform.infrastructure import RuntimeInfrastructure
from platform.runtime_platform.lifecycle import COMPENSATED, FAILED, PENDING, RUNNING, SUCCEEDED
from platform.tests.runtime_platform_helpers import attestation, request

import pytest


def test_request_is_content_addressed():
    r1 = request("w")
    r2 = request("w")
    assert r1.request_id == r2.request_id
    assert r1.request_id.startswith("UCOS-URPX-")


def test_request_validation_fail_closed():
    with pytest.raises(ExecutionRequestError):
        ExecutionRequest(workload_id="", attestation=attestation("x"))
    with pytest.raises(ExecutionRequestError):
        ExecutionRequest(workload_id="w", attestation="bad")  # type: ignore[arg-type]
    with pytest.raises(ExecutionRequestError):
        ExecutionRequest(workload_id="w", attestation=attestation("other"))
    with pytest.raises(ExecutionRequestError):
        ExecutionRequest(workload_id="w", attestation=attestation("w"), priority=True)  # type: ignore[arg-type]
    with pytest.raises(ExecutionRequestError):
        ExecutionRequest(workload_id="w", attestation=attestation("w"), dependencies=("",))
    with pytest.raises(ExecutionRequestError):
        ExecutionRequest(workload_id="w", attestation=attestation("w"), dependencies=("w",))


def test_run_success_trajectory():
    engine = ExecutionEngine()
    record = engine.run(request("w"))
    assert record.trajectory == (PENDING, "scheduled", "placed", RUNNING, SUCCEEDED)
    assert record.succeeded
    assert record.settled
    assert record.execution_id.startswith("UCOS-URPR-")
    assert record.workload_id == "w"


def test_run_failure_trajectory():
    engine = ExecutionEngine()
    record = engine.run(request("w", inject_failure=True))
    assert record.final_state == FAILED
    assert not record.succeeded


def test_run_is_deterministic():
    engine = ExecutionEngine()
    assert engine.run(request("w")).fingerprint() == engine.run(request("w")).fingerprint()


def test_compensate_succeeded_and_failed():
    engine = ExecutionEngine()
    ok = engine.run(request("w"))
    comp = engine.compensate(ok)
    assert comp.final_state == COMPENSATED
    assert comp.trajectory[-1] == COMPENSATED
    failed = engine.run(request("z", inject_failure=True))
    assert engine.compensate(failed).final_state == COMPENSATED


def test_compensate_twice_fails_closed():
    engine = ExecutionEngine()
    comp = engine.compensate(engine.run(request("w")))
    with pytest.raises(ExecutionEngineError):
        engine.compensate(comp)


def test_engine_rejects_bad_inputs():
    with pytest.raises(ExecutionEngineError):
        ExecutionEngine("bad")  # type: ignore[arg-type]
    engine = ExecutionEngine(RuntimeInfrastructure())
    with pytest.raises(ExecutionEngineError):
        engine.run("bad")  # type: ignore[arg-type]
    with pytest.raises(ExecutionEngineError):
        engine.compensate("bad")  # type: ignore[arg-type]


def test_workflow_id_carried_in_record():
    engine = ExecutionEngine()
    record = engine.run(request("w"), workflow_id="wf-9")
    assert record.workflow_id == "wf-9"
    assert record.to_dict()["workflow_id"] == "wf-9"


def test_attestation_object_reuse():
    att = WorkloadAttestation("w", "r", True, True)
    req = ExecutionRequest(workload_id="w", attestation=att)
    assert req.attestation is att
