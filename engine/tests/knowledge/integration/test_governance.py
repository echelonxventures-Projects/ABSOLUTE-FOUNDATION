"""Tests for engine.knowledge.integration.governance — Deliverable 8."""

from __future__ import annotations

import pytest

from engine.knowledge.cko import DecisionRecord
from engine.knowledge.integration.errors import GovernanceGroundingError
from engine.knowledge.integration.governance import GovernanceIntegration
from engine.knowledge.model import KnowledgeAuthority, KnowledgeKind, Lifecycle
from engine.knowledge.store import KnowledgeBase

from .conftest import make_cko


def _decision(decision_id: str, **overrides) -> DecisionRecord:
    fields = {
        "decision_id": decision_id,
        "title": f"Decision {decision_id}",
        "problem_statement": "A problem.",
        "context": "Some context.",
        "objective": "An objective.",
        "chosen_architecture": "The chosen architecture.",
        "rationale": "Because.",
        "authority": KnowledgeAuthority.ARCHITECTURAL,
        "owner": "OWN",
        "lifecycle": Lifecycle.RATIFIED,
        "version": "1.0.0",
        "review_authority": "REV",
        "supersession_rules": "Only by successor.",
        "alternatives": ("A", "B"),
    }
    fields.update(overrides)
    return DecisionRecord.create(**fields)


def _grounded_base() -> KnowledgeBase:
    principle = make_cko(
        "P",
        kind=KnowledgeKind.PRINCIPLE,
        authority=KnowledgeAuthority.CONSTITUTIONAL,
        lifecycle=Lifecycle.RATIFIED,
    )
    evidence = make_cko("EV", kind=KnowledgeKind.EVIDENCE)
    governance = make_cko(
        "GOV",
        kind=KnowledgeKind.DECISION,
        dependencies=("P",),
        knowledge_links=("P",),
        decision_links=("DEC-1",),
        evidence=("EV",),
    )
    return KnowledgeBase([principle, evidence, governance], [_decision("DEC-1")])


def test_bind_object_grounded():
    integ = GovernanceIntegration(_grounded_base())
    ref = integ.bind_object("GOV")
    assert ref.grounded
    assert ref.knowledge == ("P",)
    assert ref.laws == ("P",)
    assert ref.decisions == ("DEC-1",)
    assert ref.evidence == ("EV",)
    assert ref.to_dict()["grounded"] is True


def test_require_grounded_passes_and_fails():
    integ = GovernanceIntegration(_grounded_base())
    assert integ.require_grounded("GOV").grounded
    # a governance object with no references is ungrounded -> fail closed
    ungrounded = KnowledgeBase([make_cko("U", kind=KnowledgeKind.POLICY)])
    with pytest.raises(GovernanceGroundingError):
        GovernanceIntegration(ungrounded).require_grounded("U")


def test_bind_decision():
    principle = make_cko(
        "P",
        kind=KnowledgeKind.PRINCIPLE,
        authority=KnowledgeAuthority.CONSTITUTIONAL,
        lifecycle=Lifecycle.RATIFIED,
    )
    prior = _decision("PRIOR")
    record = _decision("R", dependencies=("P",), supersedes="PRIOR")
    integ = GovernanceIntegration(KnowledgeBase([principle], [prior, record]))
    ref = integ.bind_decision("R")
    assert ref.knowledge == ("P",)
    assert ref.laws == ("P",)
    assert ref.decisions == ("PRIOR",)
    assert ref.grounded
    # advisory issue recorded for missing evidence
    assert any("evidence" in issue for issue in ref.issues)
