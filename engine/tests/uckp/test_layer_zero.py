"""Layer Zero: the canonical primitive, the error taxonomy, identity, facets, values.

These are the modules everything else is built on, so the tests are about properties
rather than examples: determinism, purity, totality, and refusal.
"""

from __future__ import annotations

import dataclasses
import json
import uuid

import pytest

from engine.foundation.obs.errors import FoundationError
from engine.uckp.canonical import (
    CANONICAL_PROFILE,
    DIGEST_ALGORITHM,
    canonical_bytes,
    canonical_json,
    content_hash,
    digests_match,
)
from engine.uckp.errors import (
    FacetError,
    IdentityError,
    UCKPError,
)
from engine.uckp.facets import FACET_ATTRIBUTES, REQUIRED_FACETS, Facet
from engine.uckp.identity import (
    UCKO_URN_PREFIX,
    UCKP_NAMESPACE_NAME,
    UCKP_NAMESPACE_UUID,
    UniversalIdentity,
    urn_for,
    uuid_for,
)
from engine.uckp.payload import canonical_payload
from engine.uckp.values import (
    Attestation,
    AuditEntry,
    AuthorityBinding,
    Constraint,
    ContextBinding,
    DiscoveryDescriptor,
    EvidenceRef,
    MetadataSet,
    OntologyRef,
    Ownership,
    PersistenceBinding,
    Policy,
    ProjectionBinding,
    ProvenanceStep,
    Relationship,
    ReplayProof,
    SemanticIdentity,
    TaxonomyRef,
    TemporalEvent,
    TraceLink,
)

# --- canonical primitive --------------------------------------------------------


def test_canonical_json_is_sorted_compact_and_unicode_preserving():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    assert canonical_json({"k": "héllo ✓"}) == '{"k":"héllo ✓"}'


def test_canonical_json_is_order_independent():
    assert canonical_json({"a": 1, "b": 2}) == canonical_json({"b": 2, "a": 1})


def test_canonical_bytes_is_utf8_of_canonical_json():
    payload = {"k": "ünïcode"}
    assert canonical_bytes(payload) == canonical_json(payload).encode("utf-8")


def test_content_hash_is_deterministic_across_calls():
    payload = {"nested": [1, {"a": None}], "t": True}
    assert content_hash(payload) == content_hash(payload)
    assert len(content_hash(payload)) == 64


def test_content_hash_distinguishes_different_content():
    assert content_hash({"a": 1}) != content_hash({"a": 2})


def test_digests_match_is_canonical_equality_not_object_equality():
    assert digests_match({"a": 1, "b": 2}, {"b": 2, "a": 1})
    assert not digests_match({"a": 1}, {"a": "1"})


def test_the_primitive_declares_the_profile_that_produced_it():
    # A digest that cannot name its normalization is not replayable across serializers.
    assert DIGEST_ALGORITHM == "sha256"
    assert CANONICAL_PROFILE.startswith("ucos-uckp-canonical-json/")


def test_layer_zero_imports_only_the_standard_library():
    """The property that makes Layer Zero safe for the whole repository to depend on."""
    import ast
    from pathlib import Path

    source = Path(canonical_json.__code__.co_filename).read_text(encoding="utf-8")
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= {"hashlib", "json", "typing", "__future__"}


# --- errors ---------------------------------------------------------------------


def test_every_uckp_error_is_a_foundation_error_with_a_stable_code():
    assert issubclass(UCKPError, FoundationError)
    assert UCKPError.code == "UCKP-000"
    assert IdentityError.code == "UCKP-IDENTITY-001"


def test_errors_carry_structured_context():
    error = IdentityError("bad identity", urn="urn:x")
    assert "bad identity" in str(error)


# --- identity -------------------------------------------------------------------


def test_minting_is_pure_and_reproducible():
    first = UniversalIdentity.mint("ucos", "THING-1")
    second = UniversalIdentity.mint("ucos", "THING-1")
    assert first == second
    assert first.urn == f"{UCKO_URN_PREFIX}:ucos:THING-1"


def test_identity_reads_no_clock_and_no_location():
    identity = UniversalIdentity.mint("ucos", "THING-1")
    record = identity.to_dict()
    assert set(record) == {"namespace", "local_name", "urn", "uuid"}


