"""Ω∞ temporal — reference frames, time scales, and ordering as a declared discipline.

THE TWO ASSUMPTIONS UNDER TEST, and both were invisible as annotations rather than as decisions.

``default_ordering = TOTAL`` said that every pair of positions is comparable and exactly one of
precedence holds. That is true of one counter read by one observer and false of every distributed,
branching or relativistic system, and the falsehood surfaces as a WRONG ANSWER rather than as an
error — two concurrent events get an order, and the order is stable, and nothing anywhere reports
that it was invented.

A registry seeded with relations between frames would say that an Earth timestamp and a Mars sol are
comparable. ``default_frames()`` therefore ships SEVEN frames and ZERO relations: comparability
across frames is something a deployment must declare, by name and by authority.
"""

from __future__ import annotations

import pytest

from engine.omega_governance.temporal.frames import (
    EARTH_FRAME,
    INITIAL_FRAMES,
    INITIAL_SCALES,
    LOGICAL_TICK,
    MARS_FRAME,
    MARS_SOL,
    VECTOR_EVENT,
    FrameRegistry,
    FrameRelation,
    ReferenceError,
    ReferenceFrame,
    ScaleRegistry,
    TimeScale,
    default_frames,
    default_scales,
)
from engine.omega_governance.temporal.ordering import (
    AFTER,
    BEFORE,
    BRANCHING,
    CAUSAL,
    CONCURRENT,
    INCOMPARABLE,
    PARTIAL,
    SIMULTANEOUS,
    TOTAL,
    BranchingStrategy,
    CausalStrategy,
    ConsensusStrategy,
    LexicographicStrategy,
    Ordering,
    OrderingError,
    OrderingRegistry,
    Relation,
    RelationRegistry,
    assert_consistent,
    default_registry,
)

# --------------------------------------------------------------------------------- frames


def test_the_shipped_registry_declares_seven_frames_and_no_relations_between_them() -> None:
    """The absence is the deliverable. A seeded relation would assert that two frames are
    comparable, which is a physical claim this package has no standing to make."""
    registry = default_frames()
    assert len(registry) == len(INITIAL_FRAMES) == 7
    assert registry.relations() == ()


def test_earth_holds_no_privilege_over_mars_or_over_the_logical_frame() -> None:
    registry = default_frames()
    for name in ("EARTH", "MARS", "LOGICAL", "SIMULATION"):
        assert type(registry.resolve(name)) is ReferenceFrame


def test_a_frame_must_be_named() -> None:
    with pytest.raises(ReferenceError):
        ReferenceFrame("   ")


def test_an_unknown_frame_or_scale_name_is_refused() -> None:
    with pytest.raises(ReferenceError):
        default_frames().resolve("JUPITER")
    with pytest.raises(ReferenceError):
        default_scales().resolve("FURLONGS_PER_FORTNIGHT")


def test_a_frame_is_always_comparable_with_itself_and_needs_no_declaration() -> None:
    registry = default_frames()
    identity = registry.comparable(EARTH_FRAME, EARTH_FRAME)
    assert identity is not None


def test_two_frames_are_not_comparable_until_somebody_declares_the_relation() -> None:
    """The refusal that makes a Mars sol and an Earth second two different questions."""
    registry = default_frames()
    assert registry.comparable(EARTH_FRAME, MARS_FRAME) is None

    registry.relate(
        FrameRelation(
            source="EARTH",
            target="MARS",
            rule="TEST-REL-01",
            description="A declared correspondence, supplied by a mission's own ephemeris.",
        )
    )
    assert registry.comparable(EARTH_FRAME, MARS_FRAME) is not None


def test_a_symmetric_relation_is_comparable_in_both_directions() -> None:
    registry = default_frames()
    registry.relate(
        FrameRelation(source="EARTH", target="MARS", rule="TEST-REL-01", symmetric=True)
    )
    assert registry.comparable(EARTH_FRAME, MARS_FRAME) is not None
    assert registry.comparable(MARS_FRAME, EARTH_FRAME) is not None


def test_an_asymmetric_relation_is_comparable_in_one_direction_only() -> None:
    registry = default_frames()
    registry.relate(
        FrameRelation(source="EARTH", target="MARS", rule="TEST-REL-02", symmetric=False)
    )
    assert registry.comparable(EARTH_FRAME, MARS_FRAME) is not None
    assert registry.comparable(MARS_FRAME, EARTH_FRAME) is None


def test_a_frame_can_be_declared_from_primitives_with_no_edit_to_the_module() -> None:
    """Deliverable Ω∞-T3 in one call. An eighth frame nobody imagined is a registration."""
    registry = default_frames()
    declared = registry.declare_name(
        "EUROPA", "An observer on the Europan ice shell.", anchor="EUROPA", physical=True
    )
    assert registry.resolve("EUROPA") == declared
    assert len(registry) == 8


