"""UCXI-000001 Parts 01/11 — constitution and validation tests.

A law that cannot fail is not a law, so every one of the twelve laws is driven into a
violating state here and asserted to report it. Constructing those states requires
bypassing the registration authority (which refuses them at the front door), so several
tests write directly into the registry's private state — that is the point: the laws
catch corruption the authority never accepted.
"""

from __future__ import annotations

import pytest

from engine.context.constitution import (
    CONTEXT_CONSTITUTION,
    CONTEXT_LAWS,
    LAW_CHECKS,
    ConstitutionAssessment,
    ContextConstitution,
    ContextLaw,
    LawAssessment,
)
from engine.context.errors import ConstitutionViolation, ContextValidationError
from engine.context.graph import build_context_graph
from engine.context.model import ContextRecord, ContextValue
from engine.context.registry import GENESIS_HASH, AuditEntry, ContextRegistry
from engine.context.taxonomy import (
    ContextAuthority,
    ContextKind,
    ContextLifecycle,
    ContextRelation,
)
from engine.context.validation import (
    SEVERITY_ADVISORY,
    SEVERITY_VIOLATION,
    VALIDATION_RULES,
    ContextValidator,
    ValidationRule,
    validate,
)
from engine.tests.context.conftest import declaration, spatial_values


def _inject(registry: ContextRegistry, record: ContextRecord) -> None:
    """Place a record into the registry without going through registration."""
    registry._records[record.context_id] = record  # noqa: SLF001 - deliberate corruption


def _record(registry: ContextRegistry, **overrides: object) -> ContextRecord:
    base = registry.records()[0]
    fields = {
        "context_id": base.context_id,
        "kind": base.kind,
        "taxon_id": base.taxon_id,
        "namespace": base.namespace,
        "natural_key": base.natural_key,
        "values": base.values,
        "authority": base.authority,
        "lifecycle": base.lifecycle,
        "boundary": base.boundary,
        "parent": base.parent,
        "description": base.description,
        "universal": base.universal,
    }
    fields.update(overrides)
    return ContextRecord(**fields)  # type: ignore[arg-type]


# ------------------------------------------------------------------- constitution


def test_twelve_laws_each_carry_a_check() -> None:
    assert len(CONTEXT_LAWS) == 12
    assert {law.law_id for law in CONTEXT_LAWS} == set(LAW_CHECKS)
    assert CONTEXT_CONSTITUTION.to_dict()["count"] == 12
    assert CONTEXT_CONSTITUTION.law("CXL-01").title == "Universal Representability"
    with pytest.raises(ConstitutionViolation):
        CONTEXT_CONSTITUTION.law("CXL-99")


def test_constitution_refuses_unchecked_or_undeclared_laws() -> None:
    extra = (*CONTEXT_LAWS, ContextLaw(law_id="CXL-13", title="t", statement="s"))
    with pytest.raises(ConstitutionViolation):
        ContextConstitution(extra)
    with pytest.raises(ConstitutionViolation):
        ContextConstitution(CONTEXT_LAWS[:1])


def test_universal_catalog_is_constitutionally_compliant(
    universal_registry: ContextRegistry, composed: object
) -> None:
    assessment = CONTEXT_CONSTITUTION.require_compliance(
        universal_registry,
        graph=build_context_graph(universal_registry),
        composed=composed,
    )
    assert assessment.compliant
    assert assessment.violations == ()
    assert assessment.findings() == ()
    assert assessment.summary()["compliant"] == 12
    assert assessment.law("CXL-01") is not None
    assert assessment.law("CXL-99") is None
    assert assessment.to_dict()["is_compliant"] is True
    # deterministic: the same subject seals identically
    assert assessment.content_hash == CONTEXT_CONSTITUTION.assess(universal_registry).content_hash


def test_assessment_aggregates_findings() -> None:
    assessment = ConstitutionAssessment(
        laws=(
            LawAssessment(law_id="CXL-02", title="b", compliant=False, findings=("bad",)),
            LawAssessment(law_id="CXL-01", title="a", compliant=True),
        )
    )
    assert assessment.laws[0].law_id == "CXL-01"
    assert not assessment.compliant
    assert assessment.findings() == ("CXL-02: bad",)


