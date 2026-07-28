"""Tests for the constitutional compliance report and mandatory architectural proof."""

from __future__ import annotations

from engine.kernel.compliance import (
    UNKNOWN_CATEGORIES,
    architectural_proof,
    constitutional_report,
    kernel_source_fingerprint,
    quality_gates,
)


def test_architectural_proof_represents_all_unknown_categories():
    proof = architectural_proof()
    assert proof["passed"] is True
    assert proof["categories_proven"] == len(UNKNOWN_CATEGORIES)
    assert proof["kernel_unchanged"] is True
    assert proof["kernel_source_fingerprint_before"] == proof["kernel_source_fingerprint_after"]
    for record in proof["records"]:
        assert record["ok"] is True
        assert record["discoverable"] is True
        assert record["traceable"] is True


def test_quality_gates_all_pass():
    gates = quality_gates()
    assert gates["passed"] is True
    ids = {g["id"] for g in gates["gates"]}
    assert ids == {
        "no-closed-registries",
        "no-finite-enumeration",
        "no-hardcoded-assumptions",
        "no-domain-provider-technology-earth-civilization-coupling",
        "no-implementation-leakage",
        "unknown-future-compatibility",
    }
    for gate in gates["gates"]:
        assert gate["passed"] is True, gate


def test_constitutional_report_is_compliant_and_deterministic():
    a = constitutional_report()
    b = constitutional_report()
    assert a["passed"] is True
    assert a["verdict"] == "CONSTITUTIONALLY-COMPLIANT"
    assert a["report_hash"] == b["report_hash"]


def test_kernel_source_fingerprint_is_stable():
    assert kernel_source_fingerprint() == kernel_source_fingerprint()
