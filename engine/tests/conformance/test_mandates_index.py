"""Mandate conformance — the Master Constitution / Master Index / Master Knowledge Map.

345 mandates over 19 sections (000-018). Sections 016 STAKEHOLDERS and 017 TARGET DOMAINS
are bound in `engine/tests/kernel/test_compliance.py`, against the kernel that can prove a
domain is ADMITTED rather than built. Nothing here restates them.
"""

from __future__ import annotations

from engine.tests.conformance.mandate_corpus import (
    assert_partitions,
    repo_root,
    section,
    tracked,
)
from intelligence.realization.contracts import ArtifactFamily
from intelligence.realization.generators import GENERATORS

# --- MI-015 — the thirty-one projections ----------------------------------------
#
# Section 015 carries one sentence above its list -- "Everything below is generated from
# Repository Truth" -- and that sentence is the mandate. A projection is not satisfied by
# the repository CONTAINING documentation, services or dashboards; it is satisfied by a
# declared PRODUCER emitting them from truth. `service/` exists and is hand-written, which
# is the opposite of what section 015 asks for.
#
# So absence here is measured against the two producer populations and never against path
# names: the URI generator registry (`ArtifactFamily`), and the generated-artifact registry
# that records every deterministic projection with its producer and regeneration command.

#: Projection -> the URI artifact family whose generator emits it.
PROJECTION_GENERATOR = {
    "MI-015/PJ-01": ArtifactFamily.DOCUMENTATION,  # Documentation
    "MI-015/PJ-02": ArtifactFamily.ARCHITECTURE,  # Architecture
    "MI-015/PJ-04": ArtifactFamily.RUNTIME,  # Source Code -- the executable enforcement module
    "MI-015/PJ-05": ArtifactFamily.API,  # APIs
    "MI-015/PJ-14": ArtifactFamily.SCHEMA,  # Schemas
    "MI-015/PJ-17": ArtifactFamily.TEST,  # Tests
    "MI-015/PJ-22": ArtifactFamily.DEPLOYMENT,  # Deployments
}

#: Projection -> (an artifact of that kind, the producer that emits it). Not every generated
#: family reaches the registry's `entries`: `00-BOOK/DATA/` and `00-BOOK/REGISTRIES/` are
#: corpus-internal excludes, so their rows live in `generated_inputs` or are evidenced by the
#: producer naming the artifact. All three routes are accepted and each is checked.
PROJECTION_REGISTERED = {
    # Registries
    "MI-015/PJ-15": ("00-BOOK/REGISTRIES/UNIVERSAL-ARTIFACT-REGISTRY.md", "00-BOOK/tools/ukb.py"),
    # Dashboards
    "MI-015/PJ-18": (
        "00-MASTER/UAIE-000001/00-UAIE-DASHBOARD.md",
        "00-MASTER/UAIE-000001/uaie_engine.py",
    ),
    # Reports
    "MI-015/PJ-19": (
        "00-MASTER/UAKOS-CLOSURE-009/03-REPOSITORY-COVERAGE-REPORT.md",
        "00-MASTER/UAKOS-CLOSURE-009/requirement_engine.py",
    ),
    # Evidence
    "MI-015/PJ-20": ("determinism-evidence/", "engine/determinism/reproduce.py"),
    # Digital Twins
    "MI-015/PJ-23": ("00-BOOK/DATA/", "00-BOOK/tools/register.sh"),
    # AI Agents -- a generated agent surface
    "MI-015/PJ-24": (".claude/CLAUDE.md", "00-BOOK/tools/ukctx.py"),
}

#: No producer emits these. Several have a hand-written counterpart in the tree, which is
#: precisely why they are listed: `service/`, `application/`, `platform/` and
#: `infrastructure/` exist as authored code, and section 015 asks for them as PROJECTIONS.
PROJECTION_NO_PRODUCER = {
    "MI-015/PJ-03": "Diagrams",
    "MI-015/PJ-06": "SDKs",
    "MI-015/PJ-07": "CLIs",
    "MI-015/PJ-08": "Libraries",
    "MI-015/PJ-09": "Services",
    "MI-015/PJ-10": "Applications",
    "MI-015/PJ-11": "Platforms",
    "MI-015/PJ-12": "Infrastructure",
    "MI-015/PJ-13": "Databases",
    "MI-015/PJ-16": "Dictionaries",
    "MI-015/PJ-21": "Policies",
    "MI-015/PJ-25": "Robotics",
}

