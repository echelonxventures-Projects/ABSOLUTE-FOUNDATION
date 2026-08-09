"""UCXI-000001 Part 15 — the location axis and location-derived resolution.

What these tests are trying to break, stated plainly, because a test that only confirms
the happy path is a test that will pass on the day the architecture stops working:

    * that an axis value could come from anywhere but the frame chain;
    * that an unresolved axis could quietly acquire a default;
    * that the derivation order could be hardcoded rather than derived;
    * that a new axis or a new frame kind could require a code change;
    * that two runs could disagree.
"""

from __future__ import annotations

import pytest

from engine.context.errors import ContextValidationError, TaxonomyError
from engine.context.location import (
    AXIS_DERIVATION,
    AXIS_GRAPH,
    FRAME_NAMESPACE,
    LOCATION,
    UNRESOLVED,
    FrameRegistry,
    LocationResolution,
    ReferenceFrame,
    ResolvedAxis,
    axis_order,
    axis_waves,
    build_context_registry,
    build_frame_registry,
    context_registries,
    declarations_for,
    derivation_path,
    empty_context_registry,
    extended_ontology,
    extended_taxonomy,
    frames_from_catalog,
    identity_tuples,
    introduced_axes,
    load_catalog,
    location_determined_axes,
    register_resolution,
    to_document,
)
from engine.context.taxonomy import UNIVERSAL_TAXONOMY, ContextAuthority
from engine.registry.universal.identity import parse_kind_name


@pytest.fixture
def frames() -> FrameRegistry:
    return build_frame_registry()


# --------------------------------------------------------------------------- #
# The derivation graph                                                         #
# --------------------------------------------------------------------------- #


def test_location_is_the_root_every_derived_axis_hangs_from():
    determined = location_determined_axes()
    assert LOCATION not in determined
    assert set(determined) <= set(AXIS_GRAPH)
    for axis in determined:
        assert LOCATION in derivation_path(axis), axis


def test_every_axis_the_mission_names_derives_from_location():
    # The seven the brief calls out by name, plus the two it implies.
    for axis in (
        "currency",
        "language",
        "calendar",
        "time-standard",
        "units",
        "tax",
        "jurisdiction",
        "governance",
        "regulation",
    ):
        assert axis in location_determined_axes(), axis


def test_the_order_is_derived_by_the_single_ordering_authority():
    order = axis_order()
    assert len(order) == len(AXIS_DERIVATION)
    position = {axis: index for index, axis in enumerate(order)}
    for axis, requires in AXIS_DERIVATION:
        for required in requires:
            assert position[required] < position[axis], f"{required} must precede {axis}"


def test_axes_that_do_not_depend_on_each_other_share_a_wave():
    waves = {axis: wave for wave, axis in axis_waves()}
    assert waves["calendar"] == waves["time-standard"] == waves["language"]
    assert waves["existence"] < waves[LOCATION] < waves["tax"]


def test_derivation_path_is_the_transitive_closure():
    assert derivation_path("existence") == ()
    assert set(derivation_path("tax")) >= {LOCATION, "jurisdiction", "currency", "units"}


def test_an_unknown_axis_has_no_derivation_path():
    with pytest.raises(ContextValidationError):
        derivation_path("astrology")


# --------------------------------------------------------------------------- #
# Reference frames                                                             #
# --------------------------------------------------------------------------- #


def test_a_frame_mints_its_identity_through_the_one_authority(frames: FrameRegistry):
    frame = frames.frame("planetary-a1")
    assert frame.universal_id.startswith("UCOS-LOC-")
    assert parse_kind_name(frame.universal_id) == "LOCATION"


def test_a_frame_may_only_declare_a_registered_axis():
    with pytest.raises(ContextValidationError):
        ReferenceFrame(key="k", title="t", frame_kind="physical", axes={"astrology": "x"})


def test_a_frame_axis_value_must_be_a_non_empty_reference():
    with pytest.raises(ContextValidationError):
        ReferenceFrame(key="k", title="t", frame_kind="physical", axes={"calendar": "  "})


@pytest.mark.parametrize("field", ["key", "title", "frame_kind"])
def test_a_frame_must_declare_its_own_fields(field: str):
    kwargs = {"key": "k", "title": "t", "frame_kind": "physical"}
    kwargs[field] = ""
    with pytest.raises(ContextValidationError):
        ReferenceFrame(**kwargs)


def test_a_frame_kind_is_open_and_nothing_branches_on_it():
    registry = FrameRegistry()
    exotic = registry.register(
        ReferenceFrame(key="k", title="t", frame_kind="something-nobody-has-named")
    )
    assert exotic.frame_kind in registry.frame_kinds()
    assert registry.resolve("k").unresolved_axes == tuple(axis_order())


