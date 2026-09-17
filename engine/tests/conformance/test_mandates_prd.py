"""Mandate conformance — the Product Requirements Document (Constitutional Foundation v1.0).

188 mandates over 18 sections. The PRD's negative principles and success criteria are bound
separately, in `engine/tests/kernel/test_compliance.py`, against the instrument that can
actually decide a negative: a running kernel whose source fingerprint is measured. Nothing
here re-states those; a second binding of the same claim is the duplication ART-03 voids.
"""

from __future__ import annotations

from engine.tests.conformance.mandate_corpus import (
    assert_absence_rule_can_find_something,
    assert_homes_exist,
    assert_partitions,
    section,
)

# --- PRD-ADM — the Universal Admission Framework --------------------------------
#
# Section 7 states nine things every new construct must support, and closes with the
# sentence that makes them testable rather than aspirational: "No manual platform redesign."
#
# Two different claims live in that section and this suite keeps them apart. The nine steps
# are CAPABILITIES -- each needs a located instrument. The closing sentence is a property of
# the platform as a whole, and it is already proven where it can be proven: the kernel
# admission tests measure a source fingerprint across an admission and require it unchanged.
# Restating that here would add a second authority for one claim without adding evidence.

#: Admission step -> the instrument that carries it.
ADMISSION_STEP_HOME = {
    "PRD-ADM/ADM-01": "engine/universal_discovery",  # Discovery
    "PRD-ADM/ADM-02": "engine/registry",  # Registration
    "PRD-ADM/ADM-03": "engine/knowledge/ukip/classification.py",  # Classification
    "PRD-ADM/ADM-04": "engine/validation",  # Validation
    "PRD-ADM/ADM-05": "engine/governance",  # Governance
    "PRD-ADM/ADM-06": "engine/uicm/observation.py",  # Observation
    "PRD-ADM/ADM-07": "engine/constitution/evolution.py",  # Evolution
    "PRD-ADM/ADM-08": "engine/certification",  # Certification
    "PRD-ADM/ADM-09": "intelligence/publication",  # Publication
}


def test_every_admission_step_has_a_located_instrument() -> None:
    mandates = section("PRD-ADM")
    assert len(mandates) == 9, f"section 7 states 9 admission steps, corpus has {len(mandates)}"
    assert_partitions("PRD-ADM", mandates, ADMISSION_STEP_HOME)
    assert_homes_exist("PRD-ADM", ADMISSION_STEP_HOME)


def test_every_admission_instrument_is_importable_code_not_a_specification() -> None:
    """An admission step whose home is prose is a described capability, not one a construct
    can pass through. Each home is required to carry Python that imports."""
    import importlib

    from engine.tests.conformance.mandate_corpus import repo_root

    for mandate, home in ADMISSION_STEP_HOME.items():
        path = repo_root() / home
        if path.is_dir():
            assert any(path.rglob("*.py")), f"{mandate}: {home} carries no code"
            module = home.replace("/", ".")
        else:
            assert path.suffix == ".py", f"{mandate}: {home} is not code"
            module = home[: -len(".py")].replace("/", ".")
        importlib.import_module(module)


def test_the_nine_steps_are_nine_distinct_instruments() -> None:
    """NON-VACUITY. Nine mandated capabilities all pointing at one module would mean eight
    of them are unlocated and the mapping is hiding it."""
    homes = list(ADMISSION_STEP_HOME.values())
    duplicated = sorted({h for h in homes if homes.count(h) > 1})
    assert not duplicated, f"one instrument claimed for several admission steps: {duplicated}"


def test_no_manual_platform_redesign_is_bound_elsewhere_and_not_restated_here() -> None:
    """The closing sentence of section 7 is a whole-platform property. It is decided by the
    kernel admission proof, which measures a source fingerprint across an admission -- the
    only instrument here that can decide it. This test asserts that binding still exists so
    the claim cannot go missing by being nobody's."""
    from engine.kernel.compliance import architectural_proof

    proof = architectural_proof()
    assert proof["kernel_unchanged"] is True, (
        "categories are represented but the kernel source changed, so 'no manual platform "
        "redesign' is false and every admission step above admits into a moving target"
    )


def test_the_naming_rule_this_suite_relies_on_can_find_something() -> None:
    assert_absence_rule_can_find_something("knowledge ukip classification")


