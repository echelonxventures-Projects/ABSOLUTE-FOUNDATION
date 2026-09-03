"""UPA-000011 — the Provider Framework façade, driven end to end.

WHY THIS MODULE EXISTS, STATED AS A MEASUREMENT. Every collaborator of the Universal
Provider Architecture has a suite — registry, lifecycle, discovery, validation,
certification, composition — and the object that WIRES THEM TOGETHER had none. Nothing in
the repository ever constructed a :class:`ProviderFramework`, so the pipeline PC-11 is
written in (discover → admit → realize → validate → certify → activate) existed only as a
sequence of individually-tested parts, and the two properties that only the façade can have
were untested: that a provider which fails certification STOPS, recorded, at the phase it
reached; and that :meth:`ProviderFramework.provider` refuses to hand a non-serving provider
to a consumer. A pipeline is exactly the place where correct parts compose into a wrong
whole, so this is the layer the guarantee lives at.
"""

from __future__ import annotations

import json
from pathlib import Path
from platform.tests.universal_provider_helpers import (
    MEMO_ENTRY_POINT,
    memo_descriptor,
    memo_manifest,
    write_manifest,
)
from platform.universal_provider.certification import CertificationTier
from platform.universal_provider.composition import CompositionStrategy
from platform.universal_provider.errors import (
    ProviderFrameworkError,
    ProviderLifecycleError,
    ProviderRegistryError,
)
from platform.universal_provider.framework import (
    PROVIDER_FRAMEWORK_VERSION,
    OnboardingResult,
    ProviderFramework,
)
from platform.universal_provider.lifecycle import ProviderPhase
from platform.universal_provider.registry import ProviderRegistry

import pytest

BROKEN_ENTRY_POINT = "platform.tests.universal_provider_helpers:exploding_factory"


@pytest.fixture
def framework() -> ProviderFramework:
    return ProviderFramework()


def _onboarded(framework: ProviderFramework, **overrides) -> OnboardingResult:
    return framework.onboard(memo_descriptor(**overrides))


# -- composition of the collaborators --------------------------------------------------


def test_the_framework_assembles_a_complete_architecture_by_default(framework):
    assert framework.registry is not None
    assert framework.lifecycle is not None
    assert framework.validator is not None
    assert framework.certifier is not None
    assert framework.discovery is not None
    assert len(framework.constitution_hash()) == 64


def test_every_collaborator_is_injectable(framework):
    registry = ProviderRegistry()
    other = ProviderFramework(registry=registry)
    assert other.registry is registry
    assert other.registry is not framework.registry


# -- the pipeline ----------------------------------------------------------------------


def test_a_conformant_provider_is_onboarded_all_the_way_to_active(framework):
    result = _onboarded(framework)
    assert result.active is True
    assert result.phase is ProviderPhase.ACTIVE
    assert result.realized is True
    assert result.registration_id
    assert result.certificate is not None
    assert result.tier == CertificationTier.UNIVERSAL.value
    assert result.report is not None and result.report.passed
    assert framework.serving() == (result.qualified_id,)
    assert framework.provider(result.qualified_id) is framework.realized(result.qualified_id)


def test_a_provider_that_cannot_be_built_stops_recorded_rather_than_in_limbo(framework):
    """PC-09: onboarding a catalog must not be aborted by one bad member, and PC-11: a
    provider that is not certified may not serve. Both are visible in one outcome."""
    result = _onboarded(framework, entry_point=BROKEN_ENTRY_POINT)
    assert result.active is False
    assert result.realized is False
    assert any("not realized" in reason for reason in result.reasons)
    assert any("activation withheld" in reason for reason in result.reasons)
    assert framework.serving() == ()
    assert framework.realized(result.qualified_id) is None
    with pytest.raises(ProviderLifecycleError):
        framework.provider(result.qualified_id)


def test_an_admission_the_registry_refuses_marks_the_provider_rejected(framework):
    descriptor = memo_descriptor()
    framework.admit(descriptor)
    with pytest.raises(ProviderRegistryError):
        framework.admit(descriptor)
    assert framework.lifecycle.phase(descriptor.qualified_id) is ProviderPhase.REJECTED


def test_onboarding_a_provider_the_registry_refuses_reports_it_rather_than_raising(framework):
    descriptor = memo_descriptor()
    framework.admit(descriptor)
    result = framework.onboard(descriptor)
    assert result.registration_id == ""
    assert any("admission refused" in reason for reason in result.reasons)
    assert result.report is None and result.certificate is None
    assert result.tier == "none"


def test_realization_is_cached_so_one_substrate_is_observed(framework):
    record = framework.admit(memo_descriptor())
    first = framework.realize(record.qualified_id)
    assert framework.realize(record.qualified_id) is first
    assert framework.realized(record.qualified_id) is first


def test_a_provider_that_cannot_be_built_is_still_validated(framework):
    """The report has to distinguish 'not yet built' from 'built wrong', which is the whole
    reason the gates are tri-state."""
    record = framework.admit(memo_descriptor(entry_point=BROKEN_ENTRY_POINT))
    with pytest.raises(ProviderFrameworkError):
        framework.realize(record.qualified_id)
    report = framework.validate(record.qualified_id)
    assert report.indeterminate()
    assert not report.passed


def test_activation_requires_a_certificate_that_authorizes_it(framework):
    record = framework.admit(memo_descriptor(entry_point=BROKEN_ENTRY_POINT))
    with pytest.raises(ProviderLifecycleError, match="PC-11"):
        framework.activate(record.qualified_id)
    framework.validate(record.qualified_id)
    certificate = framework.certify(record.qualified_id)
    assert certificate.authorizes_activation is False
    with pytest.raises(ProviderLifecycleError, match="PC-11"):
        framework.activate(record.qualified_id)


