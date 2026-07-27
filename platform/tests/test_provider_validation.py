"""Provider Validation tests (Terminal-04).

Every gate is exercised on its passing path and on at least one failing path, and the
three-valued verdict is tested directly: a declared-but-unbuilt provider must come out
``INCOMPLETE``, never ``PASSED`` and never ``FAILED``.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from platform.tests.universal_provider_helpers import (
    MEMO_RESOURCE_KIND,
    FaultyProvider,
    MemoProvider,
    memo_capabilities,
    memo_descriptor,
)
from platform.universal_provider.constitution import ProviderOperation
from platform.universal_provider.contracts import (
    ProviderCapability,
    ProviderHealth,
    ProviderQuery,
    ProviderResource,
    ProviderState,
)
from platform.universal_provider.errors import (
    ProviderCapabilityError,
    ProviderValidationError,
)
from platform.universal_provider.lifecycle import (
    LifecycleEntry,
    ProviderLifecycle,
    ProviderPhase,
)
from platform.universal_provider.registry import ProviderRegistry
from platform.universal_provider.sdk import declare_capability, declare_dependency, declare_provider
from platform.universal_provider.validation import (
    AdditiveEvolutionGate,
    CapabilitiesDeclaredGate,
    CertifiableGate,
    ComposabilityGate,
    DeterminismGate,
    EffectsDeclaredGate,
    ExtensibilityGate,
    FailClosedGate,
    FaultIsolationGate,
    GateResult,
    GateSeverity,
    GateStatus,
    IdentityDeclaredGate,
    InterfaceCompleteGate,
    KindOpenGate,
    LifecycleGovernedGate,
    ProvenanceGate,
    ProviderGate,
    ProviderValidator,
    ValidationStatus,
    ValidationSubject,
    default_gates,
    framework_source_files,
)

import pytest


def _subject(**kwargs: object) -> ValidationSubject:
    descriptor = kwargs.pop("descriptor", None) or memo_descriptor()
    return ValidationSubject(descriptor=descriptor, **kwargs)  # type: ignore[arg-type]


def _governed(descriptor=None) -> ValidationSubject:
    """A fully equipped subject: instance, registry, and a governed lifecycle."""
    descriptor = descriptor or memo_descriptor()
    registry = ProviderRegistry.from_descriptors([descriptor])
    lifecycle = ProviderLifecycle()
    lifecycle.declare(descriptor.qualified_id)
    lifecycle.transition(descriptor.qualified_id, ProviderPhase.REGISTERED)
    return ValidationSubject(
        descriptor=descriptor,
        instance=MemoProvider(descriptor),
        registry=registry,
        lifecycle=lifecycle,
    )


# --------------------------------------------------------------------------- wiring


def test_there_is_exactly_one_gate_per_constitutional_article() -> None:
    gates = default_gates()
    assert len(gates) == 14
    assert [gate.article_id for gate in gates] == [f"PC-{n:02d}" for n in range(1, 15)]
    assert len({gate.gate_id for gate in gates}) == 14


def test_a_gate_id_is_read_from_the_article_so_it_cannot_drift() -> None:
    assert InterfaceCompleteGate().gate_id == "PV-01-INTERFACE-COMPLETE"
    assert ExtensibilityGate().gate_id == "PV-14-EXTENSIBLE"


def test_framework_source_files_excludes_the_package_init() -> None:
    files = framework_source_files()
    names = {path.name for path in files}
    assert "constitution.py" in names
    assert "__init__.py" not in names


def test_a_validator_requires_gates_and_refuses_duplicates() -> None:
    with pytest.raises(ProviderValidationError):
        ProviderValidator(gates=[])
    with pytest.raises(ProviderValidationError):
        ProviderValidator(gates=[KindOpenGate(), KindOpenGate()])
    assert ProviderValidator().gate_ids()[0] == "PV-01-INTERFACE-COMPLETE"


def test_a_subject_requires_a_descriptor() -> None:
    with pytest.raises(ProviderValidationError):
        ValidationSubject(descriptor="nope")  # type: ignore[arg-type]


def test_validate_requires_a_subject() -> None:
    with pytest.raises(ProviderValidationError):
        ProviderValidator().validate("nope")  # type: ignore[arg-type]


# ------------------------------------------------------------------- per-gate paths


def test_pv01_interface_complete() -> None:
    passing = InterfaceCompleteGate().evaluate(_governed())
    assert passing.status is GateStatus.PASS
    assert len(passing.evidence["implemented"]) == 6

    class Partial:
        def describe(self) -> None: ...
        def query(self) -> None: ...

    failing = InterfaceCompleteGate().evaluate(_subject(instance=Partial()))
    assert failing.status is GateStatus.FAIL
    assert "verify" in failing.findings[0]

    absent = InterfaceCompleteGate().evaluate(_subject())
    assert absent.status is GateStatus.INDETERMINATE


def test_pv02_kind_open_passes_for_a_provider_the_framework_never_heard_of() -> None:
    result = KindOpenGate().evaluate(_governed())
    assert result.status is GateStatus.PASS
    assert result.evidence["scanned_files"] > 5
    assert result.evidence["kind"] == "memo"


def test_pv02_kind_open_fails_when_the_framework_names_the_provider(tmp_path: Path) -> None:
    """Simulate a framework that was taught about one particular provider."""
    (tmp_path / "leaky.py").write_text('PRIVILEGED = "fixture.memo"\n', encoding="utf-8")
    subject = ValidationSubject(descriptor=memo_descriptor(), framework_root=tmp_path)
    result = KindOpenGate().evaluate(subject)
    assert result.status is GateStatus.FAIL
    assert result.evidence["offenders"] == ["leaky.py"]


def test_pv03_identity_declared() -> None:
    assert IdentityDeclaredGate().evaluate(_governed()).status is GateStatus.PASS
    anonymous = declare_provider("bare.provider", "memo", "1.0.0", capabilities=memo_capabilities())
    failing = IdentityDeclaredGate().evaluate(_subject(descriptor=anonymous))
    assert failing.status is GateStatus.FAIL
    assert any("authority" in finding for finding in failing.findings)
    assert any("source of record" in finding for finding in failing.findings)


def test_pv04_capabilities_declared() -> None:
    assert CapabilitiesDeclaredGate().evaluate(_governed()).status is GateStatus.PASS
    query_only = memo_descriptor(capabilities=memo_capabilities()[:1])
    failing = CapabilitiesDeclaredGate().evaluate(_subject(descriptor=query_only))
    assert failing.status is GateStatus.FAIL
    assert any("'fetch'" in finding for finding in failing.findings)
    keyless = memo_descriptor(
        capabilities=(
            declare_capability("memo.notes", "query"),
            *memo_capabilities()[1:],
        )
    )
    keyless_result = CapabilitiesDeclaredGate().evaluate(_subject(descriptor=keyless))
    assert keyless_result.status is GateStatus.FAIL
    assert any("resource kind" in finding for finding in keyless_result.findings)
    assert any("selector keys" in finding for finding in keyless_result.findings)


def test_pv05_determinism_is_measured_by_repeated_execution() -> None:
    passing = DeterminismGate().evaluate(_governed())
    assert passing.status is GateStatus.PASS
    assert "memo.notes" in passing.evidence["measured"]


def test_pv05_fails_when_a_deterministic_capability_is_not_reproducible() -> None:
    class DriftingProvider(MemoProvider):
        def __init__(self, descriptor, config=None) -> None:  # type: ignore[no-untyped-def]
            super().__init__(descriptor, config)
            self._calls = 0

        def resolve_query(
            self, capability: ProviderCapability, request: ProviderQuery
        ) -> Iterable[ProviderResource]:
            self._calls += 1
            yield self.resource(f"drift-{self._calls}", MEMO_RESOURCE_KIND, {})

    descriptor = memo_descriptor()
    result = DeterminismGate().evaluate(
        _subject(descriptor=descriptor, instance=DriftingProvider(descriptor))
    )
    assert result.status is GateStatus.FAIL
    assert "different result" in result.findings[0]


def test_pv05_refuses_a_provider_declaring_nothing_deterministic() -> None:
    nondeterministic = memo_descriptor(
        capabilities=tuple(
            declare_capability(
                capability.name,
                capability.operation,
                resource_kind=capability.resource_kind,
                selector_keys=capability.selector_keys,
                deterministic=False,
            )
            for capability in memo_capabilities()
        )
    )
    result = DeterminismGate().evaluate(_subject(descriptor=nondeterministic))
    assert result.status is GateStatus.FAIL


def test_pv05_is_indeterminate_without_an_instance_or_an_executable_capability() -> None:
    assert DeterminismGate().evaluate(_subject()).status is GateStatus.INDETERMINATE
    gated = memo_descriptor(
        capabilities=(
            declare_capability(
                "memo.notes",
                "query",
                resource_kind=MEMO_RESOURCE_KIND,
                selector_keys=("tag",),
                required_selector_keys=("tag",),
            ),
            *memo_capabilities()[1:],
        )
    )
    result = DeterminismGate().evaluate(_subject(descriptor=gated, instance=MemoProvider(gated)))
    assert result.status is GateStatus.INDETERMINATE


def test_pv05_reports_a_refused_query_as_a_finding() -> None:
    descriptor = memo_descriptor()
    result = DeterminismGate().evaluate(
        _subject(descriptor=descriptor, instance=FaultyProvider(descriptor))
    )
    assert result.status is GateStatus.FAIL
    assert "query refused" in result.findings[0]


def test_pv06_provenance_samples_and_attests_every_resource() -> None:
    passing = ProvenanceGate().evaluate(_governed())
    assert passing.status is GateStatus.PASS
    assert passing.evidence["sampled"] == 3
    assert passing.evidence["attested"] == 3


def test_pv06_fails_without_a_declared_source_of_record() -> None:
    descriptor = memo_descriptor(source_of_record="")
    result = ProvenanceGate().evaluate(_subject(descriptor=descriptor))
    assert result.status is GateStatus.FAIL
    assert ProvenanceGate().evaluate(_subject()).status is GateStatus.INDETERMINATE


def test_pv06_fails_when_an_attestation_cannot_be_produced() -> None:
    class UnattestableProvider(MemoProvider):
        def provenance_chain(self, resource: ProviderResource) -> tuple[str, ...]:
            return ()

    descriptor = memo_descriptor()
    result = ProvenanceGate().evaluate(
        _subject(descriptor=descriptor, instance=UnattestableProvider(descriptor))
    )
    assert result.status is GateStatus.FAIL
    assert "unverified" in result.findings[0]


def test_pv07_fail_closed_probes_three_refusal_paths() -> None:
    passing = FailClosedGate().evaluate(_governed())
    assert passing.status is GateStatus.PASS
    assert set(passing.evidence["probes"]) == {
        "undeclared_capability",
        "undeclared_selector",
        "absent_resource",
    }
    assert FailClosedGate().evaluate(_subject()).status is GateStatus.INDETERMINATE


def test_pv07_fails_a_provider_that_serves_anything_it_is_asked_for() -> None:
    class PermissiveProvider(MemoProvider):
        def query(self, request: ProviderQuery):  # type: ignore[override]
            return super().query(ProviderQuery(capability="memo.notes"))

        def fetch(self, resource_id: str) -> ProviderResource:
            return self.resource(resource_id, MEMO_RESOURCE_KIND, {"fabricated": True})

    descriptor = memo_descriptor()
    result = FailClosedGate().evaluate(
        _subject(descriptor=descriptor, instance=PermissiveProvider(descriptor))
    )
    assert result.status is GateStatus.FAIL
    assert len(result.findings) == 3


def test_pv07_treats_an_untyped_escape_as_a_finding() -> None:
    class UntypedProvider(MemoProvider):
        def query(self, request: ProviderQuery):  # type: ignore[override]
            raise RuntimeError("raw")

        def fetch(self, resource_id: str) -> ProviderResource:
            raise RuntimeError("raw")

    descriptor = memo_descriptor()
    result = FailClosedGate().evaluate(
        _subject(descriptor=descriptor, instance=UntypedProvider(descriptor))
    )
    assert result.status is GateStatus.FAIL
    assert all("untyped" in finding for finding in result.findings)


def test_pv07_notes_when_there_is_no_query_capability_to_probe() -> None:
    descriptor = memo_descriptor(
        capabilities=(
            declare_capability("memo.note", "fetch", resource_kind=MEMO_RESOURCE_KIND),
            declare_capability("memo.attestation", "verify", resource_kind=MEMO_RESOURCE_KIND),
        )
    )

    class FetchOnly:
        def describe(self):  # type: ignore[no-untyped-def]
            return descriptor

        def capabilities(self):  # type: ignore[no-untyped-def]
            return descriptor.capabilities

        def health(self) -> ProviderHealth:
            return ProviderHealth(provider_id=descriptor.provider_id, state=ProviderState.SERVING)

        def query(self, request: ProviderQuery):  # type: ignore[no-untyped-def]
            raise ProviderValidationError("no query surface")

        def fetch(self, resource_id: str):  # type: ignore[no-untyped-def]
            raise ProviderValidationError("absent")

        def verify(self, resource_id: str):  # type: ignore[no-untyped-def]
            raise ProviderValidationError("absent")

    result = FailClosedGate().evaluate(_subject(descriptor=descriptor, instance=FetchOnly()))
    assert result.status is GateStatus.FAIL
    assert any("no query capability" in finding for finding in result.findings)


def test_pv08_effects_declared() -> None:
    passing = EffectsDeclaredGate().evaluate(_governed())
    assert passing.status is GateStatus.PASS
    assert passing.evidence["declared_effects"] == ["mem:read"]


def test_pv08_refuses_a_malformed_effect() -> None:
    descriptor = memo_descriptor(
        capabilities=(
            declare_capability(
                "memo.notes",
                "query",
                resource_kind=MEMO_RESOURCE_KIND,
                selector_keys=("tag",),
                effects=("filesystem",),
            ),
            *memo_capabilities()[1:],
        )
    )
    result = EffectsDeclaredGate().evaluate(_subject(descriptor=descriptor))
    assert result.status is GateStatus.FAIL
    assert "domain:action" in result.findings[0]


def test_pv08_refuses_determinism_declared_alongside_a_mutating_effect() -> None:
    descriptor = memo_descriptor(
        capabilities=(
            declare_capability(
                "memo.notes",
                "query",
                resource_kind=MEMO_RESOURCE_KIND,
                selector_keys=("tag",),
                deterministic=True,
                effects=("db:write",),
            ),
            *memo_capabilities()[1:],
        )
    )
    result = EffectsDeclaredGate().evaluate(_subject(descriptor=descriptor))
    assert result.status is GateStatus.FAIL
    assert "mutating effect" in result.findings[0]


def test_pv08_permits_a_mutating_effect_that_is_honestly_non_deterministic() -> None:
    descriptor = memo_descriptor(
        capabilities=(
            declare_capability(
                "memo.notes",
                "query",
                resource_kind=MEMO_RESOURCE_KIND,
                selector_keys=("tag",),
                deterministic=False,
                effects=("net:send",),
            ),
            *memo_capabilities()[1:],
        )
    )
    assert EffectsDeclaredGate().evaluate(_subject(descriptor=descriptor)).status is GateStatus.PASS


def test_pv09_fault_isolation() -> None:
    passing = FaultIsolationGate().evaluate(_governed())
    assert passing.status is GateStatus.PASS
    assert passing.evidence["health_state"] == "serving"
    assert FaultIsolationGate().evaluate(_subject()).status is GateStatus.INDETERMINATE


def test_pv09_fails_when_health_raises() -> None:
    class ExplodingHealth(MemoProvider):
        def health(self) -> ProviderHealth:
            raise RuntimeError("no health")

    descriptor = memo_descriptor()
    result = FaultIsolationGate().evaluate(
        _subject(descriptor=descriptor, instance=ExplodingHealth(descriptor))
    )
    assert result.status is GateStatus.FAIL
    assert "raised" in result.findings[0]


def test_pv09_fails_when_health_returns_the_wrong_type_or_a_fault_escapes() -> None:
    class WrongHealth(MemoProvider):
        def health(self):  # type: ignore[override]
            return "fine"

        def fetch(self, resource_id: str) -> ProviderResource:
            raise RuntimeError("raw")

    descriptor = memo_descriptor()
    result = FaultIsolationGate().evaluate(
        _subject(descriptor=descriptor, instance=WrongHealth(descriptor))
    )
    assert result.status is GateStatus.FAIL
    assert len(result.findings) == 2


def test_pv09_fails_when_an_absent_fetch_neither_returns_nor_raises() -> None:
    class FabricatingProvider(MemoProvider):
        def fetch(self, resource_id: str) -> ProviderResource:
            return self.resource(resource_id, MEMO_RESOURCE_KIND, {})

    descriptor = memo_descriptor()
    result = FaultIsolationGate().evaluate(
        _subject(descriptor=descriptor, instance=FabricatingProvider(descriptor))
    )
    assert result.status is GateStatus.FAIL


def test_pv10_lifecycle_governed() -> None:
    passing = LifecycleGovernedGate().evaluate(_governed())
    assert passing.status is GateStatus.PASS
    assert passing.evidence["phase"] == "registered"
    assert LifecycleGovernedGate().evaluate(_subject()).status is GateStatus.INDETERMINATE


def test_pv10_fails_for_an_untracked_provider_and_a_broken_chain() -> None:
    untracked = _subject(lifecycle=ProviderLifecycle())
    assert LifecycleGovernedGate().evaluate(untracked).status is GateStatus.FAIL
    subject = _governed()
    lifecycle = subject.lifecycle
    assert lifecycle is not None
    original = lifecycle.entries[0]
    lifecycle._entries[0] = LifecycleEntry(  # noqa: SLF001 - tamper simulation
        sequence=original.sequence,
        qualified_id=original.qualified_id,
        from_phase=ProviderPhase.CERTIFIED,
        to_phase=ProviderPhase.ACTIVE,
        reason=original.reason,
        evidence_ref=original.evidence_ref,
        previous_hash=original.previous_hash,
        entry_hash=original.entry_hash,
    )
    result = LifecycleGovernedGate().evaluate(subject)
    assert result.status is GateStatus.FAIL
    assert any("hash chain" in finding for finding in result.findings)


def test_pv11_certifiable() -> None:
    passing = CertifiableGate().evaluate(_governed())
    assert passing.status is GateStatus.PASS
    assert CertifiableGate().evaluate(_subject()).status is GateStatus.INDETERMINATE
    unregistered = _subject(registry=ProviderRegistry())
    assert CertifiableGate().evaluate(unregistered).status is GateStatus.FAIL


def test_pv11_fails_when_the_descriptor_diverges_from_the_registered_one() -> None:
    registered = memo_descriptor()
    registry = ProviderRegistry.from_descriptors([registered])
    drifted = memo_descriptor(source_of_record="a substrate nobody registered")
    result = CertifiableGate().evaluate(ValidationSubject(descriptor=drifted, registry=registry))
    assert result.status is GateStatus.FAIL
    assert "differs from the registered descriptor" in result.findings[0]


def test_pv11_fails_in_a_non_certifiable_phase() -> None:
    descriptor = memo_descriptor()
    registry = ProviderRegistry.from_descriptors([descriptor])
    lifecycle = ProviderLifecycle()
    lifecycle.declare(descriptor.qualified_id)
    result = CertifiableGate().evaluate(
        ValidationSubject(descriptor=descriptor, registry=registry, lifecycle=lifecycle)
    )
    assert result.status is GateStatus.FAIL
    assert "not a certifiable phase" in result.findings[0]


def test_pv12_composability() -> None:
    assert ComposabilityGate().evaluate(_governed()).status is GateStatus.PASS
    assert ComposabilityGate().evaluate(_subject()).status is GateStatus.PASS


def test_pv12_is_indeterminate_when_dependencies_cannot_be_resolved() -> None:
    dependent = memo_descriptor(dependencies=(declare_dependency("some.dependency"),))
    result = ComposabilityGate().evaluate(_subject(descriptor=dependent))
    assert result.status is GateStatus.INDETERMINATE


def test_pv12_fails_on_an_unresolvable_dependency() -> None:
    dependent = memo_descriptor(dependencies=(declare_dependency("gone.away"),))
    registry = ProviderRegistry.from_descriptors([dependent])
    result = ComposabilityGate().evaluate(
        ValidationSubject(descriptor=dependent, registry=registry)
    )
    assert result.status is GateStatus.FAIL


def test_pv13_additive_evolution() -> None:
    assert AdditiveEvolutionGate().evaluate(_governed()).status is GateStatus.PASS
    assert AdditiveEvolutionGate().evaluate(_subject()).status is GateStatus.INDETERMINATE


def test_pv13_detects_a_narrowed_successor_smuggled_into_the_registry() -> None:
    """The registry refuses narrowing, so the gate is proven against a forced registry."""
    v1 = memo_descriptor(version="1.0.0")
    v2 = memo_descriptor(version="1.1.0", capabilities=memo_capabilities()[:1])
    registry = ProviderRegistry()
    registry.register(v1)
    registry._records[v2.qualified_id] = registry._records[v1.qualified_id].__class__(  # noqa: SLF001
        sequence=2, descriptor=v2, descriptor_hash=v2.content_hash(), registration_id="forced"
    )
    result = AdditiveEvolutionGate().evaluate(ValidationSubject(descriptor=v2, registry=registry))
    assert result.status is GateStatus.FAIL
    assert "removed" in result.findings[0]


def test_pv14_extensibility() -> None:
    passing = ExtensibilityGate().evaluate(_governed())
    assert passing.status is GateStatus.PASS
    assert passing.evidence["entry_point"].endswith(":build_memo")


def test_pv14_is_indeterminate_for_a_declared_only_provider() -> None:
    result = ExtensibilityGate().evaluate(_subject(descriptor=memo_descriptor(entry_point="")))
    assert result.status is GateStatus.INDETERMINATE
    assert "declared, not yet realizable" in result.findings[0]


def test_pv14_fails_on_a_malformed_entry_point() -> None:
    result = ExtensibilityGate().evaluate(
        _subject(descriptor=memo_descriptor(entry_point="no-colon-here"))
    )
    assert result.status is GateStatus.FAIL


# ----------------------------------------------------------------- aggregate verdict


def test_a_fully_equipped_conformant_provider_passes_every_gate() -> None:
    report = ProviderValidator().validate(_governed())
    assert report.status is ValidationStatus.PASSED
    assert report.passed is True
    assert report.counts() == {
        "total": 14,
        "pass": 14,
        "fail": 0,
        "indeterminate": 0,
        "blocking_failures": 0,
    }
    assert report.failures() == ()
    assert report.result("PV-01-INTERFACE-COMPLETE").status is GateStatus.PASS
    assert report.report_hash() == ProviderValidator().validate(_governed()).report_hash()


def test_a_declared_only_provider_is_incomplete_not_failed() -> None:
    descriptor = memo_descriptor(entry_point="")
    registry = ProviderRegistry.from_descriptors([descriptor])
    lifecycle = ProviderLifecycle()
    lifecycle.declare(descriptor.qualified_id)
    lifecycle.transition(descriptor.qualified_id, ProviderPhase.REGISTERED)
    report = ProviderValidator().validate(
        ValidationSubject(descriptor=descriptor, registry=registry, lifecycle=lifecycle)
    )
    assert report.status is ValidationStatus.INCOMPLETE
    assert report.failures() == ()
    assert {r.gate_id for r in report.indeterminate()} >= {
        "PV-01-INTERFACE-COMPLETE",
        "PV-14-EXTENSIBLE",
    }


def test_a_blocking_failure_outranks_indeterminacy() -> None:
    descriptor = memo_descriptor(entry_point="", source_of_record="")
    report = ProviderValidator().validate(ValidationSubject(descriptor=descriptor))
    assert report.status is ValidationStatus.FAILED


def test_an_unknown_gate_lookup_fails_closed() -> None:
    report = ProviderValidator().validate(_governed())
    with pytest.raises(ProviderValidationError):
        report.result("PV-99-IMAGINARY")


def test_a_raising_gate_is_recorded_rather_than_aborting_the_pass() -> None:
    class ExplodingGate(ProviderGate):
        article_id = "PC-01"

        def evaluate(self, subject: ValidationSubject) -> GateResult:
            raise RuntimeError("gate exploded")

    report = ProviderValidator(gates=[ExplodingGate()]).validate(_governed())
    assert report.status is ValidationStatus.FAILED
    result = report.result("PV-01-INTERFACE-COMPLETE")
    assert result.summary == "gate execution raised"
    assert "RuntimeError" in result.findings[0]


def test_an_advisory_failure_does_not_block() -> None:
    class AdvisoryGate(ProviderGate):
        article_id = "PC-02"
        severity = GateSeverity.ADVISORY

        def evaluate(self, subject: ValidationSubject) -> GateResult:
            return self._fail("advisory only", ("noted",))

    report = ProviderValidator(gates=[AdvisoryGate()]).validate(_governed())
    assert report.status is ValidationStatus.PASSED
    assert report.counts()["blocking_failures"] == 0
    assert report.result("PV-02-KIND-OPEN").blocking_failure is False


def test_report_projection_carries_the_constitution_it_was_measured_against() -> None:
    payload = ProviderValidator().validate(_governed()).to_dict()
    assert payload["constitution_id"] == "UCOS-PROVIDER-CONSTITUTION"
    assert payload["status"] == "passed"
    assert len(payload["results"]) == 14
    assert payload["results"][0]["article_id"] == "PC-01"


def test_the_query_operation_gate_binding_is_enforced() -> None:
    """A capability bound to the wrong operation is refused, not silently accepted."""
    provider = MemoProvider(memo_descriptor())
    with pytest.raises(ProviderCapabilityError) as exc:
        provider.query(ProviderQuery(capability="memo.attestation"))
    assert exc.value.code == "UPA-CAPABILITY"
    assert "not bound to the QUERY operation" in exc.value.message
    assert ProviderOperation.VERIFY.value == "verify"