# --- PRD-ECON — the Universal Economic Framework --------------------------------
#
# Section 13 has two halves and they mandate different things. Twelve FACULTIES -- "Every
# construct may support: Cost, Revenue, Billing, Settlement..." -- and nine TENURES,
# "Everything may be: Free, Paid, Owned, Shared, Leased, Licensed, Auctioned, Tokenized,
# Fractionalized." A faculty is machinery the substrate must have. A tenure is a state a
# thing may be held under, which is a vocabulary question and not a module question.
#
# Keeping them apart is what stops the section reading as twenty-one missing modules. It
# also isolates the real finding: of the twelve faculties, four are built and eight are
# not, and the eight are the ones money actually moves through -- Revenue, Billing,
# Settlement, Taxation. The substrate can price a thing and license it, and cannot charge
# for it.

#: Faculty -> the module that provides it.
ECONOMIC_FACULTY = {
    "PRD-ECON/ECON-01": "engine/verification_intelligence/cost_model.py",  # Cost
    "PRD-ECON/ECON-05": "platform/commercial_intelligence/pricing.py",  # Pricing
    "PRD-ECON/ECON-09": "engine/nucleus/ownership.py",  # Ownership
    "PRD-ECON/ECON-10": "platform/commercial_intelligence/licensing.py",  # Licensing
    "PRD-ECON/ECON-11": "platform/commercial_intelligence/marketplace.py",  # Marketplace
}

#: Faculty -> nothing. Seven of the twelve, and the settlement chain is all of it.
ECONOMIC_FACULTY_ABSENT = {
    "PRD-ECON/ECON-02": "revenue",
    "PRD-ECON/ECON-03": "billing",
    "PRD-ECON/ECON-04": "settlement",
    "PRD-ECON/ECON-06": "subscription",
    "PRD-ECON/ECON-07": "royalty",
    "PRD-ECON/ECON-08": "taxation",
    "PRD-ECON/ECON-12": "commerce",
}

#: The nine tenures. Not modules: a tenure is a state a thing is held under, and the
#: substrate's answer to "may everything be held this way" is its open vocabulary, the same
#: mechanism that answers the lifecycle. None of the nine is seeded, which is correct --
#: seeding `Auctioned` would fix a commercial model, and PRD principle P-001 forbids exactly
#: that. They are registrable, and that is the whole obligation.
ECONOMIC_TENURE = {
    "PRD-ECON/ECON-13": "Free",
    "PRD-ECON/ECON-14": "Paid",
    "PRD-ECON/ECON-15": "Owned",
    "PRD-ECON/ECON-16": "Shared",
    "PRD-ECON/ECON-17": "Leased",
    "PRD-ECON/ECON-18": "Licensed",
    "PRD-ECON/ECON-19": "Auctioned",
    "PRD-ECON/ECON-20": "Tokenized",
    "PRD-ECON/ECON-21": "Fractionalized",
}


def test_every_economic_mandate_is_a_faculty_or_a_tenure() -> None:
    mandates = section("PRD-ECON")
    assert (
        len(mandates) == 21
    ), f"section 13 states 21 economic mandates, corpus has {len(mandates)}"
    assert_partitions(
        "PRD-ECON",
        mandates,
        ECONOMIC_FACULTY,
        ECONOMIC_FACULTY_ABSENT,
        ECONOMIC_TENURE,
    )
    assert len(ECONOMIC_FACULTY) + len(ECONOMIC_FACULTY_ABSENT) == 12
    assert len(ECONOMIC_TENURE) == 9


def test_every_built_faculty_has_a_tracked_module() -> None:
    assert_homes_exist("PRD-ECON", ECONOMIC_FACULTY)


def test_the_absent_faculties_are_named_by_no_module() -> None:
    """NON-VACUITY. Cost and Ownership are why this is searched rather than assumed: both
    read as obvious gaps in a repository with no billing, and both exist."""
    from engine.tests.conformance.mandate_corpus import assert_named_by_nothing

    assert_named_by_nothing("PRD-ECON", ECONOMIC_FACULTY_ABSENT)


def test_the_settlement_chain_is_the_gap_rather_than_scattered_holes() -> None:
    """The finding, asserted so it cannot quietly stop being true. Revenue, Billing,
    Settlement and Taxation are the faculties money moves through, and none exists."""
    chain = {"revenue", "billing", "settlement", "taxation"}
    assert chain <= set(ECONOMIC_FACULTY_ABSENT.values()), (
        "part of the settlement chain now exists; the claim that this substrate can price "
        "a thing and cannot charge for it no longer holds"
    )


