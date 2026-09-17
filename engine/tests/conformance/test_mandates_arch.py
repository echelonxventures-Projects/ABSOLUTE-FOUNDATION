"""Mandate conformance — the Absolute Universal Constitutional Architecture diagram.

176 mandates over 14 sections. Each suite below takes one section, locates what the
repository actually holds for it, and declares what it cannot prove.
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

# --- ARCH-CERTV — the eight certification verdicts ------------------------------
#
# The Quality & Trust Fabric ends in Universal Certification and names its verdict set:
# PASS, REUSE, EXTEND, CREATE, SUPERSEDE, DEPRECATE, BLOCKED, NOT_APPLICABLE, under the
# rule "No mandatory obligation may fail." A verdict set is the one part of a governance
# diagram that must exist as VALUES a running instrument can return -- a verdict nothing
# emits is a verdict nobody can receive.
#
# So this binding asks a narrow, checkable question of each: does some instrument in this
# repository emit this verdict? Two do not, and the reasons differ enough to matter.

#: Verdict -> the module that emits it, and the symbol carrying the value.
VERDICT_EMITTED = {
    "ARCH-CERTV/CV-01": ("engine/certification/closure.py", "PASS"),
    "ARCH-CERTV/CV-02": ("engine/constitution/assimilation.py", "REUSE"),
    "ARCH-CERTV/CV-04": ("engine/constitution/assimilation.py", "CREATE"),
    "ARCH-CERTV/CV-05": ("engine/registry/universal/records.py", "SUPERSEDE"),
    "ARCH-CERTV/CV-06": ("engine/registry/universal/records.py", "DEPRECATE"),
    "ARCH-CERTV/CV-07": ("engine/registry/models.py", "BLOCKED"),
}

#: EXTEND is not a verdict here; it is REUSE carrying targets. `AssimilationVerdict.status`
#: returns exactly CREATE or REUSE, and `reuse_targets` is documented as "the existing
#: subjects the caller should extend instead". The instruction the diagram spells EXTEND is
#: delivered -- under another name and in another field -- so recording it as absent would
#: be false and recording it as emitted would be false too.
VERDICT_EXPRESSED_DIFFERENTLY = {
    "ARCH-CERTV/CV-03": (
        "engine/constitution/assimilation.py",
        "reuse_targets",
        "status returns CREATE or REUSE only; the extend instruction rides on reuse_targets",
    ),
}

#: Emitted by nothing. NOT_APPLICABLE is the verdict that lets an obligation be dismissed
#: without being met, which is exactly why its absence is worth stating: the rule "no
#: mandatory obligation may fail" has no escape hatch here, by omission rather than design.
VERDICT_ABSENT = {
    "ARCH-CERTV/CV-08": "NOT_APPLICABLE",
}


def test_every_certification_verdict_is_emitted_expressed_or_absent() -> None:
    mandates = section("ARCH-CERTV")
    assert len(mandates) == 8, f"the diagram names 8 verdicts, corpus has {len(mandates)}"
    assert_partitions(
        "ARCH-CERTV",
        mandates,
        VERDICT_EMITTED,
        VERDICT_EXPRESSED_DIFFERENTLY,
        VERDICT_ABSENT,
    )


def test_every_emitted_verdict_appears_as_a_value_in_its_module() -> None:
    """The verdict must be a VALUE, not a word in a comment. Each is checked as a quoted
    string literal, which is how a returnable verdict is written in this codebase."""
    from engine.tests.conformance.mandate_corpus import repo_root

    homes = {m: home for m, (home, _symbol) in VERDICT_EMITTED.items()}
    assert_homes_exist("ARCH-CERTV", homes)
    for mandate, (home, symbol) in VERDICT_EMITTED.items():
        text = (repo_root() / home).read_text(encoding="utf-8")
        assert f'"{symbol}"' in text, (
            f"ARCH-CERTV/{mandate}: {home} is declared to emit {symbol!r} and carries no "
            "such value; a verdict nothing emits is a verdict nobody can receive"
        )


def test_the_assimilation_gate_really_returns_only_create_or_reuse() -> None:
    """NON-VACUITY for CV-03. The claim is that EXTEND is not a status this gate can
    return. If it ever becomes one, the row moves to EMITTED and this tiering is wrong."""
    import inspect

    from engine.constitution.assimilation import AssimilationVerdict

    body = inspect.getsource(AssimilationVerdict.status.fget)
    assert '"CREATE"' in body and '"REUSE"' in body
    assert '"EXTEND"' not in body, (
        "the assimilation gate now returns EXTEND as a status; ARCH-CERTV/CV-03 is emitted "
        "rather than expressed differently"
    )
    assert "extend" in (AssimilationVerdict.reuse_targets.fget.__doc__ or "").lower(), (
        "reuse_targets no longer documents itself as what the caller should extend; the "
        "claim that the EXTEND instruction rides on it is no longer supported"
    )


def test_the_absent_verdict_is_emitted_by_nothing() -> None:
    """NON-VACUITY. Searched as a quoted value across every tracked Python file, because
    the question is whether anything can RETURN it, not whether anything mentions it."""
    from engine.tests.conformance.mandate_corpus import repo_root, tracked

    for mandate, verdict in VERDICT_ABSENT.items():
        emitters = [
            path
            for path in tracked()
            if path.endswith(".py")
            and "/tests/" not in path
            and f'"{verdict}"' in (repo_root() / path).read_text(encoding="utf-8", errors="ignore")
        ]
        assert (
            not emitters
        ), f"ARCH-CERTV/{mandate}: {verdict} is declared absent but is emitted by {emitters}"


def test_the_naming_rule_this_suite_relies_on_can_find_something() -> None:
    assert_absence_rule_can_find_something("constitution assimilation")


def test_absence_search_does_not_silently_match_nothing() -> None:
    assert_named_by_nothing("ARCH-CERTV", {"ARCH-CERTV/CV-08": "not applicable verdict"})


# --- ARCH-UCMM — the thirty concepts of the Universal Constitutional Meta Model --
#
# The diagram places the UCMM directly beneath the Absolute Constitutional Kernel and lists
# thirty universals in three columns. A meta-model is not a component inventory: it is the
# set of things every object in the system must be describable IN. Article 6 answers exactly
# that question with thirty-three facets -- "a question every constitutional object must be
# able to answer about itself" -- so the facets are the natural respondent, and the concepts
# they do not cover are the honest measure of the gap between diagram and law.
#
# Three tiers, and the boundary between the first two carries the weight. A FACET is
# carried by every object; a MODULE is a capability the substrate has. "Universal Trust"
# answered by `platform/foundation/trust.py` is a real answer and a weaker one than
# "Universal Identity" answered by a facet every UCKO must fill, and flattening them would
# report a meta-model that is complete when it is not.

#: Meta-model concept -> the universal facet that carries it on every object.
META_MODEL_FACET = {
    "ARCH-UCMM/UM-01": Facet.IDENTITY,  # Universal Identity
    "ARCH-UCMM/UM-02": Facet.RELATIONSHIPS,  # Universal Relationships
    "ARCH-UCMM/UM-03": Facet.CONTEXT,  # Universal Context
    "ARCH-UCMM/UM-04": Facet.SEMANTIC_IDENTITY,  # Universal Meaning
    "ARCH-UCMM/UM-05": Facet.CONSTRAINTS,  # Universal Constraints
    "ARCH-UCMM/UM-06": Facet.POLICIES,  # Universal Rules
    "ARCH-UCMM/UM-07": Facet.KNOWLEDGE_CONTEXT,  # Universal Knowledge
    "ARCH-UCMM/UM-16": Facet.TEMPORAL_HISTORY,  # Universal Event
    "ARCH-UCMM/UM-17": Facet.LIFECYCLE,  # Universal Lifecycle
    "ARCH-UCMM/UM-18": Facet.EVOLUTION_HISTORY,  # Universal Evolution
    "ARCH-UCMM/UM-19": Facet.GOVERNANCE_CONTEXT,  # Universal Governance
    "ARCH-UCMM/UM-20": Facet.AUTHORITY,  # Universal Authority
    "ARCH-UCMM/UM-21": Facet.OWNERSHIP,  # Universal Ownership
    "ARCH-UCMM/UM-22": Facet.SECURITY_CONTEXT,  # Universal Security
    "ARCH-UCMM/UM-27": Facet.RUNTIME_BINDINGS,  # Universal Runtime
    "ARCH-UCMM/UM-30": Facet.PROJECTION_BINDINGS,  # Universal Projection
}

#: Carried by a module the substrate has, not by a question every object answers.
META_MODEL_MODULE = {
    "ARCH-UCMM/UM-09": "engine/uckp/vocabulary.py",  # Universal Semantics
    "ARCH-UCMM/UM-12": "platform/universal_measurement",  # Universal Measurement
    "ARCH-UCMM/UM-13": "engine/uckp/capabilities.py",  # Universal Capability
    "ARCH-UCMM/UM-15": "engine/uckp/state.py",  # Universal State
    "ARCH-UCMM/UM-24": "platform/foundation/trust.py",  # Universal Trust
    "ARCH-UCMM/UM-26": "platform/commercial_intelligence",  # Universal Commerce
    "ARCH-UCMM/UM-28": "engine/uckp/intelligence.py",  # Universal Intelligence
}

#: Named by neither. Seven of thirty, and the set is worth reading whole: the meta-model
#: mandates Logic and Mathematics as first-class universals and the substrate has neither,
#: which means nothing in it can state a rule formally or measure a quantity dimensionally.
#: Information, Behaviour, Privacy and Economics repeat the gaps QM-CONST records under
#: other names -- the same holes seen from a second document.
META_MODEL_ABSENT = {
    "ARCH-UCMM/UM-08": "information",  # Universal Information
    "ARCH-UCMM/UM-10": "logic",  # Universal Logic
    "ARCH-UCMM/UM-11": "mathematics",  # Universal Mathematics
    "ARCH-UCMM/UM-14": "behaviour",  # Universal Behaviour
    "ARCH-UCMM/UM-23": "privacy",  # Universal Privacy
    "ARCH-UCMM/UM-25": "economics",  # Universal Economics
    "ARCH-UCMM/UM-29": "automation",  # Universal Automation
}


def test_every_meta_model_concept_is_a_facet_a_module_or_absent() -> None:
    mandates = section("ARCH-UCMM")
    assert len(mandates) == 30, f"the UCMM lists 30 universals, corpus has {len(mandates)}"
    assert_partitions(
        "ARCH-UCMM",
        mandates,
        META_MODEL_FACET,
        META_MODEL_MODULE,
        META_MODEL_ABSENT,
    )


def test_each_facet_backed_universal_is_required_and_carried_by_the_object() -> None:
    import dataclasses

    from engine.uckp.ucko import UniversalConstitutionalKnowledgeObject as UCKO

    fields = {f.name for f in dataclasses.fields(UCKO)}
    for mandate, facet in META_MODEL_FACET.items():
        assert facet in REQUIRED_FACETS, f"{mandate}: {facet} is not a required facet"
        assert facet.attribute in fields, (
            f"{mandate}: facet {facet.value!r} is declared but no UCKO field carries it, so "
            "the meta-model concept is not in fact universal over objects"
        )


def test_the_facet_mapping_is_injective() -> None:
    """NON-VACUITY. Meaning and Semantics are listed as separate universals; answering both
    with SEMANTIC_IDENTITY would report two concepts covered by one answer."""
    facets = list(META_MODEL_FACET.values())
    duplicated = sorted({f.value for f in facets if facets.count(f) > 1})
    assert not duplicated, f"facets claimed by more than one universal: {duplicated}"


def test_every_module_backed_universal_is_tracked_and_is_not_a_facet() -> None:
    """The tier boundary, asserted. A concept in the module tier that a facet also answers
    would be understated, and one in the facet tier without a field would be overstated."""
    assert_homes_exist("ARCH-UCMM", META_MODEL_MODULE)
    mandates = section("ARCH-UCMM")
    facet_names = {facet.value.replace("-", " ") for facet in Facet}
    for mandate in META_MODEL_MODULE:
        concept = mandates[mandate].removeprefix("Universal ").lower()
        assert concept not in facet_names, (
            f"{mandate}: {concept!r} is answered by a facet after all and is understated "
            "as a module"
        )


def test_the_absent_universals_are_named_by_no_module_and_no_facet() -> None:
    """NON-VACUITY in both directions. Either check alone would let a real answer read as
    missing -- a facet with no module, or a module with no facet."""
    facet_names = {facet.value.replace("-", "") for facet in Facet}
    for mandate, concept in META_MODEL_ABSENT.items():
        assert (
            concept not in facet_names
        ), f"{mandate}: {concept!r} is declared absent but a facet is named for it"
    assert_named_by_nothing("ARCH-UCMM", META_MODEL_ABSENT)


def test_the_meta_model_gaps_agree_with_the_interrogative_model() -> None:
    """Two documents, one repository.

    The UCMM and the interrogative model each mandate Information, Behaviour, Privacy and
    Economics, and each suite located them independently. If the two ever disagree, one has
    mis-located something -- which is a finding about the suites, not about the repository,
    and worth catching before it is read as a change in coverage. Behaviour is compared on
    its stem because the documents spell it differently.
    """
    from engine.tests.conformance.test_mandates_model import CONSTITUTION_ABSENT

    def stems(values):
        return {v.replace("behaviour", "behavio").replace("behavior", "behavio") for v in values}

    shared = {"information", "behavio", "privacy", "economics"}
    here, there = stems(META_MODEL_ABSENT.values()), stems(CONSTITUTION_ABSENT.values())

    assert shared <= here, f"the UCMM suite no longer reports absent: {sorted(shared - here)}"
    assert shared <= there, f"QM-CONST no longer reports absent: {sorted(shared - there)}"


# --- ARCH-VALID — the twenty-one validations ------------------------------------
#
# The Quality & Trust Fabric lists twenty-one validations and opens the section with an
# instruction rather than a description: "Automatically discover every constitutionally
# applicable activity." Thirteen have an instrument. Eight do not, and six of those eight
# are the non-functional axes -- Privacy, Risk, Performance, Reliability, Scalability,
# Interoperability. That is the shape of the gap and it is worth stating as one: the
# repository validates what it IS thoroughly and validates how it BEHAVES not at all.

#: Validation -> the instrument that performs it.
VALIDATION_INSTRUMENT = {
    "ARCH-VALID/VL-01": "scripts/ucos-env.sh",  # Static Analysis -- the ruff gate
    "ARCH-VALID/VL-02": "verify.sh",  # Dynamic Analysis -- the suite under the floor
    # Semantic Analysis
    "ARCH-VALID/VL-03": "00-MASTER/UAKOS-CLOSURE-008/02-SEMANTIC-EQUIVALENCE-REGISTER.md",
    "ARCH-VALID/VL-04": "00-MASTER/UAIE-000001/uaie.json",  # Architecture Validation
    "ARCH-VALID/VL-05": "engine/uckp/validation.py",  # Constitutional Validation
    # Requirement Validation
    "ARCH-VALID/VL-06": "00-MASTER/UAKOS-CLOSURE-009/requirement_engine.py",
    "ARCH-VALID/VL-07": "engine/validation/checks.py",  # Dependency Validation
    "ARCH-VALID/VL-08": "engine/foundation/config",  # Configuration Validation
    "ARCH-VALID/VL-09": "engine/validation/checks.py",  # Identity Validation
    "ARCH-VALID/VL-10": "engine/graph/validation.py",  # Relationship Validation
    "ARCH-VALID/VL-11": "engine/kernel/governance.py",  # Policy Validation
    "ARCH-VALID/VL-12": "engine/kernel/compliance.py",  # Compliance Validation
    "ARCH-VALID/VL-13": "engine/validation/checks.py",  # Security Validation
    "ARCH-VALID/VL-15": "engine/constitution/legality.py",  # Legal Validation
    "ARCH-VALID/VL-20": "platform/validation_intelligence/compatibility.py",  # Compatibility
}

#: Performed by nothing. Six of the seven are behavioural axes, which is the finding.
VALIDATION_ABSENT = {
    "ARCH-VALID/VL-14": "privacy",
    "ARCH-VALID/VL-16": "risk",
    "ARCH-VALID/VL-17": "performance",
    "ARCH-VALID/VL-18": "reliability",
    "ARCH-VALID/VL-19": "scalability",
    "ARCH-VALID/VL-21": "interoperability",
}


def test_every_mandated_validation_is_performed_or_absent() -> None:
    mandates = section("ARCH-VALID")
    assert len(mandates) == 21, f"the fabric lists 21 validations, corpus has {len(mandates)}"
    assert_partitions("ARCH-VALID", mandates, VALIDATION_INSTRUMENT, VALIDATION_ABSENT)


def test_every_performing_instrument_is_tracked_and_executable_or_declared_data() -> None:
    """A validation carried by a register is a record of one having been done; a validation
    carried by code is one that can be done again. Both count, and the difference is
    recorded rather than flattened."""
    assert_homes_exist("ARCH-VALID", VALIDATION_INSTRUMENT)
    executable = [home for home in VALIDATION_INSTRUMENT.values() if home.endswith((".py", ".sh"))]
    assert len(executable) >= 10, (
        f"only {len(executable)} of the located validations are executable; the rest are "
        "records of a validation having happened once"
    )


def test_the_three_checks_module_validations_name_distinct_checks() -> None:
    """NON-VACUITY for the one home claimed three times. Dependency, Identity and Security
    all resolve to `engine/validation/checks.py`, which is only honest if that module
    carries three different checks."""
    from engine.validation.checks import default_checks

    names = {type(check).__name__ for check in default_checks()}
    for expected in ("DependencyClosureCheck", "IdentityCheck", "SignatureCheck"):
        assert expected in names, (
            f"{expected} is not among the default checks {sorted(names)}; one of the three "
            "validations mapped to that module is not actually performed"
        )


def test_the_absent_validations_are_performed_by_nothing() -> None:
    """NON-VACUITY. `engine/constitution/legality.py` is why this is searched rather than
    assumed: Legal Validation reads as an obvious gap and the repository has one."""
    assert_named_by_nothing("ARCH-VALID", VALIDATION_ABSENT)


def test_the_gap_is_behavioural_rather_than_scattered() -> None:
    """The finding, asserted so it cannot quietly stop being true.

    Six of the seven absent validations are non-functional axes. If a performance or
    scalability validator ever lands, this assertion fails and the characterisation above
    has to be rewritten rather than left standing as stale narrative.
    """
    behavioural = {"performance", "reliability", "scalability", "interoperability", "risk"}
    assert behavioural <= set(VALIDATION_ABSENT.values()), (
        "a behavioural validator now exists; the claim that this repository validates what "
        "it is and not how it behaves no longer holds"
    )
