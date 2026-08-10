"""UCOS-CDG/CAG/CLE — the graph discovers, the authority graph refuses, legality proves.

Each refusal branch is forced. A gate whose refusal path has never executed is a gate
nobody has checked, so every one of "unknown referent", "cycle", "self-attestation" and
each of the nine legality obligations is driven into failure here and asserted to be
reported — not merely asserted to pass on a lawful population.
"""

from __future__ import annotations

import pytest

from engine.constitution import authority, dependency, legality
from engine.constitution.errors import (
    CircularAuthority,
    GraphError,
    IllegalExecution,
    SelfAttestation,
)
from engine.constitution.metadata import ConstitutionalMetadata, Population
from engine.tests.constitution.conftest import declare, population

# --------------------------------------------------------------------------- graph


def test_the_graph_is_discovered_from_declarations(lawful: Population) -> None:
    graph = dependency.discover(lawful)
    assert graph.subjects == ("leaf", "middle", "root")
    assert graph.relation_graph("dependencies")["middle"] == ("root",)
    assert graph.dependents("root") == ("middle",)
    assert graph.closure("leaf", relations=["dependencies"]) == ("middle", "root")


def test_an_unknown_referent_is_refused_not_projected() -> None:
    pop = population(declare("a", dependencies=("ghost",)))
    graph = dependency.build(pop)
    assert [e.target for e in graph.unknown_referents()] == ["ghost"]
    # The unresolved edge must not reach the ordering authority, or "ghost" would be
    # treated as a satisfied prerequisite.
    assert graph.relation_graph("dependencies")["a"] == ()
    with pytest.raises(GraphError) as excinfo:
        graph.require_resolved()
    assert excinfo.value.detail["unknown_referents"][0]["target"] == "ghost"


def test_a_dependency_cycle_is_reported_never_broken() -> None:
    pop = population(
        declare("a", dependencies=("b",)),
        declare("b", dependencies=("a",)),
    )
    graph = dependency.build(pop)
    assert graph.cycles("dependencies") == ("a", "b")
    with pytest.raises(GraphError) as excinfo:
        graph.require_acyclic()
    assert "dependencies" in excinfo.value.detail["cycles"]


def test_relations_are_restricted_to_graph_bearing_facets() -> None:
    with pytest.raises(GraphError):
        dependency.build(population(declare("a")), relations=["replay_rules"])
    with pytest.raises(GraphError):
        dependency.build(population(declare("a"))).relation_graph("nope")


def test_closure_of_an_unknown_subject_fails_closed(lawful: Population) -> None:
    with pytest.raises(GraphError):
        dependency.discover(lawful).closure("nobody")


# --------------------------------------------------------------------------- authority


@pytest.mark.parametrize(
    ("facet", "act"),
    [
        ("certifications", "certify"),
        ("validation_rules", "validate"),
        ("verification_rules", "verify"),
        ("governance_rules", "ratify"),
    ],
)
def test_every_act_of_self_attestation_is_refused(facet: str, act: str) -> None:
    pop = population(declare("solo", **{facet: ("solo",)}))
    report = authority.analyse(pop, dependency.build(pop))
    assert not report.passed
    assert report.measurements["CEL-INV-07"] == 1
    assert act in report.self_attestations[0].detail
    with pytest.raises(SelfAttestation):
        authority.gate(pop, dependency.build(pop))


@pytest.mark.parametrize(
    ("relation", "invariant"),
    [
        ("authorities", "CEL-INV-04"),
        ("certifications", "CEL-INV-05"),
        ("canonical_owner", "CEL-INV-06"),
    ],
)
def test_circularity_in_each_authority_relation_is_refused(relation: str, invariant: str) -> None:
    pop = population(
        declare("a", **{relation: ("b",)}),
        declare("b", **{relation: ("a",)}),
    )
    report = authority.analyse(pop, dependency.build(pop))
    assert report.measurements[invariant] == 2
    assert not report.passed
    with pytest.raises(CircularAuthority):
        authority.gate(pop, dependency.build(pop))


