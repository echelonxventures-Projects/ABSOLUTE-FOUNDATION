"""UCOS-CEL-0001 — the law is data, and the metadata mandate refuses incompleteness.

Two properties are load-bearing for everything else in the package and are asserted here
rather than assumed: that extending the law is a data edit (so no function branches on a
clause), and that an incomplete artifact is refused all four faculties at once rather than
being quietly executable-but-not-certifiable.
"""

from __future__ import annotations

import pytest

from engine.constitution import law, metadata
from engine.constitution.errors import ConstitutionalError, MetadataIncomplete
from engine.tests.constitution.conftest import declare


def test_the_law_is_deterministic_and_addressable() -> None:
    assert law.digest() == law.digest()
    assert law.clause("CEL-01").realized_by == "UCOS-CDG-000001"
    assert law.invariant("CEL-INV-07").clause_id == "CEL-05"
    assert set(law.blocking_invariant_ids()) == {i.invariant_id for i in law.EXECUTION_INVARIANTS}


def test_every_acceptance_criterion_names_a_declared_invariant() -> None:
    """A criterion measured by nothing is prose, which the law does not admit."""
    declared = {i.invariant_id for i in law.EXECUTION_INVARIANTS}
    for criterion in law.ACCEPTANCE_CRITERIA:
        assert criterion.invariant_id in declared, criterion.criterion_id


def test_every_clause_names_the_engine_that_realizes_it() -> None:
    for clause in law.EXECUTION_CLAUSES:
        assert clause.realized_by, clause.clause_id
        assert clause.refuses, clause.clause_id


def test_unknown_clause_and_invariant_fail_closed() -> None:
    with pytest.raises(ConstitutionalError):
        law.clause("CEL-99")
    with pytest.raises(ConstitutionalError):
        law.invariant("CEL-INV-99")


def test_the_mandate_declares_fifteen_facets() -> None:
    assert len(metadata.MANDATED_FACETS) == 15
    assert metadata.facet("canonical_owner").singular
    assert "canonical_owner" in metadata.graph_bearing_facets()
    assert "replay_rules" not in metadata.graph_bearing_facets()


def test_an_incomplete_artifact_loses_all_four_faculties_together() -> None:
    partial = metadata.ConstitutionalMetadata.declare(
        "partial", universal_id="", canonical_owner=("ext:owner",)
    )
    assert not partial.complete
    assert not partial.executable
    assert not partial.governable
    assert not partial.certifiable
    assert not partial.registerable
    assert "dependencies" in partial.missing_facets()

    with pytest.raises(MetadataIncomplete) as excinfo:
        metadata.require_complete(partial)
    assert "dependencies" in excinfo.value.detail["missing_facets"]


def test_two_owners_is_as_incomplete_as_none() -> None:
    """NL-04's shape, restated for CEL-09: the question must have exactly one answer."""
    two = declare("two", canonical_owner=("ext:a", "ext:b"))
    assert "canonical_owner" in two.missing_facets()
    assert two.canonical_owner == ""


def test_an_unknown_facet_is_refused_rather_than_ignored() -> None:
    """A typo'd facet would otherwise read as a silently absent obligation."""
    with pytest.raises(ConstitutionalError) as excinfo:
        metadata.ConstitutionalMetadata.declare("x", universal_id="y", dependancies=("a",))
    assert excinfo.value.detail["unknown"] == ["dependancies"]


def test_external_references_terminate_rather_than_dangle() -> None:
    record = declare("terminal")
    assert record.referents("authorities") == ()
    assert record.external_references("authorities") == ("ext:UCOS-DETERMINATION-TEST",)
    assert "authorities" in record.terminal_facets()
    assert metadata.is_external("ext:anything")
    assert not metadata.is_external("subject.key")


def test_a_population_refuses_two_declarations_of_one_subject() -> None:
    with pytest.raises(ConstitutionalError) as excinfo:
        metadata.Population.of([declare("same"), declare("same")])
    assert excinfo.value.detail["subject"] == "same"


def test_a_population_is_immutable_and_with_records_returns_a_new_one() -> None:
    base = metadata.Population.of([declare("a")])
    grown = base.with_records([declare("b")])
    assert base.subjects() == ("a",)
    assert grown.subjects() == ("a", "b")
    assert base.digest() != grown.digest()


def test_declarations_normalize_deterministically() -> None:
    """Duplicate and whitespace-only entries collapse, so a digest is stable."""
    messy = declare("messy", constraints=("  a  ", "a", "", "b"))
    assert messy.entries("constraints") == ("a", "b")
    assert messy.digest() == declare("messy", constraints=("a", "b")).digest()
