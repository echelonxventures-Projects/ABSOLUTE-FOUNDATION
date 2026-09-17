"""Tests for the constitutional compliance report and mandatory architectural proof."""

from __future__ import annotations

import json
from pathlib import Path

from engine.kernel import compliance
from engine.kernel.compliance import (
    PROHIBITED_TOKENS,
    UNKNOWN_CATEGORIES,
    architectural_proof,
    constitutional_report,
    kernel_source_fingerprint,
    quality_gates,
)
from engine.kernel.seed import FOUNDING_METATYPES


def test_architectural_proof_represents_all_unknown_categories():
    proof = architectural_proof()
    assert proof["passed"] is True
    assert proof["categories_proven"] == len(UNKNOWN_CATEGORIES)
    assert proof["kernel_unchanged"] is True
    assert proof["kernel_source_fingerprint_before"] == proof["kernel_source_fingerprint_after"]
    for record in proof["records"]:
        assert record["ok"] is True
        assert record["discoverable"] is True
        assert record["traceable"] is True


def test_quality_gates_all_pass():
    gates = quality_gates()
    assert gates["passed"] is True
    ids = {g["id"] for g in gates["gates"]}
    assert ids == {
        "no-closed-registries",
        "no-finite-enumeration",
        "no-hardcoded-assumptions",
        "no-domain-provider-technology-earth-civilization-coupling",
        "no-implementation-leakage",
        "unknown-future-compatibility",
    }
    for gate in gates["gates"]:
        assert gate["passed"] is True, gate


def test_constitutional_report_is_compliant_and_deterministic():
    a = constitutional_report()
    b = constitutional_report()
    assert a["passed"] is True
    assert a["verdict"] == "CONSTITUTIONALLY-COMPLIANT"
    assert a["report_hash"] == b["report_hash"]


def test_kernel_source_fingerprint_is_stable():
    assert kernel_source_fingerprint() == kernel_source_fingerprint()


# ------------------------------------------------ the negative mandates, bound to evidence
#
# Thirty-seven of the 1,449 mandates in `00-MASTER/CAEM-001/06-MANDATE-CORPUS.json` assert
# an ABSENCE -- "No fixed planets", "New domains require no redesign". CAEM-001 dispositions
# every one of them ASSERT, for a stated reason: corpus search cannot decide a negative.
# Finding the token proves nothing and not finding it proves nothing either.
#
# What CAN decide them is an executed instrument, and this module already runs one. The
# tests above prove the MECHANISM works; none of them names a MANDATE, so nothing tied the
# two together. These do.
#
# SCOPE, STATED ONCE AND HONESTLY. `engine/kernel/compliance.py` measures `engine/kernel/**`.
# It proves the kernel seeds no prohibited category and can represent every one of them by
# registration. It does NOT prove the property for the whole repository, and CAEM-001's
# own hard-coded-assumption register says so ("scoped to engine/kernel/** only"). A binding
# below is therefore evidence FOR a mandate at kernel scope, never a discharge of it.

#: Mandates answered by a token the kernel refuses to seed as a concrete category.
BOUND_TO_PROHIBITED_TOKEN = {
    "LYR-NEG/LN-01": "industry",  # No fixed domains
    "LYR-NEG/LN-02": "company",  # No fixed entities
    "LYR-NEG/LN-04": "earth",  # No fixed planets
    "LYR-NEG/LN-05": "industry",  # No fixed industries
    "LYR-NEG/LN-08": "framework",  # No fixed technical stacks
    "UAKP-IND/ID-03": "protocol",  # No technology-specific assumptions
    "UAKP-IND/ID-07": "database",  # No storage assumptions
    "UAKP-IND/ID-08": "cloud",  # No infrastructure assumptions
    "UAKP-PRIN/PN-20": "framework",  # No hard-coded technology assumptions
    "UAKP-PRIN/PN-22": "database",  # No hard-coded storage assumptions
}

