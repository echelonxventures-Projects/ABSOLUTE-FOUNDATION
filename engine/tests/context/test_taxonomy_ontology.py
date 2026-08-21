"""UCXI-000001 Parts 02/03 — taxonomy and ontology tests.

The properties asserted here are the ones the rest of the layer relies on: the fifteen
universal kinds are classified and specified, unknown values fail loudly rather than
defaulting, and both structures are *open* — a future context type is admitted as data
and immediately behaves like any other kind.
"""

from __future__ import annotations

import pytest

from engine.context.errors import LifecycleTransitionError, OntologyError, TaxonomyError
from engine.context.ontology import (
    UNIVERSAL_DIMENSIONS,
    UNIVERSAL_ONTOLOGY,
    UNKNOWN,
    ContextOntology,
    DimensionSpec,
    RelationRule,
)
from engine.context.taxonomy import (
    ROOT_TAXON,
    UNIVERSAL_KINDS,
    UNIVERSAL_TAXONOMY,
    ContextAuthority,
    ContextKind,
    ContextLifecycle,
    ContextRelation,
    ContextTaxon,
    ContextTaxonomy,
)
from engine.tests.context.conftest import future_dimensions, future_taxon

# --------------------------------------------------------------------------- kinds


def test_sixteen_universal_kinds_are_declared() -> None:
    assert len(UNIVERSAL_KINDS) == 16
    assert ContextKind.EXISTENCE.value == "existence"
    assert "cultural" in ContextKind.values()
    # The sixteenth (ADR-0005). Measurement is universal because every assertion is
    # made in some system of measurement; leaving it implicit assumes one.
    assert "measurement" in ContextKind.values()


def test_unknown_kind_fails_loudly() -> None:
    with pytest.raises(TaxonomyError):
        ContextKind.coerce("astral")


def test_kind_coercion_is_idempotent() -> None:
    assert ContextKind.coerce(ContextKind.TEMPORAL) is ContextKind.TEMPORAL
    assert ContextKind.coerce("temporal") is ContextKind.TEMPORAL


# --------------------------------------------------------------------- authority


def test_authority_precedence_is_total_and_ordered() -> None:
    ranks = [authority.rank for authority in ContextAuthority]
    assert ranks == sorted(ranks)
    assert len(set(ranks)) == len(ranks)
    assert ContextAuthority.CONSTITUTIONAL.outranks(ContextAuthority.OBSERVED)
    assert not ContextAuthority.INFERRED.outranks(ContextAuthority.OPERATIONAL)


def test_unknown_authority_fails_loudly() -> None:
    with pytest.raises(TaxonomyError):
        ContextAuthority.coerce("vibes")


# --------------------------------------------------------------------- lifecycle


def test_lifecycle_transitions_are_enforced() -> None:
    assert ContextLifecycle.DECLARED.can_transition_to(ContextLifecycle.REGISTERED)
    assert not ContextLifecycle.DECLARED.can_transition_to(ContextLifecycle.ACTIVE)
    with pytest.raises(LifecycleTransitionError):
        ContextLifecycle.DECLARED.require_transition(ContextLifecycle.ACTIVE)
    ContextLifecycle.REGISTERED.require_transition(ContextLifecycle.RESOLVED)


def test_lifecycle_active_and_terminal_flags() -> None:
    assert ContextLifecycle.ACTIVE.is_active
    assert not ContextLifecycle.ARCHIVED.is_active
    assert ContextLifecycle.ARCHIVED.is_terminal
    assert not ContextLifecycle.ACTIVE.is_terminal


def test_unknown_lifecycle_fails_loudly() -> None:
    with pytest.raises(TaxonomyError):
        ContextLifecycle.coerce("mothballed")


# ---------------------------------------------------------------------- relations


def test_relation_classes() -> None:
    assert ContextRelation.EQUIVALENT_TO.is_symmetric
    assert not ContextRelation.CONTAINS.is_symmetric
    assert ContextRelation.CONTAINS.is_hierarchical
    assert not ContextRelation.FEDERATES.is_hierarchical
    with pytest.raises(TaxonomyError):
        ContextRelation.coerce("vibes-with")


# ---------------------------------------------------------------------- taxonomy


def test_universal_taxonomy_shape() -> None:
    assert len(UNIVERSAL_TAXONOMY) == 17  # the root plus sixteen universal taxa
    assert UNIVERSAL_TAXONOMY.has(ROOT_TAXON)
    assert len(UNIVERSAL_TAXONOMY.universal_kinds()) == 16
    assert UNIVERSAL_TAXONOMY.future_kinds() == ()
    assert UNIVERSAL_TAXONOMY.depth("CTX-TEMPORAL") == 1
    assert UNIVERSAL_TAXONOMY.ancestors("CTX-TEMPORAL") == (ROOT_TAXON,)
    assert len(UNIVERSAL_TAXONOMY.descendants(ROOT_TAXON)) == 16
    assert UNIVERSAL_TAXONOMY.children(ROOT_TAXON)


