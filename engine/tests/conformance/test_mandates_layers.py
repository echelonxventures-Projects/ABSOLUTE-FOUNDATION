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
from engine.uckp.facets import Facet

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


# --- LYR-L4C — the thirteen commerce capabilities -------------------------------
#
# Layer 4 opens "Everything is a capability. No fixed application modules." and then gives
# Commerce as a WORKED EXAMPLE of composition -- thirteen capabilities that compose into a
# marketplace. The example is the mandate: not that the substrate ship a Cart, but that
# thirteen capabilities of this shape compose without the substrate knowing what commerce is.
#
# Three of the thirteen settle it. `product`, `tax` and `customer` are among the eighteen
# tokens the kernel REFUSES to seed as concrete categories. A Product Capability built into
# the substrate is the fixed-industry breach P-001 and LYR-NEG/LN-05 forbid -- and all three
# compose as registered capabilities anyway, which is the distinction the layer is making.

COMMERCE_CAPABILITY_PREFIX = "Capability-"


def _capability_key(label: str) -> str:
    words = label.removesuffix(" Capability").split()
    return COMMERCE_CAPABILITY_PREFIX + "".join(word.capitalize() for word in words)


def test_the_commerce_example_is_thirteen_capabilities() -> None:
    mandates = section("LYR-L4C")
    assert len(mandates) == 13, f"the example lists 13 capabilities, corpus has {len(mandates)}"
    assert all(
        label.endswith(" Capability") for label in mandates.values()
    ), f"a row is not a capability: {sorted(mandates.values())}"


def test_every_commerce_capability_composes_with_the_kernel_unchanged() -> None:
    """The mandate as written. Composition, not construction: the kernel's source
    fingerprint is required to be identical after all thirteen are registered."""
    from engine.kernel.compliance import kernel_source_fingerprint
    from engine.provider.framework import ProviderFramework

    labels = list(section("LYR-L4C").values())
    framework = ProviderFramework()
    before = kernel_source_fingerprint()

    for label in labels:
        framework.register_category(
            _capability_key(label), name=label, description=f"composed capability: {label}"
        )

    assert kernel_source_fingerprint() == before, (
        "composing the commerce capabilities changed the kernel's source, so they were built "
        "as application modules -- which is what 'No fixed application modules' forbids"
    )
    registered = set(framework.category_keys())
    refused = sorted(label for label in labels if _capability_key(label) not in registered)
    assert not refused, f"capabilities the framework would not admit: {refused}"


def test_three_of_them_name_tokens_the_kernel_refuses_to_seed() -> None:
    """The sharp end, and the reason the example is Commerce rather than something neutral.

    Product, Tax and Customer are exactly the concrete categories a commerce platform would
    hard-code. The kernel refuses all three by name and composes all three as capabilities,
    which is the whole difference between a substrate and an eCommerce platform.
    """
    from engine.kernel.compliance import PROHIBITED_TOKENS
    from engine.kernel.seed import FOUNDING_METATYPES

    labels = {label.removesuffix(" Capability").lower() for label in section("LYR-L4C").values()}
    refused = sorted(labels & set(PROHIBITED_TOKENS))
    assert refused == ["customer", "product", "tax"], (
        f"the prohibited overlap changed: {refused}; the example no longer demonstrates what "
        "it was chosen to demonstrate"
    )
    # The intersection with the founding meta-types is NAMED rather than forbidden, for the
    # same reason it is named for the object classes: `Evolution` is a universal engineering
    # abstraction that happens to appear in a commerce list, and seeding it is not a
    # commerce assumption. What would be a breach is the kernel seeding a capability it
    # could only have got from this example -- Cart, Listing, Checkout.
    founding = {key.lower() for key, _n, _d in FOUNDING_METATYPES}
    shared = sorted(labels & founding)
    assert shared == ["evolution"], (
        f"the kernel now seeds commerce capabilities beyond the universal abstraction "
        f"Evolution: {shared}"
    )
    assert labels - founding, "every commerce capability is seeded, so nothing is composed"


def test_composition_is_open_beyond_the_thirteen_that_were_listed() -> None:
    """An example that admits only its own members is not an example of composition."""
    from engine.provider.framework import ProviderFramework

    framework = ProviderFramework()
    for label in section("LYR-L4C").values():
        framework.register_category(_capability_key(label), name=label, description="composed")
    unlisted = "Capability-NoDocumentHasNamedThisOne"
    framework.register_category(unlisted, name="unlisted", description="admitted")
    assert unlisted in framework.category_keys()