def test_no_tenure_is_seeded_as_a_commercial_model() -> None:
    """The tenures are answered by refusing to fix them.

    Seeding `Auctioned` or `Tokenized` as a built-in would be a fixed business model, which
    PRD principle P-001 forbids in its first line and LYR-NEG/LN-07 forbids again. So the
    obligation is that none is hard-coded and every one is registrable -- proven the same
    way the object classes and the lifecycle states are proven.
    """
    from engine.kernel.compliance import kernel_source_fingerprint
    from engine.kernel.kernel import MetaKernel
    from engine.kernel.seed import FOUNDING_METATYPES

    tenures = list(ECONOMIC_TENURE.values())
    founding = {key.lower() for key, _name, _description in FOUNDING_METATYPES}
    leaked = sorted(t for t in tenures if t.lower() in founding)
    assert not leaked, f"tenures seeded as founding meta-types, fixing a business model: {leaked}"

    kernel = MetaKernel()
    before = kernel_source_fingerprint()
    for tenure in tenures:
        kernel.register_metatype(f"Tenure-{tenure}", name=tenure, description=f"tenure: {tenure}")
    assert kernel_source_fingerprint() == before, (
        "admitting the tenures changed the kernel's source, so they were built as business "
        "models rather than registered"
    )
    registered = {obj.natural_key for obj in kernel.metatypes()}
    refused = sorted(t for t in tenures if f"Tenure-{t}" not in registered)
    assert not refused, f"tenures the kernel would not admit: {refused}"


def test_the_three_tenures_dispositioned_create_are_admissions_not_gaps() -> None:
    """Auctioned, Tokenized and Fractionalized are three of the seventeen CREATE concepts.
    Building them is what LN-07 forbids, so the disposition is answered by admission -- the
    same correction Monorepo and Polyrepo needed."""
    assert {"Auctioned", "Tokenized", "Fractionalized"} <= set(ECONOMIC_TENURE.values())


def test_royalty_stays_a_genuine_gap_because_it_is_a_faculty_not_a_tenure() -> None:
    """The fourth CREATE concept in this section does NOT get the same answer, and the
    difference is the point: a royalty is machinery that computes and pays, not a state a
    thing is held under. Admitting the word would prove nothing about the faculty."""
    assert "PRD-ECON/ECON-07" in ECONOMIC_FACULTY_ABSENT
    assert "royalty" not in {t.lower() for t in ECONOMIC_TENURE.values()}


# --- PRD-MD — Universal Multi-Dimensional Support -------------------------------
#
# Fourteen dimensions "without limits". None of them is a feature, and treating them as
# features is the breach: shipping Multi-Currency means the substrate knows what a currency
# IS, and `currency` is one of the eighteen tokens the kernel refuses to seed. The mandate
# is satisfied by NOT knowing -- by refusing the fixed category and representing the axis by
# registration instead.
#
# So each dimension is answered one of two ways, and both are already instruments in this
# repository: a PROHIBITED TOKEN the kernel will not seed as a concrete category, or an
# UNKNOWN CATEGORY the architectural proof represents with the kernel unchanged. Five are
# answered by neither, and those five are the finding.

#: Dimension -> the token the kernel refuses to seed, which is how the axis stays open.
DIMENSION_REFUSED_TOKEN = {
    "PRD-MD/MD-02": "company",  # Multi-Organization
    "PRD-MD/MD-03": "language",  # Multi-Language
    "PRD-MD/MD-05": "currency",  # Multi-Currency
    "PRD-MD/MD-06": "tax",  # Multi-Tax
    "PRD-MD/MD-08": "cloud",  # Multi-Cloud
}

#: Dimension -> the unknown category the architectural proof represents.
DIMENSION_UNKNOWN_CATEGORY = {
    "PRD-MD/MD-04": "Civilization",  # Multi-Culture
    "PRD-MD/MD-07": "GovernanceModel",  # Multi-Jurisdiction
    "PRD-MD/MD-10": "CapabilityDomain",  # Multi-Reality
    "PRD-MD/MD-12": "TemporalModel",  # Multi-Timeline
}

#: Neither refused nor represented. The substrate has no axis for these at all, which means
#: nothing stops one of them being hard-coded tomorrow -- the gap is the absence of a
#: refusal, not the absence of a feature.
DIMENSION_UNHELD = {
    "PRD-MD/MD-01": "Multi-Tenant",
    "PRD-MD/MD-09": "Multi-Edge",
    "PRD-MD/MD-11": "Multi-Existence",
    "PRD-MD/MD-13": "Multi-Universe",
    "PRD-MD/MD-14": "Multi-Dimension",
}


def test_every_dimension_is_refused_represented_or_unheld() -> None:
    mandates = section("PRD-MD")
    assert len(mandates) == 14, f"section 19 states 14 dimensions, corpus has {len(mandates)}"
    assert_partitions(
        "PRD-MD",
        mandates,
        DIMENSION_REFUSED_TOKEN,
        DIMENSION_UNKNOWN_CATEGORY,
        DIMENSION_UNHELD,
    )


