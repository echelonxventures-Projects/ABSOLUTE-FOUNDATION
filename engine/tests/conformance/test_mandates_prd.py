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