def test_a_certificate_may_be_issued_from_evidence_already_gathered(framework):
    record = framework.admit(memo_descriptor())
    framework.realize(record.qualified_id)
    report = framework.validate(record.qualified_id)
    assert framework.certify(record.qualified_id, report).tier is CertificationTier.UNIVERSAL


# -- withdrawal ------------------------------------------------------------------------


def test_a_suspended_provider_stops_serving_and_can_be_reinstated(framework):
    result = _onboarded(framework)
    assert framework.suspend(result.qualified_id, reason="under review") is (
        ProviderPhase.SUSPENDED
    )
    assert framework.serving() == ()
    with pytest.raises(ProviderLifecycleError):
        framework.provider(result.qualified_id)
    assert framework.activate(result.qualified_id) is ProviderPhase.ACTIVE
    assert framework.serving() == (result.qualified_id,)


def test_retirement_is_terminal_and_releases_the_instance(framework):
    result = _onboarded(framework)
    assert framework.retire(result.qualified_id, reason="superseded") is ProviderPhase.RETIRED
    assert framework.realized(result.qualified_id) is None
    assert framework.serving() == ()


# -- consumers -------------------------------------------------------------------------


def test_a_consumer_resolves_the_highest_serving_version(framework):
    older = _onboarded(framework, version="1.0.0")
    newer = _onboarded(framework, version="2.0.0")
    resolved = framework.resolve(memo_descriptor().provider_id)
    assert resolved is framework.provider(newer.qualified_id)
    assert resolved is not framework.provider(older.qualified_id)


def test_a_composition_may_only_be_built_from_providers_permitted_to_serve(framework):
    """PC-12 rests on PC-11: composing a suspended member would let a withdrawn provider
    serve through a wrapper."""
    first = _onboarded(framework, provider_id="memo.one")
    second = _onboarded(framework, provider_id="memo.two")
    composite = framework.compose(
        "memo.composite",
        memo_descriptor().kind,
        "1.0.0",
        (first.qualified_id, second.qualified_id),
        strategy=CompositionStrategy.FEDERATED,
        name="Composite",
        authority="TEST",
    )
    assert len(composite.members) == 2

    framework.suspend(second.qualified_id)
    with pytest.raises(ProviderLifecycleError):
        framework.compose(
            "memo.composite",
            memo_descriptor().kind,
            "1.0.0",
            (first.qualified_id, second.qualified_id),
        )


def test_a_reference_that_is_not_version_pinned_is_refused(framework):
    with pytest.raises(ProviderRegistryError, match="version-pinned"):
        framework.realize("memo.fixture")


# -- discovery -------------------------------------------------------------------------


def test_a_catalog_directory_is_discovered_and_onboarded_in_order(framework, tmp_path: Path):
    def _manifest(provider_id: str) -> dict:
        payload = memo_manifest()
        payload["identity"] = {**payload["identity"], "provider_id": provider_id}
        return payload

    catalog = tmp_path / "catalog"
    write_manifest(catalog, "a.json", _manifest("memo.alpha"))
    write_manifest(catalog, "b.json", _manifest("memo.beta"))
    assert framework.add_catalog(catalog) is framework

    discovered = framework.discover()
    assert len(discovered.descriptors()) == 2

    results = framework.onboard_discovered(discovered)
    assert [r.qualified_id for r in results] == [d.qualified_id for d in discovered.descriptors()]
    assert all(r.active for r in results)

    # onboarding without a supplied result re-runs discovery for itself
    again = ProviderFramework().add_catalog(catalog).onboard_discovered()
    assert len(again) == 2


# -- the state report ------------------------------------------------------------------


def test_the_framework_state_is_deterministic_and_content_addressed(framework):
    result = _onboarded(framework)
    state = framework.state()
    assert state["framework_version"] == PROVIDER_FRAMEWORK_VERSION
    assert state["constitution_hash"] == framework.constitution_hash()
    assert state["registry"]["providers"] == [result.qualified_id]
    assert state["lifecycle"]["serving"] == [result.qualified_id]
    assert state["lifecycle"]["intact"] is True
    assert state["certification"]["intact"] is True
    assert state["certification"]["tiers"][result.qualified_id] == result.tier
    assert state["realized"] == [result.qualified_id]
    assert framework.state_hash() == framework.state_hash()
    assert len(framework.state_hash()) == 64
    assert json.dumps(state, sort_keys=True)


def test_an_onboarding_result_serialises_everything_it_decided(framework):
    payload = _onboarded(framework).to_dict()
    assert payload["phase"] == ProviderPhase.ACTIVE.value
    assert payload["realized"] is True
    assert payload["validation"]["status"] == "passed"
    assert payload["certificate"]["tier"] == CertificationTier.UNIVERSAL.value
    assert payload["reasons"] == []


def test_an_unrealized_result_serialises_as_a_reported_absence():
    payload = OnboardingResult(
        qualified_id="memo.fixture@1.0.0",
        phase=ProviderPhase.REGISTERED,
        registration_id="",
    ).to_dict()
    assert payload["validation"] is None
    assert payload["certificate"] is None
    assert payload["tier"] == "none"
    assert payload["realized"] is False


def test_the_entry_point_the_fixture_declares_is_the_one_resolved(framework):
    assert memo_descriptor().entry_point == MEMO_ENTRY_POINT
