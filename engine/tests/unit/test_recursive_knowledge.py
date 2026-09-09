"""URKE-000001 — positive and negative tests. A law that cannot be made to fail measures nothing.

Every law gets both directions. The positive test asserts the law holds on the seeded repository.
The negative test forges a state that violates it and asserts the refusal — either the engine
raises, or the law reports a violation it did not report before. Thirty-two laws that all passed and
could not be made to fail would be thirty-two sentences.
"""

from __future__ import annotations

import copy
import dataclasses
import json
import os
from pathlib import Path

import pytest

from engine.recursive_knowledge import (
    admission,
    bridge,
    composition,
    contract,
    discovery,
    evidence,
    evolution,
    gate,
    proposal,
    research,
    states,
    subjects,
    worlds,
)
from engine.recursive_knowledge import (
    ledger as ledger_module,
)
from engine.recursive_knowledge.declaration import (
    DIGEST_EXCLUSIONS,
    DeclarationError,
    load_declaration,
    parse,
    repo_root,
    scanned_vocabulary,
)
from engine.recursive_knowledge.ledger import KnowledgeLedger
from engine.recursive_knowledge.model import (
    ClosureCriterion,
    RecursiveKnowledgeError,
    ReviewPoint,
    StateTransition,
    VerificationEvent,
    knowledge_id,
    missing_attributes,
)
from engine.uckp.canonical import content_hash


@pytest.fixture(scope="module")
def declaration():
    return load_declaration()


@pytest.fixture(scope="module")
def probe():
    _, workspace = contract.load_contract()
    return workspace


@pytest.fixture()
def store(declaration):
    return KnowledgeLedger(declaration)


@pytest.fixture(scope="module")
def report():
    return contract.measure()


# --- the declaration itself ---------------------------------------------------------------


def test_declaration_loads_and_is_coherent(declaration):
    problems = declaration.validate(contract.implemented())
    assert problems == []


def test_declaration_is_not_a_closed_set(declaration):
    assert declaration.closed_set is False
    assert declaration.upper_limit is None


def test_declaration_refuses_a_terminal_state(declaration):
    broken = dataclasses.replace(
        declaration,
        states=(dataclasses.replace(declaration.states[0], terminal=True),)
        + declaration.states[1:],
    )
    assert any("terminal" in problem for problem in broken.validate(contract.implemented()))


def test_declaration_refuses_a_non_blocking_law(declaration):
    broken = dataclasses.replace(
        declaration,
        laws=(dataclasses.replace(declaration.laws[0], blocking=False),) + declaration.laws[1:],
    )
    assert any("non-blocking" in problem for problem in broken.validate(contract.implemented()))


def test_declaration_refuses_a_review_exemption(declaration):
    broken = dataclasses.replace(declaration, review_exemptions=("somebody",))
    assert any("exemption" in problem for problem in broken.validate(contract.implemented()))


def test_every_binding_kind_is_implemented_in_both_directions(declaration):
    declared, live = declaration.declared_bindings(), contract.implemented()
    assert set(declared) == set(live)
    for kind in sorted(declared):
        assert declared[kind] == live[kind], kind


def test_scanned_vocabulary_is_bound_both_ways(declaration):
    members = scanned_vocabulary(declaration)
    assert set(members) == set(declaration.source_discipline.scanned_vocabularies)


# --- URKE-L-01 / L-02 --------------------------------------------------------------------


def test_l01_every_domain_admits_an_unknown(probe):
    assert contract.every_identified_unknown_is_governed(probe) == []


def test_l01_negative_an_unknown_without_an_owner_is_refused(store, declaration):
    with pytest.raises(RecursiveKnowledgeError):
        store.admit(
            store.subject(
                natural_key="negative/l01",
                profile=declaration.default_profile,
                domain=declaration.residual_domain,
                owner="a-role-nobody-declared",
                origin="test",
            )
        )


def test_l02_residual_is_representable(probe):
    assert contract.residual_is_representable(probe) == []


def test_l02_negative_an_undeclared_domain_is_refused(declaration):
    with pytest.raises(RecursiveKnowledgeError):
        composition.express(
            declaration, state=declaration.initial_state, domain="a-domain-nobody-declared"
        )


# --- URKE-L-03 profile requirements ------------------------------------------------------


def test_l03_profile_requirements_are_enforced(probe):
    assert contract.profile_requirements_are_enforced(probe) == []


@pytest.mark.parametrize("attribute", ["identity", "owner", "state", "governance", "context"])
def test_l03_negative_missing_each_universal_attribute_is_detected(store, declaration, attribute):
    entity = store.subject(
        natural_key="negative/l03",
        profile=declaration.default_profile,
        domain=declaration.residual_domain,
        owner=declaration.artifact_id,
        origin="test",
    )
    hollow = dataclasses.replace(entity, **{attribute: ""})
    required, _ = declaration.required_for(entity.entity_class, entity.classification)
    assert attribute in missing_attributes(hollow, required)


def test_l03_negative_a_gap_with_no_closure_criteria_is_refused(store, declaration):
    with pytest.raises(RecursiveKnowledgeError):
        subjects.record_gap(
            store,
            natural_key="negative/l03-gap",
            classification=declaration.residual_gap_class,
            severity=declaration.severity_ids[-1],
            owner=declaration.artifact_id,
            origin="test",
            finding="a gap with nothing to satisfy",
            resolution_path="none offered",
            criteria=(),
        )


# --- URKE-L-04 histories -----------------------------------------------------------------


def test_l04_histories_are_append_only(probe):
    assert contract.histories_are_append_only(probe) == []


def test_l04_negative_a_verification_with_no_assumptions_is_refused():
    with pytest.raises(RecursiveKnowledgeError):
        VerificationEvent(
            verifier="v",
            verdict="measured",
            assumptions=(),
            limitations=("bounded",),
            basis="test",
            sequence=0,
        )


def test_l04_negative_a_verification_with_no_limitations_is_refused():
    with pytest.raises(RecursiveKnowledgeError):
        VerificationEvent(
            verifier="v",
            verdict="measured",
            assumptions=("assumed",),
            limitations=(),
            basis="test",
            sequence=0,
        )


def test_l04_negative_a_transition_without_a_basis_is_refused():
    with pytest.raises(RecursiveKnowledgeError):
        StateTransition(from_state="a", to_state="b", basis="  ", actor="x", sequence=0)


# --- URKE-L-05 gap closure ---------------------------------------------------------------


def test_l05_gap_closure_and_review_are_governed(probe):
    assert contract.gap_closure_and_review_are_governed(probe) == []


def test_l05_negative_closing_with_unsatisfied_criteria_is_refused(store, declaration):
    gap = subjects.record_gap(
        store,
        natural_key="negative/l05",
        classification=declaration.gap_classes[0].identifier,
        severity=declaration.severity_ids[0],
        owner=declaration.artifact_id,
        origin="test",
        finding="a gap",
        resolution_path="do it",
        criteria=("it is done",),
    )
    with pytest.raises(RecursiveKnowledgeError):
        subjects.close_gap(store, gap.identity, basis="premature", actor="test")


def test_l05_negative_a_satisfied_criterion_needs_a_basis():
    with pytest.raises(RecursiveKnowledgeError):
        ClosureCriterion(statement="done", satisfied=True, basis="")


def test_l05_negative_a_review_cadence_below_one_is_refused():
    with pytest.raises(RecursiveKnowledgeError):
        ReviewPoint(cadence=0, due_at_sequence=1, criteria="look again")


# --- URKE-L-06 source discipline ---------------------------------------------------------


def test_l06_no_vocabulary_member_is_a_source_literal(probe):
    assert contract.vocabulary_is_declared_not_coded(probe) == []


def test_l06_negative_the_detector_finds_a_planted_literal(
    probe, declaration, tmp_path, monkeypatch
):
    planted = f"value = {declaration.state_ids[0]!r}\n"
    target = tmp_path / "engine" / "recursive_knowledge"
    target.mkdir(parents=True)
    for name, source in probe.sources().items():
        (target / name).write_text(source, encoding="utf-8")
    (target / "planted.py").write_text(planted, encoding="utf-8")
    forged = contract.Probe(declaration=declaration, repo=str(tmp_path))
    findings = contract.vocabulary_is_declared_not_coded(forged)
    assert any("planted.py" in finding for finding in findings)


# --- URKE-L-07 / L-08 / L-09 openness ----------------------------------------------------


def test_l07_no_state_is_terminal(probe):
    assert contract.no_state_is_terminal(probe) == []


def test_l07_negative_a_state_with_no_successor_is_detected(declaration):
    broken = dataclasses.replace(
        declaration,
        states=(dataclasses.replace(declaration.states[0], successors=()),)
        + declaration.states[1:],
    )
    assert states.terminal_states(broken)


def test_l08_data_extension_changes_no_source(probe):
    assert contract.data_extension_needs_no_redesign(probe) == []


def test_l08_negative_admitting_a_declared_member_twice_is_refused(store, declaration):
    with pytest.raises(RecursiveKnowledgeError):
        admission.admit_domain(
            store, natural_key=declaration.domain_ids[0], definition="already declared"
        )


def test_l08_admitting_a_state_past_the_bound_is_refused(store, declaration):
    current = declaration
    admitted = 0
    while len(current.states) < current.state_bound:
        current, _ = admission.admit_state(
            KnowledgeLedger(current), natural_key=f"extra-{admitted}", definition="runtime state"
        )
        admitted += 1
    with pytest.raises(RecursiveKnowledgeError):
        admission.admit_state(
            KnowledgeLedger(current), natural_key="one-too-many", definition="past the bound"
        )


def test_l09_future_domain_is_admissible(probe):
    assert contract.future_domain_is_admissible(probe) == []


# --- URKE-L-10 / L-11 / L-12 discovery ---------------------------------------------------


def test_l10_discovery_converges_and_is_not_inert(probe):
    assert contract.discovery_reaches_a_fixed_point(probe) == []


def test_l10_discovery_is_driven_only_by_declared_sources(declaration):
    """With no declared source nothing is found, which is what makes the engine data-driven.

    The earlier form of this test asserted that an unseeded ledger finds nothing. That premise was
    wrong: several detectors read the declaration rather than the ledger, so they find conditions
    immediately — and an unseeded ledger has no root context for a finding to sit in, so admission
    correctly refused. The law was right and the test was not.
    """
    sourceless = dataclasses.replace(declaration, discovery_sources=())
    assert discovery.discover(KnowledgeLedger(sourceless)) == ()


def test_l11_discovery_writes_nothing_outside_the_ledger(probe):
    assert contract.discovery_never_mutates_constitutional_truth(probe) == []


def test_l12_every_target_and_detector_is_bound(probe):
    assert contract.discovery_covers_every_declared_target(probe) == []


def test_l12_negative_an_unimplemented_detector_is_detected(declaration):
    broken = dataclasses.replace(
        declaration,
        discovery_sources=(
            dataclasses.replace(declaration.discovery_sources[0], detector="not_implemented"),
        )
        + declaration.discovery_sources[1:],
    )
    forged = contract.Probe(declaration=broken, repo=repo_root())
    assert contract.discovery_covers_every_declared_target(forged)


# --- URKE-L-13 evolution -----------------------------------------------------------------


def test_l13_evolution_is_one_traceable_mechanism(probe):
    assert contract.evolution_is_one_traceable_mechanism(probe) == []


