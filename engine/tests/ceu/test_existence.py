"""UCOS-CEU-001 — the existence substrate: existence precedes entity.

What these tests exist to falsify, stated as the failures they would catch:

* a form, classification, relationship or topology that is *not* a registered unit —
  i.e. a construct privileged by being a shape in the source code (UCEP-001, UCEP-002);
* ownership decided by a predicate rather than discovered from the registry (CEU-006);
* a relationship that is an edge rather than an entity with identity and lineage (CEU-003);
* an entity confined to one topology at a time (CEU-004, S-007);
* a classification that cannot split, merge, deprecate or come back (CEU-002);
* a registered unit with no identifier, no journal entry, or a non-reproducing digest
  (UCEP-007);
* a ceiling anywhere.
"""

from __future__ import annotations

import pytest

from engine.ceu.errors import (
    ExistenceError,
    ExistenceRegistrationError,
    RelationshipAdmissibilityError,
    RelationshipError,
    TopologyCycleError,
)
from engine.ceu.existence import (
    ATTR_FACULTIES,
    ATTR_SPECIALIZES,
    ExistenceRegistry,
    ExistenceUnit,
    RelationshipView,
)
from engine.registry.universal.identity import is_well_formed, parse_kind_name

FORMS = (
    ("classification", "CLSS"),
    ("relationship-type", "RLTY"),
    ("relationship", "RSHP"),
    ("topology", "TOPO"),
    ("entity", "ENTY"),
)


@pytest.fixture
def registry() -> ExistenceRegistry:
    reg = ExistenceRegistry()
    for key, code in FORMS:
        reg.declare_form(key, title=key.title(), code=code)
    return reg


@pytest.fixture
def view(registry: ExistenceRegistry) -> RelationshipView:
    return RelationshipView(
        registry,
        type_form="relationship-type",
        relationship_form="relationship",
        topology_form="topology",
    )


def _classification(registry: ExistenceRegistry, key: str, **attributes) -> ExistenceUnit:
    return registry.register(
        ExistenceUnit(form="classification", key=key, title=key.title(), attributes=attributes)
    )


def _entity(registry: ExistenceRegistry, key: str, classification: str = "") -> ExistenceUnit:
    return registry.register(
        ExistenceUnit(form="entity", key=key, title=key.upper(), classification=classification)
    )


# --------------------------------------------------------------------------- #
# Existence precedes entity                                                    #
# --------------------------------------------------------------------------- #


def test_the_root_form_is_a_unit_of_itself():
    reg = ExistenceRegistry()
    root = reg.form_of(reg.root_form)
    assert root.form == root.key == reg.root_form
    assert is_well_formed(root.universal_id)


def test_the_root_is_not_a_reserved_word():
    """Even the name of the root is configuration, not vocabulary baked into the code."""
    reg = ExistenceRegistry(root_form="species-of-being", root_code="SPOB")
    assert reg.root_form == "species-of-being"
    assert reg.form_of("species-of-being").form == "species-of-being"
    assert not reg.has_form("form")


def test_entity_is_one_form_among_many_and_not_the_root(registry: ExistenceRegistry):
    assert "entity" in registry.form_keys()
    assert registry.form_of("entity").form == registry.root_form
    # the root form is the only self-referential one; entity has no special status
    assert registry.form_of("entity").key != registry.root_form


def test_a_future_form_needs_no_code_change(registry: ExistenceRegistry):
    registry.declare_form("dream", title="Dream", code="DRMX")
    unit = registry.register(ExistenceUnit(form="dream", key="d1", title="A Dream"))
    assert parse_kind_name(unit.universal_id) == "DREAM"
    assert registry.counts()["dream"] == 1


@pytest.mark.parametrize("form", [f for f, _ in FORMS])
def test_every_construct_is_a_registered_unit(registry: ExistenceRegistry, form: str):
    """UCEP-001: classification, relationship and topology are units, not shapes."""
    declared = registry.form_of(form)
    assert declared.form == registry.root_form
    assert is_well_formed(declared.universal_id)
    assert registry.audit(subject=declared.universal_id)


# --------------------------------------------------------------------------- #
# Identity, lineage, registration (UCEP-007)                                   #
# --------------------------------------------------------------------------- #


