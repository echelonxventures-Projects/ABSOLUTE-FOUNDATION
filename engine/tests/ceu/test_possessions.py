"""UCOS-CEU-001 Part 05 — the Constitution-Before-Code gate.

The gate's value depends entirely on it being able to *fail*, so the central tests here
assert that the seeded catalogue does **not** pass it. A gate that reported the seeds
complete would have been tuned until it did, and would then measure nothing.
"""

from __future__ import annotations

import pytest

from engine.ceu.catalog import bootstrap, relationship_view
from engine.ceu.errors import CEUError
from engine.ceu.existence import ExistenceRegistry, ExistenceUnit
from engine.ceu.possessions import (
    LEVELS,
    POSSESSIONS,
    assess,
    assess_by_form,
    certify_levels,
    completeness,
    dictionary_for_existence,
    gaps,
    governed_units,
    related_units,
    require_certified,
    require_complete,
)

FRAME = {"frame": "planetary-a1", "resolution_digest": "abc"}
STRUCTURAL = ("identity", "dictionary", "registry", "lineage", "evolution")


@pytest.fixture
def seeded() -> ExistenceRegistry:
    return bootstrap()


def test_there_are_ten_possessions():
    assert len(POSSESSIONS) == 10
    assert len({key for key, _ in POSSESSIONS}) == 10


def test_the_structural_possessions_hold_for_every_seeded_unit(seeded: ExistenceRegistry):
    report = assess(seeded)
    for possession in STRUCTURAL:
        row = next(p for p in report["possessions"] if p["possession"] == possession)
        assert row["complete"], row["examples"]
        assert row["held"] == row["total"] == len(seeded.units())


def test_the_seeded_catalogue_does_not_pass_the_whole_gate(seeded: ExistenceRegistry):
    """The point of the gate: it reports what is genuinely absent."""
    report = assess(seeded)
    assert report["complete"] is False
    assert set(report["incomplete"]) == {
        "context",
        "governance",
        "ownership",
        "relationships",
        "evidence",
    }


def test_the_dictionary_projection_verifies(seeded: ExistenceRegistry):
    dictionary = dictionary_for_existence(seeded)
    verification = dictionary.verify()
    assert verification["status"] == "PASS"
    assert verification["count"] == len(seeded.units())
    assert verification["unreproducible"] == []


def test_binding_a_reality_closes_the_context_possession(seeded: ExistenceRegistry):
    assert "context" in assess(seeded)["incomplete"]
    seeded.bind_context(FRAME)
    assert "context" not in assess(seeded)["incomplete"]


def test_governance_is_conferred_by_registration_not_by_existing(seeded: ExistenceRegistry):
    view = relationship_view(seeded)
    authority = seeded.register(
        ExistenceUnit(form="authority", key="commission", title="Commission")
    )
    subject = seeded.unit("classification", "nucleus")
    assert subject.universal_id not in governed_units(seeded)
    view.relate("governs", authority.universal_id, subject.universal_id, authority="GOV")
    assert subject.universal_id in governed_units(seeded)


def test_governance_may_also_be_declared_on_the_unit(seeded: ExistenceRegistry):
    authority = seeded.register(
        ExistenceUnit(form="authority", key="commission", title="Commission")
    )
    governed = seeded.register(
        ExistenceUnit(
            form="entity",
            key="thing",
            title="Thing",
            attributes={"governed_by": authority.universal_id},
        )
    )
    assert governed.universal_id in governed_units(seeded)


def test_a_governed_by_naming_an_unregistered_authority_confers_nothing(seeded):
    unit = seeded.register(
        ExistenceUnit(
            form="entity",
            key="thing",
            title="Thing",
            attributes={"governed_by": "UCOS-AUTH-ffffffffffff"},
        )
    )
    assert unit.universal_id not in governed_units(seeded)


def test_relationships_possession_tracks_actual_participation(seeded: ExistenceRegistry):
    view = relationship_view(seeded)
    a = seeded.register(ExistenceUnit(form="entity", key="a", title="A"))
    b = seeded.register(ExistenceUnit(form="entity", key="b", title="B"))
    assert a.universal_id not in related_units(seeded)
    view.relate("relates-to", a.universal_id, b.universal_id, authority="T")
    assert {a.universal_id, b.universal_id} <= related_units(seeded)


def test_a_unit_declaring_a_classification_possesses_ownership(seeded: ExistenceRegistry):
    nucleus = seeded.unit("classification", "nucleus").universal_id
    owned = seeded.register(
        ExistenceUnit(form="entity", key="owned", title="Owned", classification=nucleus)
    )
    assert f"entity:{owned.key}" not in gaps(seeded)["ownership"]