def test_l13_negative_an_undeclared_subject_cannot_evolve(store, declaration):
    with pytest.raises(RecursiveKnowledgeError):
        evolution.evolve(
            store,
            subject="not-a-declared-subject",
            operator=declaration.operators[0].identifier,
            before="a",
            after="b",
            basis="test",
            owner=declaration.artifact_id,
        )


def test_l13_negative_a_step_recording_no_change_is_refused(store, declaration):
    subject = declaration.evolution_subjects[0]
    with pytest.raises(RecursiveKnowledgeError):
        evolution.evolve(
            store,
            subject=subject.identifier,
            operator=subject.operators[0],
            before="same",
            after="same",
            basis="test",
            owner=declaration.artifact_id,
        )


def test_l13_negative_an_operator_the_subject_does_not_permit_is_refused(store, declaration):
    subject = next(
        spec
        for spec in declaration.evolution_subjects
        if len(spec.operators) < len(declaration.operators)
    )
    forbidden = next(
        spec.identifier
        for spec in declaration.operators
        if spec.identifier not in subject.operators
    )
    with pytest.raises(RecursiveKnowledgeError):
        evolution.evolve(
            store,
            subject=subject.identifier,
            operator=forbidden,
            before="a",
            after="b",
            basis="test",
            owner=declaration.artifact_id,
        )


# --- URKE-L-14 worlds --------------------------------------------------------------------


def test_l14_worlds_are_data_driven(probe):
    assert contract.worlds_are_data_driven(probe) == []


def test_l14_every_reality_answers_every_dimension(declaration):
    for identifier in declaration.reality_ids:
        resolved = worlds.resolve(declaration, identifier)
        assert len(resolved["systems"]) == len(declaration.reality_dimensions)


def test_l14_negative_an_undeclared_reality_is_refused(declaration):
    with pytest.raises(RecursiveKnowledgeError):
        worlds.resolve(declaration, "a-reality-nobody-declared")


def test_l14_the_residual_reality_resolves_nothing(declaration):
    residual = next(spec for spec in declaration.realities if spec.residual)
    resolved = worlds.resolve(declaration, residual.identifier)
    assert len(resolved["unresolved_dimensions"]) == len(declaration.reality_dimensions)


# --- URKE-L-15 no silent loss ------------------------------------------------------------


def test_l15_nothing_admitted_can_silently_disappear(probe):
    assert contract.nothing_admitted_can_silently_disappear(probe) == []


def test_l15_the_ledger_exposes_no_removal_path(store):
    for forbidden in ("remove", "delete", "pop", "clear", "discard", "retract", "forget"):
        assert not hasattr(store, forbidden)


def test_l15_negative_superseding_by_an_unrecorded_subject_is_refused(store):
    sample = store.all()[0]
    with pytest.raises(RecursiveKnowledgeError):
        store.supersede(sample.identity, by="not-recorded", basis="test")


def test_l15_a_superseded_subject_is_still_retrievable(store):
    first, second = store.all()[0], store.all()[1]
    store.supersede(first.identity, by=second.identity, basis="test")
    assert store.has(first.identity)
    assert store.get(first.identity).superseded_by == second.identity
    assert store.chain_is_intact()


def test_l15_negative_a_tampered_journal_is_detected(store):
    entry = store.journal[5]
    store._journal[5] = dataclasses.replace(entry, state="tampered")
    assert store.chain_is_intact() is False


# --- URKE-L-16 / L-17 governance and context ---------------------------------------------


def test_l16_no_subject_exists_outside_governance(probe):
    assert contract.no_subject_exists_outside_governance(probe) == []


def test_l16_every_subject_reaches_a_disposition(store):
    outcome = bridge.govern(store)
    assert outcome["ungoverned"] == []
    assert outcome["dispositions"]


def test_l17_no_subject_exists_outside_context(probe):
    assert contract.no_subject_exists_outside_context(probe) == []


def test_l17_negative_a_contextless_subject_is_detected(store, declaration):
    entity = store.all()[3]
    store.amend(dataclasses.replace(entity, context=""), event="test")
    forged = contract.Probe(declaration=declaration, repo=repo_root())
    forged._ledger = store
    assert contract.no_subject_exists_outside_context(forged)


# --- URKE-L-18 non-goals -----------------------------------------------------------------


def test_l18_no_completeness_claim_is_declared(probe):
    assert contract.no_completeness_claim_is_declared(probe) == []


def test_l18_negative_a_planted_guarantee_is_detected(declaration, probe, tmp_path):
    phrase = declaration.forbidden_phrases[0]
    target = tmp_path / "engine" / "recursive_knowledge"
    target.mkdir(parents=True)
    for name, source in probe.sources().items():
        (target / name).write_text(source, encoding="utf-8")
    (target / "boast.py").write_text(f'"""This offers {phrase}."""\n', encoding="utf-8")
    forged = contract.Probe(declaration=declaration, repo=str(tmp_path))
    assert contract.no_completeness_claim_is_declared(forged)


# --- URKE-L-19 determinism ---------------------------------------------------------------


def test_l19_measurement_is_deterministic(probe):
    assert contract.measurement_is_deterministic(probe) == []


def test_l19_two_ledgers_agree(declaration):
    left, right = KnowledgeLedger(declaration), KnowledgeLedger(declaration)
    assert left.digest() == right.digest()
    assert left.summary() == right.summary()


def test_l19_two_reports_agree():
    first, second = contract.measure(), contract.measure()
    for report in (first, second):
        report.pop("metrics", None)
    assert first == second


# --- URKE-L-20 / L-21 bindings and disclosure --------------------------------------------


def test_l20_bound_vocabulary_is_neither_copied_nor_narrowed(probe):
    assert contract.bound_vocabulary_is_neither_copied_nor_narrowed(probe) == []


def test_l20_negative_a_stale_binding_is_detected(declaration):
    broken = dataclasses.replace(
        declaration,
        states=(
            dataclasses.replace(
                declaration.states[0],
                binding={
                    "owner": declaration.binding_owners[0].owner,
                    "population": "not-a-population",
                    "member": "nothing",
                },
            ),
        )
        + declaration.states[1:],
    )
    assert states.binding_problems(broken)


def test_l21_disclosed_gaps_are_governed(probe):
    assert contract.disclosed_gaps_are_themselves_governed(probe) == []


def test_l21_every_disclosed_gap_is_in_the_ledger(store, declaration):
    recorded = {
        entity.natural_key
        for entity in store.of_profile(declaration.profile_for(subjects.DISCLOSURE_ROLE))
    }
    for gap in declaration.all_disclosed_gaps():
        assert gap.gap_id in recorded


# --- URKE-L-24 axes ----------------------------------------------------------------------


def test_l24_lifecycle_axes_are_independent(probe):
    assert contract.lifecycle_axes_are_independent(probe) == []


def test_l24_the_whole_cross_product_is_reachable(declaration):
    expected = 1
    for spec in declaration.lifecycle_axes:
        expected *= len(spec.values)
    assert len(states.axis_combinations(declaration)) == expected


def test_l24_negative_an_undeclared_axis_value_is_refused(store, declaration):
    with pytest.raises(RecursiveKnowledgeError):
        states.with_axis(declaration, store.all()[0], declaration.axis_ids[0], "not-a-value")


# --- URKE-L-25 relationships -------------------------------------------------------------


def test_l25_relationships_carry_governance(probe):
    assert contract.relationships_carry_governance(probe) == []


def test_l25_negative_a_relationship_to_an_absent_subject_is_refused(store, declaration):
    with pytest.raises(RecursiveKnowledgeError):
        ledger_module.relate(
            store,
            source=store.all()[0].identity,
            target="not-recorded",
            relation=declaration.relation_ids[0],
            basis="test",
            owner=declaration.artifact_id,
            origin="test",
        )


def test_l25_negative_a_relationship_without_a_basis_is_refused(store, declaration):
    with pytest.raises(RecursiveKnowledgeError):
        ledger_module.relate(
            store,
            source=store.all()[0].identity,
            target=store.all()[1].identity,
            relation=declaration.relation_ids[0],
            basis="   ",
            owner=declaration.artifact_id,
            origin="test",
        )


# --- URKE-L-26 research ------------------------------------------------------------------


def test_l26_unresolved_generates_research(probe):
    assert contract.unresolved_generates_research(probe) == []


def test_l26_research_carries_every_declared_facet(store, declaration):
    opened = research.open_research(
        store,
        natural_key="test/facets",
        question="what is unresolved?",
        owner=declaration.artifact_id,
        origin="test",
    )
    for facet in declaration.research_facets:
        assert facet in opened.payload


def test_l26_negative_research_without_a_question_is_refused(store, declaration):
    with pytest.raises(RecursiveKnowledgeError):
        research.open_research(
            store,
            natural_key="test/no-question",
            question="   ",
            owner=declaration.artifact_id,
            origin="test",
        )


# --- URKE-L-27 learning ------------------------------------------------------------------


def test_l27_learning_pipeline_cannot_be_bypassed(probe):
    assert contract.learning_pipeline_cannot_be_bypassed(probe) == []


def test_l27_negative_every_skip_is_refused(store, declaration):
    stages = [spec.identifier for spec in declaration.learning_stages]
    lesson = subjects.start_lesson(
        store, natural_key="test/skip", owner=declaration.artifact_id, origin="test"
    )
    for stage in stages[2:]:
        with pytest.raises(RecursiveKnowledgeError):
            subjects.advance(store, lesson.identity, to_stage=stage, basis="test")


def test_l27_the_full_pipeline_is_traversable(store, declaration):
    stages = [spec.identifier for spec in declaration.learning_stages]
    lesson = subjects.start_lesson(
        store, natural_key="test/full", owner=declaration.artifact_id, origin="test"
    )
    for stage in stages[1:]:
        subjects.advance(store, lesson.identity, to_stage=stage, basis="test")
    assert store.get(lesson.identity).payload["stage"] == stages[-1]


def test_l27_reversal_supersedes_rather_than_deletes(store, declaration):
    first = subjects.start_lesson(
        store, natural_key="test/reverse-a", owner=declaration.artifact_id, origin="test"
    )
    second = subjects.start_lesson(
        store, natural_key="test/reverse-b", owner=declaration.artifact_id, origin="test"
    )
    subjects.reverse_lesson(store, first.identity, by=second.identity, basis="test")
    assert store.has(first.identity)


# --- URKE-L-28 declared mechanisms -------------------------------------------------------


def test_l28_declared_mechanisms_are_live(probe):
    assert contract.declared_mechanisms_are_live_and_exercised(probe) == []


def test_l28_negative_a_missing_symbol_is_detected(declaration):
    broken = dataclasses.replace(
        declaration,
        substrate_elements=(
            dataclasses.replace(declaration.substrate_elements[0], symbol="not_a_symbol"),
        )
        + declaration.substrate_elements[1:],
    )
    forged = contract.Probe(declaration=broken, repo=repo_root())
    assert contract.declared_mechanisms_are_live_and_exercised(forged)


# --- URKE-L-29 architectural proposals ---------------------------------------------------


def test_l29_architectural_change_requires_a_governed_proposal(probe):
    assert contract.architectural_change_requires_a_governed_proposal(probe) == []


def test_l29_representability_is_measured(declaration):
    good = proposal.representability(
        declaration, state=declaration.initial_state, domain=declaration.domain_ids[0]
    )
    assert good["representable"] is True
    bad = proposal.representability(
        declaration, state="not-a-state", domain=declaration.domain_ids[0]
    )
    assert bad["representable"] is False
    assert bad["reason"]