def test_redeclaring_a_frame_with_a_different_meaning_is_refused() -> None:
    registry = default_frames()
    with pytest.raises(ReferenceError):
        registry.declare(ReferenceFrame("EARTH", "somewhere else entirely", anchor="NOT-EARTH"))


def test_the_shipped_scales_include_non_numeric_and_vector_shapes() -> None:
    """A scale set of seconds-since-an-epoch would make every non-terrestrial system unrepresentable
    while looking complete."""
    registry = default_scales()
    assert len(registry) == len(INITIAL_SCALES) == 10
    assert VECTOR_EVENT.vector
    assert not LOGICAL_TICK.vector
    assert MARS_SOL.unit == "sol"


def test_a_scale_declares_the_ordering_discipline_its_positions_obey() -> None:
    assert LOGICAL_TICK.ordering == TOTAL
    assert VECTOR_EVENT.ordering == CAUSAL


def test_a_scale_must_be_named() -> None:
    with pytest.raises(ReferenceError):
        TimeScale("   ", "s", "description", TOTAL)


def test_a_scale_can_be_declared_from_primitives() -> None:
    registry = ScaleRegistry(seed=())
    registry.declare_name("HEARTBEAT", "beat", "Beats of a declared oscillator.", TOTAL)
    assert "HEARTBEAT" in registry
    assert len(registry) == 1


def test_an_empty_frame_registry_holds_nothing_and_says_so() -> None:
    empty = FrameRegistry(seed=())
    assert len(empty) == 0
    assert empty.known() == ()
    assert "EARTH" not in empty


# ------------------------------------------------------------------------------- ordering


def test_the_five_shipped_relations_carry_their_own_semantics() -> None:
    """``CONCURRENT`` and ``INCOMPARABLE`` are the two the vocabulary existed to separate: one is an
    answer about causality, the other is a refusal to answer."""
    assert BEFORE.decided and BEFORE.ordered
    assert SIMULTANEOUS.decided and SIMULTANEOUS.coincident and not SIMULTANEOUS.ordered
    assert CONCURRENT.decided and not CONCURRENT.ordered
    assert not INCOMPARABLE.decided


def test_only_the_ordered_and_coincident_relations_admit_a_claim_of_totality() -> None:
    assert BEFORE.admits_total_order
    assert AFTER.admits_total_order
    assert SIMULTANEOUS.admits_total_order
    assert not CONCURRENT.admits_total_order
    assert not INCOMPARABLE.admits_total_order


def test_the_inverse_of_a_relation_is_read_from_the_declaration_not_a_hardcoded_table() -> None:
    registry = RelationRegistry()
    assert registry.inverse_of("BEFORE") == AFTER
    assert registry.inverse_of("AFTER") == BEFORE
    assert registry.inverse_of("SIMULTANEOUS") == SIMULTANEOUS
    assert registry.inverse_of("CONCURRENT") == CONCURRENT


def test_a_sixth_relation_can_be_declared_with_no_edit_to_the_module() -> None:
    registry = RelationRegistry()
    registry.declare_name(
        "OVERLAPPING",
        "The two intervals share at least one instant.",
        decided=True,
        ordered=False,
        inverse="OVERLAPPING",
    )
    assert registry.resolve("OVERLAPPING").decided
    assert registry.inverse_of("OVERLAPPING").name == "OVERLAPPING"


def test_an_unknown_relation_is_refused_rather_than_invented() -> None:
    with pytest.raises(OrderingError):
        RelationRegistry().resolve("SORT_OF_BEFORE")


def test_only_total_declares_itself_total() -> None:
    assert TOTAL.total
    for ordering in (PARTIAL, CAUSAL, BRANCHING):
        assert not ordering.total


def test_lexicographic_orders_a_single_counter_and_reports_simultaneity() -> None:
    strategy = LexicographicStrategy()
    assert strategy.ordering() == TOTAL
    assert strategy.compare((1,), (2,)) == "BEFORE"
    assert strategy.compare((2,), (1,)) == "AFTER"
    assert strategy.compare((1,), (1,)) == "SIMULTANEOUS"


def test_lexicographic_refuses_positions_whose_components_cannot_be_compared() -> None:
    """The honest answer for ``(1,) vs ("a",)``. A total order over mutually incomparable components
    is exactly the invented answer this vocabulary exists to prevent."""
    assert LexicographicStrategy().compare((1,), ("a",)) == "INCOMPARABLE"


