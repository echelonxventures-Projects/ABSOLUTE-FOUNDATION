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
    tracked,
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


# --- QM-FLOW — the twenty-eight stages of the constitutional flow ----------------
#
# The interrogative model ends in a FLOW: Potential through Evolution Registration and back
# to Repository Truth, then infinity. UCL-000001 declares this repository's own lifecycle as
# forty-five stages, so the question is whether the flow the document draws is the lifecycle
# the repository runs.
#
# Seventeen stages the two agree on by name. Ten more are performed by an instrument the
# lifecycle does not name as a stage -- which is a difference in where the boundary of
# "lifecycle" falls, not a missing capability, and calling them absent would be wrong. One
# is genuinely nothing: Potential, the state before anything exists, which a lifecycle of
# governed objects has no stage for by construction.
#
# The stage names are read from `ucl.json` rather than restated here, so a lifecycle that
# renamed a stage breaks this binding instead of silently passing.

#: Flow stage -> the UCL-000001 lifecycle stage that performs it, by that stage's own name.
FLOW_LIFECYCLE_STAGE = {
    "QM-FLOW/FL-02": "Observe",  # Observation
    "QM-FLOW/FL-03": "Knowledge Discovery",  # Discovery
    "QM-FLOW/FL-04": "Perceive",  # Recognition
    "QM-FLOW/FL-06": "Assign Universal Constitutional Identifier",  # Identity Resolution
    "QM-FLOW/FL-07": "Context Assimilation",  # Context Resolution
    "QM-FLOW/FL-09": "Constraint Discovery",  # Constraint Resolution
    "QM-FLOW/FL-11": "Update Repository Truth",  # Repository Truth
    "QM-FLOW/FL-17": "Validate",  # Validation
    "QM-FLOW/FL-18": "Verify",  # Verification
    "QM-FLOW/FL-19": "Certify",  # Certification
    "QM-FLOW/FL-20": "Register",  # Registration
    "QM-FLOW/FL-21": "Integrate",  # Deployment
    "QM-FLOW/FL-24": "Measure",  # Measurement
    "QM-FLOW/FL-25": "Learn",  # Learning
    "QM-FLOW/FL-26": "Extract Engineering Knowledge",  # Knowledge Extraction
    "QM-FLOW/FL-27": "Elevate",  # Capability Elevation
    "QM-FLOW/FL-28": "Register Engineering Knowledge",  # Evolution Registration
}

#: Flow stage -> an instrument that performs it outside the declared lifecycle.
FLOW_INSTRUMENT = {
    "QM-FLOW/FL-05": "engine/knowledge/ukip/classification.py",  # Classification
    "QM-FLOW/FL-08": "engine/uckp/resolution.py",  # Relationship Resolution
    "QM-FLOW/FL-10": "engine/uckp/assimilation.py",  # Knowledge Assimilation
    "QM-FLOW/FL-12": "intelligence/realization/planning.py",  # Planning
    "QM-FLOW/FL-13": "engine/knowledge/integration/composition.py",  # Composition
    "QM-FLOW/FL-14": "engine/foundation/config",  # Configuration
    "QM-FLOW/FL-15": "intelligence/realization/generators",  # Generation
    "QM-FLOW/FL-16": "intelligence/realization/implementation.py",  # Implementation
    "QM-FLOW/FL-22": "engine/runtime",  # Runtime
    "QM-FLOW/FL-23": "platform/observability",  # Monitoring
}

#: Performed by nothing, and correctly so.
FLOW_ABSENT = {"QM-FLOW/FL-01": "Potential"}


def _ucl_stage_names() -> set[str]:
    """The stage names UCL-000001 declares, read from its own generated state."""
    import json

    from engine.tests.conformance.mandate_corpus import repo_root

    ucl = json.loads(
        (repo_root() / "00-MASTER" / "UCL-000001" / "ucl.json").read_text(encoding="utf-8")
    )
    return {str(stage.get("stage") or "") for stage in ucl["stages"]}


def test_every_flow_stage_is_a_lifecycle_stage_an_instrument_or_absent() -> None:
    mandates = section("QM-FLOW")
    assert len(mandates) == 28, f"the flow draws 28 stages, corpus has {len(mandates)}"
    assert_partitions(
        "QM-FLOW",
        mandates,
        FLOW_LIFECYCLE_STAGE,
        FLOW_INSTRUMENT,
        FLOW_ABSENT,
    )


def test_every_lifecycle_backed_stage_names_a_stage_ucl_declares() -> None:
    declared = _ucl_stage_names()
    assert len(declared) >= 40, f"UCL declares only {len(declared)} stages; the join is suspect"
    for mandate, stage in FLOW_LIFECYCLE_STAGE.items():
        assert stage in declared, (
            f"{mandate}: UCL-000001 declares no stage named {stage!r}; the lifecycle renamed "
            "it or never had it, and either way this join is stale"
        )
    claimed = list(FLOW_LIFECYCLE_STAGE.values())
    duplicated = sorted({s for s in claimed if claimed.count(s) > 1})
    assert not duplicated, f"one lifecycle stage claimed by two flow stages: {duplicated}"


def test_every_instrument_backed_stage_is_tracked_and_is_not_a_lifecycle_stage() -> None:
    """The tier boundary. A stage UCL declares belongs in the lifecycle tier, and putting it
    here would understate how strongly the repository holds it."""
    assert_homes_exist("QM-FLOW", FLOW_INSTRUMENT)
    declared = {name.lower() for name in _ucl_stage_names()}
    mandates = section("QM-FLOW")
    for mandate in FLOW_INSTRUMENT:
        assert mandates[mandate].lower() not in declared, (
            f"{mandate}: {mandates[mandate]!r} IS a declared lifecycle stage and is "
            "understated as a loose instrument"
        )


def test_potential_is_absent_because_a_lifecycle_of_objects_cannot_have_a_stage_for_it() -> None:
    """NON-VACUITY for the one absent stage, and the reason is structural rather than a gap.

    `Potential` is the state before anything exists. UCL governs objects, and an object in
    the potential state is one that has not been minted -- Article 2 says nothing exists
    constitutionally until it has become a knowledge object. A stage for it would be a stage
    with no subject.
    """
    declared = {name.lower() for name in _ucl_stage_names()}
    assert "potential" not in declared
    assert not [
        path
        for path in tracked()
        if path.endswith(".py") and "potential" in path.rsplit("/", 1)[-1].lower()
    ], "a potential module now exists; FL-01 is no longer absent by construction"


def test_the_flow_and_the_lifecycle_agree_more_than_they_differ() -> None:
    """The finding. Seventeen of twenty-eight stages match by name across two documents
    written independently, which is what makes the ten differences legible as boundary
    disagreements rather than as holes."""
    assert len(FLOW_LIFECYCLE_STAGE) == 17
    assert len(FLOW_INSTRUMENT) == 10
    assert len(FLOW_LIFECYCLE_STAGE) > len(FLOW_INSTRUMENT) + len(FLOW_ABSENT)