def test_every_token_backed_dimension_names_a_token_the_kernel_refuses_to_seed() -> None:
    from engine.kernel.compliance import PROHIBITED_TOKENS
    from engine.kernel.seed import FOUNDING_METATYPES

    founding = {key.lower() for key, _n, _d in FOUNDING_METATYPES}
    for mandate, token in DIMENSION_REFUSED_TOKEN.items():
        assert token in PROHIBITED_TOKENS, (
            f"{mandate}: {token!r} is not a prohibited token, so nothing stops this "
            "dimension being fixed to one value"
        )
        assert token not in founding, f"{mandate}: {token!r} is seeded as a founding meta-type"


def test_every_category_backed_dimension_is_proven_with_the_kernel_unchanged() -> None:
    from engine.kernel.compliance import architectural_proof

    proof = architectural_proof()
    proven = {record["category"] for record in proof["records"] if record["ok"]}
    for mandate, category in DIMENSION_UNKNOWN_CATEGORY.items():
        assert (
            category in proven
        ), f"{mandate}: {category!r} is not among the represented categories {sorted(proven)}"
    assert proof["kernel_unchanged"] is True, (
        "the categories are represented but the kernel source changed, so 'without limits' "
        "is false for every dimension bound above"
    )


def test_the_two_mechanisms_are_not_the_same_claim_twice() -> None:
    """NON-VACUITY. A refused token keeps an axis open by forbidding a value; a represented
    category keeps it open by admitting one. A dimension answered by both would be
    double-counted, and one answered by neither would hide in the overlap."""
    assert not (set(DIMENSION_REFUSED_TOKEN) & set(DIMENSION_UNKNOWN_CATEGORY))
    tokens = set(DIMENSION_REFUSED_TOKEN.values())
    categories = {c.lower() for c in DIMENSION_UNKNOWN_CATEGORY.values()}
    assert not (tokens & categories)


def test_the_unheld_dimensions_are_refused_by_nothing_and_represented_by_nothing() -> None:
    """NON-VACUITY for the tier that matters most here.

    These five have no refusal, which is a different and quieter failure than a missing
    feature: nothing in the kernel would object if `tenant` or `edge` were seeded as a
    concrete category tomorrow, and the mandate would be silently broken.
    """
    from engine.kernel.compliance import PROHIBITED_TOKENS, UNKNOWN_CATEGORIES

    categories = {key.lower() for key, _i, _a in UNKNOWN_CATEGORIES}
    for mandate, dimension in DIMENSION_UNHELD.items():
        axis = dimension.removeprefix("Multi-").lower()
        assert (
            axis not in PROHIBITED_TOKENS
        ), f"{mandate}: {axis!r} is now a prohibited token and this dimension is held"
        assert not any(
            axis in category for category in categories
        ), f"{mandate}: {axis!r} is now represented by an unknown category"


# --- PRD-SELF — the fourteen self-* requirements --------------------------------
#
# "Platform must be: Self Discovering, Self Registering..." The prefix is the whole mandate.
# A repository that validates OTHER things is not self-validating, and an optimiser that
# improves the code it compiles is not self-optimising. So a row is admitted only when the
# instrument's SUBJECT is this repository, and the two that fail that test fail it for
# reasons worth naming rather than for want of a module.

#: Requirement -> the instrument whose subject is this repository.
SELF_INSTRUMENT = {
    "PRD-SELF/SELF-01": "engine/universal_discovery",  # Self Discovering
    "PRD-SELF/SELF-02": "00-BOOK/tools/register.sh",  # Self Registering
    "PRD-SELF/SELF-03": "00-BOOK/tools/config.py",  # Self Classifying -- CLASSIFY_RULES
    "PRD-SELF/SELF-04": "00-BOOK/tools/ukb.py",  # Self Documenting -- it writes its own book
    "PRD-SELF/SELF-05": "engine/constitution/gateway.py",  # Self Governing
    "PRD-SELF/SELF-06": "engine/validation",  # Self Validating
    "PRD-SELF/SELF-07": "verify.sh",  # Self Verifying
    # Self Certifying
    "PRD-SELF/SELF-08": "00-MASTER/P0-FINAL-CLOSURE-002/final_closure_engine.py",
    "PRD-SELF/SELF-09": "00-MASTER/UCOS-UGA-001/06-SELF-OBSERVATION.json",  # Self Monitoring
    "PRD-SELF/SELF-12": "00-MASTER/UCOS-AEE-001/aee_engine.py",  # Self Evolving
    "PRD-SELF/SELF-13": "intelligence/publication",  # Self Publishing
    "PRD-SELF/SELF-14": "00-BOOK/DATA/canonical-observation-audit.json",  # Self Auditing
}