def test_an_unregistered_unit_has_no_identity():
    detached = ExistenceUnit(form="entity", key="ghost", title="Ghost")
    with pytest.raises(ExistenceError):
        _ = detached.universal_id


def test_every_registered_unit_is_identified_journaled_and_intact(registry: ExistenceRegistry):
    _classification(registry, "nucleus")
    assert registry.unlineaged() == ()
    assert registry.verify_audit() == []
    for unit in registry.units():
        assert is_well_formed(unit.universal_id)
        assert unit.is_intact()


def test_registration_is_idempotent_and_refuses_a_conflicting_rewrite(registry):
    first = _classification(registry, "nucleus")
    assert _classification(registry, "nucleus") == first
    with pytest.raises(ExistenceRegistrationError):
        registry.register(
            ExistenceUnit(form="classification", key="nucleus", title="Something Else")
        )


def test_a_unit_of_an_unregistered_form_is_refused(registry: ExistenceRegistry):
    with pytest.raises(ExistenceError):
        registry.register(ExistenceUnit(form="rumour", key="r", title="R"))


def test_a_unit_naming_an_unregistered_classification_is_refused(registry):
    with pytest.raises(ExistenceRegistrationError):
        _entity(registry, "a", classification="UCOS-CLSS-ffffffffffff")


@pytest.mark.parametrize("field", ["form", "key", "title"])
def test_a_unit_must_declare_its_own_fields(field: str):
    kwargs = {"form": "entity", "key": "k", "title": "T"}
    kwargs[field] = "  "
    with pytest.raises(ExistenceError):
        ExistenceUnit(**kwargs)


# --------------------------------------------------------------------------- #
# Ownership is discovered, not hardcoded (CEU-006)                             #
# --------------------------------------------------------------------------- #


def test_ownership_is_a_registered_faculty_not_a_predicate(registry: ExistenceRegistry):
    nucleus = _classification(registry, "nucleus", **{ATTR_FACULTIES: ("own-capability",)})
    layer = _classification(registry, "layer")
    assert registry.holds(nucleus.universal_id, "own-capability")
    assert not registry.holds(layer.universal_id, "own-capability")


def test_owners_are_discovered_by_query(registry: ExistenceRegistry):
    nucleus = _classification(registry, "nucleus", **{ATTR_FACULTIES: ("own-capability",)})
    _classification(registry, "layer")
    assert registry.holding("own-capability") == (nucleus.universal_id,)


def test_a_specialization_inherits_the_faculty_without_restating_it(registry):
    nucleus = _classification(registry, "nucleus", **{ATTR_FACULTIES: ("own-capability",)})
    micro = _classification(registry, "micro-nucleus", **{ATTR_SPECIALIZES: nucleus.universal_id})
    nano = _classification(registry, "nano-nucleus", **{ATTR_SPECIALIZES: micro.universal_id})
    assert registry.holds(nano.universal_id, "own-capability")
    assert registry.ancestry(nano.universal_id) == (
        nano.universal_id,
        micro.universal_id,
        nucleus.universal_id,
    )
    assert nano.universal_id in registry.specializations_of(nucleus.universal_id)


def test_a_new_faculty_needs_no_code_change(registry: ExistenceRegistry):
    holder = _classification(registry, "steward", **{ATTR_FACULTIES: ("hold-mandate",)})
    assert registry.holding("hold-mandate") == (holder.universal_id,)


# --------------------------------------------------------------------------- #
# Classifications evolve (CEU-002)                                             #
# --------------------------------------------------------------------------- #


def test_a_classification_splits(registry: ExistenceRegistry):
    old = _classification(registry, "unit")
    a = _classification(registry, "nucleus")
    b = _classification(registry, "layer")
    record = registry.supersede(
        old.universal_id, successors=[a.universal_id, b.universal_id], authority="GOV"
    )
    assert record["successors"] == [a.universal_id, b.universal_id]
    assert registry.is_superseded(old.universal_id)
    assert old.universal_id not in {u.universal_id for u in registry.admissible()}


def test_classifications_merge(registry: ExistenceRegistry):
    a = _classification(registry, "nucleus")
    b = _classification(registry, "micro-nucleus")
    merged = _classification(registry, "capability-authority")
    for old in (a, b):
        registry.supersede(old.universal_id, successors=[merged.universal_id], authority="GOV")
    assert registry.successors_of(a.universal_id) == registry.successors_of(b.universal_id)


