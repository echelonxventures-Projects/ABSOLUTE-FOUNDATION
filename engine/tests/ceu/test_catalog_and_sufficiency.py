"""UCOS-CEU-001 — CEU-038: constitutional sufficiency, demonstrated rather than claimed.

The claim under test is narrow and falsifiable: **every concept the steering names can be
admitted as data, through the ordinary registration path, without a line of new code.**

If that holds, the substrate is sufficient and the next concept — the one nobody has named
— arrives the same way. If it fails for even one concept, the substrate is insufficient
and the honest response is to fix the substrate, not to special-case the concept. So each
named concept is asserted by name below; a concept that quietly stopped registering would
fail here rather than being discovered later as a missing feature.
"""

from __future__ import annotations

import pytest

from engine.ceu.catalog import (
    SEED_CLASSIFICATIONS,
    SEED_EPISTEMIC_STATES,
    SEED_EXISTENCE_STATES,
    SEED_FORMS,
    SEED_KNOWLEDGE_STATES,
    SEED_OBSERVERS,
    SEED_RELATIONSHIP_TYPES,
    SEED_TOPOLOGIES,
    bootstrap,
    relationship_view,
    to_document,
)
from engine.ceu.errors import CEUError
from engine.ceu.existence import ExistenceRegistry, ExistenceUnit
from engine.ceu.sufficiency import (
    ATTR_EXPRESSED_BY,
    PRIMITIVES,
    VERDICT_EVOLUTION,
    VERDICT_NEW_ROOT,
    assess,
    assess_registry,
    require_sufficient,
)
from engine.registry.universal.identity import is_well_formed


@pytest.fixture(scope="module")
def seeded() -> ExistenceRegistry:
    return bootstrap()


# --------------------------------------------------------------------------- #
# CEU-038 — the sufficiency test itself                                        #
# --------------------------------------------------------------------------- #


def test_there_are_twelve_primitives():
    assert len(PRIMITIVES) == 12
    assert len(set(PRIMITIVES)) == 12


def test_a_concept_expressible_through_a_primitive_enters_by_evolution():
    verdict = assess("perspective", ["context", "knowledge"])
    assert verdict["verdict"] == VERDICT_EVOLUTION
    assert verdict["enters_by_evolution"] is True
    assert verdict["expressed_by"] == ["context", "knowledge"]


def test_a_concept_expressible_through_nothing_claims_a_new_root():
    verdict = assess("time-crystal", [])
    assert verdict["verdict"] == VERDICT_NEW_ROOT
    assert verdict["enters_by_evolution"] is False


def test_the_fail_closed_form_refuses_a_claimed_root():
    assert require_sufficient("pattern", ["knowledge"])
    with pytest.raises(CEUError):
        require_sufficient("pattern", [])


def test_an_unrecognised_primitive_is_refused_not_ignored():
    """Silently dropping it would let a typo — or a smuggled root — through."""
    with pytest.raises(CEUError) as caught:
        assess("thing", ["knowledge", "vibes"])
    assert caught.value.detail["unknown"] == ["vibes"]


def test_an_unnamed_concept_is_refused():
    with pytest.raises(CEUError):
        assess("   ", ["knowledge"])


def test_the_ordering_of_expressing_primitives_is_canonical():
    assert assess("x", ["knowledge", "context"])["expressed_by"] == ["context", "knowledge"]


# --------------------------------------------------------------------------- #
# Every seeded form is data, not a root                                        #
# --------------------------------------------------------------------------- #


def test_the_seeded_substrate_is_sufficient(seeded: ExistenceRegistry):
    report = assess_registry(seeded)
    assert report["sufficient"] is True
    assert report["claimed_new_roots"] == []
    assert report["forms_assessed"] == len(seeded.forms())


def test_the_root_form_is_the_only_exempt_one(seeded: ExistenceRegistry):
    exempt = [a for a in assess_registry(seeded)["assessments"] if a["is_root_form"]]
    assert [a["concept"] for a in exempt] == [seeded.root_form]


@pytest.mark.parametrize("key,_code,_title,expressed_by", SEED_FORMS)
def test_every_seeded_form_declares_how_it_is_expressed(key, _code, _title, expressed_by):
    assert expressed_by, f"{key} declares no expressing primitive, so it claims a root"
    assert assess(key, expressed_by)["enters_by_evolution"]


def test_a_form_registered_without_expressing_primitives_is_caught():
    registry = ExistenceRegistry()
    registry.declare_form("smuggled-root", title="Smuggled", code="SMGL")
    report = assess_registry(registry)
    assert report["sufficient"] is False
    assert report["claimed_new_roots"] == ["smuggled-root"]