#: Requirement -> (the nearest instrument, why it is NOT the self-* capability). Both of
#: these would pass a keyword sweep and neither does what the prefix demands.
SELF_NEAR_MISS = {
    "PRD-SELF/SELF-10": (
        "engine/runtime/execution/health.py",
        "health is DETECTED and nothing acts on the detection; detecting is not healing",
    ),
    "PRD-SELF/SELF-11": (
        "engine/compiler/optimization.py",
        "the compiler optimises the output it emits, not the platform that emits it",
    ),
}


def test_every_self_requirement_is_instrumented_or_a_near_miss() -> None:
    mandates = section("PRD-SELF")
    assert (
        len(mandates) == 14
    ), f"section 20 states 14 self-* requirements, corpus has {len(mandates)}"
    assert_partitions("PRD-SELF", mandates, SELF_INSTRUMENT, SELF_NEAR_MISS)


def test_every_self_instrument_is_tracked_and_distinct() -> None:
    """Twelve capabilities pointing at one instrument would mean eleven are unlocated."""
    assert_homes_exist("PRD-SELF", SELF_INSTRUMENT)
    homes = list(SELF_INSTRUMENT.values())
    duplicated = sorted({h for h in homes if homes.count(h) > 1})
    assert not duplicated, f"one instrument claimed for several self-* requirements: {duplicated}"


def test_the_self_classifying_and_self_documenting_claims_name_what_does_the_work() -> None:
    """NON-VACUITY for the two rows that rest on a file rather than a package. Both are
    large modules and the claim is about a specific thing inside each."""
    from engine.tests.conformance.mandate_corpus import repo_root

    config = (repo_root() / "00-BOOK" / "tools" / "config.py").read_text(encoding="utf-8")
    assert (
        "CLASSIFY_RULES" in config
    ), "PRD-SELF/SELF-03 rests on config.py carrying CLASSIFY_RULES; it does not"
    book = (repo_root() / "00-BOOK" / "tools" / "ukb.py").read_text(encoding="utf-8")
    assert (
        "UNIVERSAL-ARTIFACT-REGISTRY.md" in book
    ), "PRD-SELF/SELF-04 rests on ukb.py writing the repository's own registry; it does not"


def test_the_near_misses_are_near_and_are_misses() -> None:
    """NON-VACUITY in both directions, which is the point of the tier.

    The named instrument must exist -- otherwise the row is plain absence and the
    explanation is decoration. And nothing may be named for the self-* capability itself,
    or the near miss is a hit that was overlooked.
    """
    from engine.tests.conformance.mandate_corpus import assert_named_by_nothing

    assert_homes_exist("PRD-SELF", {m: home for m, (home, _why) in SELF_NEAR_MISS.items()})
    for mandate, (_home, why) in SELF_NEAR_MISS.items():
        assert len(why) > 40, f"{mandate}: tiered a near miss without a stated reason"
    assert_named_by_nothing(
        "PRD-SELF",
        {"PRD-SELF/SELF-10": "self healing", "PRD-SELF/SELF-11": "self optimizing"},
    )


def test_self_optimizing_stays_a_genuine_gap() -> None:
    """One of the ten remaining CREATE concepts, and it stays one: unlike the tenures and
    the environments, nothing in any document forbids a platform optimising itself."""
    assert "PRD-SELF/SELF-11" in SELF_NEAR_MISS


# --- PRD-DISC — the Universal Discovery Framework -------------------------------
#
# Section 10: "The platform shall automatically discover" twelve things. Six have an
# instrument. Six do not, and five of those six are the outward-looking ones -- risk,
# opportunity, pattern, anomaly and emergent behaviour. MI-005 mandates three of the same
# five from the Master Index, so the gap is measured twice and the two suites are asserted
# to agree.

CONSTRUCT_DISCOVERY_INSTRUMENT = {
    "PRD-DISC/DISC-01": "engine/universal_discovery",  # Construct Discovery
    "PRD-DISC/DISC-02": "engine/uckp/resolution.py",  # Relationship Discovery
    "PRD-DISC/DISC-03": "engine/uckp/capabilities.py",  # Capability Discovery
    "PRD-DISC/DISC-04": "engine/context/resolution.py",  # Context Discovery
    "PRD-DISC/DISC-05": "engine/knowledge/integration/dependency.py",  # Dependency Discovery
    "PRD-DISC/DISC-06": "engine/knowledge/ukip/discovery.py",  # Knowledge Discovery
    "PRD-DISC/DISC-07": "engine/kernel/governance.py",  # Policy Discovery
}