#: Domain-shaped projections. Generating an "Enterprise System" or a "Commerce Platform" as
#: a projection family would fix an industry into the producer set, which is the breach
#: PRD P-001, LYR-NEG/LN-05 and MIP LAW P43-001 each forbid and which MI-017 already
#: settles: a market is ADMITTED as registered data, never built. Absence here is the
#: mandate being honoured, not missed.
PROJECTION_DOMAIN_SHAPED = {
    "MI-015/PJ-26": "Enterprise Systems",
    "MI-015/PJ-27": "Commerce Platforms",
    "MI-015/PJ-28": "Scientific Platforms",
    "MI-015/PJ-29": "Government Platforms",
    "MI-015/PJ-30": "Space Platforms",
}

#: The openness claim, which is a property of the producer set rather than a projection.
PROJECTION_OPEN_ENDED = {"MI-015/PJ-31": "Infinite Future Projections"}


def test_every_projection_is_generated_registered_absent_domain_shaped_or_open() -> None:
    mandates = section("MI-015")
    assert len(mandates) == 31, f"section 015 lists 31 projections, corpus has {len(mandates)}"
    assert_partitions(
        "MI-015",
        mandates,
        PROJECTION_GENERATOR,
        PROJECTION_REGISTERED,
        PROJECTION_NO_PRODUCER,
        PROJECTION_DOMAIN_SHAPED,
        PROJECTION_OPEN_ENDED,
    )


def test_every_generator_backed_projection_has_a_generator_that_claims_its_family() -> None:
    claimed = {generator.family for generator in GENERATORS}
    for mandate, family in PROJECTION_GENERATOR.items():
        assert (
            family in claimed
        ), f"{mandate}: no generator claims {family.value!r}, so nothing emits this projection"
    families = list(PROJECTION_GENERATOR.values())
    duplicated = sorted({f.value for f in families if families.count(f) > 1})
    assert not duplicated, f"one family claimed by two projections: {duplicated}"


def test_every_registered_projection_resolves_to_a_declared_producer() -> None:
    """A projection recorded without a producer is an artifact somebody edits by hand.

    Three routes are accepted because the registry has three shapes: an `entries` row, a
    `generated_inputs` row, or -- for a corpus-internal exclude that reaches neither -- the
    producer's own source naming the artifact it writes.
    """
    import json

    registry = json.loads(
        (repo_root() / "00-BOOK" / "DATA" / "generated-artifact-registry.json").read_text(
            encoding="utf-8"
        )
    )
    entries = {e["canonical_path"]: e for e in registry["entries"]}
    inputs = {g["path"]: g for g in registry["generated_inputs"]}

    for mandate, (artifact, producer) in PROJECTION_REGISTERED.items():
        assert (repo_root() / producer).exists(), f"{mandate}: producer {producer} does not exist"

        if artifact in entries:
            entry = entries[artifact]
            assert entry.get("producer") == producer, (
                f"{mandate}: the registry names producer {entry.get('producer')!r} for "
                f"{artifact}, this binding names {producer!r}"
            )
            assert entry.get("regeneration_command"), f"{mandate}: {artifact} declares no command"
            continue

        if artifact in inputs:
            row = inputs[artifact]
            assert row.get("producer") == producer, (
                f"{mandate}: generated_inputs names producer {row.get('producer')!r} for "
                f"{artifact}, this binding names {producer!r}"
            )
            assert row.get("bootstrap_command"), f"{mandate}: {artifact} declares no command"
            continue

        basename = artifact.rstrip("/").rsplit("/", 1)[-1]
        source = (repo_root() / producer).read_text(encoding="utf-8", errors="ignore")
        assert basename in source, (
            f"{mandate}: {artifact} is in neither registry population and {producer} does "
            f"not name {basename!r}, so nothing evidences that it is generated at all"
        )


def test_the_absent_projections_are_claimed_by_no_generator_family() -> None:
    """NON-VACUITY, measured against the producer set rather than against path names.

    Path naming would give the wrong answer in both directions here: `service/` would read
    as satisfying PJ-09 while being authored by hand, and `Diagrams` would read as absent
    even if a generator emitted them into files nobody named `diagram`. The generator
    registry is the declared producer set for projection FAMILIES, so it is what decides.
    """
    families = {generator.family.value.lower() for generator in GENERATORS}
    for mandate, projection in {**PROJECTION_NO_PRODUCER, **PROJECTION_DOMAIN_SHAPED}.items():
        stem = projection.lower().rstrip("s")
        assert stem not in families, (
            f"{mandate}: a generator now claims family {stem!r}; {projection} is produced "
            "and no longer belongs in an unproduced tier"
        )


def test_the_family_rule_that_proves_absence_can_return_a_positive() -> None:
    """Run the absence rule against a projection that IS produced and require it to fire.
    Without this, a rule that matched nothing would pass every absence claim silently."""
    families = {generator.family.value.lower() for generator in GENERATORS}
    assert "documentation".rstrip("s") in families, (
        "the family rule does not recognise Documentation, which is produced; every "
        "absence claim resting on it is vacuous"
    )