def test_a_duplicate_frame_is_refused():
    registry = FrameRegistry([ReferenceFrame(key="k", title="t", frame_kind="physical")])
    with pytest.raises(ContextValidationError):
        registry.register(ReferenceFrame(key="k", title="other", frame_kind="virtual"))


def test_a_frame_whose_parent_is_unregistered_is_refused():
    registry = FrameRegistry()
    with pytest.raises(ContextValidationError):
        registry.register(
            ReferenceFrame(key="child", title="t", frame_kind="physical", parent="absent")
        )


def test_an_unregistered_frame_does_not_resolve(frames: FrameRegistry):
    with pytest.raises(ContextValidationError):
        frames.frame("nowhere")


def test_the_chain_runs_from_the_frame_to_its_root(frames: FrameRegistry):
    chain = frames.chain("planetary-a1-region-r7")
    assert chain[0] == "planetary-a1-region-r7"
    assert frames.frame(chain[-1]).parent is None
    assert "planetary-a1" in chain


def test_children_are_discoverable(frames: FrameRegistry):
    assert "planetary-a1-region-r7" in frames.children("planetary-a1")


def test_frames_can_be_filtered_by_kind(frames: FrameRegistry):
    planetary = frames.frames(frame_kind="planetary")
    assert planetary
    assert {f.frame_kind for f in planetary} == {"planetary"}


# --------------------------------------------------------------------------- #
# Resolution                                                                   #
# --------------------------------------------------------------------------- #


def test_a_locality_overrides_its_planet(frames: FrameRegistry):
    planet = frames.resolve("planetary-a1")
    region = frames.resolve("planetary-a1-region-r7")
    differing = [axis for axis in axis_order() if planet.value_of(axis) != region.value_of(axis)]
    assert differing, "a region that overrides nothing proves nothing"
    for axis in differing:
        assert region.get(axis).source_frame == "planetary-a1-region-r7"


def test_an_inherited_axis_names_the_ancestor_that_declared_it(frames: FrameRegistry):
    region = frames.resolve("planetary-a1-region-r7")
    inherited = [a for a in region.axes if a.resolved and a.source_frame != region.frame]
    assert inherited
    for axis in inherited:
        assert axis.source_frame in region.chain


def test_an_undeclared_axis_resolves_to_the_stated_unknown(frames: FrameRegistry):
    resolution = frames.resolve("unresolved")
    assert resolution.unresolved_axes == tuple(axis_order())
    assert not resolution.complete
    for axis in resolution.axes:
        assert axis.value == UNRESOLVED
        assert axis.source_frame == ""


def test_a_partial_frame_reports_exactly_its_gaps(frames: FrameRegistry):
    resolution = frames.resolve("partial-frame-p0")
    assert resolution.resolved_axes
    assert resolution.unresolved_axes
    assert not resolution.complete
    assert set(resolution.resolved_axes) & set(resolution.unresolved_axes) == set()


def test_every_resolved_axis_carries_its_declared_provenance(frames: FrameRegistry):
    resolution = frames.resolve("planetary-a1")
    for axis in resolution.axes:
        assert axis.derived_from == derivation_path(axis.axis)


def test_a_resolution_reports_how_many_axes_are_location_derived(frames: FrameRegistry):
    resolution = frames.resolve("planetary-a1")
    assert resolution.complete
    assert resolution.location_derived_count() == len(location_determined_axes()) + 1


def test_asking_for_an_axis_that_was_not_resolved_fails_closed(frames: FrameRegistry):
    with pytest.raises(ContextValidationError):
        frames.resolve("planetary-a1").get("astrology")


def test_resolution_is_a_fixed_point(frames: FrameRegistry):
    assert frames.resolve("planetary-a1").digest() == frames.resolve("planetary-a1").digest()


def test_two_independently_built_registries_agree():
    assert build_frame_registry().digest() == build_frame_registry().digest()


def test_the_resolved_axis_knows_whether_it_is_location_derived():
    axis = ResolvedAxis(axis="calendar", value="v", source_frame="f", derived_from=(LOCATION,))
    assert axis.location_derived and axis.resolved
    root = ResolvedAxis(axis=LOCATION, value=UNRESOLVED, source_frame="", derived_from=())
    assert root.location_derived and not root.resolved


# --------------------------------------------------------------------------- #
# Rebase — the AC-007 proof                                                    #
# --------------------------------------------------------------------------- #


def test_changing_the_frame_re_resolves_every_dependent_axis(frames: FrameRegistry):
    report = frames.rebase("subject", frame_keys=["planetary-a1", "planetary-b4"])
    assert report["differing_count"] > 0
    for axis in location_determined_axes():
        assert axis in report["axes_differing"], axis