#: Mandates answered by a category the kernel represents by registration, unchanged.
BOUND_TO_UNKNOWN_CATEGORY = {
    "LYR-NEG/LN-07": "ValueExchangeSystem",  # No fixed business models
    "PRD-SC/SC-02": "CapabilityDomain",  # New domains
    "PRD-SC/SC-03": "CapabilityDomain",  # New realities (scope: cross-universe)
    "PRD-SC/SC-04": "ValueExchangeSystem",  # New business models
    "PRD-SC/SC-05": "ProviderCategory",  # New technologies
    "PRD-SC/SC-06": "GovernanceModel",  # New governance models
    "PRD-SC/SC-08": "Civilization",  # New existence domains
    "UAKP-IND/ID-09": "ExecutionModelUnknown",  # No execution assumptions
}

#: Mandates answered by a named quality gate.
BOUND_TO_GATE = {
    "PRD-P/P-001": "no-closed-registries",  # No Terminal Ontology
    "PRD-P/P-002": "no-finite-enumeration",  # No Terminal Taxonomy
    "PRD-P/P-003": "unknown-future-compatibility",  # No Terminal Architecture
    "PRD-SC/SC-01": "unknown-future-compatibility",  # New constructs
    "PRD-SC/SC-09": "unknown-future-compatibility",  # Architecture evolves
    "PRD-SC/SC-10": "no-domain-provider-technology-earth-civilization-coupling",
    "UAKP-PRIN/PN-32": "no-implementation-leakage",  # Zero architectural specialization
}

#: Mandates NO instrument in this repository answers. Named, with the reason, because a
#: negative mandate quietly left out of a conformance suite reads exactly like one that
#: passed. Several are corroborated by CAEM-001 output 03, which already found the same
#: axes uncovered by both prior certifications.
UNCOVERED = {
    "LYR-NEG/LN-03": "no instrument enumerates architectural LAYERS, so their openness is "
    "unmeasured; nothing here refuses a fixed layer set",
    "LYR-NEG/LN-06": "artifact TYPES are enumerated in the generated-artifact registry's "
    "exclusion classes, but no instrument proves that set is open",
    "PRD-SC/SC-07": "UNKNOWN_CATEGORIES carries no intelligence-model category; the eleven "
    "cover civilization, language, value, tax, audit, time, governance, "
    "science, provider, capability and execution",
    "UAKP-IND/ID-01": "the platform's independence FROM UCOS cannot be measured inside "
    "UCOS; it needs the separate repository the UAKP document mandates",
    "UAKP-IND/ID-02": "no instrument measures project-specific coupling",
    "UAKP-IND/ID-04": "no instrument measures repository-specific coupling",
    "UAKP-IND/ID-05": "PROHIBITED_TOKENS carries 'language' for HUMAN language; CAEM-001 "
    "output 03 records programming language as DOC-only, not a token, "
    "and realization is Python-only by declared choice",
    "UAKP-IND/ID-06": "no AI-model token and no AI-model category; nothing refuses one",
    "UAKP-PRIN/PN-18": "no instrument measures project-specific coupling; the same gap "
    "UAKP-IND/ID-02 records, stated as a principle rather than as an "
    "independence claim",
    "UAKP-PRIN/PN-19": "no instrument measures repository-specific coupling; the same "
    "gap UAKP-IND/ID-04 records, stated as a principle",
    "UAKP-PRIN/PN-21": "no AI-model token and no AI-model category; the same gap "
    "UAKP-IND/ID-06 records, stated as a principle",
    "UAKP-PRIN/PN-23": "no instrument measures workflow coupling",
}


def _assert_mandates() -> dict[str, str]:
    """The ASSERT mandates, read from CAEM-001's corpus rather than copied beside it.

    Reading the register is what makes this a ratchet: add a negative mandate to the corpus
    and the totality test below fails until somebody either binds it to an instrument or
    writes down why nothing answers it.
    """
    repo = Path(__file__).resolve().parents[3]
    corpus = json.loads(
        (repo / "00-MASTER" / "CAEM-001" / "06-MANDATE-CORPUS.json").read_text(encoding="utf-8")
    )
    disposition = json.loads(
        (repo / "00-MASTER" / "CAEM-001" / "07-MANDATE-DISPOSITION.json").read_text(
            encoding="utf-8"
        )
    )
    asserted = {
        m
        for concept in disposition["concepts"].values()
        if concept["disposition"] == "ASSERT"
        for m in concept["mandates"]
    }
    return {a["atom_id"]: a["label"] for a in corpus["atoms"] if a["atom_id"] in asserted}