@pytest.mark.parametrize(
    "omitted",
    [
        "capability_gained",
        "complexity_added",
        "governance_decision",
        "impact",
        "tradeoff_justification",
        "unrepresentable_because",
        "validation",
        "verification",
    ],
)
def test_l29_negative_an_incomplete_proposal_is_refused(store, declaration, omitted):
    payload = {
        "capability_gained": "stated",
        "complexity_added": "stated",
        "construct": f"test-{omitted}",
        "governance_decision": "stated",
        "impact": "stated",
        "tradeoff_justification": "stated",
        "unrepresentable_because": "stated",
        "validation": "stated",
        "verification": "stated",
    }
    payload[omitted] = "  "
    with pytest.raises(RecursiveKnowledgeError):
        proposal.propose(store, owner=declaration.artifact_id, **payload)


# --- URKE-L-30 / L-31 / L-32 -------------------------------------------------------------


def test_l30_representation_requires_no_understanding(probe):
    assert contract.representation_requires_no_understanding(probe) == []


def test_l31_unresolved_is_eligible_for_discovery(probe):
    assert contract.unresolved_is_eligible_for_discovery(probe) == []


def test_l31_settled_states_are_not_eligible(store, declaration):
    sample = store.all()[0]
    for identifier in declaration.settled_states:
        moved = (
            sample
            if identifier == sample.state
            else states.transition(
                declaration, sample, identifier, basis="test", actor="test", sequence=0
            )
        )
        assert states.eligible_for_discovery(declaration, moved) is False


def test_l32_stability_is_measured(probe):
    assert contract.stability_is_measured_and_instability_is_governed(probe) == []


# --- identity, evidence and the gate -----------------------------------------------------


def test_identity_is_deterministic_and_total(declaration):
    for key in ("a b c", "自然键-非拉丁文", "  padded  ", "punctuation!?,"):
        left = knowledge_id(
            declaration.universal_entity_class,
            key,
            namespace=declaration.namespace,
            key_domain=declaration.key_domain,
        )
        right = knowledge_id(
            declaration.universal_entity_class,
            key,
            namespace=declaration.namespace,
            key_domain=declaration.key_domain,
        )
        assert left == right
        assert left.startswith("UMK-")


def test_identity_refuses_an_empty_key(declaration):
    with pytest.raises(RecursiveKnowledgeError):
        knowledge_id(
            declaration.universal_entity_class,
            "   ",
            namespace=declaration.namespace,
            key_domain=declaration.key_domain,
        )


def test_evidence_payload_is_complete(declaration, store, report):
    payload = evidence.build(declaration, report, evidence.render_ledger(store))
    evidence.assert_complete(declaration, payload)
    assert payload["observed_at"]


def test_evidence_refuses_an_incomplete_payload(declaration, report):
    with pytest.raises(RecursiveKnowledgeError):
        evidence.assert_complete(declaration, {"report": report})


def test_gate_metrics_exit_open():
    assert gate.main(["--metrics"]) == gate.EXIT_OPEN


def test_gate_faults_on_an_absent_declaration(tmp_path):
    assert gate.main(["--gate", "--quiet", "--repository", str(tmp_path)]) == gate.EXIT_FAULT


def test_gate_reports_every_declared_law(report, declaration):
    assert report["counts"]["laws"] == len(declaration.laws)
    assert {row["law_id"] for row in report["laws"]} == {law.law_id for law in declaration.laws}


def test_every_declared_law_has_an_implemented_check(declaration):
    for law in declaration.laws:
        assert law.check in contract.LAW_CHECKS


def test_report_carries_no_clock_or_machine_path(report):
    rendered = str(report)
    assert repo_root() not in rendered
    for marker in ("T00:", "T01:", "T02:"):
        assert marker not in rendered


# --- certification identity completeness -----------------------------------------------------
#
# The defect UEC-000001 measured in `engine/construct` was present here too, and worse: the
# digest projected thirteen keys and left 101 of 115 parsed fields outside the identity
# entirely. Flipping `blocking` on URKE-L-01 — the flag `contract.py` reads to choose OPEN or
# CLOSED — left the digest byte-identical at af30af45…, so one identity certified two
# declarations that reached opposite verdicts.
#
# The payload is now derived from `dataclasses.fields`, so inclusion is the default. These tests
# hold BOTH halves of the property: a semantic edit must move the identity, and the exclusion
# list must be neither silently widened nor left stale.