def test_a_deprecated_classification_has_no_successor(registry: ExistenceRegistry):
    old = _classification(registry, "obsolete")
    registry.supersede(old.universal_id, authority="GOV")
    assert registry.successors_of(old.universal_id) == ()
    assert registry.supersessions()[0]["deprecated_outright"] is True


def test_a_superseded_classification_admits_no_new_units(registry: ExistenceRegistry):
    old = _classification(registry, "obsolete")
    registry.supersede(old.universal_id, authority="GOV")
    with pytest.raises(ExistenceRegistrationError):
        _entity(registry, "a", classification=old.universal_id)


def test_supersession_is_not_deletion(registry: ExistenceRegistry):
    old = _classification(registry, "obsolete")
    registry.supersede(old.universal_id, authority="GOV")
    assert registry.resolve(old.universal_id) == old


def test_a_classification_can_be_resurrected(registry: ExistenceRegistry):
    old = _classification(registry, "obsolete")
    registry.supersede(old.universal_id, authority="GOV")
    registry.resurrect(old.universal_id, authority="GOV", note="needed again")
    assert not registry.is_superseded(old.universal_id)
    assert _entity(registry, "a", classification=old.universal_id)


def test_resurrection_keeps_the_supersession_in_the_journal(registry: ExistenceRegistry):
    old = _classification(registry, "obsolete")
    registry.supersede(old.universal_id, authority="GOV")
    registry.resurrect(old.universal_id, authority="GOV")
    actions = [e.action for e in registry.audit(subject=old.universal_id)]
    assert actions == ["register", "supersede", "resurrect"]


def test_resurrection_preserves_the_pre_resurrection_field_values(registry: ExistenceRegistry):
    """P4-F-001: the record right after supersede() must survive resurrect() intact,
    not just be provable by hash — the actual field values must be readable."""
    old = _classification(registry, "obsolete")
    registry.supersede(old.universal_id, authority="GOV", note="first pass")
    registry.resurrect(old.universal_id, authority="GOV", note="needed again")
    history = registry.supersession_history(old.universal_id)
    assert len(history) == 2
    assert history[0]["active"] is True
    assert history[0]["note"] == "first pass"
    assert "resurrected_by" not in history[0]
    assert history[1]["active"] is False
    assert history[1]["resurrected_by"] == "GOV"
    assert history[1]["resurrection_note"] == "needed again"
    # the resurrection snapshot still carries the original supersession's own note —
    # it is a new record built from the old one, not an unrelated fresh record
    assert history[1]["note"] == "first pass"


def test_a_split_supersede_and_resurrect_cycle_is_fully_reconstructible(
    registry: ExistenceRegistry,
):
    """A subject superseded, resurrected, then superseded again keeps every snapshot."""
    old = _classification(registry, "cyclical")
    registry.supersede(old.universal_id, authority="GOV", note="round one")
    registry.resurrect(old.universal_id, authority="GOV")
    registry.supersede(old.universal_id, authority="GOV", note="round two")
    history = registry.supersession_history(old.universal_id)
    assert len(history) == 3
    assert [h["active"] for h in history] == [True, False, True]
    assert history[0]["note"] == "round one"
    assert history[2]["note"] == "round two"
    # supersessions() still reports only the CURRENT state — one row, not three
    assert len(registry.supersessions()) == 1
    assert registry.supersessions()[0]["note"] == "round two"


def test_supersession_history_survives_reconstruction(registry: ExistenceRegistry):
    old = _classification(registry, "obsolete")
    registry.supersede(old.universal_id, authority="GOV", note="first")
    registry.resurrect(old.universal_id, authority="GOV")
    rebuilt = ExistenceRegistry.from_document(registry.to_document())
    assert rebuilt.supersession_history(old.universal_id) == registry.supersession_history(
        old.universal_id
    )
    assert rebuilt.digest() == registry.digest()


def test_supersession_refuses_the_unlawful_cases(registry: ExistenceRegistry):
    a = _classification(registry, "a")
    b = _classification(registry, "b")
    with pytest.raises(ExistenceError):
        registry.supersede(a.universal_id, successors=[a.universal_id], authority="GOV")
    with pytest.raises(ExistenceError):
        registry.supersede(a.universal_id, successors=[b.universal_id], authority="  ")
    registry.supersede(b.universal_id, authority="GOV")
    with pytest.raises(ExistenceError):
        registry.supersede(a.universal_id, successors=[b.universal_id], authority="GOV")
    with pytest.raises(ExistenceError):
        registry.resurrect(a.universal_id, authority="GOV")