def test_uuid_is_name_based_version_five():
    identity = UniversalIdentity.mint("ucos", "THING-1")
    assert uuid.UUID(identity.uuid).version == 5
    assert identity.uuid == uuid_for(identity.urn)
    assert UCKP_NAMESPACE_UUID == uuid.uuid5(uuid.NAMESPACE_URL, UCKP_NAMESPACE_NAME)


def test_parse_is_the_inverse_of_minting():
    identity = UniversalIdentity.mint("ucos", "THING-1")
    assert UniversalIdentity.parse(identity.urn) == identity


@pytest.mark.parametrize("bad", ["", "not-a-urn", "urn:ucos:ucko:onlynamespace"])
def test_parse_refuses_a_malformed_urn(bad):
    with pytest.raises(IdentityError):
        UniversalIdentity.parse(bad)


@pytest.mark.parametrize("namespace", ["UPPER", "", "has space", "-leading"])
def test_mint_refuses_a_malformed_namespace(namespace):
    with pytest.raises(IdentityError):
        UniversalIdentity.mint(namespace, "NAME")


@pytest.mark.parametrize("local", ["", "has space", "-leading", "x" * 200])
def test_mint_refuses_a_malformed_local_name(local):
    with pytest.raises(IdentityError):
        UniversalIdentity.mint("ucos", local)


def test_verify_detects_a_post_hoc_edit_of_a_derived_field():
    identity = UniversalIdentity.mint("ucos", "THING-1")
    assert identity.verify()
    identity.require_intact()
    tampered = UniversalIdentity(
        namespace="ucos", local_name="THING-1", urn=identity.urn, uuid="0" * 36
    )
    assert not tampered.verify()
    with pytest.raises(IdentityError):
        tampered.require_intact()


def test_an_identity_may_never_change_once_minted():
    identity = UniversalIdentity.mint("ucos", "THING-1")
    identity.require_unchanged(UniversalIdentity.mint("ucos", "THING-1"))
    with pytest.raises(IdentityError):
        identity.require_unchanged(UniversalIdentity.mint("ucos", "THING-2"))


def test_from_dict_refuses_a_declared_field_that_contradicts_the_minting_function():
    identity = UniversalIdentity.mint("ucos", "THING-1")
    assert UniversalIdentity.from_dict(identity.to_dict()) == identity
    with pytest.raises(IdentityError):
        UniversalIdentity.from_dict({**identity.to_dict(), "urn": "urn:ucos:ucko:ucos:OTHER"})
    with pytest.raises(IdentityError):
        UniversalIdentity.from_dict({**identity.to_dict(), "uuid": "0" * 36})
    with pytest.raises(IdentityError):
        UniversalIdentity.from_dict("not a mapping")


def test_identity_renders_as_its_urn():
    assert str(UniversalIdentity.mint("ucos", "X")) == "urn:ucos:ucko:ucos:X"


def test_urn_for_is_pure():
    assert urn_for("a", "B") == "urn:ucos:ucko:a:B"


# --- facets ---------------------------------------------------------------------


def test_there_are_thirty_three_facets_and_all_are_required():
    assert len(Facet) == 33
    assert REQUIRED_FACETS == tuple(Facet)


def test_required_facets_is_derived_from_the_enum_not_restated():
    # A new facet cannot be added and forgotten.
    assert set(REQUIRED_FACETS) == set(Facet)
    assert FACET_ATTRIBUTES == tuple(facet.value.replace("-", "_") for facet in Facet)


def test_every_facet_declares_the_question_it_answers():
    for facet in Facet:
        assert facet.question.endswith("?")


def test_facet_coerce_accepts_a_member_a_name_and_refuses_a_stranger():
    assert Facet.coerce(Facet.IDENTITY) is Facet.IDENTITY
    assert Facet.coerce("semantic-identity") is Facet.SEMANTIC_IDENTITY
    assert Facet.coerce(" AUDIT ") is Facet.AUDIT
    with pytest.raises(FacetError):
        Facet.coerce("no-such-facet")


