"""UCOS-EPIC-014 — Commercial Intelligence contract tests (Terminal T5)."""

from __future__ import annotations

from platform.commercial_intelligence.contracts import (
    BASIS_POINTS_SCALE,
    COMMERCIAL_AUTHORITY,
    CommercialDashboard,
    CommercialDomain,
    CommercialIntelligenceReport,
    CommercialTarget,
    DomainKind,
    DomainReport,
    Finding,
    FindingStatus,
    Money,
    Severity,
    Verdict,
    domains_of_kind,
    failed,
    passed,
    sum_money,
)
from platform.commercial_intelligence.errors import CommercialTargetError, MoneyError

import pytest


def _report(*domain_reports: DomainReport) -> CommercialIntelligenceReport:
    return CommercialIntelligenceReport.create(
        target_id="T", target_digest="d", domain_reports=domain_reports
    )


def test_domain_order_matches_the_mandated_sequence():
    assert [d.value for d in CommercialDomain] == [
        "marketplace_intelligence",
        "licensing_intelligence",
        "product_intelligence",
        "portfolio_intelligence",
        "business_documentation",
        "commercial_packages",
        "pricing_intelligence",
        "investment_intelligence",
        "customer_intelligence",
        "policy_governance",
        "approval_intelligence",
        "business_evidence",
        "commercial_validation",
        "commercial_certification",
    ]
    assert CommercialDomain.MARKETPLACE_INTELLIGENCE.order == 0
    assert CommercialDomain.COMMERCIAL_CERTIFICATION.order == 13


def test_every_domain_is_classified_and_families_partition_the_domains():
    assert CommercialDomain.PRICING_INTELLIGENCE.kind is DomainKind.COMMERCE
    covered: list[CommercialDomain] = []
    for kind in DomainKind:
        covered.extend(domains_of_kind(kind))
    assert sorted(covered, key=lambda d: d.order) == sorted(CommercialDomain, key=lambda d: d.order)


def test_domain_parse_rejects_an_unknown_domain():
    with pytest.raises(CommercialTargetError):
        CommercialDomain.parse("not_a_domain")
    assert CommercialDomain.parse("policy_governance") is CommercialDomain.POLICY_GOVERNANCE


@pytest.mark.parametrize(
    "currency,minor",
    [("usd", 1), ("US", 1), ("USDD", 1), ("", 1), (None, 1)],
)
def test_money_requires_an_iso_shaped_currency(currency, minor):
    with pytest.raises(MoneyError):
        Money(currency, minor)


@pytest.mark.parametrize("minor", [1.5, "10", True, None])
def test_money_refuses_non_integer_minor_units(minor):
    with pytest.raises(MoneyError):
        Money("USD", minor)


def test_money_arithmetic_is_exact_integer_arithmetic():
    a = Money("USD", 1000)
    b = Money("USD", 250)
    assert a.add(b) == Money("USD", 1250)
    assert a.subtract(b) == Money("USD", 750)
    assert a.scale(3) == Money("USD", 3000)
    assert Money.zero("EUR") == Money("EUR", 0)
    assert Money.zero("EUR").is_zero
    assert Money("USD", -1).is_negative


def test_money_refuses_to_combine_currencies():
    with pytest.raises(MoneyError):
        Money("USD", 1).add(Money("EUR", 1))
    with pytest.raises(MoneyError):
        Money("USD", 1).subtract(Money("EUR", 1))
    with pytest.raises(MoneyError):
        Money("USD", 1).compare(Money("EUR", 1))


def test_money_scale_requires_an_integer_factor():
    with pytest.raises(MoneyError):
        Money("USD", 100).scale(1.5)
    with pytest.raises(MoneyError):
        Money("USD", 100).scale(True)


@pytest.mark.parametrize(
    "minor,bp,expected",
    [
        (1000, 1000, 100),  # 10%
        (1000, 0, 0),
        (1000, BASIS_POINTS_SCALE, 1000),  # 100%
        (333, 5000, 167),  # half-up on the magnitude (166.5 -> 167)
        (-333, 5000, -167),  # symmetric on the magnitude
    ],
)
def test_apply_basis_points_rounds_half_up_on_the_magnitude(minor, bp, expected):
    assert Money("USD", minor).apply_basis_points(bp) == Money("USD", expected)


