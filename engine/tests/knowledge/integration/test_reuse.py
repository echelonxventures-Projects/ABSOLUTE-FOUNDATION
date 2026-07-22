"""Tests for engine.knowledge.integration.reuse — Deliverable 5."""

from __future__ import annotations

from engine.knowledge.integration.contracts import Disposition
from engine.knowledge.integration.reuse import ReuseEngine
from engine.knowledge.store import KnowledgeBase

from .conftest import make_cko, make_intent


def test_reuse_on_semantic_twin(base):
    engine = ReuseEngine(base)
    # identical substance to COMP-A, same owner -> reuse
    intent = make_intent("NEW", statement="the alpha component substance", owner="TEAM-A")
    assessment = engine.assess(intent)
    assert assessment.disposition is Disposition.REUSE
    assert "COMP-A" in assessment.targets
    assert not assessment.requires_creation
    assert assessment.candidates[0].to_dict()["relation"] == "semantic"


def test_extend_on_same_kind_universe(base):
    engine = ReuseEngine(base)
    intent = make_intent(
        "NEW", title="alpha component v2", statement="alpha component substance improved"
    )
    assessment = engine.assess(intent)
    assert assessment.disposition is Disposition.EXTEND
    assert assessment.targets == ("COMP-A",)
    assert "COMP-A" in assessment.to_dict()["targets"]


def test_compose_on_existing_components(base):
    engine = ReuseEngine(base)
    intent = make_intent(
        "NEW",
        title="Zeta",
        statement="orchestrating flows via bindings",
        dependencies=("COMP-A", "COMP-B"),
    )
    assessment = engine.assess(intent)
    assert assessment.disposition is Disposition.COMPOSE
    assert assessment.targets == ("COMP-A", "COMP-B")


def test_create_when_nothing_reusable():
    engine = ReuseEngine(KnowledgeBase([]))
    assessment = engine.assess(make_intent("NEW"))
    assert assessment.disposition is Disposition.CREATE
    assert assessment.requires_creation
    assert assessment.reasons


def test_compose_needs_two_active_components():
    # only one resolvable component -> not compose (falls through to create)
    base = KnowledgeBase([make_cko("ONLY-A")])
    engine = ReuseEngine(base)
    intent = make_intent(
        "NEW", title="Zeta", statement="orchestrating flows", dependencies=("ONLY-A", "MISSING")
    )
    assert engine.assess(intent).disposition is Disposition.CREATE
