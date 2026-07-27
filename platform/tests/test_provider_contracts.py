"""Provider contract value-type tests (Terminal-04).

Each type is exercised on its conformant path and on at least one fail-closed path,
because the contracts are the boundary where a non-conformant provider is supposed to
be stopped.
"""

from __future__ import annotations

from platform.tests.universal_provider_helpers import (
    MEMO_RESOURCE_KIND,
    MemoProvider,
    memo_capabilities,
    memo_descriptor,
)
from platform.universal_provider.constitution import ProviderOperation
from platform.universal_provider.contracts import (
    DEFAULT_QUERY_LIMIT,
    MAX_QUERY_LIMIT,
    ProviderAttestation,
    ProviderCapability,
    ProviderDependency,
    ProviderDescriptor,
    ProviderHealth,
    ProviderIdentity,
    ProviderQuery,
    ProviderResource,
    ProviderResponse,
    ProviderState,
    canonical_json,
    content_hash,
    provider_operations,
)
from platform.universal_provider.errors import (
    ProviderCapabilityError,
    ProviderContractError,
)

import pytest


def _resource(resource_id: str = "r1", **overrides: object) -> ProviderResource:
    payload = {
        "resource_id": resource_id,
        "kind": MEMO_RESOURCE_KIND,
        "provider_id": "fixture.memo",
        "payload": {"a": 1},
        "provenance": {"source_of_record": "fixture"},
    }
    payload.update(overrides)
    return ProviderResource(**payload)  # type: ignore[arg-type]


def test_canonical_json_is_key_order_independent() -> None:
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})
    assert content_hash({"b": 1, "a": 2}) == content_hash({"a": 2, "b": 1})


def test_identity_normalizes_and_defaults_name() -> None:
    identity = ProviderIdentity(provider_id="  A.B ", kind="Memo", version="1.2.3")
    assert identity.provider_id == "a.b"
    assert identity.kind == "memo"
    assert identity.name == "a.b"
    assert identity.qualified_id == "a.b@1.2.3"
    assert ProviderIdentity.from_dict(identity.to_dict()) == identity


def test_identity_round_trips_from_a_flat_payload() -> None:
    identity = ProviderIdentity.from_dict(
        {"provider_id": "x.y", "kind": "memo", "version": "1.0.0"}
    )
    assert identity.qualified_id == "x.y@1.0.0"
    with pytest.raises(ProviderContractError):
        ProviderIdentity.from_dict("not a mapping")  # type: ignore[arg-type]
    with pytest.raises(ProviderContractError):
        ProviderIdentity.from_dict({"provider_id": "x.y", "kind": "memo"})


def test_capability_admits_only_declared_selector_keys() -> None:
    capability = ProviderCapability(
        name="c",
        operation=ProviderOperation.QUERY,
        selector_keys=("tag", "id"),
        required_selector_keys=("tag",),
    )
    assert capability.accepts({"tag": 1}) == ()
    assert capability.accepts({"tag": 1, "nope": 2}) == ("nope",)
    assert capability.missing_required({"id": 1}) == ("tag",)
    assert capability.missing_required({"tag": 1}) == ()
    assert ProviderCapability.from_dict(capability.to_dict()) == capability


def test_capability_refuses_required_keys_it_never_declared() -> None:
    with pytest.raises(ProviderContractError) as exc:
        ProviderCapability(
            name="c", operation=ProviderOperation.QUERY, required_selector_keys=("ghost",)
        )
    assert exc.value.detail["undeclared"] == ["ghost"]


def test_capability_coerces_a_string_operation_and_refuses_an_unknown_one() -> None:
    assert ProviderCapability(name="c", operation="query").operation is ProviderOperation.QUERY
    with pytest.raises(ProviderContractError):
        ProviderCapability(name="c", operation="teleport")


def test_capability_refuses_a_non_boolean_determinism_claim() -> None:
    with pytest.raises(ProviderContractError):
        ProviderCapability(name="c", operation="query", deterministic="yes")  # type: ignore[arg-type]


def test_capability_refuses_a_string_where_a_sequence_is_required() -> None:
    with pytest.raises(ProviderContractError):
        ProviderCapability(name="c", operation="query", selector_keys="tag")  # type: ignore[arg-type]


def test_dependency_defaults_alias_to_provider_id() -> None:
    dependency = ProviderDependency(provider_id="a.b")
    assert dependency.alias == "a.b"
    assert dependency.min_version == "0.0.0"
    assert ProviderDependency.from_dict(dependency.to_dict()) == dependency
    with pytest.raises(ProviderContractError):
        ProviderDependency.from_dict("nope")  # type: ignore[arg-type]


