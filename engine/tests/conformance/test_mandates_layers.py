"""Mandate conformance — the Self-Evolving Constitutional Substrate Architecture (Layers 0-15).

227 mandates over 23 sections. The document's eight forbidden hard-codings (LYR-NEG) are
bound in `engine/tests/kernel/test_compliance.py`, against the kernel that can decide a
negative by refusing to seed a token. Nothing here restates them.
"""

from __future__ import annotations

from engine.tests.conformance.mandate_corpus import (
    assert_homes_exist,
    assert_named_by_nothing,
    assert_partitions,
    repo_root,
    section,
)

# --- LYR-L12V / LYR-L12C — Layer 12, verification and certification --------------
#
# Layer 12 opens "No trust without proof" and then splits into two lists that are easy to
# read as one. They are not. VERIFICATION names six MEANS of establishing proof;
# CERTIFICATION names four STANDINGS an artifact can hold once proof exists. A means is an
# instrument that runs; a standing is a record something carries. Binding them into one tier
# would let six running instruments cover for four missing records, or the reverse.

#: Verification means -> the instrument that performs it.
VERIFICATION_MEANS = {
    "LYR-L12V/VF-01": "engine/certification/evidence.py",  # Evidence
    "LYR-L12V/VF-02": "engine/validation",  # Validation
    "LYR-L12V/VF-03": "verify.sh",  # Testing -- the repository-standard entry point
    "LYR-L12V/VF-04": "engine/determinism/reproduce.py",  # Replay
    "LYR-L12V/VF-05": "engine/omega_infinite/contradiction.py",  # Consistency
    "LYR-L12V/VF-06": "engine/certification_integrity",  # Integrity
}

#: Certification standing -> the record that carries it.
CERTIFICATION_STANDING = {
    "LYR-L12C/CF-01": "00-BOOK/DATA/certification.json",  # Certified State
    "LYR-L12C/CF-02": "00-BOOK/DATA/baseline-authority.json",  # Baseline
    "LYR-L12C/CF-03": "00-MASTER/RELEASE-001",  # Release
}

#: Evolution Approval is a standing nothing records. The repository HAS an evolution
#: constitution (CEP-009) and an evolution engine, and neither produces an approval an
#: artifact can carry: evolution here is measured and gated, never approved. That is a
#: coherent design and it is not what the mandate says, so it is recorded as absent.
CERTIFICATION_ABSENT = {
    "LYR-L12C/CF-04": "evolution approval",
}


def test_every_verification_means_has_an_instrument() -> None:
    mandates = section("LYR-L12V")
    assert len(mandates) == 6, f"layer 12 names 6 verification means, corpus has {len(mandates)}"
    assert_partitions("LYR-L12V", mandates, VERIFICATION_MEANS)
    assert_homes_exist("LYR-L12V", VERIFICATION_MEANS)


def test_every_verification_instrument_is_executable_rather_than_descriptive() -> None:
    """A means of proof that is a document proves nothing. Each home must be code or a
    runnable gate."""
    for mandate, home in VERIFICATION_MEANS.items():
        path = repo_root() / home
        if path.is_dir():
            assert any(path.rglob("*.py")), f"{mandate}: {home} carries no code"
        else:
            assert path.suffix in {
                ".py",
                ".sh",
            }, f"{mandate}: {home} is neither a module nor a script, so nothing runs it"


def test_the_six_means_are_six_distinct_instruments() -> None:
    """NON-VACUITY. Six means pointing at one instrument would mean five are unlocated."""
    homes = list(VERIFICATION_MEANS.values())
    duplicated = sorted({h for h in homes if homes.count(h) > 1})
    assert not duplicated, f"one instrument claimed for several means of proof: {duplicated}"


def test_every_certification_standing_is_recorded_or_declared_absent() -> None:
    mandates = section("LYR-L12C")
    assert len(mandates) == 4, f"layer 12 names 4 standings, corpus has {len(mandates)}"
    assert_partitions("LYR-L12C", mandates, CERTIFICATION_STANDING, CERTIFICATION_ABSENT)
    assert_homes_exist("LYR-L12C", CERTIFICATION_STANDING)


def test_a_standing_is_a_record_and_never_an_instrument() -> None:
    """The distinction the split rests on. A standing carried by a module would mean the
    repository can compute it on demand and never stores it, which is not a standing."""
    instruments = set(VERIFICATION_MEANS.values())
    overlap = instruments & set(CERTIFICATION_STANDING.values())
    assert not overlap, f"a verification instrument is also claimed as a standing: {overlap}"
    for mandate, home in CERTIFICATION_STANDING.items():
        path = repo_root() / home
        if not path.is_dir():
            assert path.suffix in {".json", ".md"}, (
                f"{mandate}: {home} is executable, so it computes a standing rather than "
                "recording one"
            )


def test_evolution_approval_is_recorded_by_nothing() -> None:
    """NON-VACUITY for the one absent standing, checked in both populations: no module is
    named for it, and the evolution instruments that exist do not emit an approval."""
    assert_named_by_nothing("LYR-L12C", CERTIFICATION_ABSENT)
    evolution = (repo_root() / "engine" / "constitution" / "evolution.py").read_text(
        encoding="utf-8"
    )
    assert "approval" not in evolution.lower(), (
        "the evolution engine now speaks of approval; LYR-L12C/CF-04 may be recorded after "
        "all and must be re-decided rather than left declared absent"
    )


def test_the_naming_rule_this_suite_relies_on_can_find_something() -> None:
    from engine.tests.conformance.mandate_corpus import assert_absence_rule_can_find_something

    assert_absence_rule_can_find_something("certification integrity")