def test_causal_reports_genuine_concurrency_rather_than_inventing_an_order() -> None:
    """The property TOTAL could not express. Neither vector dominates, and that is an ANSWER."""
    strategy = CausalStrategy()
    assert strategy.ordering() == CAUSAL
    assert strategy.compare((1, 0), (1, 1)) == "BEFORE"
    assert strategy.compare((1, 1), (1, 0)) == "AFTER"
    assert strategy.compare((1, 1), (1, 1)) == "SIMULTANEOUS"
    assert strategy.compare((1, 0), (0, 1)) == "CONCURRENT"


def test_causal_refuses_vectors_of_different_arity() -> None:
    assert CausalStrategy().compare((1, 0), (1, 0, 0)) == "INCOMPARABLE"


def test_branching_positions_are_comparable_only_within_one_branch() -> None:
    """Two histories, not two views of one history — so the answer is INCOMPARABLE and never
    CONCURRENT, and the distinction is the whole reason BRANCHING is its own discipline."""
    strategy = BranchingStrategy()
    assert strategy.ordering() == BRANCHING
    assert strategy.compare(("main", 1), ("main", 2)) == "BEFORE"
    assert strategy.compare(("main", 1), ("fork", 2)) == "INCOMPARABLE"


def test_consensus_positions_are_comparable_only_between_agreeing_observers() -> None:
    strategy = ConsensusStrategy(agreeing=frozenset({"a", "b"}))
    assert strategy.compare(("a", 1), ("b", 2)) == "BEFORE"
    assert strategy.compare(("a", 1), ("c", 2)) == "INCOMPARABLE"


def test_the_shipped_registry_holds_four_strategies_and_five_declared_orderings() -> None:
    registry = default_registry()
    assert registry.known() == ("BRANCHING", "CAUSAL", "DISTRIBUTED", "TOTAL")
    assert len(registry.declared()) == 5


def test_partial_is_declared_as_a_vocabulary_word_with_no_strategy_bound_to_it() -> None:
    """A declared discipline nothing implements is a NAMED gap. Silently omitting PARTIAL from the
    vocabulary would have made the same gap unreportable."""
    registry = default_registry()
    assert "PARTIAL" in {ordering.name for ordering in registry.declared()}
    assert "PARTIAL" not in registry.known()
    with pytest.raises(OrderingError):
        registry.resolve("PARTIAL")


def test_a_strategy_can_be_registered_at_runtime() -> None:
    registry = OrderingRegistry()
    registry.register(LexicographicStrategy())
    assert registry.resolve("TOTAL").compare((1,), (2,)) == "BEFORE"


def test_re_registering_the_same_strategy_is_idempotent() -> None:
    """Two modules seeding the same discipline must not fight, so an identical registration is a
    no-op rather than an error."""
    registry = default_registry()
    registry.register(LexicographicStrategy())
    assert registry.known() == ("BRANCHING", "CAUSAL", "DISTRIBUTED", "TOTAL")


def test_a_second_comparison_behaviour_under_one_ordering_name_is_refused() -> None:
    """One name with two behaviours makes every claim about event order unenforceable — a caller
    asking for TOTAL would get whichever strategy registered last."""

    class RivalTotal:
        def ordering(self) -> Ordering:
            return TOTAL

        def compare(self, left: tuple[object, ...], right: tuple[object, ...]) -> str:
            return "SIMULTANEOUS"

    registry = default_registry()
    with pytest.raises(OrderingError):
        registry.register(RivalTotal())


def test_assert_consistent_accepts_a_strategy_whose_behaviour_matches_its_claim() -> None:
    relations = RelationRegistry()
    assert_consistent(LexicographicStrategy(), [(1,), (2,), (3,)], relations)
    assert_consistent(CausalStrategy(), [(1, 0), (0, 1), (1, 1)], relations)


def test_assert_consistent_refuses_a_strategy_that_claims_totality_and_returns_concurrency() -> (
    None
):
    """Non-vacuity. This is the exact defect ``default_ordering = TOTAL`` produced, caught by
    measuring the strategy's behaviour against its own declaration."""

    class LyingStrategy:
        def ordering(self) -> Ordering:
            return TOTAL

        def compare(self, left: tuple[object, ...], right: tuple[object, ...]) -> str:
            return "CONCURRENT"

    with pytest.raises(OrderingError):
        assert_consistent(LyingStrategy(), [(1,), (2,)], RelationRegistry())


def test_a_relation_naming_an_inverse_nobody_declared_is_refused() -> None:
    registry = RelationRegistry()
    registry.declare(Relation("ODD", "An outcome.", inverse="NEVER_DECLARED"))
    with pytest.raises(OrderingError):
        registry.inverse_of("ODD")
