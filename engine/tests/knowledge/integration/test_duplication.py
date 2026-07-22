"""Tests for engine.knowledge.integration.duplication — Deliverable 6 (fail-closed)."""

from __future__ import annotations

import pytest

from engine.knowledge.integration.duplication import DuplicatePreventionEngine
from engine.knowledge.integration.errors import DuplicationViolationError
from engine.knowledge.store import KnowledgeBase

from .conftest import make_cko, make_intent


def test_clean_intent(base):
    report = DuplicatePreventionEngine(base).screen(make_intent("NOVEL"))
    assert report.clean
    assert report.to_dict()["clean"] is True


def test_duplicate_identity(base):
    report = DuplicatePreventionEngine(base).screen(make_intent("COMP-A"))
    assert "duplicate-identity" in report.kinds()


def test_semantic_duplicate_and_overlapping_ownership():
    base = KnowledgeBase([make_cko("TWIN", statement="twin substance", owner="TEAM-A")])
    intent = make_intent("NEW", statement="twin substance", owner="TEAM-B")
    kinds = DuplicatePreventionEngine(base).screen(intent).kinds()
    assert "semantic-duplicate" in kinds
    assert "overlapping-ownership" in kinds


def test_conflicting_capability():
    base = KnowledgeBase([make_cko("ORIG", title="Shared Name", statement="original substance")])
    intent = make_intent("NEW", title="Shared Name", statement="different substance")
    assert "conflicting-capability" in DuplicatePreventionEngine(base).screen(intent).kinds()


def test_parallel_implementation():
    base = KnowledgeBase(
        [make_cko("P1", title="P One", statement="alpha beta gamma delta epsilon")]
    )
    intent = make_intent("NEW", title="P Two", statement="epsilon delta gamma beta alpha")
    report = DuplicatePreventionEngine(base).screen(intent)
    assert "parallel-implementation" in report.kinds()
    assert report.violations[0].to_dict()["kind"]


def test_redundant_universe():
    base = KnowledgeBase([make_cko("U1")])  # universe TEST
    intent = make_intent("NEW", universe="T.E.S.T", statement="wholly unique substance here")
    assert "redundant-universe" in DuplicatePreventionEngine(base).screen(intent).kinds()


def test_require_raises(base):
    engine = DuplicatePreventionEngine(base)
    with pytest.raises(DuplicationViolationError):
        engine.require(make_intent("COMP-A"))
    # a clean intent returns its report
    assert engine.require(make_intent("NOVEL")).clean
