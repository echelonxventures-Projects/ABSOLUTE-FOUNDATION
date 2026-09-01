"""Ω∞ reference layer — the fourteen minimum domains, and the honesty of three-valued checking.

TWO PROPERTIES CARRY THIS MODULE.

First, ``components`` is OPAQUE. A measurement architecture typed as ``tuple[int, ...]`` silently
excludes every domain of grades, symbols or lattice elements, and the exclusion looks like a type
annotation rather than like a decision. QUANTITATIVE is a declared capability precisely so its
ABSENCE is expressible.

Second, ``Invariant.check`` returns three outcomes rather than two. An invariant nothing here can
evaluate is not false and is not true — reporting it as either is the failure this design refuses,
and ``unexecutable_invariants`` is what turns that gap into a countable population.
"""

from __future__ import annotations

import pytest

from engine.omega_governance.reference.capability import (
    ENCODABLE,
    ORDERABLE,
    QUANTITATIVE,
    Capability,
    CapabilitySet,
)
from engine.omega_governance.reference.domain import (
    MINIMUM_DOMAINS,
    TIME_DOMAIN,
    DomainError,
    DomainRegistry,
    Field,
    Invariant,
    Provenance,
    ReferenceDomain,
    Schema,
    Value,
    assert_encodable,
    default_domains,
)
from engine.omega_governance.reference.encoding import (
    CanonicalJsonCodec,
    Encoding,
    EncodingError,
    PolynomialIdentity,
    Sha256Identity,
    default_encoding,
)


def test_the_fourteen_minimum_domains_are_registered() -> None:
    registry = default_domains()
    assert len(registry) == len(MINIMUM_DOMAINS) == 14
    assert "TIME" in registry
    assert "TEMPERATURE" in registry


def test_no_domain_is_privileged_over_any_other() -> None:
    """TIME and TEMPERATURE are registrations of the same kind. The architecture's central claim is
    that it has no root domain, and a root would show up here as a domain with a different shape."""
    registry = default_domains()
    time, temperature = registry.resolve("TIME"), registry.resolve("TEMPERATURE")
    assert type(time) is type(temperature) is ReferenceDomain
    assert time.authority and temperature.authority


def test_a_field_and_a_schema_must_be_named() -> None:
    with pytest.raises(DomainError):
        Field("  ", "OPAQUE_STRING")
    with pytest.raises(DomainError):
        Schema("   ")


def test_a_schema_reports_findings_as_sentences_and_never_raises() -> None:
    schema = Schema(
        "test-shape",
        (
            Field("required_one", "OPAQUE_STRING"),
            Field("optional_one", "OPAQUE_STRING", required=False),
        ),
    )
    assert schema.validate({"required_one": "present"}) == ()
    findings = schema.validate({})
    assert findings and all(isinstance(finding, str) for finding in findings)


def test_an_open_schema_admits_an_undeclared_field_and_a_closed_one_refuses_it() -> None:
    """Openness is the default because a governance vocabulary that rejected unknown fields could
    not receive a record written by a later version of itself."""
    fields = (Field("declared", "OPAQUE_STRING"),)
    assert Schema("open-shape", fields).validate({"declared": "x", "extra": 1}) == ()
    closed = Schema("closed-shape", fields, closed=True).validate({"declared": "x", "extra": 1})
    assert any("extra" in finding for finding in closed)


def test_an_invariant_reports_not_checkable_rather_than_false() -> None:
    """The three-valued outcome IS the deliverable. ``None`` is not a failure and not a pass."""
    executable = Invariant("I-1", "Components are non-empty.", lambda value: bool(value.components))
    declared_only = Invariant("I-2", "The position matches an external ephemeris.")

    assert executable.executable
    assert not declared_only.executable
    assert executable.check(Value(domain="TIME", components=(1,))) is True
    assert executable.check(Value(domain="TIME")) is False
    assert declared_only.check(Value(domain="TIME", components=(1,))) is None


def test_the_unexecutable_invariants_are_a_countable_population_not_an_absence() -> None:
    registry = default_domains()
    unexecutable = registry.unexecutable_invariants()
    assert ("TIME", "Ω∞-D-T-02") in unexecutable


def test_a_value_carries_opaque_components_so_measurement_need_not_be_numeric() -> None:
    """A grade domain. If this raised, ``tuple[int, ...]`` would still be the real contract."""
    grades = Value(domain="ASSESSMENT", components=("MERIT", "DISTINCTION"))
    assert grades.components == ("MERIT", "DISTINCTION")
    assert grades.as_record()["domain"] == "ASSESSMENT"


def test_a_domain_can_lack_quantitative_and_still_be_orderable() -> None:
    """The separation that makes non-numeric measurement expressible."""
    lattice = ReferenceDomain(
        name="LATTICE",
        authority="TEST-AUTHORITY",
        schema=Schema("lattice-value"),
        capabilities=CapabilitySet.of(ORDERABLE, ENCODABLE),
    )
    assert lattice.supports(ORDERABLE)
    assert not lattice.supports(QUANTITATIVE)