def test_gaps_are_complete_and_not_truncated(seeded: ExistenceRegistry):
    found = gaps(seeded)
    report = assess(seeded)
    for row in report["possessions"]:
        assert row["missing"] == len(found[row["possession"]])
        assert len(row["examples"]) <= 5


def test_the_per_form_breakdown_agrees_with_the_whole(seeded: ExistenceRegistry):
    """Item 5: forms, relationship types, topologies … each measured, by group-by."""
    per_form = assess_by_form(seeded)
    assert set(per_form) == {u.form for u in seeded.units()}
    for possession, _ in POSSESSIONS:
        total = sum(f["by_possession"][possession]["held"] for f in per_form.values())
        row = next(p for p in assess(seeded)["possessions"] if p["possession"] == possession)
        assert total == row["held"], possession


def test_form_level_failure_is_visible_even_when_most_forms_pass(seeded):
    """Steering 014: aggregate success must never hide a form failure."""
    per_form = assess_by_form(seeded)
    assert any(f["incomplete"] for f in per_form.values())
    for form in per_form.values():
        assert form["units"] > 0


def test_completeness_is_measured_with_its_denominator(seeded: ExistenceRegistry):
    metrics = completeness(seeded)
    assert metrics["required"] == metrics["units"] * len(POSSESSIONS)
    assert 0.0 < metrics["ratio"] < 1.0
    assert metrics["complete"] is False
    assert metrics["by_possession"]["identity"]["held"] == metrics["units"]


def test_the_gate_fails_closed_and_names_what_is_missing(seeded: ExistenceRegistry):
    with pytest.raises(CEUError) as caught:
        require_complete(seeded)
    missing = caught.value.detail["missing"]
    assert "governance" in missing
    assert missing["governance"], "the refusal must name units, not merely the possession"


def test_the_gate_may_be_narrowed_explicitly(seeded: ExistenceRegistry):
    assert require_complete(seeded, possessions=STRUCTURAL)
    with pytest.raises(CEUError):
        require_complete(seeded, possessions=(*STRUCTURAL, "governance"))


def test_narrowing_to_an_unknown_possession_is_refused(seeded: ExistenceRegistry):
    with pytest.raises(CEUError) as caught:
        require_complete(seeded, possessions=("vibes",))
    assert caught.value.detail["unknown"] == ["vibes"]


def _fully_possess(registry: ExistenceRegistry, targets: tuple[str, ...]) -> None:
    """Confer governance, ownership and evidence on exactly ``targets``."""
    view = relationship_view(registry)
    authority = registry.register(
        ExistenceUnit(form="authority", key="commission", title="Commission")
    )
    nucleus = registry.unit("classification", "nucleus").universal_id
    evidence = registry.register(
        ExistenceUnit(form="evidence", key="proof", title="Proof", classification=nucleus)
    )
    for target in targets:
        view.relate("governs", authority.universal_id, target, authority="GOV")
        view.relate("owns", authority.universal_id, target, authority="GOV")
        view.relate("evidences", evidence.universal_id, target, authority="GOV")


def test_the_gate_is_reachable_in_the_pass_direction():
    """A named population can hold all ten — so the gate is not merely unsatisfiable."""
    registry = bootstrap()
    registry.bind_context(FRAME)
    subjects = tuple(u.universal_id for u in registry.units(form="classification"))
    _fully_possess(registry, subjects)
    found = gaps(registry)
    labels = {f"{registry.resolve(s).form}:{registry.resolve(s).key}" for s in subjects}
    for possession, _ in POSSESSIONS:
        assert labels.isdisjoint(found[possession]), possession


def test_full_possession_of_everything_is_a_fixpoint_the_naive_pass_never_reaches():
    """A consequence of CEU-003 worth stating rather than hiding.

    Relationships are units. Conferring governance, ownership and evidence on every unit
    therefore *creates* three new units per unit, each itself unpossessed. One pass never
    converges, and a gate that reported completeness after one pass would be wrong. The
    lawful routes are to govern relationships reflexively or to narrow the gate to the
    possessions a stage requires — never to stop counting relationships as units.
    """
    registry = bootstrap()
    registry.bind_context(FRAME)
    before = len(registry.units())
    _fully_possess(registry, tuple(u.universal_id for u in registry.units()))
    assert len(registry.units()) > before * 3
    report = assess(registry)
    assert report["complete"] is False
    assert set(report["incomplete"]) <= {"governance", "ownership", "relationships", "evidence"}
    # and the units that were targeted did gain what they were given
    assert report["possessions"][0]["complete"] is True