def _urke_document() -> dict:
    path = os.path.join(repo_root(), "00-MASTER", "URKE-000001", "urke-declaration.json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _urke_identity(document: dict) -> str:
    return content_hash(parse(document, source="test").digest_payload())


URKE_SEMANTIC_MUTATIONS: dict[str, object] = {
    "flip a law's blocking flag": lambda d: d["laws"][0].__setitem__(
        "blocking", not d["laws"][0]["blocking"]
    ),
    "rewrite a law's statement": lambda d: d["laws"][0].__setitem__("statement", "something else"),
    "rebind a law to another check": lambda d: d["laws"][0].__setitem__("check", "other_check"),
    "change the declared authority": lambda d: d.__setitem__("authority", "SOMETHING ELSE"),
    "change the declared version": lambda d: d.__setitem__("version", "9.9.9"),
    "change the constitutional superior": lambda d: d.__setitem__(
        "constitutional_superior", "SOMEBODY ELSE"
    ),
}


@pytest.mark.parametrize("name", sorted(URKE_SEMANTIC_MUTATIONS))
def test_every_semantic_mutation_moves_the_certification_identity(name: str) -> None:
    """A value that can alter a verdict must be inside the identity that certifies it."""
    document = _urke_document()
    baseline = _urke_identity(copy.deepcopy(document))
    mutated = copy.deepcopy(document)
    URKE_SEMANTIC_MUTATIONS[name](mutated)
    assert _urke_identity(mutated) != baseline, (
        f"{name!r} changed the declaration's meaning and left the certification identity at "
        f"{baseline[:16]}…. The same digest now certifies two different declarations."
    )


def test_the_identity_is_independent_of_the_path_it_was_read_from() -> None:
    """The half that WAS asserted before, kept: a digest that changed with the reader would
    not be a digest of the declaration."""
    document = _urke_document()
    left = _urke_identity(copy.deepcopy(document))
    right = content_hash(
        parse(copy.deepcopy(document), source="/somewhere/else.json").digest_payload()
    )
    assert left == right


def test_the_identity_covers_every_parsed_field_except_the_declared_exclusions(
    declaration,
) -> None:
    """Inclusion is the default; an omission must be a declared, reasoned exclusion."""
    payload = declaration.digest_payload()
    parsed = {field.name for field in dataclasses.fields(declaration)}
    missing = parsed - set(payload)
    assert missing <= set(DIGEST_EXCLUSIONS), (
        "fields silently absent from the certification identity: "
        f"{sorted(missing - set(DIGEST_EXCLUSIONS))}"
    )
    for name, reason in DIGEST_EXCLUSIONS.items():
        assert reason.strip(), f"exclusion {name!r} states no reason"


def test_a_stale_exclusion_is_refused(declaration) -> None:
    """The other direction. An exclusion matching no field may silently widen later."""
    assert set(DIGEST_EXCLUSIONS) <= {field.name for field in dataclasses.fields(declaration)}


# --- law mutation resistance -------------------------------------------------------------
#
# MEASURED, NOT ASSUMED, AND THE MEASUREMENT WAS BAD. Every law check in `LAW_CHECKS` was
# replaced, one at a time, with `return []` — the `return True` of a law engine — and this suite
# was re-run against each mutant in an isolated worktree. TWENTY-ONE OF THIRTY-TWO SURVIVED. Two
# thirds of this capability's laws could be deleted outright while the gate reported OPEN, every
# workflow stayed green, and this file passed.
#
# The cause is a single habit visible throughout the tests above: `assert contract.law(probe) ==
# []`. That asserts the law HOLDS, which is the half a neutered law satisfies trivially. Nothing
# asserted that any law could say NO. These laws are unusually good at forging their own hostile
# states internally — and that is exactly why the gap was invisible, because deleting the
# function deletes its internal forgery too, and no external observer notices.
#
# A gate cannot close this. A law reporting no violations is indistinguishable, from inside the
# gate, from a law that holds. The suite is the only possible detector, so each test below puts
# the law in a state where it MUST refuse and asserts that it does. Sixteen forge the
# declaration; five forge the collaborator the law delegates its refusal to, because that is
# where the property actually lives.

_URKE_DECLARATION_PATH = os.path.join(
    repo_root(), "00-MASTER", "URKE-000001", "urke-declaration.json"
)


def _forged(mutate) -> contract.Probe:
    """A probe over a deliberately damaged declaration, measured against the real repository."""
    document = json.loads(open(_URKE_DECLARATION_PATH, encoding="utf-8").read())
    mutate(document)
    return contract.Probe(declaration=parse(document, source="test"), repo=repo_root())


class _EmptyLedger(KnowledgeLedger):
    """A ledger that admits nothing. Several laws exist to notice exactly this."""

    def all(self):
        return ()

    def of_profile(self, *args, **kwargs):
        return ()


def _probe_with_an_empty_ledger() -> contract.Probe:
    declaration = load_declaration()

    class Forged(contract.Probe):
        __slots__ = ()

        def fresh_ledger(self):
            return _EmptyLedger(self.declaration)

        def seeded(self):
            return _EmptyLedger(self.declaration)

    return Forged(declaration=declaration, repo=repo_root())


# --- sixteen laws forged through the declaration -------------------------------------------

DECLARATION_FORGERIES = {
    "every_identified_unknown_is_governed": (
        lambda d: d["gaps"].__setitem__("residual", "not-a-declared-class"),
        "could not be admitted",
    ),
    "residual_is_representable": (
        lambda d: d["relations"].__setitem__("residual", "not-a-declared-relation"),
        "residual relation is not declared",
    ),
    "profile_requirements_are_enforced": (
        lambda d: d["profiles"]["seed"][0]
        .setdefault("required_attributes", [])
        .append("an_attribute_nothing_reads"),
        "which nothing can read",
    ),
    "no_state_is_terminal": (
        lambda d: d["states"]["seed"][0].__setitem__("successors", []),
        "dead end",
    ),
    "future_domain_is_admissible": (
        lambda d: d["future_domain_subjects"][0].__setitem__("admission", "admit_nothing_at_all"),
        "could not be admitted",
    ),
    "discovery_never_mutates_constitutional_truth": (
        lambda d: d["discovery"]["forbidden_write_calls"].append("append"),
        "which is a declared write",
    ),
    "worlds_are_data_driven": (
        lambda d: d["temporal"].__setitem__("exempt_modules", []),
        "embeds the temporal or spatial literal",
    ),
    "bound_vocabulary_is_neither_copied_nor_narrowed": (
        lambda d: d["bound_vocabularies"]["ucon_unknown_classes"].pop(),
        "no declared binding reaches it",
    ),
    "reality_parity_and_review_are_enforced": (
        lambda d: d["laws"][0].__setitem__("blocking", False),
        "is non-blocking",
    ),
    "expressiveness_is_preserved_within_bounds": (
        lambda d: d["primitives"].__setitem__("bound", 1),
        "exceed the bound",
    ),
    "relationships_carry_governance": (
        lambda d: d["entity_classes"].__setitem__("link", d["entity_classes"]["universal"]),
        "rather than its own",
    ),
    "unresolved_is_eligible_for_discovery": (
        lambda d: d["states"].__setitem__("settled", []),
        "eligibility would be vacuous",
    ),
    "stability_is_measured_and_instability_is_governed": (
        lambda d: d["stability"].__setitem__("exempt", ["a-mechanism"]),
        "exempt from review",
    ),
}


@pytest.mark.parametrize("law", sorted(DECLARATION_FORGERIES))
def test_every_law_refuses_a_declaration_that_violates_it(law: str) -> None:
    """The mutant `law -> []` dies here, for each law a declaration forgery can reach."""
    mutate, expected = DECLARATION_FORGERIES[law]
    violations = getattr(contract, law)(_forged(mutate))
    assert violations, f"{law} accepted a declaration that violates it"
    assert any(
        expected in str(item) for item in violations
    ), f"{law} refused, but for a different reason than the forgery: {violations[:2]}"


# --- three laws forged by emptying the ledger ----------------------------------------------

EMPTY_LEDGER_FORGERIES = {
    "disclosed_gaps_are_themselves_governed": "is not admitted into the ledger",
    "evolution_is_one_traceable_mechanism": "not reconstructible",
    "representation_requires_no_understanding": "did not become a research subject",
}


@pytest.mark.parametrize("law", sorted(EMPTY_LEDGER_FORGERIES))
def test_every_law_refuses_a_ledger_that_admitted_nothing(law: str) -> None:
    """A law quantified over an empty ledger must say so rather than hold over nothing."""
    violations = getattr(contract, law)(_probe_with_an_empty_ledger())
    assert violations, f"{law} held over a ledger that admitted nothing"
    assert any(EMPTY_LEDGER_FORGERIES[law] in str(item) for item in violations), violations[:2]


# --- five laws forged at the collaborator they delegate their refusal to --------------------


def test_l11_refuses_discovery_that_does_not_converge(
    probe, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second pass that keeps finding things is a walk with no fixed point."""
    monkeypatch.setattr(discovery, "discover", lambda store: ["a finding that never stops"])
    violations = contract.discovery_reaches_a_fixed_point(probe)
    assert violations
    assert any("does not converge" in str(item) for item in violations)


def test_l11_refuses_discovery_that_is_inert(probe, monkeypatch: pytest.MonkeyPatch) -> None:
    """The other half. A walk that finds nothing on a seeded ledger has stopped looking."""
    monkeypatch.setattr(discovery, "discover", lambda store: [])
    violations = contract.discovery_reaches_a_fixed_point(probe)
    assert violations
    assert any("inert" in str(item) for item in violations)


def test_l27_refuses_a_pipeline_that_permits_a_skip(probe, monkeypatch: pytest.MonkeyPatch) -> None:
    """The law's whole claim is that a stage cannot be skipped. Make the skip succeed."""
    real = subjects.advance
    monkeypatch.setattr(
        subjects,
        "advance",
        lambda store, identity, *, to_stage, basis: real(
            store, identity, to_stage=to_stage, basis=basis
        )
        if _in_order(store, identity, to_stage)
        else store.get(identity),
    )
    violations = contract.learning_pipeline_cannot_be_bypassed(probe)
    assert violations
    assert any(
        "was not refused" in str(item) or "advancing straight to" in str(item)
        for item in violations
    )


def _in_order(store, identity, to_stage) -> bool:
    """True only for a legitimate one-step move, so every skip silently succeeds instead."""
    declaration = store.declaration
    stages = [spec.identifier for spec in declaration.learning_stages]
    current = str(store.get(identity).payload.get("stage") or stages[0])
    return stages.index(to_stage) == stages.index(current) + 1


def test_l05_refuses_a_gap_that_closes_without_its_criteria(
    probe, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Closure with unsatisfied criteria must be refused. Make it succeed; the law must say so."""
    real = subjects.close_gap
    monkeypatch.setattr(
        subjects,
        "close_gap",
        lambda store, identity, *, basis, actor: real(
            store, identity, basis=basis, actor=actor, _force=True
        )
        if "_force" in real.__code__.co_varnames
        else store.get(identity),
    )
    violations = contract.gap_closure_and_review_are_governed(probe)
    assert violations
    assert any("was not refused" in str(item) or "criteri" in str(item) for item in violations)


def test_l29_refuses_a_proposal_mechanism_that_accepts_an_incomplete_proposal(
    probe, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An incomplete proposal must be refused. Make `propose` accept anything."""
    monkeypatch.setattr(proposal, "propose", lambda store, **kwargs: None)
    violations = contract.architectural_change_requires_a_governed_proposal(probe)
    assert violations
    assert any("was not refused" in str(item) or "missing" in str(item) for item in violations)


def test_l24_refuses_axes_that_are_not_independent(probe, monkeypatch: pytest.MonkeyPatch) -> None:
    """Moving one axis must move no other. Make it move them all."""
    real = states.with_axis

    def coupled(declaration, entity, axis, value):
        moved = real(declaration, entity, axis, value)
        other = next((s for s in declaration.lifecycle_axes if s.axis != axis), None)
        if other is None:
            return moved
        return real(declaration, moved, other.axis, other.values[-1])

    monkeypatch.setattr(states, "with_axis", coupled)
    violations = contract.lifecycle_axes_are_independent(probe)
    assert violations
    assert any("they are not" in str(item) or "did not take" in str(item) for item in violations)


def test_l33_vocabulary_is_not_hardcoded_fails_in_both_directions() -> None:
    """The predicate must catch a decision and spare a coincidence, or it is worth nothing.

    This law replaced an inline heredoc in urke-gate.yml whose predicate flagged EVERY string
    equal to a vocabulary member. The members are ordinary words — ``identity``, ``governance``
    and ``verification`` are all domain ids — so every one of its seven findings was a false
    positive, and a detector that cannot spare can never honestly reach its floor
    (UZX-000001). Both directions are pinned here as source snippets fed to the predicate.
    """
    import ast

    members = {"identity", "governance", "verification"}

    def decides(source: str) -> bool:
        return any(
            contract._vocabulary_decisions(node, members) for node in ast.walk(ast.parse(source))
        )

    must_catch = (
        'if kind == "identity":\n    pass\n',
        'if kind in ("identity", "governance"):\n    pass\n',
        'DOMAINS = ("identity", "governance")\n',
    )
    must_not_catch = (
        'd = {"identity": self.identity}\n',
        'f(event="verification")\n',
        'm = {"identity": lambda e: e.identity}\n',
    )
    for source in must_catch:
        assert decides(source), f"predicate cannot catch: {source!r}"
    for source in must_not_catch:
        assert not decides(source), f"predicate wrongly catches: {source!r}"


def test_l33_the_engine_hardcodes_no_vocabulary(probe) -> None:
    """And the live measurement, which is what the CI heredoc was actually asserting."""
    assert contract.vocabulary_is_not_hardcoded(probe) == []


def test_every_law_check_is_named_by_this_suite() -> None:
    """The class-level guard. A law arriving without a forged-violation test fails HERE.

    The twenty-one survivors were not found by reading the code; they were found by neutering
    every law in turn and re-running this suite in a worktree. That experiment is expensive and
    nobody will run it per commit, so the cheap invariant it implies is enforced instead: a law
    this file never names cannot have a test that exercises it, and a law nobody exercises is
    one nobody has shown can fail.

    Naming is necessary, not sufficient. It is the strongest property available in-process, and
    it closes the door the survivors came through.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    unnamed = sorted(name for name in contract.LAW_CHECKS if name not in source)
    assert not unnamed, f"law checks this suite never names: {unnamed}"


# --- the refusal branches of the bound laws -------------------------------------------------
#
# Every law below holds on the live declaration, so only its "holds" path ran and its REFUSAL
# path was measured by nothing. UEC-L-05 states the principle these tests answer: a detector
# with no failing case is a detector nobody has shown can fail. Each test therefore drives one
# violation and asserts the message that violation produces, rather than asserting that some
# problem was reported — a test that accepted any problem would pass on the wrong one.


def _forge(declaration, **changes):
    """The declaration with one field replaced, probed against the real repository."""
    return contract.Probe(declaration=dataclasses.replace(declaration, **changes), repo=repo_root())


def test_a_primitive_count_over_its_bound_is_refused(declaration):
    problems = contract.expressiveness_is_preserved_within_bounds(
        _forge(declaration, primitive_bound=1)
    )
    assert any("primitives exceed the bound of 1" in p for p in problems), problems


def test_an_entity_class_count_over_its_bound_is_refused(declaration):
    problems = contract.expressiveness_is_preserved_within_bounds(
        _forge(declaration, entity_class_bound=1)
    )
    assert any("entity classes exceed the bound of 1" in p for p in problems), problems


def test_a_state_count_over_its_bound_is_refused(declaration):
    problems = contract.expressiveness_is_preserved_within_bounds(
        _forge(declaration, state_bound=1)
    )
    assert any("states exceed the bound of 1" in p for p in problems), problems


def test_a_catalogue_expressing_no_more_than_its_primitives_is_refused(declaration):
    # The catalogue must compose MORE conditions than it has primitives, or it has added
    # vocabulary without adding expressiveness.
    problems = contract.expressiveness_is_preserved_within_bounds(
        _forge(declaration, conditions=declaration.conditions[:1])
    )
    assert any("no more conditions than there are primitives" in p for p in problems), problems


def test_a_residual_relation_the_declaration_does_not_carry_is_refused(declaration):
    problems = contract.residual_is_representable(
        _forge(declaration, residual_relation="not-a-declared-relation")
    )
    assert any("residual relation is not declared" in p for p in problems), problems


def test_an_undeclared_residual_context_kind_is_reported(declaration):
    kept = tuple(
        k for k in declaration.context_kinds if k.identifier != declaration.residual_context_kind
    )
    problems = contract.residual_is_representable(_forge(declaration, context_kinds=kept))
    assert any("residual context kind is not declared" in p for p in problems), problems


def test_an_undeclared_residual_domain_is_reported(declaration):
    problems = contract.residual_is_representable(
        _forge(declaration, residual_domain="not-a-declared-domain")
    )
    assert any("residual domain is not declared" in p for p in problems), problems


def test_an_inadmissible_residual_gap_class_is_reported(declaration):
    problems = contract.residual_is_representable(
        _forge(declaration, residual_gap_class="not-a-declared-gap-class")
    )
    assert any("residual gap class cannot be admitted" in p for p in problems), problems


# --- URKE-L-15: the ledger-integrity refusals ----------------------------------------------
#
# These laws do not read the declaration, they interrogate the LEDGER, so a mutated
# declaration cannot reach them. Each test substitutes a ledger that violates exactly one
# property and asserts the law names that property. The substitute delegates everything it
# does not override to a real KnowledgeLedger, so a law reaching any other behaviour reaches
# the genuine one rather than a stub that agrees with the test.


class _Doctored:
    """A real ledger with named behaviours replaced."""

    def __init__(self, real, **overrides):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_overrides", overrides)

    def __getattr__(self, name):
        overrides = object.__getattribute__(self, "_overrides")
        if name in overrides:
            return overrides[name]
        return getattr(object.__getattribute__(self, "_real"), name)


class _ProbeWith(contract.Probe):
    """A probe whose fresh_ledger yields the doctored store."""

    def __init__(self, declaration, store):
        super().__init__(declaration=declaration, repo=repo_root())
        object.__setattr__(self, "_doctored", store)

    def fresh_ledger(self):
        return object.__getattribute__(self, "_doctored")


def _ledger_probe(declaration, **overrides):
    return _ProbeWith(declaration, _Doctored(KnowledgeLedger(declaration), **overrides))


def test_a_ledger_that_does_not_reconcile_is_refused(declaration):
    real = KnowledgeLedger(declaration)
    bad = dict(real.verify())
    bad["status"] = "FAIL"
    probe = _ledger_probe(declaration, verify=lambda: bad)
    problems = contract.nothing_admitted_can_silently_disappear(probe)
    assert any("does not reconcile" in p for p in problems), problems


def test_admissions_that_do_not_match_journal_entries_are_refused(declaration):
    real = KnowledgeLedger(declaration)
    bad = dict(real.verify())
    bad["journal_entries"] = bad["admitted"] + 1
    probe = _ledger_probe(declaration, verify=lambda: bad)
    problems = contract.nothing_admitted_can_silently_disappear(probe)
    assert any("journal entries" in p for p in problems), problems


@pytest.mark.parametrize("forbidden", ["remove", "delete", "pop", "clear", "discard"])
def test_a_ledger_exposing_a_removal_path_is_refused(declaration, forbidden):
    # Append-only is a property of the INTERFACE, not only of the data: a ledger that offers
    # a removal method has already lost it, whether or not anything calls it.
    probe = _ledger_probe(declaration, **{forbidden: lambda *a, **k: None})
    problems = contract.nothing_admitted_can_silently_disappear(probe)
    assert any(f"removal path named {forbidden!r}" in p for p in problems), problems


def test_a_superseded_subject_that_stops_being_retrievable_is_refused(declaration):
    probe = _ledger_probe(declaration, has=lambda identity: False)
    problems = contract.nothing_admitted_can_silently_disappear(probe)
    assert any("stopped being retrievable" in p for p in problems), problems


def test_a_chain_broken_by_supersession_is_refused(declaration):
    probe = _ledger_probe(declaration, chain_is_intact=lambda: False)
    problems = contract.nothing_admitted_can_silently_disappear(probe)
    assert any("chain broke on a supersession" in p for p in problems), problems


def test_superseding_by_an_unrecorded_subject_must_refuse(declaration):
    # The law asserts a REFUSAL, so the violation is a ledger that quietly accepts.
    real = KnowledgeLedger(declaration)
    probe = _ledger_probe(declaration, supersede=lambda *a, **k: None, has=real.has)
    problems = contract.nothing_admitted_can_silently_disappear(probe)
    assert any("superseding by an unrecorded subject" in p for p in problems), problems


def test_reading_an_unrecorded_identity_must_refuse(declaration):
    # A miss that returns None instead of raising lets absence pass as an answer.
    probe = _ledger_probe(declaration, get=lambda identity: None)
    problems = contract.nothing_admitted_can_silently_disappear(probe)
    assert any("a miss could pass as absent" in p for p in problems), problems


def test_a_declared_residual_domain_that_cannot_be_composed_is_reported(declaration, monkeypatch):
    """The guard above proves the domain is DECLARED; this proves the law survives it failing.

    Measured: all 31 declared domains compose with the declared initial state and no
    qualifiers, so no real declaration reaches this handler today. It is not dead code — a
    domain added later that requires a qualifier would raise here — so the handler is tested
    by injecting the failure its contract exists to absorb, rather than deleted because
    today's data happens not to trigger it.
    """
    from engine.recursive_knowledge import composition as composition_module

    def _refuse(*args, **kwargs):
        raise RecursiveKnowledgeError("composition refused for the test")

    monkeypatch.setattr(composition_module, "express", _refuse)
    problems = contract.residual_is_representable(_forge(declaration))
    assert any("residual domain cannot be expressed" in p for p in problems), problems


# --- URKE-L-04: the append-only refusals ----------------------------------------------------
#
# The law asserts properties of what `subjects.add_resolution` and `add_verification` RETURN,
# so the violation has to come from those operations. Each test replaces one of them with a
# wrapper that calls the real function and then breaks exactly one property of its result, so
# everything the law does apart from the property under test is genuine.


def _wrap(monkeypatch, name, mangle):
    real = getattr(subjects, name)

    def wrapper(*args, **kwargs):
        return mangle(real(*args, **kwargs))

    monkeypatch.setattr(subjects, name, wrapper)


def test_a_resolution_step_that_does_not_append_is_refused(declaration, monkeypatch):
    _wrap(monkeypatch, "add_resolution", lambda s: dataclasses.replace(s, resolution_history=()))
    problems = contract.histories_are_append_only(_forge(declaration))
    assert any("resolution step did not append" in p for p in problems), problems


def test_a_resolution_step_that_rewrites_earlier_entries_is_refused(declaration, monkeypatch):
    def mangle(subject):
        history = subject.resolution_history
        rewritten = (dataclasses.replace(history[0], action="rewritten"),) + history[1:]
        return dataclasses.replace(subject, resolution_history=rewritten)

    _wrap(monkeypatch, "add_resolution", mangle)
    problems = contract.histories_are_append_only(_forge(declaration))
    assert any("altered the earlier entries" in p for p in problems), problems


def test_a_verification_event_that_does_not_append_is_refused(declaration, monkeypatch):
    _wrap(
        monkeypatch, "add_verification", lambda s: dataclasses.replace(s, verification_history=())
    )
    problems = contract.histories_are_append_only(_forge(declaration))
    assert any("verification event did not append" in p for p in problems), problems


def test_a_hollow_verification_that_is_accepted_is_refused(declaration, monkeypatch):
    # The law asserts a REFUSAL: a verification with no assumptions or no limitations must be
    # rejected. The violation is therefore an `add_verification` that accepts one.
    real = subjects.add_verification

    def permissive(*args, **kwargs):
        if not kwargs.get("assumptions") or not kwargs.get("limitations"):
            return real(
                *args,
                **{**kwargs, "assumptions": ("assumed",), "limitations": ("bounded",)},
            )
        return real(*args, **kwargs)

    monkeypatch.setattr(subjects, "add_verification", permissive)
    problems = contract.histories_are_append_only(_forge(declaration))
    assert any("a verification declaring no assumptions" in p for p in problems), problems
    assert any("a verification declaring no limitations" in p for p in problems), problems


def test_a_transition_that_rewrites_earlier_state_history_is_refused(declaration, monkeypatch):
    real = states.transition

    def mangle(*args, **kwargs):
        moved = real(*args, **kwargs)
        history = moved.state_history
        rewritten = (dataclasses.replace(history[0], basis="rewritten"),) + history[1:]
        return dataclasses.replace(moved, state_history=rewritten)

    monkeypatch.setattr(states, "transition", mangle)
    problems = contract.histories_are_append_only(_forge(declaration))
    assert any("altered the earlier state history" in p for p in problems), problems


# --- URKE-L-09: the open-vocabulary refusals -------------------------------------------------


def test_a_member_that_cannot_be_exercised_is_reported(declaration, monkeypatch):
    def refuse(*args, **kwargs):
        raise RecursiveKnowledgeError("admission refused for the test")

    monkeypatch.setattr(admission, "exercise", refuse)
    problems = contract.data_extension_needs_no_redesign(_forge(declaration))
    assert any("could not be exercised" in p for p in problems), problems


def test_an_admitted_subject_the_ledger_did_not_retain_is_refused(declaration, monkeypatch):
    real = admission.exercise

    def forgetful(store, name, **kwargs):
        extended, entity = real(store, name, **kwargs)
        # The admission succeeds and the ledger forgets it: exactly the loss the law exists
        # to catch, and invisible to a test that only checked `exercise` returned.
        object.__setattr__(entity, "identity", entity.identity + "-never-recorded")
        return extended, entity

    monkeypatch.setattr(admission, "exercise", forgetful)
    problems = contract.data_extension_needs_no_redesign(_forge(declaration))
    assert any("the ledger did not retain" in p for p in problems), problems


def test_an_admission_that_returns_no_declaration_is_refused(declaration, monkeypatch):
    real = admission.exercise
    monkeypatch.setattr(admission, "exercise", lambda *a, **k: (None, real(*a, **k)[1]))
    problems = contract.data_extension_needs_no_redesign(_forge(declaration))
    assert any("returned no declaration" in p for p in problems), problems


def test_admitting_a_member_that_changes_the_package_is_refused(declaration, monkeypatch):
    # The vocabulary is data, so admitting a member nobody declared must move no byte of the
    # package. The violation is a fingerprint that moves.
    calls = {"n": 0}

    def drifting(self):
        calls["n"] += 1
        return f"fingerprint-{calls['n']}"

    monkeypatch.setattr(contract.Probe, "fingerprint", drifting)
    problems = contract.data_extension_needs_no_redesign(_forge(declaration))
    assert any("changed this package" in p for p in problems), problems


# --- URKE-L-19: the governance refusals -----------------------------------------------------


def test_an_unreachable_construct_foundation_is_a_fault_not_a_verdict(declaration, monkeypatch):
    # A superior that cannot be reached is not "no problems found": it is no verdict at all,
    # which is why this law raises rather than returning an empty list.
    def refuse(store):
        raise RecursiveKnowledgeError("bridge refused for the test")

    monkeypatch.setattr(bridge, "govern", refuse)
    with pytest.raises(contract.ContractError, match="construct foundation could not be reached"):
        contract.no_subject_exists_outside_governance(_forge(declaration))


def test_a_subject_reaching_no_active_disposition_is_refused(declaration, monkeypatch):
    real = bridge.govern
    monkeypatch.setattr(
        bridge,
        "govern",
        lambda store: {**real(store), "ungoverned": ("a-subject-nobody-dispositioned",)},
    )
    problems = contract.no_subject_exists_outside_governance(_forge(declaration))
    assert any("reached no active disposition" in p for p in problems), problems


def test_not_presenting_every_subject_for_disposition_is_refused(declaration, monkeypatch):
    real = bridge.govern
    monkeypatch.setattr(bridge, "govern", lambda store: {**real(store), "presented_count": 0})
    problems = contract.no_subject_exists_outside_governance(_forge(declaration))
    assert any("not every subject was presented" in p for p in problems), problems


def test_recording_no_disposition_at_all_is_refused(declaration, monkeypatch):
    real = bridge.govern
    monkeypatch.setattr(bridge, "govern", lambda store: {**real(store), "dispositions": ()})
    problems = contract.no_subject_exists_outside_governance(_forge(declaration))
    assert any("nothing was actually governed" in p for p in problems), problems


# --- URKE-L-32 companion: the stability refusals ---------------------------------------------


def test_a_broken_chain_is_reported_as_an_unstable_measurement(declaration):
    probe = _ledger_probe(declaration, chain_is_intact=lambda: False)
    problems = contract.stability_is_measured_and_instability_is_governed(probe)
    assert any("'chain_integrity' does not hold" in p for p in problems), problems


def test_a_population_that_does_not_reconcile_is_reported(declaration):
    real = KnowledgeLedger(declaration)
    bad = dict(real.verify())
    bad["reconciles"] = False
    probe = _ledger_probe(declaration, verify=lambda: bad)
    problems = contract.stability_is_measured_and_instability_is_governed(probe)
    assert any("'population_reconciles' does not hold" in p for p in problems), problems


def test_detecting_no_instability_on_an_unstable_ledger_is_refused(declaration, monkeypatch):
    monkeypatch.setattr(discovery, "discover", lambda store: [])
    problems = contract.stability_is_measured_and_instability_is_governed(_forge(declaration))
    assert any("no instability was detected" in p for p in problems), problems


def test_an_instability_not_admitted_as_a_governed_subject_is_refused(declaration, monkeypatch):
    real = discovery.discover

    def misclassified(store):
        found = real(store)
        return [dataclasses.replace(found[0], classification="not-the-finding-role"), *found[1:]]

    monkeypatch.setattr(discovery, "discover", misclassified)
    problems = contract.stability_is_measured_and_instability_is_governed(_forge(declaration))
    assert any("not admitted as a governed subject" in p for p in problems), problems


def test_a_stability_property_naming_no_measurement_is_refused(declaration):
    unmeasured = ({"property": "invented", "measured_by": ""},)
    problems = contract.stability_is_measured_and_instability_is_governed(
        _forge(declaration, stability_properties=unmeasured)
    )
    assert any("names no measurement" in p for p in problems), problems


def test_a_stability_mechanism_declared_exempt_from_review_is_refused(declaration):
    problems = contract.stability_is_measured_and_instability_is_governed(
        _forge(declaration, stability_exemptions=("somebody",))
    )
    assert any("declared exempt from review" in p for p in problems), problems


# --- URKE-L-20 companion: the binding refusals ------------------------------------------------


def test_an_unreadable_construct_foundation_declaration_is_a_fault(declaration, tmp_path):
    # A superior that cannot be read yields no verdict, so the law raises rather than
    # returning "no problems" over a declaration it never saw.
    forged = contract.Probe(declaration=declaration, repo=str(tmp_path))
    with pytest.raises(
        contract.ContractError, match="construct foundation declaration cannot be read"
    ):
        contract.bound_vocabulary_is_neither_copied_nor_narrowed(forged)


def test_a_reachability_row_naming_an_undeclared_member_is_refused(declaration):
    rows = (
        {"ucon_class": "some-unknown-class", "reached_by": "not-a-declared-member"},
        *declaration.ucon_unknown_bindings,
    )
    problems = contract.bound_vocabulary_is_neither_copied_nor_narrowed(
        _forge(declaration, ucon_unknown_bindings=rows)
    )
    assert any("not a declared member" in p for p in problems), problems


def test_an_unknown_class_no_binding_reaches_is_refused(declaration):
    problems = contract.bound_vocabulary_is_neither_copied_nor_narrowed(
        _forge(declaration, ucon_unknown_bindings=())
    )
    assert any("no declared binding" in p for p in problems), problems


# --- URKE-L-28: the live-mechanism refusals ---------------------------------------------------


def test_a_substrate_naming_an_unimportable_module_is_refused(declaration):
    broken = (
        dataclasses.replace(
            declaration.substrate_elements[0], module="engine/recursive_knowledge/no_such_module.py"
        ),
        *declaration.substrate_elements[1:],
    )
    problems = contract.declared_mechanisms_are_live_and_exercised(
        _forge(declaration, substrate_elements=broken)
    )
    assert any("cannot be imported" in p for p in problems), problems


def test_a_substrate_naming_a_symbol_that_does_not_exist_is_refused(declaration):
    broken = (
        dataclasses.replace(declaration.substrate_elements[0], symbol="NoSuchSymbol"),
        *declaration.substrate_elements[1:],
    )
    problems = contract.declared_mechanisms_are_live_and_exercised(
        _forge(declaration, substrate_elements=broken)
    )
    assert any("which does not exist" in p for p in problems), problems


def test_a_future_capability_requiring_undeclared_substrate_is_refused(declaration):
    extra = (
        *declaration.future_capabilities,
        type(declaration.future_capabilities[0])(
            identifier="invented-capability", requires=("URKE-S-NOT-DECLARED",)
        ),
    )
    problems = contract.declared_mechanisms_are_live_and_exercised(
        _forge(declaration, future_capabilities=extra)
    )
    assert any("requires undeclared substrate" in p for p in problems), problems


def test_a_substrate_nothing_requires_is_refused(declaration):
    extra = (
        *declaration.substrate_elements,
        dataclasses.replace(declaration.substrate_elements[0], substrate_id="URKE-S-UNREQUIRED"),
    )
    problems = contract.declared_mechanisms_are_live_and_exercised(
        _forge(declaration, substrate_elements=extra)
    )
    assert any("nothing requires it" in p for p in problems), problems


# --- URKE-L-22/27/28/29: the parity and review refusals ---------------------------------------


def test_a_reality_probe_divergence_is_reported(declaration, monkeypatch):
    real = discovery.probe_all
    monkeypatch.setattr(
        discovery,
        "probe_all",
        lambda decl, repository=None: {
            **real(decl, repository=repository),
            "invented-probe": ("the world and the record disagree",),
        },
    )
    problems = contract.reality_parity_and_review_are_enforced(_forge(declaration))
    assert any("the world and the record disagree" in p for p in problems), problems


def test_not_performing_every_declared_probe_is_refused(declaration, monkeypatch):
    monkeypatch.setattr(discovery, "probe_all", lambda decl, repository=None: {})
    problems = contract.reality_parity_and_review_are_enforced(_forge(declaration))
    assert any("not every declared probe was performed" in p for p in problems), problems


def test_a_parity_layer_naming_an_unimplemented_measure_is_refused(declaration):
    broken = (
        dataclasses.replace(declaration.parity_layers[0], measured_by="no_such_measure"),
        *declaration.parity_layers[1:],
    )
    problems = contract.reality_parity_and_review_are_enforced(
        _forge(declaration, parity_layers=broken)
    )
    assert any("names an unimplemented measure" in p for p in problems), problems


def test_a_parity_layer_whose_evidence_is_absent_is_refused(declaration):
    broken = (
        dataclasses.replace(declaration.parity_layers[0], evidence="no/such/evidence.py"),
        *declaration.parity_layers[1:],
    )
    problems = contract.reality_parity_and_review_are_enforced(
        _forge(declaration, parity_layers=broken)
    )
    assert any("is absent" in p for p in problems), problems


def test_a_non_empty_review_exemption_list_is_refused(declaration):
    problems = contract.reality_parity_and_review_are_enforced(
        _forge(declaration, review_exemptions=("somebody",))
    )
    assert any("review exemption list is not empty" in p for p in problems), problems


def test_a_capability_carrying_no_review_obligation_of_its_own_is_refused(declaration):
    problems = contract.reality_parity_and_review_are_enforced(
        _forge(declaration, self_review_gap="not-a-disclosed-gap")
    )
    assert any("no review obligation of its own" in p for p in problems), problems


# --- URKE-L-29: the proposal refusals ----------------------------------------------------------


def test_an_expressible_condition_reported_unrepresentable_is_refused(declaration, monkeypatch):
    monkeypatch.setattr(proposal, "representability", lambda *a, **k: {"representable": False})
    problems = contract.architectural_change_requires_a_governed_proposal(_forge(declaration))
    assert any("reported unrepresentable" in p for p in problems), problems


def test_an_undeclared_state_reported_representable_is_refused(declaration, monkeypatch):
    monkeypatch.setattr(proposal, "representability", lambda *a, **k: {"representable": True})
    problems = contract.architectural_change_requires_a_governed_proposal(_forge(declaration))
    assert any("reported representable" in p for p in problems), problems


def test_a_complete_proposal_that_is_refused_is_itself_a_problem(declaration, monkeypatch):
    # The law measures both directions: a complete proposal must be ACCEPTED, so the
    # violation is a proposer that rejects one.
    def refuse(*args, **kwargs):
        raise RecursiveKnowledgeError("proposal refused for the test")

    monkeypatch.setattr(proposal, "propose", refuse)
    problems = contract.architectural_change_requires_a_governed_proposal(_forge(declaration))
    assert any("a complete proposal was refused" in p for p in problems), problems


def test_declaring_no_proposal_requirement_is_refused(declaration):
    problems = contract.architectural_change_requires_a_governed_proposal(
        _forge(declaration, proposal_requirements=())
    )
    assert any("no proposal requirement is declared" in p for p in problems), problems


def test_declaring_no_default_rule_is_refused(declaration):
    problems = contract.architectural_change_requires_a_governed_proposal(
        _forge(declaration, default_rule="")
    )
    assert any("no default rule is declared" in p for p in problems), problems


# --- the law selector -------------------------------------------------------------------------
#
# These three were written, passed, and were then deleted by a careless string splice in this
# same file; the loss surfaced only because `measure`'s selector lines reappeared as uncovered.
# Restored, and worth restoring: adr/0041's shape is a selector that matches nothing, measures
# nothing, and exits 0.


def test_a_law_selector_matching_nothing_is_a_fault():
    with pytest.raises(contract.ContractError, match="no declared law matches"):
        contract.measure(laws=["NOT-A-REAL-LAW"])


def test_a_law_selector_naming_a_check_rather_than_a_law_is_a_fault(declaration):
    # The dangerous half: a check name looks like a law selector and silently matched none.
    with pytest.raises(contract.ContractError, match="no declared law matches"):
        contract.measure(laws=[declaration.laws[0].check])


def test_selecting_one_law_measures_only_that_law(declaration):
    only = declaration.laws[0].law_id
    report = contract.measure(laws=[only])
    assert [row["law_id"] for row in report["laws"]] == [only]


def test_a_law_that_cannot_be_computed_is_a_fault_not_a_violation(declaration, monkeypatch):
    # A law whose check raises has produced no verdict. Reporting it as a violation would
    # convert "could not measure" into "measured and failed", which are different facts.
    first = declaration.laws[0]

    def explode(probe):
        raise RecursiveKnowledgeError("check exploded for the test")

    monkeypatch.setitem(contract.LAW_CHECKS, first.check, explode)
    with pytest.raises(contract.ContractError, match="could not be computed"):
        contract.measure(laws=[first.law_id])


# --- URKE-L-14: the evolution-coverage refusals -------------------------------------------------


def test_a_subject_that_cannot_evolve_is_reported(declaration, monkeypatch):
    def refuse(*args, **kwargs):
        raise RecursiveKnowledgeError("evolution refused for the test")

    monkeypatch.setattr(evolution, "evolve", refuse)
    problems = contract.evolution_covers_every_declared_subject(_forge(declaration))
    assert any("could not evolve through" in p for p in problems), problems


def test_an_operator_never_exercised_is_refused(declaration):
    # An operator nobody's subjects use is declared and dead.
    extra = (
        *declaration.operators,
        dataclasses.replace(declaration.operators[0], identifier="never-used-operator"),
    )
    problems = contract.evolution_covers_every_declared_subject(
        _forge(declaration, operators=extra)
    )
    assert any("never-used-operator' was never exercised" in p for p in problems), problems


def test_an_operator_naming_an_unimplemented_function_is_refused(declaration):
    broken = (
        dataclasses.replace(declaration.operators[0], implementation="no_such_operator"),
        *declaration.operators[1:],
    )
    problems = contract.evolution_covers_every_declared_subject(
        _forge(declaration, operators=broken)
    )
    assert any("names an unimplemented function" in p for p in problems), problems


# --- URKE-L-13: the traceable-evolution refusals -------------------------------------------------


@pytest.mark.parametrize("key", ["subject", "operator", "before", "after"])
def test_an_evolution_step_recording_no_field_is_refused(declaration, monkeypatch, key):
    real = evolution.evolve

    def hollow(*args, **kwargs):
        step = real(*args, **kwargs)
        return dataclasses.replace(step, payload={**step.payload, key: "  "})

    monkeypatch.setattr(evolution, "evolve", hollow)
    problems = contract.evolution_is_one_traceable_mechanism(_forge(declaration))
    assert any(f"records no {key}" in p for p in problems), problems


def test_an_evolution_step_recording_no_basis_is_refused(declaration, monkeypatch):
    real = evolution.evolve

    def unevidenced(*args, **kwargs):
        return dataclasses.replace(real(*args, **kwargs), evidence=())

    monkeypatch.setattr(evolution, "evolve", unevidenced)
    problems = contract.evolution_is_one_traceable_mechanism(_forge(declaration))
    assert any("records no basis as evidence" in p for p in problems), problems


def test_a_step_recording_no_change_must_be_refused(declaration, monkeypatch):
    # A before that equals its after records nothing, so accepting it is the violation.
    real = evolution.evolve

    def permissive(store, **kwargs):
        if kwargs.get("before") == kwargs.get("after"):
            kwargs = {**kwargs, "after": content_hash(["different-after"])}
        return real(store, **kwargs)

    monkeypatch.setattr(evolution, "evolve", permissive)
    problems = contract.evolution_is_one_traceable_mechanism(_forge(declaration))
    assert any("a step recording no change" in p for p in problems), problems


def test_a_chain_not_intact_after_evolution_is_refused(declaration):
    probe = _ledger_probe(declaration, chain_is_intact=lambda: False)
    problems = contract.evolution_is_one_traceable_mechanism(probe)
    assert any("chain is not intact after a recorded evolution" in p for p in problems), problems


def test_evolution_naming_a_subject_as_a_special_case_is_refused(declaration, monkeypatch):
    # One mechanism, no per-subject branch: a subject identifier appearing as a literal in
    # evolution.py is a special case by definition.
    identifier = declaration.evolution_subjects[0].identifier
    source = f"SPECIAL_CASE = {identifier!r}\n"
    monkeypatch.setattr(contract.Probe, "source", lambda self, name: source)
    problems = contract.evolution_is_one_traceable_mechanism(_forge(declaration))
    assert any("which is a special case" in p for p in problems), problems


# --- URKE-L-23/32: the composition refusals --------------------------------------------------


def test_a_condition_that_cannot_be_composed_is_reported(declaration, monkeypatch):
    from engine.recursive_knowledge import composition as composition_module

    def refuse(decl, condition):
        raise RecursiveKnowledgeError("composition refused for the test")

    monkeypatch.setattr(composition_module, "express_condition", refuse)
    problems = contract.expressiveness_is_preserved_within_bounds(_forge(declaration))
    assert any("cannot be composed" in p for p in problems), problems


def test_two_conditions_with_the_same_signature_are_refused(declaration, monkeypatch):
    # Two catalogue entries composing to one expression means the catalogue claims more
    # distinctions than it can express.
    from engine.recursive_knowledge import composition as composition_module

    monkeypatch.setattr(composition_module, "signature", lambda expression: "one-signature")
    problems = contract.expressiveness_is_preserved_within_bounds(_forge(declaration))
    assert any("catalogue collision" in p for p in problems), problems


# --- URKE-L-26: the research-generation refusals ------------------------------------------------


def test_a_gap_that_generates_no_research_subject_is_refused(declaration, monkeypatch):
    monkeypatch.setattr(research, "research_for", lambda store, identity: ())
    problems = contract.unresolved_generates_research(_forge(declaration))
    assert any("did not generate a research subject" in p for p in problems), problems


def test_a_research_subject_missing_a_declared_facet_is_refused(declaration, monkeypatch):
    real = research.open_research

    def stripped(*args, **kwargs):
        opened = real(*args, **kwargs)
        facet = declaration.research_facets[0]
        return dataclasses.replace(
            opened, payload={k: v for k, v in opened.payload.items() if k != facet}
        )

    monkeypatch.setattr(research, "open_research", stripped)
    problems = contract.unresolved_generates_research(_forge(declaration))
    assert any("carries no" in p for p in problems), problems


def test_a_contradiction_generating_the_wrong_consequence_count_is_refused(
    declaration, monkeypatch
):
    monkeypatch.setattr(subjects, "generate_consequences", lambda store, identity, owner: ())
    problems = contract.unresolved_generates_research(_forge(declaration))
    assert any("consequences and" in p for p in problems), problems


def test_a_reflexive_form_that_cannot_be_admitted_is_reported(declaration, monkeypatch):
    def refuse(*args, **kwargs):
        raise RecursiveKnowledgeError("relate refused for the test")

    monkeypatch.setattr(ledger_module, "relate", refuse)
    problems = contract.unresolved_generates_research(_forge(declaration))
    assert any("could not be admitted" in p for p in problems), problems


def test_admitting_reflexive_knowledge_that_changes_the_package_is_refused(
    declaration, monkeypatch
):
    calls = {"n": 0}

    def drifting(self):
        calls["n"] += 1
        return f"fingerprint-{calls['n']}"

    monkeypatch.setattr(contract.Probe, "fingerprint", drifting)
    problems = contract.unresolved_generates_research(_forge(declaration))
    assert any("changed this package" in p for p in problems), problems


# --- URKE-L-30: representation without understanding --------------------------------------------


def test_an_unintelligible_construct_refused_admission_is_reported(declaration, monkeypatch):
    # The law's claim is that the LEAST understood thing imaginable is still admissible.
    # Refusing it is the violation, and the law returns early because nothing follows from a
    # construct that never entered.
    real = subjects.record_gap

    def refuse_only_this_one(store, **kwargs):
        # Narrow on purpose: the ledger seeds itself through record_gap, so refusing every
        # call would break construction and never reach the law.
        if kwargs.get("natural_key") == "law30/not-understood":
            raise RecursiveKnowledgeError("admission refused for the test")
        return real(store, **kwargs)

    monkeypatch.setattr(subjects, "record_gap", refuse_only_this_one)
    problems = contract.representation_requires_no_understanding(_forge(declaration))
    assert any("refused admission" in p for p in problems), problems
    # The law returns early: nothing follows from a construct that never entered.
    assert len(problems) == 1, problems


def test_an_unintelligible_construct_reaching_no_disposition_is_refused(declaration, monkeypatch):
    real = bridge.govern

    def ungoverned(store):
        outcome = real(store)
        every = tuple(subject.identity for subject in store.all())
        return {**outcome, "ungoverned": every}

    monkeypatch.setattr(bridge, "govern", ungoverned)
    problems = contract.representation_requires_no_understanding(_forge(declaration))
    assert any("reached no disposition" in p for p in problems), problems


# --- URKE-L-22: the determinism refusals ---------------------------------------------------------


def test_two_ledgers_seeded_identically_that_differ_are_refused(declaration, monkeypatch):
    seen = {"n": 0}

    def drifting_digest(self):
        seen["n"] += 1
        return f"digest-{seen['n']}"

    monkeypatch.setattr(KnowledgeLedger, "digest", drifting_digest)
    problems = contract.measurement_is_deterministic(_forge(declaration))
    assert any("seeded from identical data differ" in p for p in problems), problems


def test_two_summaries_of_identical_ledgers_that_differ_are_refused(declaration, monkeypatch):
    seen = {"n": 0}

    def drifting_summary(self):
        seen["n"] += 1
        return {"summary": seen["n"]}

    monkeypatch.setattr(KnowledgeLedger, "summary", drifting_summary)
    problems = contract.measurement_is_deterministic(_forge(declaration))
    assert any("two summaries of identical ledgers differ" in p for p in problems), problems


def test_a_report_embedding_a_clock_is_refused(declaration, monkeypatch):
    # A timestamp in a report makes the report a function of when it ran rather than of the
    # bytes it measured, and two identical states would then disagree.
    monkeypatch.setattr(discovery, "report", lambda store: "measured at T00:00:00")
    problems = contract.measurement_is_deterministic(_forge(declaration))
    assert any("T00:'" in p or "T00:" in p for p in problems), problems


def test_a_report_embedding_the_repository_path_is_refused(declaration, monkeypatch):
    repo = repo_root()
    monkeypatch.setattr(discovery, "report", lambda store: f"measured under {repo}")
    problems = contract.measurement_is_deterministic(_forge(declaration))
    assert any("so it is not a function of the bytes" in p for p in problems), problems


def test_two_discovery_reports_over_identical_ledgers_that_differ_are_refused(
    declaration, monkeypatch
):
    seen = {"n": 0}

    def drifting_report(store):
        seen["n"] += 1
        return f"report-{seen['n']}"

    monkeypatch.setattr(discovery, "report", drifting_report)
    problems = contract.measurement_is_deterministic(_forge(declaration))
    assert any("two discovery reports" in p for p in problems), problems


# --- URKE-L-31: the eligibility refusals ---------------------------------------------------------


def test_a_settled_state_that_stays_eligible_is_refused(declaration, monkeypatch):
    # Eligibility comes from the lattice: a settled subject must not remain open to discovery,
    # or "settled" means nothing.
    monkeypatch.setattr(states, "eligible_for_discovery", lambda decl, entity: True)
    problems = contract.unresolved_is_eligible_for_discovery(_forge(declaration))
    assert any("is still eligible" in p for p in problems), problems


def test_an_unsettled_state_that_is_not_eligible_is_refused(declaration, monkeypatch):
    monkeypatch.setattr(states, "eligible_for_discovery", lambda decl, entity: False)
    problems = contract.unresolved_is_eligible_for_discovery(_forge(declaration))
    assert any("is not eligible for discovery" in p for p in problems), problems


def test_declaring_every_state_settled_is_refused(declaration):
    # If every state is settled nothing is ever eligible, and discovery has been switched off
    # by declaration rather than by argument.
    every = tuple(spec.identifier for spec in declaration.states)
    problems = contract.unresolved_is_eligible_for_discovery(
        _forge(declaration, settled_states=every)
    )
    assert any("every state is settled" in p for p in problems), problems


# --- URKE-L-20: the context refusals ------------------------------------------------------


def test_a_subject_naming_an_absent_context_is_refused(declaration):
    real = KnowledgeLedger(declaration)
    everything = real.all()
    orphan = dataclasses.replace(everything[0], context="a-context-nobody-recorded")

    class _Store:
        root_context = real.root_context

        def all(self):
            return [orphan, *everything[1:]]

        def has(self, identity):
            return identity != "a-context-nobody-recorded" and real.has(identity)

        def get(self, identity):
            return real.get(identity)

    probe = _ProbeWith(declaration, _Store())
    probe._ledger = _Store()
    problems = contract.no_subject_exists_outside_context(probe)
    assert any("which is absent" in p for p in problems), problems


def test_an_unrecorded_root_context_is_refused(declaration):
    real = KnowledgeLedger(declaration)

    class _Rootless:
        root_context = ""

        def all(self):
            return real.all()

        def has(self, identity):
            return real.has(identity)

        def get(self, identity):
            return real.get(identity)

    probe = _ProbeWith(declaration, _Rootless())
    probe._ledger = _Rootless()
    problems = contract.no_subject_exists_outside_context(probe)
    assert any("root context is not recorded" in p for p in problems), problems


# --- URKE-L-25: the relationship refusals ---------------------------------------------------


@pytest.mark.parametrize("label", ["source", "target", "relation", "basis"])
def test_a_relationship_carrying_no_field_is_refused(declaration, monkeypatch, label):
    real = ledger_module.relate

    def hollow(*args, **kwargs):
        return dataclasses.replace(real(*args, **kwargs), **{label: "  "})

    monkeypatch.setattr(ledger_module, "relate", hollow)
    problems = contract.relationships_carry_governance(_forge(declaration))
    assert any(f"carries no {label}" in p for p in problems), problems


def test_a_relationship_carrying_no_evidence_is_refused(declaration, monkeypatch):
    real = ledger_module.relate
    monkeypatch.setattr(
        ledger_module, "relate", lambda *a, **k: dataclasses.replace(real(*a, **k), evidence=())
    )
    problems = contract.relationships_carry_governance(_forge(declaration))
    assert any("carries no evidence" in p for p in problems), problems


@pytest.mark.parametrize("label", ["an absent source", "an absent target"])
def test_a_relationship_naming_an_absent_endpoint_must_be_refused(declaration, monkeypatch, label):
    # The law asserts a REFUSAL, so the violation is a relate() that accepts an endpoint the
    # ledger never recorded.
    real = ledger_module.relate

    def permissive(store, **kwargs):
        kwargs = {
            k: (store.all()[0].identity if v == "not-recorded" else v) for k, v in kwargs.items()
        }
        return real(store, **kwargs)

    monkeypatch.setattr(ledger_module, "relate", permissive)
    problems = contract.relationships_carry_governance(_forge(declaration))
    assert any(f"a relationship naming {label}" in p for p in problems), problems


# --- URKE-L-27: the learning-pipeline refusals -----------------------------------------------


def test_a_pipeline_refusing_a_legitimate_move_is_reported(declaration, monkeypatch):
    # The law measures both directions: skips must be refused AND legitimate moves accepted.
    # Refusing everything would satisfy the first half while breaking the second.

    def refuse_everything(store, identity, *, to_stage, basis):
        raise RecursiveKnowledgeError("advance refused for the test")

    monkeypatch.setattr(subjects, "advance", refuse_everything)
    problems = contract.learning_pipeline_cannot_be_bypassed(_forge(declaration))
    assert any("refused a legitimate move" in p for p in problems), problems


def test_a_lesson_that_does_not_reach_the_last_stage_is_refused(declaration, monkeypatch):
    real = subjects.advance
    stages = [spec.identifier for spec in declaration.learning_stages]

    def stall_before_the_end(store, identity, *, to_stage, basis):
        if to_stage == stages[-1]:
            return store.get(identity)
        return real(store, identity, to_stage=to_stage, basis=basis)

    monkeypatch.setattr(subjects, "advance", stall_before_the_end)
    problems = contract.learning_pipeline_cannot_be_bypassed(_forge(declaration))
    assert any("did not reach the last one" in p for p in problems), problems


def test_a_reversal_that_removes_the_lesson_is_refused(declaration, monkeypatch):
    # Reversal must supersede, never delete: the record of what was learned and unlearned has
    # to survive both.
    real = subjects.reverse_lesson
    monkeypatch.setattr(
        subjects,
        "reverse_lesson",
        lambda store, identity, *, by, basis: dataclasses.replace(
            real(store, identity, by=by, basis=basis), superseded_by=""
        ),
    )
    problems = contract.learning_pipeline_cannot_be_bypassed(_forge(declaration))
    assert any("removed the lesson instead of superseding it" in p for p in problems), problems


# --- the remaining refusals ------------------------------------------------------------------


def _drifting_fingerprint(monkeypatch):
    calls = {"n": 0}

    def drifting(self):
        calls["n"] += 1
        return f"fingerprint-{calls['n']}"

    monkeypatch.setattr(contract.Probe, "fingerprint", drifting)


def test_a_refusal_of_the_wrong_error_type_is_still_reported(declaration):
    # A refusal is required; a refusal by TypeError is a refusal for the wrong reason, and
    # `_refused` names that rather than accepting it as success.
    def raise_the_wrong_type():
        raise TypeError("wrong shape entirely")

    assert "unexpected error type: TypeError" in contract._refused(raise_the_wrong_type)


def test_an_unknown_carrying_no_governance_field_is_refused(declaration, monkeypatch):
    real = subjects.record_gap

    def hollow(store, **kwargs):
        return dataclasses.replace(real(store, **kwargs), owner="  ")

    monkeypatch.setattr(subjects, "record_gap", hollow)
    problems = contract.every_identified_unknown_is_governed(_forge(declaration))
    assert any("carries no owner" in p for p in problems), problems


def test_an_unknown_the_ledger_did_not_retain_is_refused(declaration, monkeypatch):
    real = subjects.record_gap

    def forgotten(store, **kwargs):
        gap = real(store, **kwargs)
        return dataclasses.replace(gap, identity=gap.identity + "-never-recorded")

    monkeypatch.setattr(subjects, "record_gap", forgotten)
    problems = contract.every_identified_unknown_is_governed(_forge(declaration))
    assert any("was not retained" in p for p in problems), problems


def test_admitting_a_future_domain_that_changes_the_package_is_refused(declaration, monkeypatch):
    _drifting_fingerprint(monkeypatch)
    problems = contract.future_domain_is_admissible(_forge(declaration))
    assert any("admitting a future domain changed this package" in p for p in problems), problems


def test_admitting_a_reality_that_changes_the_package_is_refused(declaration, monkeypatch):
    _drifting_fingerprint(monkeypatch)
    problems = contract.worlds_are_data_driven(_forge(declaration))
    assert any("changed this package" in p for p in problems), problems


def test_an_unscannable_vocabulary_is_a_fault_not_a_verdict(declaration, monkeypatch):
    # A vocabulary that cannot be scanned yields no verdict about hardcoding, so the law
    # raises rather than reporting "no literals found" over a scan that never happened.
    def refuse(decl):
        raise DeclarationError("vocabulary could not be scanned")

    monkeypatch.setattr(contract, "scanned_vocabulary", refuse)
    with pytest.raises(contract.ContractError, match="could not be scanned"):
        contract.vocabulary_is_declared_not_coded(_forge(declaration))


def test_a_settled_state_that_cannot_be_reopened_is_refused(declaration, monkeypatch):
    # Settled is not terminal: a settled subject must remain reopenable, or the lattice has a
    # one-way door in it.
    real = states.successors
    settled = declaration.settled_states[0]
    monkeypatch.setattr(
        states,
        "successors",
        lambda decl, identifier: () if identifier == settled else real(decl, identifier),
    )
    problems = contract.no_state_is_terminal(_forge(declaration))
    assert any(f"settled state {settled!r} cannot be reopened" in p for p in problems), problems


def test_a_gap_missing_its_required_attributes_must_be_refused(declaration):
    # The law asserts a REFUSAL, and the refusal happens at `store.admit`, so the violation is
    # a ledger that admits a subject carrying none of its profile's required attributes.
    probe = _ledger_probe(declaration, admit=lambda subject: subject)
    problems = contract.profile_requirements_are_enforced(probe)
    assert any("carrying none of its required attributes" in p for p in problems), problems


def test_a_subject_owned_by_an_undeclared_role_must_be_refused(declaration):
    probe = _ledger_probe(declaration, admit=lambda subject: subject)
    problems = contract.profile_requirements_are_enforced(probe)
    assert any("owned by an undeclared role" in p for p in problems), problems


def test_a_gap_with_no_closure_criterion_must_be_refused(declaration, monkeypatch):
    real = subjects.record_gap

    def permissive(store, **call):
        if not call.get("criteria"):
            call["criteria"] = ("filled in by a permissive ledger",)
        return real(store, **call)

    monkeypatch.setattr(subjects, "record_gap", permissive)
    problems = contract.profile_requirements_are_enforced(_forge(declaration))
    assert any("with no closure criterion" in p for p in problems), problems


def test_a_discovery_run_that_changes_the_declaration_is_refused(declaration, monkeypatch):
    # Discovery observes; it must not rewrite the truth it observes. The violation is a
    # discover() that mutates the declaration underneath the law.
    calls = {"n": 0}

    def drifting_payload(self):
        calls["n"] += 1
        return {"reading": calls["n"]}

    monkeypatch.setattr(type(declaration), "digest_payload", drifting_payload)
    problems = contract.discovery_never_mutates_constitutional_truth(_forge(declaration))
    assert any("changed the declaration" in p for p in problems), problems


def test_a_declared_target_no_source_claims_is_refused(declaration):
    orphan = (
        *declaration.discovery_targets,
        dataclasses.replace(declaration.discovery_targets[0], identifier="target-nobody-claims"),
    )
    problems = contract.discovery_covers_every_declared_target(
        _forge(declaration, discovery_targets=orphan)
    )
    assert any("no source claims it" in p for p in problems), problems


def test_a_reality_that_does_not_answer_every_dimension_is_refused(declaration, monkeypatch):
    monkeypatch.setattr(
        worlds, "resolve", lambda decl, identifier: {"systems": {}, "identifier": identifier}
    )
    problems = contract.worlds_are_data_driven(_forge(declaration))
    assert any("does not answer every dimension" in p for p in problems), problems


def test_a_preserved_site_that_no_longer_occurs_is_refused(declaration):
    # A preserved site records that a forbidden phrase is allowed in one named place. When
    # that place stops containing it the exemption is stale, and a stale exemption silently
    # widens what is permitted.
    stale = (*declaration.preserved_sites, "contract.py:a phrase that is not in the file")
    problems = contract.no_completeness_claim_is_declared(
        _forge(declaration, preserved_sites=stale)
    )
    assert any("no longer occurs" in p for p in problems), problems


def test_a_contradiction_class_nothing_reaches_is_refused(declaration):
    narrowed = tuple(
        dataclasses.replace(spec, ucon_contradiction_class="reaches-nothing")
        for spec in declaration.contradiction_classes
    )
    problems = contract.bound_vocabulary_is_neither_copied_nor_narrowed(
        _forge(declaration, contradiction_classes=narrowed)
    )
    assert any("contradiction class" in p and "nothing reaches it" in p for p in problems), problems


def test_a_resolution_state_nothing_reaches_is_refused(declaration):
    narrowed = tuple(
        dataclasses.replace(spec, ucon_resolution_state="reaches-nothing")
        for spec in declaration.resolution_states
    )
    problems = contract.bound_vocabulary_is_neither_copied_nor_narrowed(
        _forge(declaration, resolution_states=narrowed)
    )
    assert any("resolution state" in p and "nothing reaches it" in p for p in problems), problems


def test_a_disclosed_gap_missing_a_field_is_refused(declaration, monkeypatch):
    # The ledger seeds itself from these same gaps and refuses an empty remediation, so the
    # declaration cannot simply be mutated: seeding would fail before the law read anything.
    # The ledger is built from the real gaps first, then the reading the law does is hollowed.
    probe = _forge(declaration)
    probe.seeded()
    real = type(declaration).all_disclosed_gaps
    monkeypatch.setattr(
        type(declaration),
        "all_disclosed_gaps",
        lambda self: tuple(
            dataclasses.replace(gap, remediation="  ") if index == 0 else gap
            for index, gap in enumerate(real(self))
        ),
    )
    problems = contract.disclosed_gaps_are_themselves_governed(probe)
    assert any("carries no remediation" in p for p in problems), problems


def test_a_failing_self_improvement_exercise_is_reported(declaration, monkeypatch):
    def refuse(store):
        raise RecursiveKnowledgeError("exercise refused for the test")

    monkeypatch.setattr(discovery, "discover", refuse)
    problems = contract.declared_mechanisms_are_live_and_exercised(_forge(declaration))
    assert any("self-improvement exercise" in p and "failed" in p for p in problems), problems


def test_self_analysis_producing_no_evidence_is_refused(declaration):
    probe = _ledger_probe(declaration, of_profile=lambda profile: ())
    problems = contract.declared_mechanisms_are_live_and_exercised(probe)
    assert any("produced no evidence in the ledger" in p for p in problems), problems