def test_taxon_lookup_by_kind_and_universality() -> None:
    taxon = UNIVERSAL_TAXONOMY.taxon_for_kind(ContextKind.SECURITY)
    assert taxon.taxon_id == "CTX-SECURITY"
    assert UNIVERSAL_TAXONOMY.is_universal("security")
    assert not UNIVERSAL_TAXONOMY.is_universal("quantum")
    with pytest.raises(TaxonomyError):
        UNIVERSAL_TAXONOMY.taxon_for_kind("quantum")
    with pytest.raises(TaxonomyError):
        UNIVERSAL_TAXONOMY.taxon("CTX-NOPE")


def test_taxonomy_admits_a_future_context_type() -> None:
    extended = UNIVERSAL_TAXONOMY.extend(future_taxon())
    assert len(extended) == 18
    assert extended.future_kinds() == ("quantum",)
    assert extended.is_universal("quantum") is False
    assert extended.taxon_for_kind("quantum").title == "Quantum Context"
    # extension is non-mutating: the universal instance is untouched
    assert len(UNIVERSAL_TAXONOMY) == 17


def test_taxonomy_extension_is_bounded() -> None:
    with pytest.raises(TaxonomyError):  # duplicate taxon
        UNIVERSAL_TAXONOMY.extend(
            ContextTaxon(taxon_id="CTX-TEMPORAL", kind="x", title="X", parent=ROOT_TAXON)
        )
    with pytest.raises(TaxonomyError):  # universality cannot be granted
        UNIVERSAL_TAXONOMY.extend(
            ContextTaxon(taxon_id="CTX-X", kind="x", title="X", parent=ROOT_TAXON, universal=True)
        )
    with pytest.raises(TaxonomyError):  # a second root
        UNIVERSAL_TAXONOMY.extend(ContextTaxon(taxon_id="CTX-X", kind="x", title="X"))
    with pytest.raises(TaxonomyError):  # unknown parent
        UNIVERSAL_TAXONOMY.extend(
            ContextTaxon(taxon_id="CTX-X", kind="x", title="X", parent="CTX-NOPE")
        )
    with pytest.raises(TaxonomyError):  # kind already claimed
        UNIVERSAL_TAXONOMY.extend(
            ContextTaxon(taxon_id="CTX-X", kind="temporal", title="X", parent=ROOT_TAXON)
        )


def test_taxon_requires_non_empty_fields() -> None:
    with pytest.raises(TaxonomyError):
        ContextTaxon(taxon_id="", kind="x", title="X", parent=ROOT_TAXON)
    with pytest.raises(TaxonomyError):
        ContextTaxon(taxon_id="CTX-X", kind="x", title="X", parent="")


def test_taxonomy_refuses_a_cycle_and_a_detached_branch() -> None:
    taxa = (
        ContextTaxon(taxon_id=ROOT_TAXON, kind="context", title="root", universal=True),
        ContextTaxon(taxon_id="A", kind="a", title="A", parent="B"),
        ContextTaxon(taxon_id="B", kind="b", title="B", parent="A"),
    )
    with pytest.raises(TaxonomyError):
        ContextTaxonomy(taxa)


def test_taxonomy_serialises_deterministically() -> None:
    first = UNIVERSAL_TAXONOMY.to_dict()
    assert first == UNIVERSAL_TAXONOMY.to_dict()
    assert first["root"] == ROOT_TAXON
    assert len(first["taxa"]) == 17


# ---------------------------------------------------------------------- ontology


def test_every_universal_kind_has_a_declared_shape() -> None:
    for kind in UNIVERSAL_KINDS:
        specs = UNIVERSAL_ONTOLOGY.dimensions_for(kind)
        assert specs
        assert UNIVERSAL_ONTOLOGY.required_for(kind)
        assert any(spec.name == "note" and not spec.required for spec in specs)
    assert set(UNIVERSAL_ONTOLOGY.kinds()) == set(UNIVERSAL_DIMENSIONS)


def test_every_relation_has_a_rule() -> None:
    rules = {rule.relation for rule in UNIVERSAL_ONTOLOGY.rules()}
    assert rules == set(ContextRelation)