def test_the_report_is_deterministic(seeded: ExistenceRegistry):
    assert assess(seeded) == assess(seeded)
    assert completeness(seeded) == completeness(seeded)


# --------------------------------------------------------------------------- #
# Steering 014 — four-level fail-closed                                        #
# --------------------------------------------------------------------------- #


def test_certification_executes_at_four_levels(seeded: ExistenceRegistry):
    report = certify_levels(seeded)
    assert [level["level"] for level in report["levels"]] == list(LEVELS)
    assert report["certified"] is False


def test_no_level_can_mask_a_lower_one(seeded: ExistenceRegistry):
    """A unit failure must surface at form and registry level too, never be averaged away."""
    report = certify_levels(seeded)
    assert {"unit", "form", "registry"} <= set(report["failing_levels"])
    for name in ("unit", "form", "registry"):
        level = next(lvl for lvl in report["levels"] if lvl["level"] == name)
        assert level["passed"] is False
        assert level["failing"]


def test_classification_level_only_judges_units_that_declare_one(seeded):
    """Not a mask: a unit with no classification cannot fail *at classification level*.

    It still fails at unit, form and registry level, so nothing is hidden — the level
    simply reports about the thing it is a level over.
    """
    report = certify_levels(seeded)
    classification = next(lvl for lvl in report["levels"] if lvl["level"] == "classification")
    assert classification["passed"] is True
    assert report["certified"] is False


def test_a_narrowed_gate_certifies_at_every_level(seeded: ExistenceRegistry):
    report = certify_levels(seeded, possessions=STRUCTURAL)
    assert report["certified"] is True
    assert report["failing_levels"] == []
    assert all(level["passed"] for level in report["levels"])


def test_one_incomplete_unit_fails_every_level():
    """The decisive case: a single bad unit must not be diluted by a large good set."""
    registry = bootstrap()
    registry.bind_context(FRAME)
    subjects = tuple(u.universal_id for u in registry.units())
    _fully_possess(registry, subjects)
    report = certify_levels(registry, possessions=("governance",))
    assert report["certified"] is False
    # the relationship units created by _fully_possess are themselves ungoverned
    assert report["levels"][0]["failing_count"] > 0
    assert "relationship" in report["levels"][1]["failing"]


def test_require_certified_fails_closed_and_names_the_levels(seeded: ExistenceRegistry):
    with pytest.raises(CEUError) as caught:
        require_certified(seeded)
    assert {"unit", "form", "registry"} <= set(caught.value.detail["failing_levels"])
    assert caught.value.detail["levels"]["form"]


def test_require_certified_passes_on_a_narrowed_gate(seeded: ExistenceRegistry):
    assert require_certified(seeded, possessions=STRUCTURAL)["certified"] is True


def test_level_certification_refuses_an_unknown_possession(seeded: ExistenceRegistry):
    with pytest.raises(CEUError):
        certify_levels(seeded, possessions=("vibes",))


def test_level_certification_is_deterministic(seeded: ExistenceRegistry):
    assert certify_levels(seeded) == certify_levels(seeded)


# --------------------------------------------------------------------------- #
# Steering 017 — evolution preserves replayability                             #
# --------------------------------------------------------------------------- #


def test_supersession_preserves_historical_reconstruction(seeded: ExistenceRegistry):
    """Erasure of constitutional history is not permitted; supersession is."""
    subject = seeded.unit("classification", "layer")
    before = seeded.to_document()
    seeded.supersede(subject.universal_id, authority="GOV")
    after = seeded.to_document()
    # the unit is still resolvable, still identified, still journaled
    assert seeded.resolve(subject.universal_id) == subject
    assert seeded.audit(subject=subject.universal_id)
    # nothing was removed: the population only grew a supersession record
    assert len(after["units"]) == len(before["units"])
    assert after["supersessions"] and not before["supersessions"]


def test_resurrection_does_not_erase_the_supersession(seeded: ExistenceRegistry):
    subject = seeded.unit("classification", "layer")
    seeded.supersede(subject.universal_id, authority="GOV")
    seeded.resurrect(subject.universal_id, authority="GOV")
    actions = [entry.action for entry in seeded.audit(subject=subject.universal_id)]
    assert actions == ["register", "supersede", "resurrect"]
    assert seeded.supersessions()
