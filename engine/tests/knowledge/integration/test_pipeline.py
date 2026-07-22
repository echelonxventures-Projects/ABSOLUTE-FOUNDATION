"""Tests for engine.knowledge.integration.pipeline — the constitutional execution path."""

from __future__ import annotations

import pytest

from engine.knowledge.integration.contracts import Operation, SequenceStage
from engine.knowledge.integration.errors import IntegrationError
from engine.knowledge.integration.pipeline import ConstitutionalPipeline, Outcome, StageStatus
from engine.knowledge.model import KnowledgeAuthority, KnowledgeKind, Lifecycle
from engine.knowledge.store import KnowledgeBase

from .conftest import make_cko, make_intent


def test_create_novel(empty_base):
    decision = ConstitutionalPipeline(empty_base).execute(make_intent("N-1"))
    assert decision.outcome is Outcome.CREATED
    assert decision.accepted
    assert decision.artifact["cko_id"] == "N-1"
    # every sequence stage is recorded
    recorded = {s.stage for s in decision.stages}
    assert recorded == set(SequenceStage)
    assert decision.stage(SequenceStage.CREATE).status is StageStatus.DONE
    assert decision.to_dict()["outcome"] == "created"


def test_modify_existing_evolves_in_place():
    base = KnowledgeBase([make_cko("M", owner="TEAM-A")])
    intent = make_intent(
        "M", owner="TEAM-A", operation=Operation.MODIFY, statement="revised distinct wording now"
    )
    decision = ConstitutionalPipeline(base).execute(intent)
    assert decision.outcome is Outcome.MODIFIED
    assert decision.accepted
    assert decision.stage(SequenceStage.CREATE).status is StageStatus.SKIPPED
    assert any("evolves the existing" in r for r in decision.reasons)


def test_modify_missing_blocked():
    decision = ConstitutionalPipeline(KnowledgeBase([])).execute(
        make_intent("MISSING", operation=Operation.MODIFY)
    )
    assert decision.outcome is Outcome.BLOCKED
    assert not decision.accepted


def test_create_duplicate_identity_blocked(base):
    decision = ConstitutionalPipeline(base).execute(make_intent("COMP-A"))
    assert decision.outcome is Outcome.BLOCKED


def test_reuse_pure_semantic_twin():
    base = KnowledgeBase([make_cko("TW", statement="reusable substance", owner="TEAM-A")])
    intent = make_intent("NEW", statement="reusable substance", owner="TEAM-A")
    decision = ConstitutionalPipeline(base).execute(intent)
    assert decision.outcome is Outcome.REUSED
    assert decision.artifact["cko_id"] == "TW"


def test_foreign_owner_twin_blocked():
    base = KnowledgeBase([make_cko("TW", statement="reusable substance", owner="OTHER")])
    intent = make_intent("NEW", statement="reusable substance", owner="TEAM-A")
    decision = ConstitutionalPipeline(base).execute(intent)
    assert decision.outcome is Outcome.BLOCKED
    assert "overlapping-ownership" in decision.reasons


def test_extend(base):
    intent = make_intent(
        "NEW", title="alpha component v2", statement="alpha component substance improved"
    )
    decision = ConstitutionalPipeline(base).execute(intent)
    assert decision.outcome is Outcome.EXTENDED
    assert decision.stage(SequenceStage.EXTEND).status is StageStatus.DONE


def test_compose(base):
    intent = make_intent(
        "NEW",
        title="Zeta",
        statement="orchestrating flows via bindings",
        dependencies=("COMP-A", "COMP-B"),
    )
    decision = ConstitutionalPipeline(base).execute(intent)
    assert decision.outcome is Outcome.COMPOSED
    assert decision.stage(SequenceStage.COMPOSE).status is StageStatus.DONE


def test_governance_kind_grounds_in_evolve():
    principle = make_cko(
        "P",
        universe="GOV",
        kind=KnowledgeKind.PRINCIPLE,
        authority=KnowledgeAuthority.CONSTITUTIONAL,
        lifecycle=Lifecycle.RATIFIED,
    )
    intent = make_intent(
        "POL-1",
        universe="GOV",
        kind=KnowledgeKind.POLICY,
        statement="a distinct governance policy body",
        dependencies=("P",),
        knowledge_links=("P",),
    )
    decision = ConstitutionalPipeline(KnowledgeBase([principle])).execute(intent)
    assert decision.accepted
    evolve = decision.stage(SequenceStage.EVOLVE)
    assert "governance" in evolve.detail
    assert evolve.detail["governance"]["grounded"] is True


def test_require_raises_on_block_and_returns_on_accept(empty_base):
    pipe = ConstitutionalPipeline(empty_base)
    assert pipe.require(make_intent("OK-1")).accepted
    with pytest.raises(IntegrationError):
        pipe.require(make_intent("MISSING", operation=Operation.MODIFY))