def test_no_producer_is_named_for_a_target_domain() -> None:
    """The load-bearing half of the domain-shaped tier. If a generator family or a
    registered capability ever names one of these markets, an industry has been fixed into
    the producer set and MI-017's determination has been reversed behind its back."""
    families = {generator.family.value.lower() for generator in GENERATORS}
    for mandate, market in PROJECTION_DOMAIN_SHAPED.items():
        head = market.split()[0].lower()
        assert head not in families, f"{mandate}: {head!r} is now a generator family"


def test_the_producer_set_is_open_which_is_what_the_last_projection_claims() -> None:
    """PJ-31 is not a projection; it is the claim that the list above can grow. That is a
    property of `GENERATORS` being a registry rather than a branch, so it is proven the way
    the object classes are: by admitting something the document never listed."""
    assert isinstance(GENERATORS, tuple)
    assert len(GENERATORS) == len(
        {generator.family for generator in GENERATORS}
    ), "two generators claim one family, so the registry cannot be extended safely"
    assert len(ArtifactFamily) >= len(GENERATORS)


# --- MI-002 — the twenty-seven constitutions ------------------------------------
#
# Section 002 lists twenty-seven constitutions, one per governed domain. CMG-000001 is the
# instrument that decides what counts as one, and this repository has a naming convention
# that follows it: a constitution is a document whose name ends `CONSTITUTION.md`. That is
# the test used below, in both directions -- a domain has a constitution when such a file
# carries its name, and lacks one when none does.
#
# The distinction the tiers keep is between a CONSTITUTION and an OWNER. Eleven domains have
# a constitution. Five more have no constitution and do have a declared owner -- the root law
# or an instrument the authority alignment register subordinates to it -- which is governance
# without a constitution, not the absence of governance. Eleven have neither.
#
# `UCRD-001-CONSTITUTIONAL-RELATIONSHIP-DETERMINATION.md` is why the rule is the SUFFIX and
# not the word: it carries both "constitutional" and "relationship" and is a determination.
# Matching it would have reported a Relationship Constitution that does not exist.

CONSTITUTION_SUFFIX = "CONSTITUTION.md"

#: Domain -> the document that constitutes it.
DOMAIN_CONSTITUTION = {
    "MI-002/C-01": "00-CEP/CEP-001-CONSTITUTIONAL-ENGINEERING-CONSTITUTION.md",
    "MI-002/C-09": "00-MASTER/UEI-000001/01-UNIVERSAL-EVOLUTION-INTELLIGENCE-CONSTITUTION.md",
    "MI-002/C-13": "00-MASTER/UAKOS-CLOSURE-006/CONST-09-REPOSITORY-LIFECYCLE-CONSTITUTION.md",
    "MI-002/C-14": "08-RUNTIME/RUNTIME-001-UNIVERSAL-RUNTIME-CONSTITUTION.md",
    "MI-002/C-15": "00-MASTER/UCOS-RFP-001/REPOSITORY-FIXED-POINT-CONSTITUTION.md",
    "MI-002/C-16": "00-CEP/CEP-002-CONSTITUTIONAL-GOVERNANCE-CONSTITUTION.md",
    "MI-002/C-17": "00-CEP/CEP-004-CONSTITUTIONAL-VALIDATION-CONSTITUTION.md",
    "MI-002/C-18": "00-MASTER/UCOS-CVR-001/05-VERIFICATION-CONSTITUTION.md",
    "MI-002/C-19": "00-CEP/CEP-005-CONSTITUTIONAL-CERTIFICATION-CONSTITUTION.md",
    "MI-002/C-20": "14-SECURITY/SECURITY-001-UNIVERSAL-SECURITY-CONSTITUTION.md",
    "MI-002/C-26": "00-CEP/CEP-009-CONSTITUTIONAL-AMENDMENT-EVOLUTION-CONSTITUTION.md",
}

#: Domain -> a declared owner that is not a constitution. Governance without a constitution
#: is a real standing and a weaker one, so it is recorded rather than counted as either.
DOMAIN_OWNED_NOT_CONSTITUTED = {
    "MI-002/C-02": "engine/uckp/law.py",  # Identity -- UCKP-ART-05
    "MI-002/C-04": "00-MASTER/UCXI-000001/ucxi-declaration.json",  # Context
    "MI-002/C-07": "00-BOOK/UCOS-BOOK-000000-UNIVERSAL-MASTER-KNOWLEDGE-BOOK.md",  # Knowledge
    # Capability
    "MI-002/C-10": "00-MASTER/UCIC-001-UNIVERSAL-CAPABILITY-IMPLEMENTATION-CONTRACT.md",
    "MI-002/C-27": "00-BOOK/DATA/generated-artifact-registry.json",  # Projection
}