def test_apply_basis_points_requires_integer_basis_points():
    with pytest.raises(MoneyError):
        Money("USD", 100).apply_basis_points(1.5)


def test_money_compare_is_a_total_order_within_one_currency():
    assert Money("USD", 1).compare(Money("USD", 2)) == -1
    assert Money("USD", 2).compare(Money("USD", 2)) == 0
    assert Money("USD", 3).compare(Money("USD", 2)) == 1


def test_money_from_mapping_and_serialization_round_trip():
    parsed = Money.from_mapping({"currency": "GBP", "minor_units": 42})
    assert parsed.to_dict() == {"currency": "GBP", "minor_units": 42}
    with pytest.raises(MoneyError):
        Money.from_mapping(["GBP", 42])


def test_sum_money_totals_in_one_currency_and_handles_the_empty_case():
    assert sum_money([], currency="USD") == Money("USD", 0)
    assert sum_money([Money("USD", 1), Money("USD", 2)], currency="USD") == Money("USD", 3)
    with pytest.raises(MoneyError):
        sum_money([Money("EUR", 1)], currency="USD")


def test_target_normalizes_facts_and_digests_deterministically():
    target = CommercialTarget.from_mapping(
        {"target_id": "T", "facts": {"pricing_intelligence": {"price_book": {}}}}
    )
    assert target.domain_facts(CommercialDomain.PRICING_INTELLIGENCE) == {"price_book": {}}
    assert target.domain_facts(CommercialDomain.POLICY_GOVERNANCE) == {}
    assert target.declared_domains() == (CommercialDomain.PRICING_INTELLIGENCE,)
    assert target.digest() == CommercialTarget.from_mapping(target.to_dict()).digest()


def test_declared_domains_are_returned_in_canonical_order():
    target = CommercialTarget.from_mapping(
        {
            "target_id": "T",
            "facts": {
                "commercial_certification": {"a": 1},
                "marketplace_intelligence": {"b": 2},
            },
        }
    )
    assert target.declared_domains() == (
        CommercialDomain.MARKETPLACE_INTELLIGENCE,
        CommercialDomain.COMMERCIAL_CERTIFICATION,
    )


@pytest.mark.parametrize(
    "raw",
    [
        [],
        {"facts": {}},
        {"target_id": ""},
        {"target_id": 7},
        {"target_id": "T", "facts": []},
        {"target_id": "T", "facts": {"unknown_domain": {}}},
        {"target_id": "T", "facts": {"policy_governance": []}},
    ],
)
def test_target_refuses_a_malformed_commercial_surface(raw):
    with pytest.raises(CommercialTargetError):
        CommercialTarget.from_mapping(raw)


def test_finding_helpers_classify_pass_blocking_and_advisory():
    ok = passed("C-1", CommercialDomain.PRICING_INTELLIGENCE, "fine", extra=1)
    block = failed("C-2", CommercialDomain.PRICING_INTELLIGENCE, "bad")
    advise = failed("C-3", CommercialDomain.PRICING_INTELLIGENCE, "meh", severity=Severity.ADVISORY)
    assert ok.passed and not ok.failed
    assert block.is_blocking_failure and not block.is_advisory_failure
    assert advise.is_advisory_failure and not advise.is_blocking_failure
    assert ok.to_dict()["details"] == {"extra": 1}
    assert "details" not in ok.core()
    assert ok.status is FindingStatus.PASS


def test_domain_report_fails_only_on_a_blocking_failure():
    domain = CommercialDomain.CUSTOMER_INTELLIGENCE
    advisory_only = DomainReport.create(
        domain, (failed("C-1", domain, "m", severity=Severity.ADVISORY),)
    )
    blocking = DomainReport.create(domain, (failed("C-2", domain, "m"),))
    assert advisory_only.verdict is Verdict.PASS
    assert advisory_only.advisory_failures() == ("C-1",)
    assert blocking.verdict is Verdict.FAIL
    assert blocking.blocking_failures() == ("C-2",)
    assert blocking.kind is DomainKind.COMMERCE
    assert advisory_only.counts() == {
        "total": 1,
        "passed": 0,
        "failed": 1,
        "blocking_failed": 0,
        "advisory_failed": 1,
    }
    assert advisory_only.to_dict()["passed"] is True