def test_every_construct_supersedes_through_the_one_mechanism(registry, view):
    """CEU-002/003/004: forms, topologies and relationship types evolve identically."""
    registry.register(ExistenceUnit(form="topology", key="mesh", title="Mesh"))
    registry.register(ExistenceUnit(form="relationship-type", key="peers", title="Peers"))
    for form, key in (("form", "entity"), ("topology", "mesh"), ("relationship-type", "peers")):
        unit = registry.unit(form, key)
        registry.supersede(unit.universal_id, authority="GOV")
        assert registry.is_superseded(unit.universal_id)


# --------------------------------------------------------------------------- #
# Relationships are entities (CEU-003)                                         #
# --------------------------------------------------------------------------- #


def _wire(registry: ExistenceRegistry, view: RelationshipView) -> tuple[str, str]:
    registry.register(ExistenceUnit(form="topology", key="hierarchy", title="Hierarchy"))
    registry.register(ExistenceUnit(form="topology", key="mesh", title="Mesh"))
    registry.register(
        ExistenceUnit(
            form="relationship-type",
            key="composes",
            title="Composes",
            attributes={"acyclic": True, "topologies": ("hierarchy",)},
        )
    )
    registry.register(
        ExistenceUnit(
            form="relationship-type",
            key="peers-with",
            title="Peers With",
            attributes={"topologies": ("mesh",)},
        )
    )
    return _entity(registry, "a").universal_id, _entity(registry, "b").universal_id


def test_a_relationship_is_a_registered_identified_lineaged_unit(registry, view):
    a, b = _wire(registry, view)
    edge = view.relate("composes", a, b, authority="T")
    assert edge.form == "relationship"
    assert is_well_formed(edge.universal_id)
    assert registry.audit(subject=edge.universal_id)
    assert edge.is_intact()
    assert registry.resolve(edge.universal_id) == edge


def test_a_relationship_supersedes_like_any_other_unit(registry, view):
    a, b = _wire(registry, view)
    edge = view.relate("composes", a, b, authority="T")
    registry.supersede(edge.universal_id, authority="GOV")
    assert registry.is_superseded(edge.universal_id)


def test_any_form_may_relate_to_any_form_by_default(registry, view):
    """CEU-007: validity is registry-driven, and the default declares no restriction."""
    a, _ = _wire(registry, view)
    topology = registry.unit("topology", "mesh").universal_id
    edge = view.relate("peers-with", a, topology, authority="T")
    assert edge.attribute("target") == topology


def test_a_relationship_may_relate_two_relationships(registry, view):
    a, b = _wire(registry, view)
    first = view.relate("composes", a, b, authority="T")
    second = view.relate("peers-with", a, b, authority="T")
    linked = view.relate("peers-with", first.universal_id, second.universal_id, authority="T")
    assert linked.attribute("source") == first.universal_id


def test_a_declared_constraint_is_enforced(registry, view):
    a, b = _wire(registry, view)
    registry.register(
        ExistenceUnit(
            form="relationship-type",
            key="entities-only",
            title="Entities Only",
            attributes={"source_forms": ("entity",), "target_forms": ("entity",)},
        )
    )
    assert view.relate("entities-only", a, b, authority="T")
    topology = registry.unit("topology", "mesh").universal_id
    with pytest.raises(RelationshipAdmissibilityError):
        view.relate("entities-only", a, topology, authority="T")


def test_an_unregistered_endpoint_is_refused(registry, view):
    a, _ = _wire(registry, view)
    with pytest.raises(RelationshipAdmissibilityError):
        view.relate("composes", a, "UCOS-ENTY-ffffffffffff", authority="T")


def test_an_unregistered_or_superseded_type_is_refused(registry, view):
    a, b = _wire(registry, view)
    with pytest.raises(RelationshipError):
        view.relate("imagines", a, b, authority="T")
    declared = registry.unit("relationship-type", "composes")
    registry.supersede(declared.universal_id, authority="GOV")
    with pytest.raises(RelationshipError):
        view.relate("composes", a, b, authority="T")


