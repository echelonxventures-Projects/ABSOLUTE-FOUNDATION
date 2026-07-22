"""Tests for engine.knowledge.cko — CKO + Universal Decision Model (Part 02/03)."""

from __future__ import annotations

import dataclasses

import pytest

from engine.knowledge.cko import CanonicalKnowledgeObject, DecisionRecord, RejectedOption
from engine.knowledge.errors import (
    KnowledgeIntegrityError,
    KnowledgeValidationError,
    LifecycleTransitionError,
)
from engine.knowledge.model import KnowledgeAuthority, KnowledgeKind, Lifecycle

from .conftest import make_cko, make_decision


def test_create_seals_hash_and_verifies():
    obj = make_cko("UCKO-T-0001")
    assert obj.content_sha256
    assert obj.verify_integrity()
    obj.require_integrity()  # no raise


def test_require_integrity_raises_after_mutation():
    obj = make_cko("UCKO-T-0002")
    mutated = dataclasses.replace(obj, title="tampered")  # hash no longer matches
    assert not mutated.verify_integrity()
    with pytest.raises(KnowledgeIntegrityError):
        mutated.require_integrity()


def test_from_dict_roundtrip_and_all_links():
    obj = make_cko(
        "UCKO-T-0003",
        parent="UCKO-P",
        children=("UCKO-C",),
        dependencies=("UCKO-D",),
        consumers=("UCKO-K",),
        supersedes=("UCKO-S",),
        superseded_by="UCKO-N",
        knowledge_links=("UCKO-L",),
    )
    restored = CanonicalKnowledgeObject.from_dict(obj.to_dict())
    assert restored == obj
    expected_links = {"UCKO-P", "UCKO-C", "UCKO-D", "UCKO-K", "UCKO-S", "UCKO-N", "UCKO-L"}
    assert set(obj.all_links()) == expected_links


def test_from_dict_without_hash_is_sealed():
    payload = make_cko("UCKO-T-0004").to_dict()
    del payload["content_sha256"]
    restored = CanonicalKnowledgeObject.from_dict(payload)
    assert restored.verify_integrity()


def test_from_dict_with_bad_stored_hash_raises():
    payload = make_cko("UCKO-T-0005").to_dict()
    payload["content_sha256"] = "0" * 64
    with pytest.raises(KnowledgeIntegrityError):
        CanonicalKnowledgeObject.from_dict(payload)


def test_from_dict_missing_required_field():
    payload = make_cko("UCKO-T-0006").to_dict()
    del payload["title"]
    with pytest.raises(KnowledgeValidationError):
        CanonicalKnowledgeObject.from_dict(payload)


def test_from_dict_type_errors():
    with pytest.raises(KnowledgeValidationError):
        CanonicalKnowledgeObject.from_dict("not a mapping")
    payload = make_cko("UCKO-T-0007").to_dict()
    payload["tags"] = ["ok", 3]
    with pytest.raises(KnowledgeValidationError):
        CanonicalKnowledgeObject.from_dict(payload)
    payload2 = make_cko("UCKO-T-0008").to_dict()
    payload2["parent"] = 5
    with pytest.raises(KnowledgeValidationError):
        CanonicalKnowledgeObject.from_dict(payload2)


def test_transition_to_legal_and_illegal():
    obj = make_cko("UCKO-T-0009", lifecycle=Lifecycle.RATIFIED)
    moved = obj.transition_to(Lifecycle.IMPLEMENTED, updated="2026-01-01")
    assert moved.lifecycle is Lifecycle.IMPLEMENTED
    assert moved.updated == "2026-01-01"
    assert moved.verify_integrity()
    with pytest.raises(LifecycleTransitionError):
        obj.transition_to(Lifecycle.HISTORICAL)


def test_is_active_property():
    assert make_cko("UCKO-T-0010", lifecycle=Lifecycle.OPERATIONAL).is_active
    assert not make_cko("UCKO-T-0011", lifecycle=Lifecycle.DRAFT).is_active


def test_semantic_hash_ignores_identity():
    a = make_cko("UCKO-A", statement="same knowledge", rationale="r")
    b = make_cko("UCKO-B", statement="same knowledge", rationale="r")
    assert a.semantic_hash() == b.semantic_hash()
    assert a.content_sha256 != b.content_sha256


def test_rejected_option_from_dict_errors():
    opt = RejectedOption.from_dict({"option": "o", "reason": "r"}, at="x")
    assert opt == RejectedOption("o", "r")
    with pytest.raises(KnowledgeValidationError):
        RejectedOption.from_dict("nope", at="x")
    with pytest.raises(KnowledgeValidationError):
        RejectedOption.from_dict({"option": "o"}, at="x")


def test_decision_create_roundtrip_and_reviewable():
    dec = make_decision("UKDA-DEC-T1")
    assert dec.is_reviewable
    assert dec.verify_integrity()
    restored = DecisionRecord.from_dict(dec.to_dict())
    assert restored == dec


def test_decision_not_reviewable_when_incomplete():
    dec = make_decision("UKDA-DEC-T2", alternatives=())
    assert not dec.is_reviewable


def test_decision_from_dict_errors():
    with pytest.raises(KnowledgeValidationError):
        DecisionRecord.from_dict("nope")
    payload = make_decision("UKDA-DEC-T3").to_dict()
    del payload["problem_statement"]
    with pytest.raises(KnowledgeValidationError):
        DecisionRecord.from_dict(payload)
    payload2 = make_decision("UKDA-DEC-T4").to_dict()
    payload2["rejected_options"] = "not-a-list"
    with pytest.raises(KnowledgeValidationError):
        DecisionRecord.from_dict(payload2)


def test_decision_bad_stored_hash_and_transition():
    payload = make_decision("UKDA-DEC-T5").to_dict()
    payload["content_sha256"] = "f" * 64
    with pytest.raises(KnowledgeIntegrityError):
        DecisionRecord.from_dict(payload)
    dec = make_decision("UKDA-DEC-T6", lifecycle=Lifecycle.RATIFIED)
    moved = dec.transition_to(Lifecycle.IMPLEMENTED)
    assert moved.lifecycle is Lifecycle.IMPLEMENTED
    with pytest.raises(LifecycleTransitionError):
        dec.transition_to(Lifecycle.HISTORICAL)


def test_decision_require_integrity_raises():
    dec = make_decision("UKDA-DEC-T7")
    mutated = dataclasses.replace(dec, rationale="changed")
    with pytest.raises(KnowledgeIntegrityError):
        mutated.require_integrity()


def test_kind_and_authority_are_enforced_on_parse():
    payload = make_cko(
        "UCKO-T-0012",
        kind=KnowledgeKind.PRINCIPLE,
        authority=KnowledgeAuthority.CONSTITUTIONAL,
    ).to_dict()
    payload["kind"] = "bogus"
    with pytest.raises(KnowledgeValidationError):
        CanonicalKnowledgeObject.from_dict(payload)
