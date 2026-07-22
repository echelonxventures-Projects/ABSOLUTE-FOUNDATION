"""Tests for engine.knowledge.integration.composition — Deliverable 10."""

from __future__ import annotations

import pytest

from engine.knowledge.integration.composition import AutonomousComposer
from engine.knowledge.integration.errors import CompositionError

from .conftest import make_intent


def _compose_intent(intent_id: str = "NEW"):
    return make_intent(
        intent_id,
        title="Zeta",
        statement="orchestrating flows via bindings",
        dependencies=("COMP-A", "COMP-B"),
    )


def test_compose_from_sufficient_components(base):
    result = AutonomousComposer(base).compose(_compose_intent())
    assert result.sufficient
    assert result.components == ("COMP-A", "COMP-B")
    assert result.composed is not None
    assert result.composed["cko_id"] == "NEW"
    assert result.validated
    assert result.certified
    assert "components" in result.to_dict()


def test_compose_insufficient(base):
    result = AutonomousComposer(base).compose(make_intent("NEW"))  # no components
    assert not result.sufficient
    assert result.composed is None
    assert result.reasons


def test_compose_existing_identity(base):
    result = AutonomousComposer(base).compose(_compose_intent("COMP-A"))
    assert not result.sufficient
    assert any("identity" in r for r in result.reasons)


def test_require_raises_when_insufficient(base):
    composer = AutonomousComposer(base)
    with pytest.raises(CompositionError):
        composer.require(make_intent("NEW"))
    # a sufficient intent returns a result
    assert composer.require(_compose_intent()).sufficient