def test_descriptor_exposes_identity_and_is_content_addressed() -> None:
    descriptor = memo_descriptor()
    assert descriptor.provider_id == "fixture.memo"
    assert descriptor.kind == "memo"
    assert descriptor.qualified_id == "fixture.memo@1.0.0"
    assert descriptor.content_hash() == descriptor.content_hash()
    assert descriptor.declared_effects() == ("mem:read",)
    assert [c.name for c in descriptor.capabilities_for(ProviderOperation.QUERY)] == ["memo.notes"]


def test_descriptor_round_trips_losslessly_through_data() -> None:
    descriptor = memo_descriptor()
    assert ProviderDescriptor.from_dict(descriptor.to_dict()).content_hash() == (
        descriptor.content_hash()
    )


def test_descriptor_capability_lookup_fails_closed() -> None:
    descriptor = memo_descriptor()
    assert descriptor.capability("memo.notes").name == "memo.notes"
    with pytest.raises(ProviderCapabilityError) as exc:
        descriptor.capability("memo.absent")
    assert "memo.notes" in exc.value.detail["declared"]


def test_descriptor_refuses_a_second_interface() -> None:
    with pytest.raises(ProviderContractError) as exc:
        ProviderDescriptor(
            identity=ProviderIdentity(provider_id="a.b", kind="memo", version="1.0.0"),
            interface="some.other.interface",
        )
    assert exc.value.detail["constitutional"] == "ucos.provider.universal"


def test_descriptor_refuses_duplicate_capabilities_aliases_and_self_dependency() -> None:
    identity = ProviderIdentity(provider_id="a.b", kind="memo", version="1.0.0")
    duplicate = ProviderCapability(name="same", operation=ProviderOperation.QUERY)
    with pytest.raises(ProviderContractError):
        ProviderDescriptor(identity=identity, capabilities=(duplicate, duplicate))
    with pytest.raises(ProviderContractError):
        ProviderDescriptor(
            identity=identity,
            dependencies=(
                ProviderDependency(provider_id="c.d", alias="x"),
                ProviderDependency(provider_id="e.f", alias="x"),
            ),
        )
    with pytest.raises(ProviderContractError):
        ProviderDescriptor(identity=identity, dependencies=(ProviderDependency(provider_id="a.b"),))


def test_descriptor_refuses_wrongly_typed_members_and_unserializable_metadata() -> None:
    identity = ProviderIdentity(provider_id="a.b", kind="memo", version="1.0.0")
    with pytest.raises(ProviderContractError):
        ProviderDescriptor(identity=identity, capabilities=("not a capability",))  # type: ignore[arg-type]
    with pytest.raises(ProviderContractError):
        ProviderDescriptor(identity=identity, dependencies=("not a dependency",))  # type: ignore[arg-type]
    with pytest.raises(ProviderContractError):
        ProviderDescriptor(identity=identity, metadata={"f": object()})
    with pytest.raises(ProviderContractError):
        ProviderDescriptor(identity="not an identity")  # type: ignore[arg-type]


def test_descriptor_from_dict_refuses_malformed_collections() -> None:
    payload = memo_descriptor().to_dict()
    with pytest.raises(ProviderContractError):
        ProviderDescriptor.from_dict({**payload, "capabilities": {"a": 1}})
    with pytest.raises(ProviderContractError):
        ProviderDescriptor.from_dict({**payload, "dependencies": "x"})
    with pytest.raises(ProviderContractError):
        ProviderDescriptor.from_dict("nope")  # type: ignore[arg-type]


def test_query_defaults_and_fingerprint_stability() -> None:
    query = ProviderQuery(capability="memo.notes")
    assert query.limit == DEFAULT_QUERY_LIMIT
    assert query.fingerprint() == ProviderQuery(capability="memo.notes").fingerprint()
    reordered_a = ProviderQuery(capability="c", selector={"a": 1, "b": 2})
    reordered_b = ProviderQuery(capability="c", selector={"b": 2, "a": 1})
    assert reordered_a.fingerprint() == reordered_b.fingerprint()


@pytest.mark.parametrize("limit", [0, -1, True, "10", MAX_QUERY_LIMIT + 1])
def test_query_limit_is_bounded(limit: object) -> None:
    with pytest.raises(ProviderContractError):
        ProviderQuery(capability="c", limit=limit)  # type: ignore[arg-type]