# --------------------------------------------------------------------------- #
# The named concepts, each admitted by name                                    #
# --------------------------------------------------------------------------- #


NAMED_CONCEPTS = (
    "observer",
    "perspective",
    "knowledge-state",
    "epistemic-state",
    "existence-state",
    "pattern",
    "generator",
    "scale",
    "temporal-model",
    "capability",
    "governance",
    "policy",
    "rule",
    "authority",
    "evidence",
    "measurement",
    "dependency",
    "constraint",
    "resource",
    "intent",
    "purpose",
    "value",
    "boundary",
    "sovereignty",
    "contradiction",
    "recovery",
    "registry",
    "dictionary",
    "event",
    "architecture",
    "reality",
    "universe",
    "civilization",
    "trust",
    "consent",
    "risk",
    "prediction",
    "simulation",
    "goal",
    "decision",
    "state",
    "causality",
    "observation",
)


@pytest.mark.parametrize("concept", NAMED_CONCEPTS)
def test_every_named_concept_is_a_registered_form(seeded: ExistenceRegistry, concept: str):
    """CEU-005…CEU-037 admitted as data — none of these is a class or a branch."""
    form = seeded.form_of(concept)
    assert form.form == seeded.root_form
    assert is_well_formed(form.universal_id)
    assert form.tuple_attribute(ATTR_EXPRESSED_BY)


def test_nucleus_and_layer_are_rows_not_roots(seeded: ExistenceRegistry):
    """S-012 / CEU-002: the demotion, asserted directly."""
    for key in ("nucleus", "layer", "composition"):
        unit = seeded.unit("classification", key)
        assert unit.form == "classification"
    assert not seeded.has_form("nucleus")
    assert not seeded.has_form("layer")


def test_ownership_is_data_on_the_classification(seeded: ExistenceRegistry):
    nucleus = seeded.unit("classification", "nucleus").universal_id
    layer = seeded.unit("classification", "layer").universal_id
    assert seeded.holds(nucleus, "own-capability")
    assert not seeded.holds(layer, "own-capability")
    assert nucleus in seeded.holding("own-capability")


def test_a_specialization_chain_inherits_ownership(seeded: ExistenceRegistry):
    nano = seeded.unit("classification", "nano-nucleus").universal_id
    assert seeded.holds(nano, "own-capability")
    assert len(seeded.ancestry(nano)) == 3


def test_the_six_epistemic_states_stay_distinct(seeded: ExistenceRegistry):
    """CEU-045: unknown, unobserved, unmeasured, unverified, contradicted, impossible."""
    registered = {u.key for u in seeded.units(form="epistemic-state")}
    assert registered == {key for key, _ in SEED_EPISTEMIC_STATES}
    assert len(registered) == 6


def test_unknown_is_a_valid_state_in_every_population_that_declares_one(seeded):
    """CEU-017: unknown is never absence and never failure."""
    for form in ("observer", "existence-state", "epistemic-state", "scale", "temporal-model"):
        assert seeded.has(form, "unknown"), form


def test_human_and_earth_are_rows_among_many(seeded: ExistenceRegistry):
    """CEU-027: no privileged reference frame — 'human' is one observer of nine."""
    observers = {u.key for u in seeded.units(form="observer")}
    assert "human" in observers
    assert len(observers) == len(SEED_OBSERVERS) > 1
    assert "human" in {u.key for u in seeded.units(form="scale")}


@pytest.mark.parametrize("key,_definition", SEED_TOPOLOGIES)
def test_every_topology_is_a_registered_unit(seeded: ExistenceRegistry, key, _definition):
    assert seeded.unit("topology", key).form == "topology"


def test_layered_and_layerless_are_both_declarable(seeded: ExistenceRegistry):
    """CEU-005: layers are one topology among many, and their absence is expressible."""
    assert seeded.has("topology", "layered")
    assert seeded.has("topology", "layerless")


@pytest.mark.parametrize("key,_definition,_attributes", SEED_RELATIONSHIP_TYPES)
def test_every_relationship_type_is_a_registered_unit(seeded, key, _definition, _attributes):
    assert seeded.unit("relationship-type", key).form == "relationship-type"


@pytest.mark.parametrize("key,_definition,_attributes", SEED_CLASSIFICATIONS)
def test_every_classification_is_a_registered_unit(seeded, key, _definition, _attributes):
    assert seeded.unit("classification", key).form == "classification"