def test_rebasing_onto_the_same_frame_changes_nothing(frames: FrameRegistry):
    report = frames.rebase("subject", frame_keys=["planetary-a1", "planetary-a1"])
    assert report["axes_differing"] == []


def test_a_rebase_carries_a_digest_per_frame(frames: FrameRegistry):
    report = frames.rebase("s", frame_keys=["planetary-a1", "virtual-realm-v9"])
    assert set(report["digests"]) == {"planetary-a1", "virtual-realm-v9"}
    assert len(set(report["digests"].values())) == 2


# --------------------------------------------------------------------------- #
# The catalogue is data                                                        #
# --------------------------------------------------------------------------- #


def test_the_catalogue_ships_as_package_data():
    payload = load_catalog()
    assert isinstance(payload["frames"], list) and payload["frames"]


def test_a_malformed_catalogue_is_refused():
    with pytest.raises(ContextValidationError):
        frames_from_catalog(
            {"frames": [{"key": "a", "title": "t", "frame_kind": "k", "parent": "missing"}]}
        )


def test_a_catalogue_without_frames_is_refused():
    with pytest.raises(ContextValidationError):
        frames_from_catalog({"not-frames": []})  # type: ignore[arg-type]


def test_catalogue_frames_are_ordered_so_parents_precede_children():
    built = frames_from_catalog()
    seen: set[str] = set()
    for frame in built:
        if frame.parent is not None:
            assert frame.parent in seen
        seen.add(frame.key)


def test_a_new_frame_needs_no_code_change():
    """The open-world test: a civilisation nobody has met is a JSON object."""
    payload = {
        "frames": [
            {
                "key": "root",
                "title": "R",
                "frame_kind": "universal",
                "axes": {"existence": "e", "reality": "r"},
            },
            {
                "key": "elsewhere",
                "title": "E",
                "frame_kind": "galactic",
                "parent": "root",
                "axes": {axis: f"{axis}.authority" for axis, _ in AXIS_DERIVATION},
            },
        ]
    }
    registry = FrameRegistry(frames_from_catalog(payload))
    resolution = registry.resolve("elsewhere")
    assert resolution.complete
    assert resolution.location_derived_count() == len(location_determined_axes()) + 1


def test_no_axis_value_appears_in_the_module_source():
    """AC-001, checked mechanically: every resolved value traces to the catalogue."""
    import inspect

    from engine.context import location

    source = inspect.getsource(location)
    catalog = build_frame_registry()
    values = {
        axis.value
        for frame in catalog.frames()
        for axis in catalog.resolve(frame.key).axes
        if axis.resolved
    }
    assert values, "nothing resolved, so the check would be vacuous"
    for value in values:
        assert value not in source, f"{value!r} is hardcoded in the resolver"


# --------------------------------------------------------------------------- #
# Integration with the context layer                                           #
# --------------------------------------------------------------------------- #


def test_the_taxonomy_is_extended_not_replaced():
    extended = extended_taxonomy()
    for axis, _ in AXIS_DERIVATION:
        assert extended.taxon_for_kind(axis) is not None
    # the axes the context layer already owns keep their original taxon
    assert extended.taxon_for_kind("existence") == UNIVERSAL_TAXONOMY.taxon_for_kind("existence")


def test_the_universal_taxonomy_itself_is_untouched():
    extended_taxonomy()
    with pytest.raises(TaxonomyError):
        UNIVERSAL_TAXONOMY.taxon_for_kind("calendar")


def test_the_ontology_declares_one_shape_for_every_introduced_axis():
    ontology = extended_ontology()
    for axis in introduced_axes():
        names = {spec.name for spec in ontology.dimensions_for(axis)}
        assert names == {"authority", "frame"}


def test_an_axis_the_context_layer_already_owns_is_not_re_shaped():
    for owned in ("existence", "reality", "governance"):
        assert owned not in introduced_axes()


def test_only_resolved_axes_become_declarations(frames: FrameRegistry):
    declarations = declarations_for(frames.resolve("partial-frame-p0"))
    resolution = frames.resolve("partial-frame-p0")
    declared = {d.kind for d in declarations}
    assert declared <= set(resolution.resolved_axes)
    assert declared.isdisjoint(resolution.unresolved_axes)


def test_a_declaration_carries_the_frame_that_supplied_the_value(frames: FrameRegistry):
    for declaration in declarations_for(frames.resolve("planetary-a1-region-r7")):
        values = declaration.value_mapping()
        assert values["frame"] in frames.chain("planetary-a1-region-r7")
        assert declaration.boundary == "planetary-a1-region-r7"