def test_domains_are_resolved_by_capability_never_by_name() -> None:
    registry = default_domains()
    assert registry.capable(QUANTITATIVE) == ("SPACE", "TEMPERATURE", "UNITS", "VELOCITY")
    assert "TIME" in registry.capable(ORDERABLE)
    assert "TIME" not in registry.capable(QUANTITATIVE)


def test_an_unknown_domain_name_is_refused_rather_than_created() -> None:
    with pytest.raises(DomainError):
        default_domains().resolve("PHLOGISTON")


def test_a_domain_can_be_declared_from_primitives_with_no_edit_to_any_module() -> None:
    """Rule 3, over the domain vocabulary itself. A fifteenth domain is a registration."""
    registry = default_domains()
    registry.declare_domain(
        "MORALE",
        "TEST-AUTHORITY",
        Schema("morale-value", (Field("reading", "GRADE"),)),
        description="An ordinal reading with no magnitude.",
        capabilities=CapabilitySet.of(ORDERABLE),
    )
    assert len(registry) == 15
    assert "MORALE" in registry.capable(ORDERABLE)


def test_redeclaring_a_domain_with_a_different_meaning_is_refused() -> None:
    registry = default_domains()
    with pytest.raises(DomainError):
        registry.declare(
            ReferenceDomain(name="TIME", authority="A-RIVAL-AUTHORITY", schema=Schema("rival-time"))
        )


def test_a_registry_refuses_to_hold_a_domain_nobody_answers_for() -> None:
    with pytest.raises(DomainError):
        ReferenceDomain(name="ORPHAN", authority="   ", schema=Schema("orphan-value"))


def test_assert_authority_total_passes_over_the_shipped_registry() -> None:
    default_domains().assert_authority_total()


def test_a_value_is_validated_against_its_own_declared_domain() -> None:
    registry = default_domains()
    incomplete = Value(domain="TIME", components=(1,), attributes={"frame": "EARTH"})
    findings = registry.validate(incomplete)
    assert any("clock" in finding for finding in findings)


def test_a_complete_time_value_produces_only_the_not_checkable_finding() -> None:
    registry = default_domains()
    complete = Value(
        domain="TIME",
        components=(1,),
        attributes={
            "clock": "logical",
            "frame": "LOGICAL",
            "ordering": "TOTAL",
            "scale": "LOGICAL_TICK",
        },
    )
    findings = registry.validate(complete)
    assert all(
        "NOT EXECUTABLE HERE" in finding or "not executable" in finding for finding in findings
    )


def test_a_value_fingerprint_is_under_a_named_encoding_and_differs_between_encodings() -> None:
    value = Value(domain="TIME", components=(1, 2))
    left = Encoding(CanonicalJsonCodec(), Sha256Identity())
    right = Encoding(CanonicalJsonCodec(), PolynomialIdentity())
    assert value.fingerprint(left) != value.fingerprint(right)
    assert value.fingerprint(left) == value.fingerprint(left)


def test_assert_encodable_refuses_a_value_this_codec_cannot_represent() -> None:
    encoding = default_encoding()
    assert_encodable(Value(domain="TIME", components=(1, 2)), encoding)
    with pytest.raises((DomainError, EncodingError)):
        assert_encodable(Value(domain="TIME", components=(object(),)), encoding)


def test_provenance_records_where_a_registration_came_from() -> None:
    provenance = Provenance(declared_by="the suite", rule="TEST-R-01", notes="seeded by a fixture")
    record = provenance.as_record()
    assert record["declared_by"] == "the suite"
    assert record["rule"] == "TEST-R-01"


def test_provenance_must_name_a_declarer_and_a_rule() -> None:
    with pytest.raises(DomainError):
        Provenance(declared_by="   ", rule="TEST-R-01")
    with pytest.raises(DomainError):
        Provenance(declared_by="the suite", rule="  ")


def test_the_registry_report_describes_the_whole_vocabulary() -> None:
    report = default_domains().report()
    assert len(report["domains"]) == 14
    assert {entry["domain"] for entry in report["domains"]} == {
        domain.name for domain in default_domains().known()
    }


def test_an_empty_registry_knows_nothing_and_says_so() -> None:
    empty = DomainRegistry()
    assert len(empty) == 0
    assert empty.known() == ()
    assert empty.capable(Capability("ANYTHING", "x")) == ()


def test_the_time_domain_declares_the_capabilities_the_temporal_package_relies_on() -> None:
    assert TIME_DOMAIN.supports(ORDERABLE)
    assert TIME_DOMAIN.supports(ENCODABLE)
    assert not TIME_DOMAIN.supports(
        QUANTITATIVE
    ), "TIME must not claim magnitude: a Lamport counter has order and no duration"