def test_facet_attribute_is_the_python_name():
    assert Facet.SEMANTIC_IDENTITY.attribute == "semantic_identity"


# --- values ---------------------------------------------------------------------


def test_semantic_identity_digests_meaning_and_normalises_it():
    left = SemanticIdentity(concept="  Thing ", definition="A  Meaning ")
    right = SemanticIdentity(concept="thing", definition="a meaning")
    assert left.digest() == right.digest()
    assert "concept" in left.normalised()


def test_semantic_digest_changes_when_meaning_changes():
    assert SemanticIdentity("a", "x").digest() != SemanticIdentity("a", "y").digest()


def test_replay_proof_holds_only_for_the_output_it_certifies():
    proof = ReplayProof(procedure="p/1.0.0", input_digest="in", output_digest="out")
    assert proof.holds("out")
    assert not proof.holds("other")


def test_metadata_set_is_ordered_and_addressable():
    metadata = MetadataSet.of({"b": 1, "a": 2}, c=3)
    assert metadata.keys() == ("a", "b", "c")
    assert metadata.get("a") == "2"
    assert metadata.get("missing", "fallback") == "fallback"
    assert metadata.as_dict() == {"a": "2", "b": "1", "c": "3"}


def test_authority_binding_requires_a_parent():
    with pytest.raises(FacetError):
        AuthorityBinding(tier="constitutional", derives_from="")
    with pytest.raises(FacetError):
        AuthorityBinding(tier="", derives_from="urn:x")


@pytest.mark.parametrize(
    "value",
    [
        Attestation("certification"),
        AuditEntry(actor="a", action="b", subject="c"),
        AuthorityBinding(tier="constitutional", derives_from="urn:x"),
        Constraint(constraint_id="C", expression="always"),
        ContextBinding("security", "open"),
        DiscoveryDescriptor(),
        EvidenceRef(evidence_id="E", digest="d", kind="k", locator="l"),
        MetadataSet.of({"a": "b"}),
        OntologyRef(ontology_id="o", class_id="c"),
        Ownership(owner="o"),
        PersistenceBinding("git", "loc", False),
        Policy(policy_id="P", statement="s", enforcement="fail-closed"),
        ProjectionBinding("json", "t", True, False),
        ProvenanceStep(actor="a", action="b", source="s"),
        Relationship("depends-on", "urn:x", "knowledge"),
        ReplayProof(procedure="p", input_digest="i", output_digest="o"),
        SemanticIdentity(concept="c", definition="d"),
        TaxonomyRef(kind="fact", category="knowledge"),
        TemporalEvent(sequence=0, event="e"),
        TraceLink(upstream="u", downstream="d", kind="requirement"),
    ],
)
def test_every_value_round_trips_through_its_own_dict_form(value):
    """Serializability is a constitutional requirement, not a convenience."""
    record = value.to_dict()
    assert content_hash(record) == content_hash(type(value).from_dict(record).to_dict())


def test_attestation_defaults_to_unattested_and_never_to_attested():
    assert not Attestation("certification").attested


def test_unattested_is_distinguishable_from_absent():
    # Article 6: a facet may be unattested but never absent.
    attestation = Attestation("validation")
    assert attestation.to_dict()["kind"] == "validation"
    assert not attestation.attested


def test_the_canonical_payload_refuses_a_value_it_would_have_to_guess_about() -> None:
    """INVERSION IS THE REMEDY, AND REFUSAL IS WHAT KEEPS IT HONEST.

    Every declaration this renders is built from scalars, mappings, sequences, sets and other
    dataclasses, so the refusal at the end had no case — and it is the whole reason the
    renderer is safe to invert. A value it cannot render has exactly two other options:
    render it as its ``repr``, which puts a memory address into a certification identity and
    makes the digest non-deterministic, or drop it, which leaves a field out of the identity
    the inversion promised would be there. Refusing is the only answer that keeps "a new
    field is covered on the day it is written" true.

    The arms it DOES render are asserted beside it, because a refusal with no admitted cases
    is indistinguishable from a renderer that refuses everything.
    """

    @dataclasses.dataclass(frozen=True)
    class _Declared:
        name: str
        weights: tuple[int, ...]
        labels: frozenset[str]
        nested: dict[str, int]

    rendered = canonical_payload(_Declared("n", (1, 2), frozenset({"b", "a"}), {"k": 1}))

    assert rendered == {
        "name": "n",
        "weights": [1, 2],
        "labels": ["a", "b"],
        "nested": {"k": 1},
    }
    assert canonical_payload(_Declared("n", (1, 2), frozenset(), {}), exclude=("name",)) == {
        "weights": [1, 2],
        "labels": [],
        "nested": {},
    }

    with pytest.raises(TypeError, match="without guessing"):
        canonical_payload(object())
    with pytest.raises(TypeError, match="without guessing"):
        canonical_payload({"declared": object()})