def test_a_lawful_population_closes_its_authority(lawful: Population) -> None:
    report = authority.gate(lawful, dependency.discover(lawful))
    assert report.passed
    assert report.status == "PASS"
    assert authority.authority_closure(dependency.discover(lawful), "leaf") == ("root",)


# --------------------------------------------------------------------------- legality


def test_a_lawful_population_proves_every_obligation(lawful: Population) -> None:
    report = legality.assess(lawful, dependency.discover(lawful))
    assert report.passed
    assert len(report.legal_subjects) == 3
    assert set(report.measurements().values()) == {0}
    assert len(legality.obligation_names()) == 9


@pytest.mark.parametrize(
    ("facet", "obligation"),
    [
        ("dependencies", "dependency_complete"),
        ("governance_rules", "governance_complete"),
        ("authorities", "authority_complete"),
        ("registrations", "registry_complete"),
        ("certifications", "certification_complete"),
        ("verification_rules", "verification_complete"),
        ("traceability_rules", "traceability_complete"),
        ("inputs", "evidence_complete"),
    ],
)
def test_each_obligation_fails_when_its_facet_is_absent(facet: str, obligation: str) -> None:
    pop = population(declare("x", **{facet: ()}))
    verdict = legality.prove(pop.get("x"), dependency.build(pop), pop)
    assert obligation in verdict.unproven
    assert not verdict.legal
    assert verdict.status == "ILLEGAL"


def test_identity_completeness_rejects_a_malformed_identifier() -> None:
    lawful_record = declare("x")
    broken = ConstitutionalMetadata(
        subject="x", universal_id="not-an-id", facets=lawful_record.facets
    )
    broken_pop = population(broken)
    verdict = legality.prove(broken, dependency.build(broken_pop), broken_pop)
    assert "identity_complete" in verdict.unproven


def test_a_dependency_that_is_itself_incomplete_does_not_satisfy_the_closure() -> None:
    """CEL-01 transitively: the whole chain must be complete, not only the first hop."""
    incomplete = declare("weak", governance_rules=())
    pop = population(incomplete, declare("strong", dependencies=("weak",)))
    verdict = legality.prove(pop.get("strong"), dependency.build(pop), pop)
    assert "dependency_complete" in verdict.unproven
    proof = next(p for p in verdict.proofs if p.name == "dependency_complete")
    assert "weak" in proof.detail


def test_a_dangling_referent_fails_the_facet_it_appears_in() -> None:
    pop = population(declare("x", registrations=("nowhere",)))
    verdict = legality.prove(pop.get("x"), dependency.build(pop), pop)
    assert "registry_complete" in verdict.unproven


def test_require_legal_refuses_and_names_the_unproven(lawful: Population) -> None:
    pop = population(declare("x", certifications=("x",)))
    with pytest.raises(IllegalExecution) as excinfo:
        legality.require_legal(pop.get("x"), dependency.build(pop), pop)
    assert "authority_complete" in excinfo.value.detail["unproven"]
    # and the lawful case does not raise
    graph = dependency.discover(lawful)
    assert legality.require_legal(lawful.get("root"), graph, lawful).legal


def test_an_unevaluable_proof_is_an_unproven_proof(lawful: Population) -> None:
    """Fail-closed: a proof that raises must not be reported as satisfied."""

    def explode(record, graph, pop):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")

    obligations = (legality.Obligation("exploding", "always raises", explode),)
    verdict = legality.prove(
        lawful.get("root"), dependency.discover(lawful), lawful, obligations=obligations
    )
    assert not verdict.proofs[0].satisfied
    assert "boom" in verdict.proofs[0].detail


def test_a_verdict_for_an_unassessed_subject_fails_closed(lawful: Population) -> None:
    report = legality.assess(lawful, dependency.discover(lawful))
    with pytest.raises(IllegalExecution):
        report.verdict_for("nobody")