def test_one_frame_projects_into_one_registered_context_set(frames: FrameRegistry):
    registry = build_context_registry("planetary-a1", frames=frames)
    assert len(registry) == len(introduced_axes())
    assert not registry.verify_audit()
    for record in registry.records():
        assert record.context_id == record.expected_identity()


def test_registration_is_idempotent(frames: FrameRegistry):
    registry = empty_context_registry()
    resolution = frames.resolve("planetary-a1")
    first = register_resolution(registry, resolution)
    second = register_resolution(registry, resolution)
    assert [r.context_id for r in first] == [r.context_id for r in second]
    assert len(registry) == len(first)


def test_an_incomplete_frame_can_be_refused_at_registration(frames: FrameRegistry):
    with pytest.raises(ContextValidationError):
        register_resolution(
            empty_context_registry(), frames.resolve("partial-frame-p0"), require_complete=True
        )


def test_an_incomplete_frame_registers_only_what_it_resolved(frames: FrameRegistry):
    registry = build_context_registry("partial-frame-p0", frames=frames)
    resolved = set(frames.resolve("partial-frame-p0").resolved_axes)
    assert set(registry.kinds()) == resolved & set(introduced_axes())


def test_every_frame_gets_its_own_registry(frames: FrameRegistry):
    registries = context_registries(frames)
    assert set(registries) == set(frames.frame_keys())
    assert len(registries["planetary-a1"]) > len(registries["unresolved"])


def test_the_projection_is_deterministic(frames: FrameRegistry):
    first = build_context_registry("planetary-a1", frames=frames).seal()
    second = build_context_registry("planetary-a1", frames=frames).seal()
    assert first == second


def test_two_frames_project_to_different_seals(frames: FrameRegistry):
    a = build_context_registry("planetary-a1", frames=frames).seal()
    b = build_context_registry("planetary-b4", frames=frames).seal()
    assert a != b


# --------------------------------------------------------------------------- #
# Identity                                                                     #
# --------------------------------------------------------------------------- #


def test_every_assigned_identifier_parses_under_the_one_grammar(frames: FrameRegistry):
    from engine.registry.universal.identity import deterministic_id, is_well_formed

    tuples = identity_tuples(frames)
    assert tuples
    for kind, namespace, natural_key in tuples:
        assert namespace == FRAME_NAMESPACE
        assert is_well_formed(deterministic_id(kind, namespace, natural_key))


def test_no_two_subjects_claim_one_identifier(frames: FrameRegistry):
    from engine.registry.universal.identity import deterministic_id

    tuples = identity_tuples(frames)
    minted = [deterministic_id(*t) for t in tuples]
    assert len(set(minted)) == len(minted)


def test_the_context_identity_agrees_with_the_registry(frames: FrameRegistry):
    from engine.registry.universal.identity import deterministic_id

    registry = build_context_registry("planetary-a1", frames=frames)
    registered = {record.context_id for record in registry.records()}
    for kind, namespace, natural_key in identity_tuples(frames):
        if kind == "CONTEXT" and natural_key.startswith("planetary-a1."):
            assert deterministic_id(kind, namespace, natural_key) in registered


# --------------------------------------------------------------------------- #
# The document                                                                 #
# --------------------------------------------------------------------------- #


def test_the_architecture_document_declares_no_default_and_no_ceiling(frames: FrameRegistry):
    document = to_document(frames)
    assert document["defaults"] == []
    assert document["closed_set"] is False
    assert document["upper_limit"] is None
    assert document["unresolved_marker"] == UNRESOLVED


def test_the_document_reports_coverage_per_frame(frames: FrameRegistry):
    coverage = to_document(frames)["coverage"]
    assert coverage["frame_count"] == len(frames)
    assert coverage["complete_frames"] + coverage["incomplete_frames"] == len(frames)


def test_the_document_is_deterministic(frames: FrameRegistry):
    assert to_document(frames) == to_document(frames)


def test_a_resolution_renders_its_own_gaps(frames: FrameRegistry):
    payload: dict = frames.resolve("partial-frame-p0").to_dict()
    assert payload["complete"] is False
    assert payload["unresolved"]
    assert set(payload["resolved"]).isdisjoint(payload["unresolved"])


def test_a_resolution_exposes_its_values_as_a_mapping(frames: FrameRegistry):
    resolution: LocationResolution = frames.resolve("planetary-a1")
    mapping = resolution.value_mapping()
    assert set(mapping) == set(axis_order())
    assert mapping[LOCATION] == resolution.value_of(LOCATION)


def test_declarations_carry_the_declared_authority(frames: FrameRegistry):
    declarations = declarations_for(
        frames.resolve("planetary-a1"), authority=ContextAuthority.CONSTITUTIONAL
    )
    assert declarations
    for declaration in declarations:
        assert declaration.authority is ContextAuthority.CONSTITUTIONAL
