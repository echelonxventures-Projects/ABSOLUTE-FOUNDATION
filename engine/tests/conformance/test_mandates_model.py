"""Mandate conformance — the Absolute Universal Constitutional Model (interrogative).

163 mandates over 11 sections. The document is a set of questions every constitutional
object must be able to answer -- WHY, WHAT, WHO, WHERE, WHEN, HOW, WHICH, CAN -- followed by
the CONSTITUTION facets that answer them, the FLOW that produces them and the OUTPUTS.

That shape makes Article 6 the natural respondent: a facet IS "a question every
constitutional object must be able to answer about itself", and the facet enum already
declares the question each one answers. Where a mandated facet has no facet, the suite says
so rather than reaching for the nearest module that shares a word.
"""

from __future__ import annotations

from engine.tests.conformance.mandate_corpus import (
    assert_absence_rule_can_find_something,
    assert_homes_exist,
    assert_named_by_nothing,
    assert_partitions,
    section,
)
from engine.uckp.facets import REQUIRED_FACETS, Facet

# --- QM-CONST — the twenty-five constitutional facets ---------------------------

#: Mandated facet -> the universal facet that answers it.
CONSTITUTION_FACET = {
    "QM-CONST/CO-01": Facet.IDENTITY,  # Identity
    "QM-CONST/CO-02": Facet.SEMANTIC_IDENTITY,  # Meaning
    "QM-CONST/CO-04": Facet.CONTEXT,  # Context
    "QM-CONST/CO-05": Facet.RELATIONSHIPS,  # Relationships
    "QM-CONST/CO-06": Facet.CONSTRAINTS,  # Constraints
    "QM-CONST/CO-07": Facet.POLICIES,  # Rules -- "What rules govern its use?"
    "QM-CONST/CO-11": Facet.LIFECYCLE,  # States
    "QM-CONST/CO-12": Facet.TEMPORAL_HISTORY,  # Events
    "QM-CONST/CO-14": Facet.EVIDENCE,  # Evidence
    "QM-CONST/CO-15": Facet.KNOWLEDGE_CONTEXT,  # Knowledge
    "QM-CONST/CO-18": Facet.GOVERNANCE_CONTEXT,  # Governance
    "QM-CONST/CO-19": Facet.SECURITY_CONTEXT,  # Security
    "QM-CONST/CO-23": Facet.RUNTIME_BINDINGS,  # Runtime
    "QM-CONST/CO-24": Facet.EVOLUTION_HISTORY,  # Evolution
    "QM-CONST/CO-25": Facet.PROJECTION_BINDINGS,  # Projection
}

#: Answered by an instrument rather than by a facet. These are things the substrate HAS, not
#: questions an object answers about itself, and forcing them into the facet enum would be a
#: constitutional amendment -- every object in the universe suddenly owing a new answer.
CONSTITUTION_INSTRUMENT = {
    "QM-CONST/CO-08": "engine/uckp/law.py",  # Laws
    "QM-CONST/CO-09": "engine/uckp/capabilities.py",  # Capabilities
    "QM-CONST/CO-13": "platform/universal_measurement",  # Measurements
    "QM-CONST/CO-17": "engine/uckp/intelligence.py",  # Intelligence
    "QM-CONST/CO-22": "platform/commercial_intelligence",  # Commercialization
}

#: Neither a facet nor an instrument. Five of the twenty-five, and the list is worth reading
#: as a set: Purpose, Behaviors, Information, Privacy and Economics. The substrate can say
#: what a thing IS and who governs it, and cannot say what it is FOR, how it ACTS, or what
#: it costs.
CONSTITUTION_ABSENT = {
    "QM-CONST/CO-03": "purpose",
    "QM-CONST/CO-10": "behavior",
    "QM-CONST/CO-16": "information",
    "QM-CONST/CO-20": "privacy",
    "QM-CONST/CO-21": "economics",
}


def test_every_constitutional_facet_is_a_facet_an_instrument_or_absent() -> None:
    mandates = section("QM-CONST")
    assert len(mandates) == 25, f"the model names 25 facets, corpus has {len(mandates)}"
    assert_partitions(
        "QM-CONST",
        mandates,
        CONSTITUTION_FACET,
        CONSTITUTION_INSTRUMENT,
        CONSTITUTION_ABSENT,
    )


def test_each_mapped_facet_is_required_and_declares_the_question_it_answers() -> None:
    for mandate, facet in CONSTITUTION_FACET.items():
        assert facet in REQUIRED_FACETS, f"{mandate}: {facet} is not a required facet"
        assert facet.question.endswith("?"), (
            f"{mandate}: facet {facet.value!r} declares no question, so it cannot be the "
            "answer to an interrogative mandate"
        )


def test_the_facet_mapping_is_injective() -> None:
    """NON-VACUITY. Two mandated facets answered by one facet means one is unanswered."""
    facets = list(CONSTITUTION_FACET.values())
    duplicated = sorted({f.value for f in facets if facets.count(f) > 1})
    assert not duplicated, f"facets claimed by more than one mandate: {duplicated}"


def test_every_instrument_home_is_tracked() -> None:
    assert_homes_exist("QM-CONST", CONSTITUTION_INSTRUMENT)


def test_the_absent_five_are_neither_a_facet_nor_a_module() -> None:
    """NON-VACUITY, in both directions: no facet carries the name, and no tracked module is
    named for it. Either alone would let a real answer read as missing."""
    facet_names = {facet.value.replace("-", "") for facet in Facet}
    for mandate, concept in CONSTITUTION_ABSENT.items():
        assert (
            concept.replace(" ", "") not in facet_names
        ), f"{mandate}: {concept!r} is declared absent but a facet is named for it"
    assert_named_by_nothing("QM-CONST", CONSTITUTION_ABSENT)


def test_the_naming_rule_this_suite_relies_on_can_find_something() -> None:
    assert_absence_rule_can_find_something("uckp capabilities")
