"""Tests for engine.knowledge.integration.registration — Deliverable 9."""

from __future__ import annotations

import pytest

from engine.knowledge.integration.errors import RegistrationConflictError
from engine.knowledge.integration.registration import RegistrationIntegration

from .conftest import make_cko, make_intent


def test_plan_new_object_registers_universe_capability_dependency(base):
    integ = RegistrationIntegration(base)
    obj = make_cko("N", dependencies=("COMP-A",))
    plan = integ.plan_object(obj)
    by_cat = {(e.category, e.identifier): e for e in plan.entries}
    assert by_cat[("universe", "TEST")].status == "already-registered"
    assert by_cat[("capability", "N")].status == "registered"
    dep = by_cat[("dependency", "N-depends-on->COMP-A")]
    assert dep.status == "registered"
    assert dep.is_new
    counts = plan.counts()
    assert counts["registered"] >= 2
    assert plan.to_dict()["target"] == "N"


def test_idempotent_registration_of_existing_object(base):
    integ = RegistrationIntegration(base)
    plan = integ.plan_object(base.require_object("COMP-A"))
    # everything COMP-A introduces is already registered -> no new entries
    assert plan.new_entries == ()
    assert plan.counts()["registered"] == 0


def test_plan_intent(base):
    plan = RegistrationIntegration(base).plan_intent(make_intent("NEW"))
    assert any(e.category == "capability" and e.identifier == "NEW" for e in plan.entries)


def test_require_rejects_divergent_duplicate(base):
    integ = RegistrationIntegration(base)
    # same id, divergent content -> conflict
    with pytest.raises(RegistrationConflictError):
        integ.require(make_intent("COMP-A", statement="totally different substance"))
    # same id, identical substance -> no conflict, returns a plan
    same = make_intent("COMP-A", title="alpha component", statement="the alpha component substance")
    assert integ.require(same) is not None
