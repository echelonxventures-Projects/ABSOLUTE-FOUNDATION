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
