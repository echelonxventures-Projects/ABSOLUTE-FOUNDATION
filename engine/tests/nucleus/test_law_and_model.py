"""UCOS-NUC-001 — the ownership law, the structural model, and the Commerce correction."""

from __future__ import annotations

import pytest

from engine.nucleus import law
from engine.nucleus.errors import MisclassificationError, StructuralValidationError
from engine.nucleus.law import OWNERSHIP_CLAUSES, OWNERSHIP_INVARIANTS, StructuralRole
from engine.nucleus.model import (
    CapabilityDeclaration,
    OwnershipAssignment,
    SubjectDeclaration,
    SubjectRecord,
    derive_role,
)


def test_only_the_nucleus_role_may_own():
    assert StructuralRole.NUCLEUS.may_own_capability is True
    assert StructuralRole.LAYER.may_own_capability is False
    assert StructuralRole.COMPOSITION.may_own_capability is False
    assert StructuralRole.COMPOSITION.may_select_nuclei is True
    assert StructuralRole.NUCLEUS.may_select_nuclei is False


def test_role_coercion_fails_closed():
    assert StructuralRole.coerce("nucleus") is StructuralRole.NUCLEUS
    assert StructuralRole.coerce(StructuralRole.LAYER) is StructuralRole.LAYER
    with pytest.raises(StructuralValidationError):
        StructuralRole.coerce("universe")
    assert set(StructuralRole.values()) == {"nucleus", "layer", "composition"}


def test_law_document_is_complete_and_deterministic():
    document = law.to_document()
    assert document["law_id"] == law.LAW_ID
    assert len(document["clauses"]) == len(OWNERSHIP_CLAUSES) == 10
    assert len(document["invariants"]) == len(OWNERSHIP_INVARIANTS) == 10
    assert law.digest() == law.digest()
    assert law.clause("NL-02").refuses
    with pytest.raises(StructuralValidationError):
        law.clause("NL-99")


def test_law_carries_the_negative_clauses_that_were_absent():
    statements = " ".join(c.statement for c in OWNERSHIP_CLAUSES)
    assert "Layer SHALL NOT own a capability" in statements
    assert "Composition SHALL NOT own a capability" in statements
    assert "Commerce" in statements


def test_role_is_derived_from_the_declaration_itself():
    nucleus = SubjectDeclaration(key="payment", title="Payment", concept="payment")
    layer = SubjectDeclaration(key="platform", title="Platform Layer")
    composition = SubjectDeclaration(key="commerce", title="Commerce", composes=("payment",))
    assert derive_role(nucleus) is StructuralRole.NUCLEUS
    assert derive_role(layer) is StructuralRole.LAYER
    assert derive_role(composition) is StructuralRole.COMPOSITION
    assert composition.structural_role is StructuralRole.COMPOSITION


def test_commerce_cannot_be_declared_a_nucleus():
    with pytest.raises(MisclassificationError) as exc:
        SubjectDeclaration(
            key="commerce", title="Commerce Nucleus", role="nucleus", composes=("payment",)
        )
    assert exc.value.detail["derived"] == "composition"
    assert exc.value.detail["declared"] == "nucleus"


def test_a_subject_may_not_both_own_a_concept_and_compose():
    with pytest.raises(MisclassificationError):
        SubjectDeclaration(key="hybrid", title="Hybrid", concept="x", composes=("payment",))


def test_declared_role_must_match_derived_role():
    with pytest.raises(MisclassificationError):
        SubjectDeclaration(key="platform", title="Platform", role="nucleus")
    with pytest.raises(MisclassificationError):
        SubjectDeclaration(key="payment", title="Payment", role="layer", concept="payment")


def test_identity_is_derived_and_kind_specific():
    nucleus = SubjectDeclaration(key="governance", title="G", concept="governance")
    layer = SubjectDeclaration(key="governance", title="G Layer")
    assert nucleus.identity.startswith("UCOS-NUC-")
    assert layer.identity.startswith("UCOS-LYR-")
    assert nucleus.identity != layer.identity
    twin = SubjectDeclaration(key="governance", title="G", concept="governance")
    assert nucleus.identity == twin.identity


def test_records_are_sealed_and_reproduce_themselves():
    record = SubjectRecord.of(SubjectDeclaration(key="tax", title="Tax", concept="taxation"))
    assert record.is_intact()
    assert record.content_hash
    assert record.expected_identity() == record.universal_id
    tampered = SubjectRecord(
        universal_id=record.universal_id,
        key="tax",
        title="Tampered",
        role=StructuralRole.NUCLEUS,
        namespace=record.namespace,
        concept="taxation",
        content_hash=record.content_hash,
    )
    assert tampered.is_intact() is False


def test_capability_declaration_requires_an_owner():
    with pytest.raises(StructuralValidationError):
        CapabilityDeclaration(key="orphan", title="Orphan", owner="")
    declaration = CapabilityDeclaration(key="tax.rate", title="Rate", owner="tax")
    assert declaration.identity.startswith("UCOS-CAP-")


def test_declaration_refuses_malformed_fields():
    with pytest.raises(StructuralValidationError):
        SubjectDeclaration(key="k", title="")
    with pytest.raises(StructuralValidationError):
        SubjectDeclaration(key="k", title="T", composes="payment")
    with pytest.raises(StructuralValidationError):
        SubjectDeclaration(key="k", title="T", composes=("a", "a"))


def test_ownership_assignment_lawfulness_follows_the_role():
    lawful = OwnershipAssignment(
        capability_id="UCOS-CAP-000000000001",
        capability_key="tax.rate",
        owner_id="UCOS-NUC-000000000001",
        owner_key="tax",
        owner_role=StructuralRole.NUCLEUS,
        authority=law.LAW_ID,
    )
    unlawful = OwnershipAssignment(
        capability_id="UCOS-CAP-000000000001",
        capability_key="tax.rate",
        owner_id="UCOS-CMPO-000000000001",
        owner_key="commerce",
        owner_role=StructuralRole.COMPOSITION,
        authority=law.LAW_ID,
    )
    assert lawful.is_lawful is True
    assert unlawful.is_lawful is False
    assert lawful.assignment_id != unlawful.assignment_id
    assert lawful.to_dict()["owner_role"] == "nucleus"


def test_assignment_requires_an_authority():
    with pytest.raises(StructuralValidationError):
        OwnershipAssignment(
            capability_id="UCOS-CAP-000000000001",
            capability_key="tax.rate",
            owner_id="UCOS-NUC-000000000001",
            owner_key="tax",
            owner_role=StructuralRole.NUCLEUS,
            authority="",
        )


def test_structural_role_terms_are_data():
    terms = dict(law.structural_role_terms())
    assert set(terms) == {"nucleus", "layer", "composition"}
    assert "owns nothing" in terms["layer"]
    assert "owns nothing" in terms["composition"]