def test_every_negative_mandate_is_bound_or_declared_uncovered() -> None:
    """TOTALITY. No negative mandate may be silently absent from this suite."""
    mandates = _assert_mandates()
    accounted = (
        set(BOUND_TO_PROHIBITED_TOKEN)
        | set(BOUND_TO_UNKNOWN_CATEGORY)
        | set(BOUND_TO_GATE)
        | set(UNCOVERED)
    )
    assert set(mandates) == accounted, (
        "negative mandates neither bound to an instrument nor declared uncovered: "
        f"{sorted(set(mandates) - accounted)}; "
        f"accounted-for identifiers that are not ASSERT mandates: "
        f"{sorted(accounted - set(mandates))}"
    )
    # Disjoint: a mandate cannot be both answered and unanswered.
    bound = set(BOUND_TO_PROHIBITED_TOKEN) | set(BOUND_TO_UNKNOWN_CATEGORY) | set(BOUND_TO_GATE)
    assert not (bound & set(UNCOVERED)), sorted(bound & set(UNCOVERED))


def test_each_token_bound_mandate_names_a_category_the_kernel_refuses_to_seed() -> None:
    founding = {key.lower() for key, _name, _description in FOUNDING_METATYPES}
    for mandate, token in BOUND_TO_PROHIBITED_TOKEN.items():
        assert token in PROHIBITED_TOKENS, f"{mandate}: {token!r} is not a prohibited token"
        assert token not in founding, (
            f"{mandate}: {token!r} is seeded as a founding meta-type, so the kernel does "
            "hard-code the very category this mandate forbids"
        )


def test_each_category_bound_mandate_names_a_category_proven_by_registration() -> None:
    proof = architectural_proof()
    proven = {record["category"] for record in proof["records"] if record["ok"]}
    for mandate, category in BOUND_TO_UNKNOWN_CATEGORY.items():
        assert category in proven, (
            f"{mandate}: {category!r} is not among the categories the architectural proof "
            f"represents; proven={sorted(proven)}"
        )
    assert proof["kernel_unchanged"] is True, (
        "categories were represented but the kernel source changed, so 'requires no "
        "redesign' is false for every mandate bound above"
    )


def test_each_gate_bound_mandate_names_a_gate_that_passes() -> None:
    gates = {gate["id"]: gate for gate in quality_gates()["gates"]}
    for mandate, gate_id in BOUND_TO_GATE.items():
        assert gate_id in gates, f"{mandate}: no gate named {gate_id!r}"
        assert gates[gate_id]["passed"] is True, f"{mandate}: gate {gate_id!r} fails"


def test_the_uncovered_mandates_are_genuinely_uncovered() -> None:
    """NON-VACUITY. Without this, UNCOVERED is a place to hide anything inconvenient.

    Each entry claims nothing answers the mandate. The three specific claims that can be
    checked mechanically are checked here, so the list cannot quietly grow to cover a
    mandate an instrument does answer.
    """
    assert "intelligencemodel" not in {
        key.lower() for key, _instance, _attributes in UNKNOWN_CATEGORIES
    }, "PRD-SC/SC-07 is listed uncovered but an intelligence-model category now exists"

    assert not any(
        "ai" == token for token in PROHIBITED_TOKENS
    ), "UAKP-IND/ID-06 is listed uncovered but an AI token is now prohibited"

    assert "layer" not in PROHIBITED_TOKENS and "layer" not in {
        key.lower() for key, _instance, _attributes in UNKNOWN_CATEGORIES
    }, "LYR-NEG/LN-03 is listed uncovered but a layer instrument now exists"

    for mandate, reason in UNCOVERED.items():
        assert reason and len(reason) > 30, f"{mandate}: uncovered without a stated reason"


def test_the_binding_is_kernel_scoped_and_the_suite_says_so() -> None:
    """The scope limit is load-bearing, so it is asserted rather than left in a comment.

    Every gate above runs a `MetaKernel`, which seeds from `engine.kernel.seed`. A reader
    who takes these bindings as repository-wide proof would be wrong, and CAEM-001 output
    03 records exactly that scope limit for this instrument.
    """
    assert Path(compliance.__file__).resolve().parent.name == "kernel"
    assert compliance._KERNEL_DIR.name == "kernel"  # noqa: SLF001 - the scope under test