def test_value_checks_report_completeness_closure_and_type() -> None:
    findings = UNIVERSAL_ONTOLOGY.check_values(
        "temporal", {"reference_frame": "utc", "ordering": "causal"}
    )
    assert any("resolution" in finding for finding in findings)

    findings = UNIVERSAL_ONTOLOGY.check_values(
        "temporal",
        {"reference_frame": "utc", "ordering": "causal", "resolution": "s", "extra": 1},
    )
    assert any("not declared" in finding for finding in findings)

    findings = UNIVERSAL_ONTOLOGY.check_values(
        "temporal", {"reference_frame": 7, "ordering": "causal", "resolution": "s"}
    )
    assert any("expects string" in finding for finding in findings)


def test_unknown_sentinel_satisfies_any_dimension() -> None:
    findings = UNIVERSAL_ONTOLOGY.check_values(
        "security",
        {"classification": UNKNOWN, "trust_boundary": UNKNOWN, "controls": UNKNOWN},
    )
    assert findings == []


def test_require_values_is_fail_closed() -> None:
    with pytest.raises(OntologyError):
        UNIVERSAL_ONTOLOGY.require_values("temporal", {}, at="subject")
    with pytest.raises(OntologyError):
        UNIVERSAL_ONTOLOGY.dimensions_for("quantum")
    assert UNIVERSAL_ONTOLOGY.check_values("quantum", {}) == [
        "quantum: kind 'quantum' has no declared ontological shape"
    ]


def test_relation_rules_constrain_source_kinds() -> None:
    assert UNIVERSAL_ONTOLOGY.check_relation(ContextRelation.OBSERVES, "observer", "temporal") == []
    findings = UNIVERSAL_ONTOLOGY.check_relation(ContextRelation.OBSERVES, "temporal", "temporal")
    assert findings
    with pytest.raises(OntologyError):
        UNIVERSAL_ONTOLOGY.require_relation(ContextRelation.CONSTRAINS, "temporal", "spatial")
    UNIVERSAL_ONTOLOGY.require_relation(ContextRelation.CONSTRAINS, "governance", "spatial")


def test_spec_lookup_and_number_is_not_boolean() -> None:
    spec = UNIVERSAL_ONTOLOGY.spec_for("temporal", "resolution")
    assert spec is not None and spec.required
    assert UNIVERSAL_ONTOLOGY.spec_for("temporal", "nope") is None
    number = DimensionSpec(name="n", value_type="number", required=True)
    assert number.accepts(3) and number.accepts(1.5)
    assert not number.accepts(True)


def test_ontology_admits_a_future_kind() -> None:
    extended = UNIVERSAL_ONTOLOGY.extend("quantum", future_dimensions())
    assert extended.specifies("quantum")
    assert extended.required_for("quantum") == ("basis",)
    assert extended.check_values("quantum", {"basis": "z"}) == []
    assert not UNIVERSAL_ONTOLOGY.specifies("quantum")  # non-mutating
    with pytest.raises(OntologyError):
        extended.extend("quantum", future_dimensions())
    with pytest.raises(OntologyError):
        UNIVERSAL_ONTOLOGY.extend("quantum", ())


def test_ontology_construction_refuses_bad_declarations() -> None:
    with pytest.raises(OntologyError):
        ContextOntology({"x": ()})
    with pytest.raises(OntologyError):
        ContextOntology(
            {
                "x": (
                    DimensionSpec(name="a", value_type="string", required=True),
                    DimensionSpec(name="a", value_type="string", required=False),
                )
            }
        )
    with pytest.raises(OntologyError):
        ContextOntology({"x": (DimensionSpec(name="a", value_type="string", required=False),)})
    with pytest.raises(OntologyError):
        DimensionSpec(name="a", value_type="quaternion", required=True)
    with pytest.raises(OntologyError):
        DimensionSpec(name=" ", value_type="string", required=True)


def test_ontology_refuses_duplicate_or_missing_relation_rules() -> None:
    duplicate = (
        RelationRule(relation=ContextRelation.CONTAINS),
        RelationRule(relation=ContextRelation.CONTAINS),
    )
    with pytest.raises(OntologyError):
        ContextOntology(UNIVERSAL_DIMENSIONS, duplicate)
    with pytest.raises(OntologyError):
        ContextOntology(UNIVERSAL_DIMENSIONS, (RelationRule(relation=ContextRelation.CONTAINS),))


def test_ontology_serialises_deterministically() -> None:
    payload = UNIVERSAL_ONTOLOGY.to_dict()
    assert payload == UNIVERSAL_ONTOLOGY.to_dict()
    assert payload["unknown_sentinel"] == UNKNOWN
    assert len(payload["relations"]) == len(ContextRelation)