def test_report_aggregates_fail_closed_and_carries_authority_and_disclosure():
    good = DomainReport.create(
        CommercialDomain.MARKETPLACE_INTELLIGENCE,
        (passed("C-1", CommercialDomain.MARKETPLACE_INTELLIGENCE),),
    )
    bad = DomainReport.create(
        CommercialDomain.PRICING_INTELLIGENCE,
        (failed("C-2", CommercialDomain.PRICING_INTELLIGENCE, "m"),),
    )
    report = _report(good, bad)
    assert report.verdict is Verdict.FAIL
    assert not report.passed
    assert report.authority == COMMERCIAL_AUTHORITY
    assert report.disclosure["asserts_constitutional_finality"] is False
    assert report.domains_run() == ("marketplace_intelligence", "pricing_intelligence")
    assert report.blocking_failures() == ("C-2",)
    assert report.advisory_failures() == ()
    assert report.domain_verdicts() == {
        "marketplace_intelligence": "pass",
        "pricing_intelligence": "fail",
    }
    assert report.counts()["domains"] == 2
    assert report.report_for(CommercialDomain.PRICING_INTELLIGENCE) is bad
    assert report.report_for(CommercialDomain.BUSINESS_EVIDENCE) is None
    assert report.reports_of_kind(DomainKind.OFFER) == (good,)


def test_kind_verdicts_pass_when_a_family_has_no_run_domain():
    only_offer = DomainReport.create(
        CommercialDomain.MARKETPLACE_INTELLIGENCE,
        (failed("C-1", CommercialDomain.MARKETPLACE_INTELLIGENCE, "m"),),
    )
    verdicts = _report(only_offer).kind_verdicts()
    assert verdicts["offer"] == "fail"
    assert verdicts["commerce"] == "pass"
    assert verdicts["governance"] == "pass"
    assert verdicts["assurance"] == "pass"


def test_report_hash_ignores_volatile_detail_but_tracks_the_verdict():
    domain = CommercialDomain.BUSINESS_EVIDENCE
    plain = DomainReport.create(domain, (passed("C-1", domain, "same"),))
    detailed = DomainReport.create(
        domain,
        (
            Finding(
                check_id="C-1",
                domain=domain,
                severity=Severity.BLOCKING,
                status=FindingStatus.PASS,
                message="same",
                details={"volatile": "value"},
            ),
        ),
    )
    flipped = DomainReport.create(domain, (failed("C-1", domain, "same"),))
    assert _report(plain).report_sha256 == _report(detailed).report_sha256
    assert _report(plain).report_sha256 != _report(flipped).report_sha256


def test_dashboard_projects_the_report_deterministically():
    domain = CommercialDomain.APPROVAL_INTELLIGENCE
    report = _report(DomainReport.create(domain, (passed("C-1", domain),)))
    dashboard = report.dashboard()
    assert isinstance(dashboard, CommercialDashboard)
    assert dashboard.checks_total == 1
    assert dashboard.checks_passed == 1
    assert dashboard.checks_failed == 0
    assert dashboard.domains_total == 1
    assert dashboard.to_dict()["dashboard_sha256"] == dashboard.dashboard_sha256
    assert report.dashboard().dashboard_sha256 == dashboard.dashboard_sha256


def test_report_to_dict_is_complete_and_self_describing():
    domain = CommercialDomain.COMMERCIAL_VALIDATION
    payload = _report(DomainReport.create(domain, (passed("C-1", domain),))).to_dict()
    for key in (
        "report_format",
        "target_id",
        "verdict",
        "passed",
        "target_digest",
        "counts",
        "domain_verdicts",
        "kind_verdicts",
        "blocking_failures",
        "advisory_failures",
        "domains",
        "authority",
        "disclosure",
        "report_sha256",
    ):
        assert key in payload
