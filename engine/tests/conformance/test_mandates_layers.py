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


# --- LYR-L2 — the fourteen context dimensions -----------------------------------
#
# Layer 2 lists fourteen context dimensions and closes the list with "Future Context Types",
# which is the instruction rather than a fourteenth dimension. UCXI-000001 owns exactly this
# question and answers it the same way: the context taxonomy is "the open classification
# tree over context kinds", and its declaration says of the kinds it recognises today that
# they "are not a closed list, and no consumer branches on a particular kind."
#
# Twelve of the thirteen real dimensions are already `ContextKind` members, by name. One is
# not, and is admissible by the declared extension mechanism -- which is the same answer,
# arrived at by the mechanism instead of by the seed.

#: Dimension -> the ContextKind value that is it.
CONTEXT_KIND_SEEDED = {
    "LYR-L2/CX-01": "spatial",
    "LYR-L2/CX-02": "temporal",
    "LYR-L2/CX-04": "environmental",
    "LYR-L2/CX-05": "cultural",
    "LYR-L2/CX-06": "linguistic",
    "LYR-L2/CX-07": "economic",
    "LYR-L2/CX-08": "governance",
    "LYR-L2/CX-09": "regulatory",
    "LYR-L2/CX-10": "identity",
    "LYR-L2/CX-11": "security",
    "LYR-L2/CX-12": "knowledge",
    "LYR-L2/CX-13": "computational",
}

#: Recognised by no seeded kind, and admissible as data. Not a gap: the declaration's own
#: extension path, exercised.
CONTEXT_KIND_BY_EXTENSION = {"LYR-L2/CX-03": "physical"}

#: The openness claim itself, which is not a dimension.
CONTEXT_OPENNESS = {"LYR-L2/CX-14": "Future Context Types"}


def test_every_context_dimension_is_a_kind_extensible_or_the_openness_claim() -> None:
    mandates = section("LYR-L2")
    assert len(mandates) == 14, f"layer 2 lists 14 dimensions, corpus has {len(mandates)}"
    assert_partitions(
        "LYR-L2",
        mandates,
        CONTEXT_KIND_SEEDED,
        CONTEXT_KIND_BY_EXTENSION,
        CONTEXT_OPENNESS,
    )


def test_every_seeded_dimension_is_a_context_kind_under_its_own_name() -> None:
    from engine.context.taxonomy import ContextKind

    kinds = {kind.value for kind in ContextKind}
    mandates = section("LYR-L2")
    for mandate, value in CONTEXT_KIND_SEEDED.items():
        assert value in kinds, f"{mandate}: {value!r} is not a recognised context kind"
        assert (
            mandates[mandate].lower().startswith(value)
        ), f"{mandate}: {mandates[mandate]!r} was mapped to {value!r}, which is not its own name"
    claimed = list(CONTEXT_KIND_SEEDED.values())
    assert len(claimed) == len(set(claimed)), "one context kind claimed by two dimensions"


def test_the_extensible_dimension_is_genuinely_not_a_seeded_kind() -> None:
    """NON-VACUITY. If `physical` is ever seeded, this row belongs a tier up and the claim
    that the taxonomy had to be extended for it is false."""
    from engine.context.taxonomy import ContextKind

    kinds = {kind.value for kind in ContextKind}
    for mandate, value in CONTEXT_KIND_BY_EXTENSION.items():
        assert value not in kinds, (
            f"{mandate}: {value!r} is now a seeded context kind and is understated as an "
            "extension"
        )


def test_the_taxonomy_declares_itself_open_and_offers_the_extension_path() -> None:
    """CX-14 is the whole point of the section, so it is checked against the declaration
    that owns the question rather than against a module that happens to allow it."""
    import json

    from engine.context.taxonomy import UNIVERSAL_TAXONOMY

    declaration = json.loads(
        (repo_root() / "00-MASTER" / "UCXI-000001" / "ucxi-declaration.json").read_text(
            encoding="utf-8"
        )
    )
    openness = declaration["openness"]
    assert (
        openness["closed_set"] is False
    ), "UCXI now declares the context kinds a closed set; LYR-L2/CX-14 is unsatisfied"
    assert openness["upper_limit"] is None
    assert "extend" in openness["extension_mechanism"]
    assert hasattr(UNIVERSAL_TAXONOMY, "extend"), (
        "the declaration names ContextTaxonomy.extend as the extension mechanism and the "
        "taxonomy does not have it"
    )