CONSTRUCT_DISCOVERY_ABSENT = {
    "PRD-DISC/DISC-08": "risk",
    "PRD-DISC/DISC-09": "opportunity",
    "PRD-DISC/DISC-10": "pattern",
    "PRD-DISC/DISC-11": "anomaly",
    "PRD-DISC/DISC-12": "emergent",
}


def test_every_mandated_discovery_is_instrumented_or_absent() -> None:
    mandates = section("PRD-DISC")
    assert len(mandates) == 12, f"section 10 lists 12 discoveries, corpus has {len(mandates)}"
    assert_partitions(
        "PRD-DISC",
        mandates,
        CONSTRUCT_DISCOVERY_INSTRUMENT,
        CONSTRUCT_DISCOVERY_ABSENT,
    )


def test_every_discovery_instrument_is_tracked_and_distinct() -> None:
    assert_homes_exist("PRD-DISC", CONSTRUCT_DISCOVERY_INSTRUMENT)
    homes = list(CONSTRUCT_DISCOVERY_INSTRUMENT.values())
    duplicated = sorted({h for h in homes if homes.count(h) > 1})
    assert not duplicated, f"one instrument claimed for several discoveries: {duplicated}"


def test_the_absent_discoveries_are_performed_by_nothing() -> None:
    from engine.tests.conformance.mandate_corpus import assert_named_by_nothing

    assert_named_by_nothing("PRD-DISC", CONSTRUCT_DISCOVERY_ABSENT)


def test_the_platform_discovers_what_is_and_not_what_might_be() -> None:
    """The finding, asserted so it cannot quietly stop being true. Every discovery the
    platform performs is of something already present in the corpus; every one it does not
    perform is a judgement about what is not there -- a risk, an opportunity, an
    alternative, a pattern, an anomaly, an emergent behaviour."""
    outward = {"risk", "opportunity", "pattern", "anomaly", "emergent"}
    assert outward <= set(CONSTRUCT_DISCOVERY_ABSENT.values()), (
        "an outward-looking discovery now exists; the claim that this platform discovers "
        "what is and not what might be no longer holds"
    )


# --- PRD-PUB — the Universal Publication Framework ------------------------------
#
# "Automatically generate" eleven kinds of document. `intelligence/publication` declares
# twenty-three built-in FORMATS across eleven genres, each with its required sections and a
# renderer, so ten of the eleven are answered by a declared genre.
#
# TWO OF THESE ARE ON THE CREATE LIST AND SHOULD NOT BE. CAEM-001 dispositions `Whitepapers`
# and `Research Papers` as genuine greenfield gaps -- the only disposition that authorises
# new construction -- because it searched the document's spelling. The repository writes
# them `White Paper` and `Research Paper`, two words each, and declares both as built-in
# formats with academic section sets. Building either would be a second authoring of a
# format that already exists, void under UCKP-ART-03.

#: Publication kind -> the genre that produces it.
PUBLICATION_GENRE = {
    "PRD-PUB/PUB-01": "technical-article",  # Technical Documents
    "PRD-PUB/PUB-03": "standards",  # Specifications
    "PRD-PUB/PUB-04": "standards",  # Standards -- the same genre; see the test below
    "PRD-PUB/PUB-05": "white-paper",  # Whitepapers
    "PRD-PUB/PUB-06": "paper",  # Research Papers
    "PRD-PUB/PUB-07": "journal",  # Journal Publications
    "PRD-PUB/PUB-08": "patent",  # Patent Applications
    "PRD-PUB/PUB-11": "technical-article",  # Training Materials -- the Tutorial format
}

#: Produced outside the publication engine.
PUBLICATION_ELSEWHERE = {
    "PRD-PUB/PUB-02": "intelligence/realization/generators/architecture.py",  # Architecture Docs
    # Knowledge Artifacts
    "PRD-PUB/PUB-10": "00-BOOK/UCOS-BOOK-000000-UNIVERSAL-MASTER-KNOWLEDGE-BOOK.md",
}

#: No genre and no producer. A regulatory submission has a recipient and a filing format,
#: and the engine models neither.
PUBLICATION_ABSENT = {"PRD-PUB/PUB-09": "regulatory"}


def test_every_publication_kind_is_a_genre_produced_elsewhere_or_absent() -> None:
    mandates = section("PRD-PUB")
    assert len(mandates) == 11, f"section 14 lists 11 publication kinds, corpus has {len(mandates)}"
    assert_partitions(
        "PRD-PUB",
        mandates,
        PUBLICATION_GENRE,
        PUBLICATION_ELSEWHERE,
        PUBLICATION_ABSENT,
    )