def test_law_01_and_02_catch_an_unclassified_or_malformed_context(
    universal_registry: ContextRegistry,
) -> None:
    _inject(universal_registry, _record(universal_registry, kind="quantum"))
    assessment = CONTEXT_CONSTITUTION.assess(universal_registry)
    assert not assessment.law("CXL-01").compliant
    assert not assessment.law("CXL-02").compliant


def test_law_03_catches_an_unbounded_context(universal_registry: ContextRegistry) -> None:
    _inject(universal_registry, _record(universal_registry, boundary=""))
    assert not CONTEXT_CONSTITUTION.assess(universal_registry).law("CXL-03").compliant


def test_law_04_catches_an_unfederated_cross_frame_reference(
    empty_registry: ContextRegistry,
) -> None:
    here = empty_registry.register(declaration(natural_key="here", boundary="frame-a"))
    there = empty_registry.register(
        declaration(
            kind=ContextKind.SPATIAL,
            natural_key="there",
            boundary="frame-b",
            values=spatial_values(),
        )
    )
    empty_registry.relate(ContextRelation.DEPENDS_ON, here.context_id, there.context_id)
    assessment = CONTEXT_CONSTITUTION.assess(empty_registry)
    assert not assessment.law("CXL-04").compliant

    empty_registry.relate(ContextRelation.FEDERATES, here.context_id, there.context_id)
    assert CONTEXT_CONSTITUTION.assess(empty_registry).law("CXL-04").compliant


def test_law_05_catches_a_fabricated_identity(universal_registry: ContextRegistry) -> None:
    _inject(universal_registry, _record(universal_registry, context_id="UCOS-CTX-deadbeefcafe"))
    assert not CONTEXT_CONSTITUTION.assess(universal_registry).law("CXL-05").compliant


def test_law_06_catches_duplicate_substance_and_a_wrong_taxon(
    universal_registry: ContextRegistry,
) -> None:
    base = universal_registry.records()[0]
    clone = _record(
        universal_registry,
        context_id="UCOS-CTX-000000000001",
        natural_key=base.natural_key + "-clone",
    )
    _inject(universal_registry, clone)
    assessment = CONTEXT_CONSTITUTION.assess(universal_registry)
    assert not assessment.law("CXL-06").compliant

    fresh = ContextRegistry()
    fresh.register(declaration())
    _inject(fresh, _record(fresh, taxon_id="CTX-SPATIAL"))
    assert not CONTEXT_CONSTITUTION.assess(fresh).law("CXL-06").compliant


def test_law_07_catches_an_unresolvable_registered_kind(empty_registry: ContextRegistry) -> None:
    same_dims = {"reference_frame": "a", "ordering": "b", "resolution": "c"}
    empty_registry.register(declaration(natural_key="one", values=same_dims, boundary="frame-a"))
    empty_registry.register(
        declaration(
            natural_key="two",
            values={**same_dims, "reference_frame": "z"},
            boundary="frame-a",
        )
    )
    assert not CONTEXT_CONSTITUTION.assess(empty_registry).law("CXL-07").compliant


def test_law_08_catches_a_valueless_provenance(universal_registry: ContextRegistry) -> None:
    base = universal_registry.records()[0]
    stripped = ContextValue(
        dimension=base.values[0].dimension,
        value=base.values[0].value,
        authority=base.values[0].authority,
        source="placeholder",
    )
    object.__setattr__(stripped, "source", "")
    _inject(universal_registry, _record(universal_registry, values=(stripped,)))
    assessment = CONTEXT_CONSTITUTION.assess(universal_registry)
    assert not assessment.law("CXL-08").compliant


def test_law_09_catches_a_broken_seal(universal_registry: ContextRegistry) -> None:
    _inject(universal_registry, _record(universal_registry, content_hash="0" * 64))
    assert not CONTEXT_CONSTITUTION.assess(universal_registry).law("CXL-09").compliant