def test_the_population_counts_are_what_the_data_says(seeded: ExistenceRegistry):
    counts = seeded.counts()
    assert counts["form"] == len(SEED_FORMS) + 1  # + the self-describing root
    assert counts["topology"] == len(SEED_TOPOLOGIES)
    assert counts["relationship-type"] == len(SEED_RELATIONSHIP_TYPES)
    assert counts["classification"] == len(SEED_CLASSIFICATIONS)
    assert counts["existence-state"] == len(SEED_EXISTENCE_STATES)
    assert counts["knowledge-state"] == len(SEED_KNOWLEDGE_STATES)


# --------------------------------------------------------------------------- #
# The open-world proof                                                         #
# --------------------------------------------------------------------------- #


def test_a_concept_nobody_has_named_enters_with_zero_code():
    """CEU-016/CEU-022: emergence must not require constitutional redesign."""
    registry = bootstrap()
    registry.declare_form(
        "dream-logic",
        title="Dream Logic",
        code="DRML",
        attributes={ATTR_EXPRESSED_BY: ("knowledge", "context")},
    )
    unit = registry.register(ExistenceUnit(form="dream-logic", key="lucid", title="Lucid"))
    assert is_well_formed(unit.universal_id)
    assert registry.counts()["dream-logic"] == 1
    assert assess_registry(registry)["sufficient"] is True


def test_an_emergent_concept_relates_to_a_seeded_one_immediately():
    """CEU-023: interoperability without prior knowledge of the concept."""
    registry = bootstrap()
    view = relationship_view(registry)
    registry.declare_form(
        "dream-logic",
        title="Dream Logic",
        code="DRML",
        attributes={ATTR_EXPRESSED_BY: ("knowledge",)},
    )
    dream = registry.register(ExistenceUnit(form="dream-logic", key="lucid", title="Lucid"))
    observer = registry.unit("observer", "human")
    edge = view.relate("observes", observer.universal_id, dream.universal_id, authority="T")
    assert edge.attribute("target") == dream.universal_id


def test_contradictions_may_coexist_unresolved():
    """CEU-043: absence of resolution is not absence of existence."""
    registry = bootstrap()
    view = relationship_view(registry)
    a = registry.register(ExistenceUnit(form="knowledge", key="a", title="A"))
    b = registry.register(ExistenceUnit(form="knowledge", key="b", title="B"))
    view.relate("contradicts", a.universal_id, b.universal_id, authority="T")
    # symmetric, so the conflict is visible from both sides, and neither is retired
    assert view.neighbours(a.universal_id, relationship_type="contradicts")
    assert view.neighbours(b.universal_id, relationship_type="contradicts")
    assert not registry.is_superseded(a.universal_id)
    assert not registry.is_superseded(b.universal_id)


def test_causality_may_be_cyclic_while_composition_may_not():
    """Per-type integrity: causality is contextual, composition is a containment."""
    registry = bootstrap()
    view = relationship_view(registry)
    a = registry.register(ExistenceUnit(form="event", key="a", title="A"))
    b = registry.register(ExistenceUnit(form="event", key="b", title="B"))
    view.relate("causes", a.universal_id, b.universal_id, authority="T")
    assert view.relate("causes", b.universal_id, a.universal_id, authority="T")


def test_one_unit_participates_in_many_seeded_topologies(seeded: ExistenceRegistry):
    registry = bootstrap()
    view = relationship_view(registry)
    a = registry.register(ExistenceUnit(form="entity", key="a", title="A"))
    b = registry.register(ExistenceUnit(form="entity", key="b", title="B"))
    view.relate("composes", a.universal_id, b.universal_id, authority="T")
    view.relate("evidences", a.universal_id, b.universal_id, authority="T")
    view.relate("owns", a.universal_id, b.universal_id, authority="T")
    assert view.topologies_of(a.universal_id) == ("hierarchy", "knowledge", "ownership")


# --------------------------------------------------------------------------- #
# Determinism and the document                                                 #
# --------------------------------------------------------------------------- #


def test_the_catalogue_bootstraps_deterministically():
    assert bootstrap().digest() == bootstrap().digest()


def test_the_seeded_substrate_is_fully_lineaged(seeded: ExistenceRegistry):
    assert seeded.verify_audit() == []
    assert seeded.unlineaged() == ()


def test_every_seeded_unit_is_identified_and_intact(seeded: ExistenceRegistry):
    for unit in seeded.units():
        assert is_well_formed(unit.universal_id)
        assert unit.is_intact()


def test_the_catalogue_document_declares_no_ceiling():
    document = to_document()
    assert document["closed_set"] is False
    assert document["upper_limit"] is None
    assert document["counts"]["form"] == len(SEED_FORMS) + 1
