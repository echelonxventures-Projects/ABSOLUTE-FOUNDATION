"""Ω∞ reference layer — representation and identity as provider slots.

THE ASSUMPTION UNDER TEST. ``json.dumps`` and ``hashlib.sha256`` were requirements of the first
draft, which meant every value in the architecture had to be JSON-shaped and every digest had to be
a SHA-256, in a system whose stated purpose is to outlive both. The refutation is not an interface
that wraps them; it is a SECOND codec with no relationship to JSON and a SECOND identity provider
that never imports ``hashlib``. These tests hold the pair apart and check that nothing downstream
can tell which one it is talking to.
"""

from __future__ import annotations

import pytest

from engine.omega_governance.reference.capability import ENCODABLE, IDENTIFIABLE, REPRODUCIBLE
from engine.omega_governance.reference.encoding import (
    CanonicalJsonCodec,
    Encoding,
    EncodingError,
    PolynomialIdentity,
    Sha256Identity,
    TagLengthValueCodec,
    assert_reproducible,
    default_encoding,
    default_registries,
)

SAMPLES: tuple[object, ...] = (
    {"a": 1, "b": [1, "x", True, None]},
    [1, 2, 3],
    "a string",
    42,
    True,
    None,
)


def test_both_shipped_codecs_declare_what_they_are() -> None:
    codecs, identities = default_registries()
    assert codecs.known() == ("canonical-json", "tag-length-value")
    assert identities.known() == ("polynomial-61", "sha256")


def test_the_second_codec_is_not_json_in_disguise() -> None:
    """A wrapper around ``json.dumps`` would satisfy every interface test and refute nothing, so the
    property that matters is that the two codecs produce DIFFERENT bytes for the same value."""
    value = {"a": 1, "b": [1, "x", True, None]}
    assert CanonicalJsonCodec().encode(value) != TagLengthValueCodec().encode(value)


def test_the_second_identity_provider_never_reaches_for_hashlib() -> None:
    """``PolynomialIdentity`` is integer arithmetic. If a deployment's platform has no ``hashlib``,
    identity must still be available — that is the whole claim of an identity SLOT.

    Measured over the EXECUTABLE code with docstrings stripped, because the class documents its own
    independence in prose and a substring search would match the sentence making the claim.
    """
    import ast
    import inspect
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(PolynomialIdentity)))
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            node.value = ast.Constant(value="")
    assert "hashlib" not in ast.unparse(ast.fix_missing_locations(tree))
    assert PolynomialIdentity().width() == len(PolynomialIdentity().fingerprint(b"abc"))


def test_a_codec_is_asked_before_it_is_used_never_told_afterwards() -> None:
    codec = CanonicalJsonCodec()
    assert codec.supports({"a": 1})
    assert not codec.supports(object())


def test_encoding_a_value_the_codec_refused_raises_rather_than_guessing() -> None:
    with pytest.raises(EncodingError):
        CanonicalJsonCodec().encode(object())


def test_neither_shipped_codec_claims_to_represent_a_set() -> None:
    """A set has no declared ordering, so any byte rendering of one is a choice the codec would be
    making silently. Both codecs refuse, and the refusal is the honest answer."""
    codecs, _ = default_registries()
    assert codecs.supporting({1, 2}) == ()


def test_supporting_lists_every_codec_that_can_take_the_value() -> None:
    codecs, _ = default_registries()
    assert codecs.supporting({"a": 1}) == ("canonical-json", "tag-length-value")


def test_an_unknown_codec_or_identity_name_is_refused() -> None:
    codecs, identities = default_registries()
    with pytest.raises(EncodingError):
        codecs.resolve("protobuf")
    with pytest.raises(EncodingError):
        identities.resolve("md5")


def test_the_shipped_providers_declare_the_capabilities_they_actually_have() -> None:
    assert CanonicalJsonCodec().capabilities().supports(ENCODABLE)
    assert CanonicalJsonCodec().capabilities().supports(REPRODUCIBLE)
    assert Sha256Identity().capabilities().supports(IDENTIFIABLE)


def test_an_encoding_travels_as_one_pair_so_no_call_site_can_mismatch_it() -> None:
    """``fingerprint`` takes a VALUE rather than bytes. Two calls — encode here, digest there —
    is exactly how a codec and a digest drift apart across a codebase."""
    encoding = default_encoding()
    description = encoding.describe()
    assert description["codec"] == "canonical-json"
    assert description["identity"] == "sha256"
    assert description["identity_width"] == 64
    assert len(encoding.fingerprint({"a": 1})) == 64


def test_the_same_value_under_two_encodings_has_two_identities_and_that_is_correct() -> None:
    """Identity is UNDER a named encoding. Two deployments choosing different providers must not
    silently believe they agree about what a value is."""
    value = {"a": 1}
    left = Encoding(CanonicalJsonCodec(), Sha256Identity())
    right = Encoding(TagLengthValueCodec(), PolynomialIdentity())
    assert left.fingerprint(value) != right.fingerprint(value)


def test_every_shipped_pairing_is_reproducible_over_the_sample_values() -> None:
    """The property REPRODUCIBLE claims, actually measured, for all four pairings — a capability
    that is declared and never checked is the assumption this layer exists to remove."""
    for codec in (CanonicalJsonCodec(), TagLengthValueCodec()):
        for identity in (Sha256Identity(), PolynomialIdentity()):
            assert_reproducible(Encoding(codec, identity), SAMPLES)


def test_assert_reproducible_refuses_a_codec_that_is_not_a_pure_function() -> None:
    """Non-vacuity: the check must be able to FAIL, or it certifies nothing."""

    class DriftingCodec:
        def __init__(self) -> None:
            self._calls = 0

        def identifier(self) -> str:
            return "drifting"

        def capabilities(self):  # noqa: ANN201 - mirrors the Codec protocol
            return CanonicalJsonCodec().capabilities()

        def supports(self, value: object) -> bool:
            return True

        def encode(self, value: object) -> bytes:
            self._calls += 1
            return f"{value}:{self._calls}".encode()

    with pytest.raises(EncodingError):
        assert_reproducible(Encoding(DriftingCodec(), Sha256Identity()), ({"a": 1},))


def test_a_codec_registry_refuses_a_duplicate_identifier() -> None:
    codecs, _ = default_registries()
    with pytest.raises(EncodingError):
        codecs.register(CanonicalJsonCodec())