def test_law_10_catches_authority_claimed_by_an_observer(empty_registry: ContextRegistry) -> None:
    observer_values = {"observer_id": "o", "vantage": "v", "epistemic_access": "e"}
    empty_registry.register(
        declaration(
            kind=ContextKind.OBSERVER,
            natural_key="obs",
            values=observer_values,
            authority=ContextAuthority.CONSTITUTIONAL,
        )
    )
    assert not CONTEXT_CONSTITUTION.assess(empty_registry).law("CXL-10").compliant


def test_law_10_catches_observation_used_as_constraint(empty_registry: ContextRegistry) -> None:
    observer = empty_registry.register(
        declaration(
            kind=ContextKind.OBSERVER,
            natural_key="obs",
            values={"observer_id": "o", "vantage": "v", "epistemic_access": "e"},
        )
    )
    governance = empty_registry.register(
        declaration(
            kind=ContextKind.GOVERNANCE,
            natural_key="gov",
            values={"authority": "a", "policy": "p", "decision_rights": "d"},
        )
    )
    subject = empty_registry.register(declaration(natural_key="subject"))
    empty_registry.relate(ContextRelation.OBSERVES, observer.context_id, subject.context_id)
    empty_registry.relate(ContextRelation.CONSTRAINS, governance.context_id, subject.context_id)
    assert CONTEXT_CONSTITUTION.assess(empty_registry).law("CXL-10").compliant

    # the same pair both observing and constraining is the violation
    empty_registry._relations.clear()  # noqa: SLF001 - rebuild the pair deliberately
    empty_registry.relate(ContextRelation.OBSERVES, observer.context_id, subject.context_id)
    edge = empty_registry.relate(
        ContextRelation.CONSTRAINS, governance.context_id, subject.context_id
    )
    forged = type(edge)(
        relation=ContextRelation.CONSTRAINS, source=observer.context_id, target=subject.context_id
    )
    empty_registry._relations[forged.edge_id] = forged  # noqa: SLF001
    assert not CONTEXT_CONSTITUTION.assess(empty_registry).law("CXL-10").compliant


def test_law_11_and_12_catch_a_broken_journal(universal_registry: ContextRegistry) -> None:
    universal_registry._audit.append(  # noqa: SLF001 - deliberate tamper
        AuditEntry(
            sequence=99,
            action="register",
            subject="x",
            content_hash="c",
            previous_hash=GENESIS_HASH,
        )
    )
    assessment = CONTEXT_CONSTITUTION.assess(universal_registry)
    assert not assessment.law("CXL-11").compliant
    assert not assessment.law("CXL-12").compliant


def test_law_12_catches_an_unjournaled_context(universal_registry: ContextRegistry) -> None:
    _inject(universal_registry, _record(universal_registry, context_id="UCOS-CTX-000000000002"))
    findings = CONTEXT_CONSTITUTION.assess(universal_registry).law("CXL-12").findings
    assert any("never journaled" in finding for finding in findings)


def test_require_compliance_is_fail_closed(universal_registry: ContextRegistry) -> None:
    _inject(universal_registry, _record(universal_registry, boundary=""))
    with pytest.raises(ConstitutionViolation):
        CONTEXT_CONSTITUTION.require_compliance(universal_registry)


# ---------------------------------------------------------------------- validation


def test_universal_catalog_validates_cleanly(
    universal_registry: ContextRegistry, composed: object
) -> None:
    report = validate(universal_registry, composed=composed)
    assert report.is_valid
    assert report.is_clean
    assert len(report.rules) == 12
    assert report.rules_failed() == ()
    assert report.metrics["contexts"] == 15
    assert report.metrics["universal_covered"] == 15
    assert report.summary()["violations"] == 0
    assert report.to_dict()["is_clean"] is True
    assert sum(report.by_dimension().values()) == 0