# --- LYR-L8 — the Universal Runtime ---------------------------------------------
#
# Five claims about WHAT the runtime carries -- any application, domain, capability,
# environment, infrastructure -- and seven about what it UNDERSTANDS: identity, context,
# relationships, policies, events, state, evolution. The two halves are different kinds of
# claim and are kept apart: the first is openness, the second is a facet the runtime can
# read.
#
# All seven understandings are Article 6 facets, which is the strongest possible answer --
# the runtime does not need to be taught them, because every object carries them.

RUNTIME_OPENNESS = {
    "LYR-L8/RT-01": "Any Application",
    "LYR-L8/RT-02": "Any Domain",
    "LYR-L8/RT-03": "Any Capability",
    "LYR-L8/RT-04": "Any Environment",
    "LYR-L8/RT-05": "Any Infrastructure",
}

RUNTIME_UNDERSTANDING = {
    "LYR-L8/RT-06": Facet.IDENTITY,
    "LYR-L8/RT-07": Facet.CONTEXT,
    "LYR-L8/RT-08": Facet.RELATIONSHIPS,
    "LYR-L8/RT-09": Facet.POLICIES,
    "LYR-L8/RT-10": Facet.TEMPORAL_HISTORY,
    "LYR-L8/RT-11": Facet.LIFECYCLE,
    "LYR-L8/RT-12": Facet.EVOLUTION_HISTORY,
}


def test_the_runtime_layer_is_five_opennesses_and_seven_understandings() -> None:
    mandates = section("LYR-L8")
    assert len(mandates) == 12, f"layer 8 states 12 claims, corpus has {len(mandates)}"
    assert_partitions("LYR-L8", mandates, RUNTIME_OPENNESS, RUNTIME_UNDERSTANDING)


def test_every_runtime_understanding_is_a_facet_the_object_carries() -> None:
    """The runtime does not need teaching: every object carries these by Article 6."""
    import dataclasses

    from engine.uckp.facets import REQUIRED_FACETS
    from engine.uckp.ucko import UniversalConstitutionalKnowledgeObject as UCKO

    fields = {f.name for f in dataclasses.fields(UCKO)}
    for mandate, facet in RUNTIME_UNDERSTANDING.items():
        assert facet in REQUIRED_FACETS, f"{mandate}: {facet} is not required"
        assert (
            facet.attribute in fields
        ), f"{mandate}: no UCKO field carries {facet.value!r}, so the runtime cannot read it"
    facets = list(RUNTIME_UNDERSTANDING.values())
    assert len(facets) == len(set(facets)), "one facet claimed by two runtime understandings"


def test_the_runtime_openness_is_the_admission_property_already_proven() -> None:
    """The five `Any X` claims are the same openness the kernel proof establishes, so they
    are bound to it rather than re-proven -- a second proof of one property would be a second
    authoring of it."""
    from engine.kernel.compliance import architectural_proof

    proof = architectural_proof()
    assert proof["kernel_unchanged"] is True
    proven = {record["category"] for record in proof["records"] if record["ok"]}
    assert {
        "CapabilityDomain",
        "ProviderCategory",
        "ExecutionModelUnknown",
    } <= proven, "the categories the runtime's openness rests on are no longer represented"
    assert len(RUNTIME_OPENNESS) == 5


# --- LYR-L1 — the thirteen kinds of existence -----------------------------------
#
# "Represent anything that exists. Not only Earth. Not only humans. Not only physical
# reality." Thirteen kinds follow, and the layer's worked example is Earth beside Mars under
# the caption "Same architecture. Different configuration."
#
# That caption is the mandate and the kernel already enforces it: `earth` is one of the
# eighteen tokens the kernel refuses to seed, while `planet` is not. A Planet KIND is
# representable; the planet Earth is not a category the substrate may hold. Ten of the
# thirteen have a located home, two are representable and deliberately unbuilt, and the
# thirteenth is the openness claim.