# --- the mandated object attributes, bound to the facet law ---------------------
#
# The Universal Autonomous Knowledge Platform foundation states that EVERY constitutional
# object shall possess thirteen attributes. Article 6 already answers that question with
# thirty-three facets, so the mandate is not new construction -- it is a claim about this
# law's completeness, and the honest way to settle it is to map all thirteen and let the
# two that do not map say so out loud.
#
# SCOPE. A binding below proves the facet EXISTS and is carried by the UCKO dataclass. It
# does not prove any particular object has attested it: Article 6 permits a facet to be
# unattested, and `test_attestation_defaults_to_unattested_and_never_to_attested` is the
# instrument for that distinction.

#: Mandated attribute -> the universal facet that answers it, one to one.
OBJECT_ATTRIBUTE_FACET = {
    "UAKP-OBJ/OJ-01": Facet.IDENTITY,  # Universal Identity attribute
    "UAKP-OBJ/OJ-02": Facet.ONTOLOGY,  # Type attribute -- "What kind of being is it?"
    "UAKP-OBJ/OJ-03": Facet.METADATA,  # Metadata attribute
    "UAKP-OBJ/OJ-04": Facet.LIFECYCLE,  # Lifecycle State attribute
    "UAKP-OBJ/OJ-05": Facet.RELATIONSHIPS,  # Relationships attribute
    "UAKP-OBJ/OJ-06": Facet.AUTHORITY,  # Authority attribute
    "UAKP-OBJ/OJ-07": Facet.PROVENANCE,  # Provenance attribute
    "UAKP-OBJ/OJ-08": Facet.EVIDENCE,  # Evidence attribute
    "UAKP-OBJ/OJ-10": Facet.GOVERNANCE_CONTEXT,  # Governance attribute
    "UAKP-OBJ/OJ-12": Facet.TEMPORAL_HISTORY,  # History attribute
    "UAKP-OBJ/OJ-13": Facet.EVOLUTION_HISTORY,  # Evolution History attribute
}

#: Answered by a deliberate REFUSAL rather than by a facet. A mutable version field would
#: contradict Article 5 (an identity, once minted, never changes) and Article 12 (every
#: transition creates a NEW state referencing its parent). The law answers "which version?"
#: with the state chain, so the absence of a `version` facet is the answer, not a gap.
OBJECT_ATTRIBUTE_BY_REFUSAL = {
    "UAKP-OBJ/OJ-11": (Facet.EVOLUTION_HISTORY, Facet.TEMPORAL_HISTORY),  # Version attribute
}

#: Present in the repository, but NOT at the scope the mandate states. "Every object shall
#: possess Confidence"; this repository binds confidence to a registered KNOWLEDGE record
#: (`engine.knowledge.ukip.confidence`), which is a strictly smaller population than every
#: UCKO. Recorded here rather than counted as satisfied, because a scope difference that
#: only a reader notices is a scope difference nothing enforces.
OBJECT_ATTRIBUTE_SCOPED_ELSEWHERE = {
    "UAKP-OBJ/OJ-09": "engine.knowledge.ukip.confidence binds confidence to a knowledge "
    "record, never to a UCKO; the mandate says every object",
}


def _object_model_mandates() -> dict[str, str]:
    from pathlib import Path

    repo = Path(__file__).resolve().parents[3]
    corpus = json.loads(
        (repo / "00-MASTER" / "CAEM-001" / "06-MANDATE-CORPUS.json").read_text(encoding="utf-8")
    )
    return {a["atom_id"]: a["label"] for a in corpus["atoms"] if a["section"] == "UAKP-OBJ"}


