"""Unit tests for engine.graph.projections — the ten mission graphs."""

from __future__ import annotations

import pytest

from engine.graph.errors import ProjectionError
from engine.graph.model import KIND_CATEGORY, KIND_CERT_DOMAIN, KIND_PROGRAM, KIND_SIGNAL
from engine.graph.projections import (
    PROJECTION_NAMES,
    CapabilityGraph,
    CertificationGraph,
    DependencyGraph,
    EvidenceGraph,
    ImpactGraph,
    ImplementationGraph,
    OntologyGraph,
    RequirementGraph,
    TraceabilityGraph,
    ValidationGraph,
    build_projection,
)


def test_projection_names_are_ten():
    assert len(PROJECTION_NAMES) == 10
    assert PROJECTION_NAMES[0] == "ontology"
    assert PROJECTION_NAMES[-1] == "impact"


def test_build_projection_unknown_raises(core):
    with pytest.raises(ProjectionError):
        build_projection("nope", core)


# --- 1. Ontology ---------------------------------------------------------------
def test_ontology_graph(core):
    onto = OntologyGraph(core)
    assert "CON" in onto.categories()
    assert "ARCH" in onto.programs()
    anchor = onto.anchor_of("UCOS-ARCH-000001")
    assert anchor["volume"] == "VOL-003"
    assert anchor["category"] == "ARCH"
    assert anchor["program"] == "ARCH"
    # synthetic anchor nodes exist
    assert onto.graph.nodes_of_kind(KIND_CATEGORY)
    assert onto.graph.nodes_of_kind(KIND_PROGRAM)
    # a volume node has no artifact anchor
    assert onto.anchor_of("VOL-003") == {}
    assert onto.summary()["projection"] == "ontology"


# --- 2. Capability -------------------------------------------------------------
def test_capability_graph(core):
    cap = CapabilityGraph(core)
    assert cap.consumes("UCOS-SVC-000001") == ("UCOS-REG-000001",)
    assert cap.consumers_of("UCOS-REG-000001") == ("UCOS-SVC-000001",)
    assert "UCOS-ARCH-000001" in cap.required_by("UCOS-CON-000001")


# --- 3. Dependency -------------------------------------------------------------
def test_dependency_graph(core):
    dep = DependencyGraph(core)
    assert dep.dependencies_of("UCOS-IMP-000001") == ("UCOS-ARCH-000001",)
    assert dep.dependents_of("UCOS-ARCH-000001") == ("UCOS-IMP-000001",)
    assert set(dep.transitive_dependencies("UCOS-IMP-000001")) == {
        "UCOS-ARCH-000001",
        "UCOS-CON-000001",
    }
    assert dep.is_acyclic() is True
    order = dep.topological_order()
    # standard topological order: every Depends-On edge points forward
    # (IMP Depends-On ARCH Depends-On CON  =>  IMP before ARCH before CON)
    assert order.index("UCOS-IMP-000001") < order.index("UCOS-ARCH-000001")
    assert order.index("UCOS-ARCH-000001") < order.index("UCOS-CON-000001")
    assert dep.find_cycle() == ()


# --- 4. Traceability -----------------------------------------------------------
def test_traceability_graph(core):
    trace = TraceabilityGraph(core)
    # IMP implements + traces-to reach ARCH and CON
    assert "UCOS-ARCH-000001" in trace.trace_forward("UCOS-IMP-000001")
    assert "UCOS-IMP-000001" in trace.trace_backward("UCOS-ARCH-000001")
    stages = trace.stages_of("UCOS-ARCH-000001")
    assert stages["requirement"] == ("UCOS-CON-000001",)


# --- 5. Evidence ---------------------------------------------------------------
def test_evidence_graph(core, sample_signals):
    ev = EvidenceGraph(core, tuple(sample_signals))
    signals = ev.evidence_for("UCOS-IMP-000001")
    assert {n.attributes["dimension"] for n in signals} == {"build", "unit_testing"}
    assert ev.by_dimension("security")[0].node_id == "USIG-000000003"
    assert "build" in ev.dimensions()
    # signal nodes are present as a distinct kind
    assert ev.graph.nodes_of_kind(KIND_SIGNAL)


# --- 6. Requirement ------------------------------------------------------------
def test_requirement_graph(core):
    req = RequirementGraph(core)
    # ARCH declares CON-000001 as a requirement
    assert "UCOS-CON-000001" in req.requirements_of("UCOS-ARCH-000001")
    assert "UCOS-ARCH-000001" in req.satisfied_by("UCOS-CON-000001")


# --- 7. Implementation ---------------------------------------------------------
def test_implementation_graph(core):
    impl = ImplementationGraph(core)
    assert impl.implements("UCOS-IMP-000001") == ("UCOS-ARCH-000001",)
    assert "UCOS-IMP-000001" in impl.implemented_by("UCOS-ARCH-000001")


# --- 8. Validation -------------------------------------------------------------
def test_validation_graph(core, sample_signals, sample_twin):
    val = ValidationGraph(core, tuple(sample_signals), sample_twin)
    sigs = val.validation_signals("UCOS-IMP-000001")
    assert {n.attributes["dimension"] for n in sigs} == {"build", "unit_testing"}
    assert val.twin_state("build")["status"] == "IMPLEMENTED"
    assert val.twin_state("nonexistent") == {}
    assert "security" in val.dimensions()


# --- 9. Certification ----------------------------------------------------------
def test_certification_graph(core, sample_certification):
    cert = CertificationGraph(core, sample_certification)
    assert cert.verdict() == "CERTIFIED"
    assert cert.domains() == ("identity", "knowledge_graph")
    assert cert.is_certified() is True
    assert cert.graph.nodes_of_kind(KIND_CERT_DOMAIN)
    # certified artifacts: CON (FROZEN) and REG (CERTIFIED)
    assert set(cert.certified_artifacts()) == {"UCOS-CON-000001", "UCOS-REG-000001"}


def test_certification_graph_empty_record(core):
    cert = CertificationGraph(core, {})
    assert cert.verdict() == "UNKNOWN"
    assert cert.is_certified() is False
    assert cert.domains() == ()


# --- 10. Impact ----------------------------------------------------------------
def test_impact_graph(core):
    impact = ImpactGraph(core)
    # CON is depended on (transitively) by ARCH and IMP -> impact reaches both
    impacted = impact.impact_of("UCOS-CON-000001")
    assert "UCOS-ARCH-000001" in impacted
    assert "UCOS-IMP-000001" in impacted
    assert impact.blast_radius("UCOS-CON-000001") >= 2
    # upstream of IMP reaches its transitive dependencies
    assert "UCOS-CON-000001" in impact.upstream_of("UCOS-IMP-000001")
    # unknown node -> empty
    assert impact.impact_of("UCOS-NOPE-000000") == ()
    assert impact.upstream_of("UCOS-NOPE-000000") == ()


def test_build_projection_all_names(core, sample_signals, sample_certification, sample_twin):
    for name in PROJECTION_NAMES:
        proj = build_projection(
            name,
            core,
            signals=tuple(sample_signals),
            certification=sample_certification,
            twin=sample_twin,
        )
        assert proj.name == name
        assert proj.summary()["nodes"] >= 0