def test_query_refuses_a_non_string_cursor_and_non_mapping_selector() -> None:
    with pytest.raises(ProviderContractError):
        ProviderQuery(capability="c", cursor=3)  # type: ignore[arg-type]
    with pytest.raises(ProviderContractError):
        ProviderQuery(capability="c", selector=[("a", 1)])  # type: ignore[arg-type]
    with pytest.raises(ProviderContractError):
        ProviderQuery(capability="")


def test_resource_requires_provenance_source_of_record() -> None:
    with pytest.raises(ProviderContractError) as exc:
        _resource(provenance={"note": "no source"})
    assert "PC-06" in exc.value.message
    with pytest.raises(ProviderContractError):
        _resource(provenance={"source_of_record": "   "})


def test_resource_hash_covers_payload_but_not_identity() -> None:
    first = _resource("r1")
    second = _resource("r2")
    assert first.resource_hash == second.resource_hash
    assert _resource("r1", payload={"a": 2}).resource_hash != first.resource_hash
    assert first.to_dict()["resource_hash"] == first.resource_hash


def test_response_length_ids_and_hash() -> None:
    response = ProviderResponse(
        provider_id="fixture.memo",
        capability="memo.notes",
        query_fingerprint="f",
        resources=(_resource("r1"), _resource("r2")),
    )
    assert len(response) == 2
    assert response.resource_ids() == ("r1", "r2")
    assert response.response_hash == response.response_hash


def test_response_refuses_non_resources_and_non_boolean_truncation() -> None:
    with pytest.raises(ProviderContractError):
        ProviderResponse(
            provider_id="fixture.memo",
            capability="c",
            query_fingerprint="f",
            resources=("nope",),  # type: ignore[arg-type]
        )
    with pytest.raises(ProviderContractError):
        ProviderResponse(
            provider_id="fixture.memo",
            capability="c",
            query_fingerprint="f",
            truncated="yes",  # type: ignore[arg-type]
        )


def test_health_states_and_invariants() -> None:
    serving = ProviderHealth(provider_id="a.b", state=ProviderState.SERVING, checks={"x": True})
    assert serving.serving is True
    assert serving.to_dict()["state"] == "serving"
    assert ProviderHealth(provider_id="a.b", state="degraded").state is ProviderState.DEGRADED
    with pytest.raises(ProviderContractError):
        ProviderHealth(provider_id="a.b", state="melted")
    with pytest.raises(ProviderContractError):
        ProviderHealth(provider_id="a.b", state=ProviderState.SERVING, reasons=("odd",))
    with pytest.raises(ProviderContractError):
        ProviderHealth(provider_id="a.b", state=ProviderState.DEGRADED, checks={"x": "no"})


def test_attestation_requires_a_chain_when_verified() -> None:
    with pytest.raises(ProviderContractError) as exc:
        ProviderAttestation(provider_id="a.b", resource_id="r", resource_hash="h", verified=True)
    assert "PC-06" in exc.value.message
    unverified = ProviderAttestation(
        provider_id="a.b", resource_id="r", resource_hash="h", verified=False, reasons=("absent",)
    )
    assert unverified.to_dict()["verified"] is False
    hashless = ProviderAttestation(
        provider_id="a.b", resource_id="r", resource_hash="", verified=False, reasons=("absent",)
    )
    assert hashless.resource_hash == ""
    with pytest.raises(ProviderContractError) as silent:
        ProviderAttestation(provider_id="a.b", resource_id="r", resource_hash="", verified=False)
    assert "PC-07" in silent.value.message
    with pytest.raises(ProviderContractError):
        ProviderAttestation(
            provider_id="a.b",
            resource_id="r",
            resource_hash=None,
            verified=False,
            reasons=("x",),  # type: ignore[arg-type]
        )
    with pytest.raises(ProviderContractError):
        ProviderAttestation(
            provider_id="a.b",
            resource_id="r",
            resource_hash="h",
            verified="maybe",  # type: ignore[arg-type]
        )


def test_provider_operations_introspects_the_constitutional_surface() -> None:
    instance = MemoProvider(memo_descriptor())
    assert provider_operations(instance) == (
        "capabilities",
        "describe",
        "fetch",
        "health",
        "query",
        "verify",
    )
    assert provider_operations(object()) == ()


def test_capabilities_fixture_declares_every_substrate_operation() -> None:
    operations = {capability.operation for capability in memo_capabilities()}
    assert operations == {
        ProviderOperation.QUERY,
        ProviderOperation.FETCH,
        ProviderOperation.VERIFY,
    }