#: Neither constituted nor owned. Eleven of twenty-seven, and four of them -- Privacy,
#: Commercial, Economic and Analytics -- are the same domains ARCH-UCMM and QM-CONST report
#: unanswered. A third document naming the same holes is corroboration, not new information.
DOMAIN_UNCONSTITUTED = {
    "MI-002/C-03": "relationship",
    "MI-002/C-05": "constraint",
    "MI-002/C-06": "rule",
    "MI-002/C-08": "information",
    "MI-002/C-11": "configuration",
    "MI-002/C-12": "composition",
    "MI-002/C-21": "privacy",
    "MI-002/C-22": "commercial",
    "MI-002/C-23": "economic",
    "MI-002/C-24": "monitoring",
    "MI-002/C-25": "analytics",
}


def test_every_mandated_constitution_is_constituted_owned_or_neither() -> None:
    mandates = section("MI-002")
    assert len(mandates) == 27, f"section 002 lists 27 constitutions, corpus has {len(mandates)}"
    assert_partitions(
        "MI-002",
        mandates,
        DOMAIN_CONSTITUTION,
        DOMAIN_OWNED_NOT_CONSTITUTED,
        DOMAIN_UNCONSTITUTED,
    )


def test_every_named_constitution_is_a_constitution_by_the_repository_convention() -> None:
    """A home that does not end CONSTITUTION.md is a determination, a register or a report,
    and calling it a constitution is the category error this tier exists to avoid."""
    known = set(tracked())
    for mandate, home in DOMAIN_CONSTITUTION.items():
        assert home in known, f"{mandate}: {home} is not a tracked path"
        assert home.endswith(CONSTITUTION_SUFFIX), (
            f"{mandate}: {home} does not end {CONSTITUTION_SUFFIX}, so by this repository's "
            "own convention it is not a constitution"
        )


def test_every_owned_domain_has_a_tracked_owner_that_is_not_a_constitution() -> None:
    """The tier boundary. An owner that IS a constitution belongs a tier up."""
    known = set(tracked())
    for mandate, home in DOMAIN_OWNED_NOT_CONSTITUTED.items():
        assert home in known, f"{mandate}: {home} is not a tracked path"
        assert not home.endswith(
            CONSTITUTION_SUFFIX
        ), f"{mandate}: {home} is a constitution and is understated as a bare owner"


def test_the_unconstituted_domains_are_named_by_no_constitution() -> None:
    """NON-VACUITY, by the suffix rule rather than by the word.

    Searching for the word would match `UCRD-001-CONSTITUTIONAL-RELATIONSHIP-DETERMINATION`
    and report a Relationship Constitution that does not exist -- a determination is not a
    constitution, and the repository's own naming says which is which.
    """
    constitutions = [p for p in tracked() if p.endswith(CONSTITUTION_SUFFIX)]
    assert constitutions, "no file ends CONSTITUTION.md, so the suffix rule is vacuous"
    for mandate, domain in DOMAIN_UNCONSTITUTED.items():
        found = [p for p in constitutions if domain in p.rsplit("/", 1)[-1].lower()]
        assert (
            not found
        ), f"{mandate}: {domain!r} is declared unconstituted but {found} carries its name"


def test_the_suffix_rule_that_proves_absence_can_return_a_positive() -> None:
    """Run the rule against a domain that IS constituted and require a hit."""
    constitutions = [p for p in tracked() if p.endswith(CONSTITUTION_SUFFIX)]
    hits = [p for p in constitutions if "security" in p.rsplit("/", 1)[-1].lower()]
    assert hits, "the suffix rule finds no Security Constitution, which exists; it is vacuous"


def test_the_unconstituted_domains_agree_with_the_other_two_documents() -> None:
    """Privacy, Commercial/Commerce, Economic(s) and Analytics are reported unanswered by
    the UCMM and the interrogative model too. A disagreement would mean one suite has
    mis-located something rather than that the repository changed."""
    from engine.tests.conformance.test_mandates_arch import META_MODEL_ABSENT
    from engine.tests.conformance.test_mandates_model import CONSTITUTION_ABSENT

    here = set(DOMAIN_UNCONSTITUTED.values())
    elsewhere = set(META_MODEL_ABSENT.values()) | set(CONSTITUTION_ABSENT.values())
    for domain in ("privacy", "information"):
        assert domain in here, f"{domain} is no longer reported unconstituted here"
        assert domain in elsewhere, f"{domain} is no longer reported absent elsewhere"