def test_every_named_genre_is_declared_with_a_renderer_and_required_sections() -> None:
    """A genre with no renderer generates nothing, and a format with no required sections
    would accept an empty document."""
    from intelligence.publication.formats import BUILT_IN_FORMATS

    by_genre: dict[str, list[dict]] = {}
    for fmt in BUILT_IN_FORMATS:
        by_genre.setdefault(fmt["genre"], []).append(fmt)

    for mandate, genre in PUBLICATION_GENRE.items():
        assert genre in by_genre, f"{mandate}: no built-in format declares genre {genre!r}"
        for fmt in by_genre[genre]:
            assert fmt.get("renderer"), f"{mandate}: format {fmt['label']!r} has no renderer"
            assert fmt.get("required"), f"{mandate}: format {fmt['label']!r} requires no sections"


def test_whitepapers_and_research_papers_are_declared_formats_not_gaps() -> None:
    """The correction this binding exists to make.

    Both are dispositioned CREATE by CAEM-001 -- new construction -- because the search used
    the document's one-word spelling. The repository writes them as two words and declares
    each as a built-in format. This test names the exact labels, so if either is ever
    removed the CREATE disposition becomes true again and this assertion fails.
    """
    from intelligence.publication.formats import BUILT_IN_FORMATS

    labels = {fmt["label"] for fmt in BUILT_IN_FORMATS}
    assert (
        "White Paper" in labels
    ), "no White Paper format is declared; PRD-PUB/PUB-05 is a genuine gap after all"
    assert (
        "Research Paper" in labels
    ), "no Research Paper format is declared; PRD-PUB/PUB-06 is a genuine gap after all"
    mandates = section("PRD-PUB")
    assert mandates["PRD-PUB/PUB-05"] == "Whitepapers"
    assert mandates["PRD-PUB/PUB-06"] == "Research Papers"


def test_specifications_and_standards_share_a_genre_and_that_is_stated() -> None:
    """NON-VACUITY for the one genre claimed twice. The standards genre carries two formats
    -- a Standards Proposal and an RFC-style Memo -- so two mandates resolving to it is two
    documents, not one answer counted twice."""
    from intelligence.publication.formats import BUILT_IN_FORMATS

    claimed = list(PUBLICATION_GENRE.values())
    doubled = sorted({g for g in claimed if claimed.count(g) > 1})
    assert doubled == ["standards", "technical-article"], f"unexpected doubling: {doubled}"
    for genre in doubled:
        formats = [f for f in BUILT_IN_FORMATS if f["genre"] == genre]
        assert (
            len(formats) >= 2
        ), f"genre {genre!r} answers two mandates and declares only {len(formats)} format"


def test_the_absent_publication_kind_has_no_genre_and_no_producer() -> None:
    from engine.tests.conformance.mandate_corpus import assert_named_by_nothing
    from intelligence.publication.formats import BUILT_IN_FORMATS

    genres = {fmt["genre"] for fmt in BUILT_IN_FORMATS}
    for mandate, kind in PUBLICATION_ABSENT.items():
        assert not any(kind in genre for genre in genres), f"{mandate}: a {kind!r} genre now exists"
    assert_named_by_nothing("PRD-PUB", PUBLICATION_ABSENT)


def test_every_elsewhere_producer_is_tracked() -> None:
    assert_homes_exist("PRD-PUB", PUBLICATION_ELSEWHERE)


# --- PRD-NFR — the eleven non-functional requirements ---------------------------
#
# Each of the eleven carries a one-line claim in the document, and the claim is what makes
# it checkable: Scalability is "no architectural upper limit", Reliability is "deterministic
# operation", Portability is "technology agnostic". A module named for the quality proves
# nothing; the instrument has to make the CLAIM.
#
# PORTABILITY IS ON THE CREATE LIST AND SHOULD NOT BE. It is dispositioned new construction
# because nothing is named `portability`. The claim is "technology agnostic", and
# `engine/conformance` is the agnosticism conformance harness -- UAC-000001, which measures
# whether a contract discriminates between implementations and whose own docstring says
# "Nothing below names a technology, a language, a database or an interpreter."