EXISTENCE_HOME = {
    "LYR-L1/EX-01": "engine/uckp/facets.py",  # Existence -- the existence-context facet
    "LYR-L1/EX-02": "engine/construct/reality.py",  # Reality
    "LYR-L1/EX-03": "engine/uckp/universe.py",  # Universe
    "LYR-L1/EX-06": "engine/execution_environment",  # Environment
    "LYR-L1/EX-07": "engine/context/location.py",  # Location
    "LYR-L1/EX-08": "engine/zero_class/entity_derivation.py",  # Entity
    "LYR-L1/EX-09": "engine/uckp/ucko.py",  # Object
    "LYR-L1/EX-10": "engine/uckp/values.py",  # Event -- TemporalEvent
    "LYR-L1/EX-11": "engine/graph/model.py",  # Relationship
    "LYR-L1/EX-12": "engine/uckp/state.py",  # State
}

#: Representable and deliberately unbuilt. A Galaxy class and a Planet class would be the
#: fixed-cosmology equivalent of a fixed industry, and the layer says so in its own caption.
EXISTENCE_REPRESENTABLE = {
    "LYR-L1/EX-04": "Galaxy",
    "LYR-L1/EX-05": "Planet",
}

EXISTENCE_OPENNESS = {"LYR-L1/EX-13": "Unknown Future Construct"}


def test_every_kind_of_existence_is_homed_representable_or_the_openness_claim() -> None:
    mandates = section("LYR-L1")
    assert len(mandates) == 13, f"layer 1 lists 13 kinds, corpus has {len(mandates)}"
    assert_partitions(
        "LYR-L1",
        mandates,
        EXISTENCE_HOME,
        EXISTENCE_REPRESENTABLE,
        EXISTENCE_OPENNESS,
    )


def test_every_homed_kind_is_tracked_and_distinct() -> None:
    assert_homes_exist("LYR-L1", EXISTENCE_HOME)
    homes = list(EXISTENCE_HOME.values())
    duplicated = sorted({h for h in homes if homes.count(h) > 1})
    assert not duplicated, f"one module claimed for several kinds of existence: {duplicated}"


def test_planet_is_representable_and_earth_is_refused() -> None:
    """The layer's own example, executed.

    "Not only Earth" is enforced by the kernel refusing `earth` as a seedable category,
    while `planet` is not refused -- so a Planet KIND registers and the planet Earth cannot
    become one. If `planet` is ever prohibited the kind becomes unrepresentable, and if
    `earth` is ever permitted the caption stops being true; both directions are asserted.
    """
    from engine.kernel.compliance import PROHIBITED_TOKENS, kernel_source_fingerprint
    from engine.kernel.kernel import MetaKernel

    assert (
        "earth" in PROHIBITED_TOKENS
    ), "`earth` is no longer refused; 'Not only Earth' is no longer enforced by anything"
    for kind in EXISTENCE_REPRESENTABLE.values():
        assert (
            kind.lower() not in PROHIBITED_TOKENS
        ), f"{kind!r} is now refused, so this kind of existence cannot be represented at all"

    kernel = MetaKernel()
    before = kernel_source_fingerprint()
    for kind in EXISTENCE_REPRESENTABLE.values():
        kernel.register_metatype(f"Existence-{kind}", name=kind, description=f"existence: {kind}")
    assert kernel_source_fingerprint() == before
    registered = {obj.natural_key for obj in kernel.metatypes()}
    assert {"Existence-Galaxy", "Existence-Planet"} <= registered


def test_the_representable_kinds_are_not_built_as_classes() -> None:
    """NON-VACUITY. Representable-and-unbuilt is only a finding if nothing builds them."""
    assert_named_by_nothing(
        "LYR-L1",
        {m: kind.lower() for m, kind in EXISTENCE_REPRESENTABLE.items()},
    )


def test_the_existence_set_is_open() -> None:
    """EX-13 is not a kind; it is the claim the list can grow."""
    from engine.kernel.compliance import kernel_source_fingerprint
    from engine.kernel.kernel import MetaKernel

    kernel = MetaKernel()
    before = kernel_source_fingerprint()
    unlisted = "Existence-KindNoDocumentHasNamedYet"
    kernel.register_metatype(unlisted, name="unlisted", description="admitted by registration")
    assert unlisted in {obj.natural_key for obj in kernel.metatypes()}
    assert kernel_source_fingerprint() == before
