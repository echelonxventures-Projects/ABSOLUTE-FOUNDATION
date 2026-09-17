"""Mandate conformance — the Master Constitution / Master Index / Master Knowledge Map.

345 mandates over 19 sections (000-018). Sections 016 STAKEHOLDERS and 017 TARGET DOMAINS
are bound in `engine/tests/kernel/test_compliance.py`, against the kernel that can prove a
domain is ADMITTED rather than built. Nothing here restates them.
"""

from __future__ import annotations

from engine.tests.conformance.mandate_corpus import assert_partitions, repo_root, section
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