#: Quality -> (the instrument, the claim it makes).
NFR_INSTRUMENT = {
    "PRD-NFR/NFR-01": ("engine/infinite_scope", "no architectural upper limit"),
    "PRD-NFR/NFR-03": ("engine/determinism", "deterministic operation"),
    "PRD-NFR/NFR-04": ("14-SECURITY/SECURITY-001-UNIVERSAL-SECURITY-CONSTITUTION.md", "zero trust"),
    "PRD-NFR/NFR-05": ("engine/conformance", "technology agnostic"),
    "PRD-NFR/NFR-09": ("platform/observability", "full-stack observability"),
    "PRD-NFR/NFR-10": ("engine/governance", "full governance"),
    "PRD-NFR/NFR-11": ("00-BOOK/DATA/canonical-observation-audit.json", "full audit trail"),
}

#: Quality -> the quality gate that refuses its violation. Stronger than an instrument: a
#: gate fails the build rather than being available to call.
NFR_GATE = {
    "PRD-NFR/NFR-07": "unknown-future-compatibility",  # Evolvability -- no terminal architecture
    "PRD-NFR/NFR-08": "no-finite-enumeration",  # Extensibility -- infinite extensibility
}

#: Availability's claim is "autonomous failover" and nothing fails over; `resilience` records
#: that a unit survived, which is not the same as one taking over. Interoperability repeats
#: the gap ARCH-VALID/VL-21 records -- nothing validates it either.
NFR_ABSENT = {
    "PRD-NFR/NFR-02": "failover",
    "PRD-NFR/NFR-06": "interoperability",
}


def test_every_non_functional_requirement_is_instrumented_gated_or_absent() -> None:
    mandates = section("PRD-NFR")
    assert len(mandates) == 11, f"section 21 states 11 qualities, corpus has {len(mandates)}"
    assert_partitions("PRD-NFR", mandates, NFR_INSTRUMENT, NFR_GATE, NFR_ABSENT)


def test_every_instrumented_quality_has_a_tracked_home_and_a_stated_claim() -> None:
    assert_homes_exist("PRD-NFR", {m: home for m, (home, _c) in NFR_INSTRUMENT.items()})
    homes = [home for home, _c in NFR_INSTRUMENT.values()]
    duplicated = sorted({h for h in homes if homes.count(h) > 1})
    assert not duplicated, f"one instrument claimed for several qualities: {duplicated}"
    for mandate, (_home, claim) in NFR_INSTRUMENT.items():
        assert len(claim) > 8, f"{mandate}: no claim stated, so nothing distinguishes the row"


def test_portability_is_answered_by_the_agnosticism_harness_and_is_not_a_gap() -> None:
    """The correction this binding makes.

    Portability is dispositioned CREATE because nothing is named `portability`. Its claim is
    "technology agnostic", and UAC-000001 measures exactly that: it reads a declared axis
    register and asks whether each contract DISCRIMINATES between implementations, refusing
    to name a technology anywhere in the process. Building a portability module would be a
    second authoring of a harness that already exists.
    """
    from engine.conformance.measure import REGISTER_PATH, load_register
    from engine.tests.conformance.mandate_corpus import repo_root

    register = load_register(REGISTER_PATH)
    assert register, "the agnosticism axis register is empty; the harness measures nothing"
    home, claim = NFR_INSTRUMENT["PRD-NFR/NFR-05"]
    assert home == "engine/conformance" and claim == "technology agnostic"
    source = (repo_root() / "engine" / "conformance" / "measure.py").read_text(encoding="utf-8")
    assert "names a technology" in source, (
        "the harness no longer states that it names no technology; the portability claim it "
        "answers rests on that property"
    )


def test_every_gated_quality_names_a_gate_that_passes() -> None:
    """A gate is stronger than an instrument: it refuses rather than being available."""
    from engine.kernel.compliance import quality_gates

    gates = {gate["id"]: gate for gate in quality_gates()["gates"]}
    for mandate, gate_id in NFR_GATE.items():
        assert gate_id in gates, f"{mandate}: no gate named {gate_id!r}"
        assert gates[gate_id]["passed"] is True, f"{mandate}: gate {gate_id!r} fails"
    assert not (set(NFR_GATE) & set(NFR_INSTRUMENT)), "a quality is both gated and instrumented"


def test_availability_and_interoperability_are_answered_by_nothing() -> None:
    """NON-VACUITY, and the distinction Availability needs.

    `infrastructure/resilience.py` exists and records that a unit survived. The claim is
    "autonomous failover" -- one unit taking over from another -- and nothing does that. A
    keyword sweep would have called this satisfied.
    """
    from engine.tests.conformance.mandate_corpus import assert_named_by_nothing

    assert_named_by_nothing("PRD-NFR", NFR_ABSENT)
    from engine.tests.conformance.test_mandates_arch import VALIDATION_ABSENT

    assert "interoperability" in set(
        VALIDATION_ABSENT.values()
    ), "interoperability validation now exists; PRD-NFR/NFR-06 may be answered"