def test_an_acyclic_type_refuses_a_cycle(registry, view):
    a, b = _wire(registry, view)
    view.relate("composes", a, b, authority="T")
    with pytest.raises(TopologyCycleError):
        view.relate("composes", b, a, authority="T")


def test_a_type_that_is_not_acyclic_permits_a_cycle(registry, view):
    a, b = _wire(registry, view)
    view.relate("peers-with", a, b, authority="T")
    assert view.relate("peers-with", b, a, authority="T")
    assert view.cycle_in("peers-with")


def test_relationship_depth_is_unlimited(registry, view):
    _wire(registry, view)
    chain = [_entity(registry, f"n{i}").universal_id for i in range(12)]
    for source, target in zip(chain, chain[1:], strict=False):
        view.relate("composes", source, target, authority="T")
    assert len(view.reachable(chain[0], "composes")) == len(chain) - 1


# --------------------------------------------------------------------------- #
# Simultaneous, unlimited topologies (CEU-004, S-007)                          #
# --------------------------------------------------------------------------- #


def test_one_entity_participates_in_many_topologies_at_once(registry, view):
    a, b = _wire(registry, view)
    for extra in ("fractal", "semantic", "temporal"):
        registry.register(ExistenceUnit(form="topology", key=extra, title=extra.title()))
    view.relate("composes", a, b, authority="T")
    view.relate("peers-with", a, b, authority="T", topologies=("fractal", "semantic", "temporal"))
    assert view.topologies_of(a) == ("fractal", "hierarchy", "mesh", "semantic", "temporal")


def test_topology_membership_is_discoverable(registry, view):
    a, b = _wire(registry, view)
    view.relate("composes", a, b, authority="T")
    assert view.participants("hierarchy") == tuple(sorted((a, b)))
    assert view.participants("mesh") == ()


def test_a_relationship_naming_an_unregistered_topology_is_refused(registry, view):
    a, b = _wire(registry, view)
    with pytest.raises(ExistenceError):
        view.relate("composes", a, b, authority="T", topologies=("nowhere",))


def test_the_graph_reports_no_dangling_endpoints(registry, view):
    a, b = _wire(registry, view)
    view.relate("composes", a, b, authority="T")
    assert view.dangling() == ()


# --------------------------------------------------------------------------- #
# Context, determinism, no ceiling                                             #
# --------------------------------------------------------------------------- #


def test_the_substrate_binds_to_one_reality(registry: ExistenceRegistry):
    fingerprint = {"frame": "planetary-a1", "resolution_digest": "abc"}
    assert registry.bind_context(fingerprint) == fingerprint
    assert registry.bind_context(fingerprint) == fingerprint
    assert registry.is_context_bound
    with pytest.raises(ExistenceError):
        registry.bind_context({"frame": "planetary-b4", "resolution_digest": "def"})


def test_an_unbound_substrate_fails_closed(registry: ExistenceRegistry):
    with pytest.raises(ExistenceError):
        registry.require_context()
    with pytest.raises(ExistenceError):
        registry.bind_context({"frame": "f"})


def test_the_substrate_is_deterministic(registry: ExistenceRegistry):
    assert registry.digest() == registry.digest()
    assert ExistenceRegistry().digest() == ExistenceRegistry().digest()


def test_two_identically_built_substrates_agree():
    def build() -> ExistenceRegistry:
        reg = ExistenceRegistry()
        for key, code in FORMS:
            reg.declare_form(key, title=key.title(), code=code)
        _classification(reg, "nucleus", **{ATTR_FACULTIES: ("own-capability",)})
        return reg

    assert build().digest() == build().digest()


def test_the_document_declares_no_ceiling(registry: ExistenceRegistry):
    document = registry.to_document()
    assert document["closed_set"] is False
    assert document["upper_limit"] is None
    assert document["root_form"] == registry.root_form
    assert document["counts"]["by_form"]


def test_the_journal_detects_tampering(registry: ExistenceRegistry):
    _classification(registry, "nucleus")
    assert registry.verify_audit() == []
    registry._audit[0] = registry._audit[0].__class__(  # noqa: SLF001 - forced state
        sequence=99,
        action="register",
        subject="tampered",
        content_hash="x",
        prev_hash="y",
    )
    assert registry.verify_audit()