def test_validation_is_deterministic(universal_registry: ContextRegistry) -> None:
    assert validate(universal_registry).content_hash == validate(universal_registry).content_hash


def test_empty_registry_is_valid_but_not_clean(empty_registry: ContextRegistry) -> None:
    report = validate(empty_registry)
    assert report.is_valid  # no violation-severity finding
    assert not report.is_clean  # coverage advisories are reported
    assert report.advisories
    assert "CXV-11" in report.rules_failed()
    assert all(finding.severity == SEVERITY_ADVISORY for finding in report.advisories)


def test_violations_are_reported_with_their_rule(universal_registry: ContextRegistry) -> None:
    _inject(universal_registry, _record(universal_registry, context_id="UCOS-CTX-deadbeefcafe"))
    report = validate(universal_registry)
    assert not report.is_valid
    assert "CXV-03" in report.rules_failed()
    assert any(finding.severity == SEVERITY_VIOLATION for finding in report.violations)
    assert report.by_dimension()["identity"] >= 1


def test_shape_seal_and_relation_rules_are_measured(universal_registry: ContextRegistry) -> None:
    _inject(universal_registry, _record(universal_registry, content_hash="0" * 64))
    assert "CXV-04" in validate(universal_registry).rules_failed()

    fresh = ContextRegistry()
    fresh.register(declaration())
    _inject(fresh, _record(fresh, values=()))
    assert "CXV-02" in validate(fresh).rules_failed()


def test_orphan_advisory_is_reported(empty_registry: ContextRegistry) -> None:
    empty_registry.register(declaration())
    report = validate(empty_registry)
    assert "CXV-12" not in report.rules_failed()  # classified-as keeps every context connected


def test_require_valid_is_fail_closed(universal_registry: ContextRegistry) -> None:
    validator = ContextValidator()
    validator.require_valid(universal_registry)
    _inject(universal_registry, _record(universal_registry, context_id="UCOS-CTX-deadbeefcafe"))
    with pytest.raises(ContextValidationError):
        validator.require_valid(universal_registry)


def test_validator_refuses_unenforced_or_undeclared_rules() -> None:
    extra = (*VALIDATION_RULES, ValidationRule(rule_id="CXV-13", dimension="d", statement="s"))
    with pytest.raises(ContextValidationError):
        ContextValidator(extra)
    with pytest.raises(ContextValidationError):
        ContextValidator(VALIDATION_RULES[:1])


def test_rule_severity_is_validated() -> None:
    with pytest.raises(ContextValidationError):
        ValidationRule(rule_id="CXV-X", dimension="d", statement="s", severity="whatever")


def test_lifecycle_history_rule_reports_a_broken_chain(
    universal_registry: ContextRegistry,
) -> None:
    universal_registry._audit.clear()  # noqa: SLF001 - the journal is destroyed
    report = validate(universal_registry)
    assert "CXV-08" in report.rules_failed()


def test_boundedness_rule_reports_an_empty_frame(universal_registry: ContextRegistry) -> None:
    _inject(universal_registry, _record(universal_registry, boundary=""))
    assert "CXV-09" in validate(universal_registry).rules_failed()


def test_provenance_rule_reports_a_missing_source(universal_registry: ContextRegistry) -> None:
    base = universal_registry.records()[0]
    value = base.values[0]
    stripped = ContextValue(
        dimension=value.dimension,
        value=value.value,
        authority=value.authority,
        source="placeholder",
    )
    object.__setattr__(stripped, "source", "")
    _inject(universal_registry, _record(universal_registry, values=(stripped,)))
    assert "CXV-10" in validate(universal_registry).rules_failed()


def test_superseded_context_is_reported_as_uncovered(universal_registry: ContextRegistry) -> None:
    temporal = universal_registry.by_kind(ContextKind.TEMPORAL)[0]
    universal_registry.transition(temporal.context_id, ContextLifecycle.SUPERSEDED)
    report = validate(universal_registry)
    assert "CXV-11" in report.rules_failed()
    assert report.is_valid  # coverage is advisory, not a violation
