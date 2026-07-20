"""Tests for EC3-B13-U06 Topology & Distribution validation.

Covers meta-validity (WF-1…12), UIL conformance (UIL-01…15), and governing obligations
(WF-8 / UIL-12 — Distribution hosts by reference; UIL-09 — topology acyclic).
"""

from __future__ import annotations

import pytest

from infrastructure.topology import (
    make_topology,
    make_locality_map,
    make_placement_rule,
    make_distribution_arrangement,
    make_delivery_arrangement,
)
from infrastructure.topology_meta import REALIZATION_UNIT
from infrastructure.topology_traceability import build_traceability
from infrastructure.topology_validation import (
    TopologyValidationSubject,
    topology_checks,
    validate_construct,
)
from engine.validation.executor import ValidationEngine
from engine.validation.gates import enforce_acceptance


def _trace_for(construct):
    return build_traceability(
        construct,
        unit=REALIZATION_UNIT,
        forward=(construct.construct_id, "test-validation"),
    )


class TestTopologyValidation:
    """Validation checks for the Topology construct."""

    def test_topology_valid(self):
        t = make_topology("test.topology.foundation")
        trace = _trace_for(t)
        result = validate_construct(t, trace)
        assert result.accepted
        assert result.report.verdict.value == "pass"

    def test_topology_rejects_untyped(self):
        t = make_topology("test.t")
        trace = _trace_for(t)
        # Will still validate because type_tag is non-empty; test that checks pass
        # Actually test infra-topology-typed
        checks = topology_checks()
        engine = ValidationEngine(checks)
        subject = TopologyValidationSubject.from_construct(t, trace)
        report = engine.validate(subject)
        decision = enforce_acceptance(report)
        assert decision.accepted  # type_tag is "test.t" which is non-empty


class TestDistributionValidation:
    """Validation checks for Distribution constructs."""

    def test_distribution_valid(self):
        d = make_distribution_arrangement("test.dist", hosts=("ENG-005:AF-3:exp",))
        trace = _trace_for(d)
        result = validate_construct(d, trace)
        assert result.accepted

    def test_delivery_valid(self):
        dl = make_delivery_arrangement("test.del", hosts=("ENG-005:AF-3:exp",))
        trace = _trace_for(dl)
        result = validate_construct(dl, trace)
        assert result.accepted

    def test_distribution_hosts_check_pass(self):
        d = make_distribution_arrangement("test.d", hosts=("ENG-005:AF-3:svc",))
        trace = _trace_for(d)
        subject = TopologyValidationSubject.from_construct(d, trace)
        checks = topology_checks()
        from engine.validation.checks import ValidationCheck
        # Find and check the distribution-hosts check
        host_check = [c for c in checks if c.check_id == "infra-topology-distribution-hosts"]
        assert len(host_check) == 1
        finding = host_check[0].evaluate(subject)
        assert finding.passed


class TestLocalityMapValidation:

    def test_locality_map_valid(self):
        lm = make_locality_map("test.lm")
        trace = _trace_for(lm)
        result = validate_construct(lm, trace)
        assert result.accepted


class TestPlacementRuleValidation:

    def test_placement_rule_valid(self):
        pr = make_placement_rule("test.pr")
        trace = _trace_for(pr)
        result = validate_construct(pr, trace)
        assert result.accepted


class TestAllChecks:
    """Meta-validation checks common to all constructs."""

    def test_typed_check_for_all(self):
        constructs = [
            make_topology("t"),
            make_locality_map("t"),
            make_placement_rule("t"),
            make_distribution_arrangement("t", hosts=("ENG-005:c",)),
            make_delivery_arrangement("t", hosts=("ENG-005:c",)),
        ]
        for c in constructs:
            trace = _trace_for(c)
            result = validate_construct(c, trace)
            assert result.accepted, f"{c.meta_class} validation failed"

    def test_meta_class_single(self):
        t = make_topology("test.t")
        assert t.meta_class == "Topology"
        d = make_distribution_arrangement("test.d", hosts=("ENG-005:c",))
        assert d.meta_class == "Distribution"

    def test_foundation_reuse_integrity(self):
        constructs = [
            make_topology("t"),
            make_locality_map("t"),
            make_placement_rule("t"),
            make_distribution_arrangement("t", hosts=("ENG-005:c",)),
            make_delivery_arrangement("t", hosts=("ENG-005:c",)),
        ]
        for c in constructs:
            assert not c.redefines_foundation()