def test_every_mandated_object_attribute_is_answered_or_declared_out_of_scope() -> None:
    """TOTALITY. No mandated attribute may be silently missing from this mapping."""
    mandates = _object_model_mandates()
    assert (
        len(mandates) == 13
    ), f"the UAKP object model states 13 attributes, corpus has {sorted(mandates)}"

    accounted = (
        set(OBJECT_ATTRIBUTE_FACET)
        | set(OBJECT_ATTRIBUTE_BY_REFUSAL)
        | set(OBJECT_ATTRIBUTE_SCOPED_ELSEWHERE)
    )
    assert set(mandates) == accounted, (
        f"attributes neither mapped nor declared: {sorted(set(mandates) - accounted)}; "
        f"identifiers mapped that are not object-model mandates: "
        f"{sorted(accounted - set(mandates))}"
    )
    overlap = set(OBJECT_ATTRIBUTE_FACET) & (
        set(OBJECT_ATTRIBUTE_BY_REFUSAL) | set(OBJECT_ATTRIBUTE_SCOPED_ELSEWHERE)
    )
    assert not overlap, f"an attribute cannot be both answered and unanswered: {sorted(overlap)}"


def test_each_mapped_attribute_names_a_required_facet_the_object_actually_carries() -> None:
    from engine.uckp.ucko import UniversalConstitutionalKnowledgeObject as UCKO

    fields = {f.name for f in dataclasses.fields(UCKO)}
    for mandate, facet in OBJECT_ATTRIBUTE_FACET.items():
        assert facet in REQUIRED_FACETS, f"{mandate}: {facet} is not a required facet"
        assert facet.attribute in fields, (
            f"{mandate}: facet {facet.value!r} is declared but the UCKO carries no "
            f"{facet.attribute!r} field, so the object cannot answer the question"
        )


def test_the_attribute_mapping_is_injective() -> None:
    """NON-VACUITY. Two attributes answered by one facet would mean one of them is
    unanswered and the mapping is hiding it."""
    facets = list(OBJECT_ATTRIBUTE_FACET.values())
    duplicated = sorted({f.value for f in facets if facets.count(f) > 1})
    assert not duplicated, f"facets claimed by more than one mandated attribute: {duplicated}"


def test_version_is_answered_by_refusal_and_the_refusal_is_real() -> None:
    """The claim is that no version FIELD exists because the law forbids one. If a version
    facet or field ever appears, this mapping became a rationalisation and must be redone."""
    from engine.uckp.ucko import UniversalConstitutionalKnowledgeObject as UCKO

    assert "version" not in {facet.value for facet in Facet}
    fields = {f.name for f in dataclasses.fields(UCKO)}
    assert "version" not in fields, (
        "UAKP-OBJ/OJ-11 is mapped to the state chain on the grounds that no version field "
        "exists; one now does, so the mapping is false"
    )
    for facet in OBJECT_ATTRIBUTE_BY_REFUSAL["UAKP-OBJ/OJ-11"]:
        assert facet.attribute in fields


def test_confidence_is_scoped_to_knowledge_and_the_scope_limit_is_real() -> None:
    """NON-VACUITY for the one attribute declared out of scope. Without this, the scoped
    list is a place to put anything inconvenient."""
    from engine.knowledge.ukip.confidence import CONFIDENCE_DIMENSION
    from engine.uckp.ucko import UniversalConstitutionalKnowledgeObject as UCKO

    assert CONFIDENCE_DIMENSION == "confidence"
    assert "confidence" not in {f.name for f in dataclasses.fields(UCKO)}, (
        "UAKP-OBJ/OJ-09 is declared out of scope because no UCKO carries confidence; "
        "one now does, so it is in scope and must be bound rather than excused"
    )
    assert "confidence" not in {facet.value for facet in Facet}
    for mandate, reason in OBJECT_ATTRIBUTE_SCOPED_ELSEWHERE.items():
        assert len(reason) > 40, f"{mandate}: declared out of scope without a stated reason"
