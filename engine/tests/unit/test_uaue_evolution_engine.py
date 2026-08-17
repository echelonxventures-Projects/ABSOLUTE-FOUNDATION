"""UAUE-000001 Epoch 3 — the evolution engine, phase by phase.

The eight properties the epoch requires, each with the mutation that closes it:

1. **Unknown evolution candidate.** The declared unknown probe — an object in no registry, of no
   declared class, with no owner — traverses every phase on the same code path as a capability
   gap, and needs no new registry, authority, engine or schema to do it.
2. **Missing evidence rejection.** A candidate with no resolving evidence cannot be understood,
   and an object cannot be derived without evidence at all.
3. **Missing identity rejection.** An object whose identity inputs are empty is refused at
   derivation; one whose identity does not equal its own digest fails correctness and identity
   integrity.
4. **Dependency failure.** An unresolvable dependency makes the simulation non-executable, which
   refuses execution — no uncontrolled execution.
5. **Validation failure.** An unsealed chain fails completeness; a short chain fails traceability.
6. **Certification failure.** Each of the eight proofs is shown to fail for its own reason.
7. **Successful evolution path.** With the substrate complete, one candidate traverses all eleven
   phases and every validation, verification and certification criterion is satisfied.
8. **Deterministic replay.** Two traversals of one candidate over one tree produce byte-identical
   chains, history documents and digests; a mutated history is refused on read.

Also proved: **the engine performs no mutation** (the execution phase reports
``mutation_performed`` false and no module reaches repository state), and **no module names a
phase, register or stage** — every one is resolved from the authority.
"""

from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from engine.uaue.authority import load_evolution_authority
from engine.uaue.certification import certification_object, certify_evolution
from engine.uaue.discovery import discover_evolution_candidates
from engine.uaue.execution import execute_evolution
from engine.uaue.history import (
    build_ledger,
    history_records,
    learning_object,
    project_history,
    query_history,
    rehydrate_history,
    state_transition_object,
)
from engine.uaue.model import EvolutionAuthority, EvolutionAuthorityError
from engine.uaue.objects import (
    EvolutionCandidate,
    EvolutionChain,
    EvolutionObject,
    as_context,
    derive_identity,
)
from engine.uaue.observation import observe_evolution
from engine.uaue.planning import create_evolution_plan
from engine.uaue.resolution import REPO_ROOT, DeclarationReader, Substrate
from engine.uaue.simulation import simulate_evolution
from engine.uaue.understanding import understand_evolution
from engine.uaue.validation import validate_evolution, validation_object
from engine.uaue.verification import verification_object, verify_evolution
from engine.uckp.errors import EvolutionError

UAUE_PACKAGE = REPO_ROOT / "engine" / "uaue"


class WiredSubstrate(Substrate):
    """The real tree, with one declared-but-unwired gate treated as wired.

    Needed for the successful-path property and nothing else. ``make uaue-gate`` is declared by
    the register and is not yet in the Makefile — that is Epoch 4's work — so against the real
    tree the governance dimension correctly fails. Rather than weaken the measurement to make a
    test pass, the test supplies the substrate the measurement expects and states plainly which
    single fact it is supplying.
    """

    def make_targets(self) -> frozenset[str]:
        return super().make_targets() | {"uaue-gate"}


@pytest.fixture(scope="module")
def authority() -> EvolutionAuthority:
    return load_evolution_authority()


@pytest.fixture(scope="module")
def wired() -> Substrate:
    return WiredSubstrate()


@pytest.fixture(scope="module")
def wired_authority(wired: Substrate) -> EvolutionAuthority:
    return load_evolution_authority(DeclarationReader.canonical(), wired)


@pytest.fixture(scope="module")
def declaration() -> dict[str, Any]:
    import json

    from engine.uaue.resolution import DECLARATION_PATH

    return json.loads((REPO_ROOT / DECLARATION_PATH).read_text("utf-8"))


@pytest.fixture(scope="module")
def candidates(authority: EvolutionAuthority):
    return discover_evolution_candidates(authority)


def _first_object(authority: EvolutionAuthority, candidate: EvolutionCandidate):
    """The discovery phase's own object for a candidate — the head of every chain."""
    phase = authority.phase_by_ordinal(1)
    return EvolutionObject.derive(
        rule=authority.identity,
        candidate=candidate,
        object_kind=authority.object_kind_of(phase.identifier).identifier,
        phase=phase.identifier,
        lifecycle_state=authority.stage_of(phase.identifier),
        dependencies=authority.dependencies_of(phase.identifier),
        evidence=candidate.evidence,
        authority=phase.authority,
    )


def traverse(
    candidate: EvolutionCandidate,
    authority: EvolutionAuthority,
    substrate: Substrate,
    *,
    rounds: int = 2,
) -> EvolutionChain:
    """Carry one candidate through all eleven phases, then settle the verdicts.

    This is the *test's* wiring, not the engine's: autonomous orchestration is Epoch 4. Two
    rounds settle the one interdependence in the declaration — completeness requires a verdict,
    and the verdict measures completeness — by measuring, sealing, and measuring again.
    """
    understanding = understand_evolution(candidate, authority, substrate)
    plan = create_evolution_plan(understanding, authority)
    simulation = simulate_evolution(plan, authority, substrate)
    execution = execute_evolution(simulation, authority, substrate)
    observation = observe_evolution(execution, authority, substrate)

    chain = EvolutionChain(
        candidate=candidate,
        objects=(
            _first_object(authority, candidate),
            understanding.obj,
            plan.obj,
            simulation.obj,
            execution.obj,
            observation.obj,
        ),
        understanding=understanding,
        plan=plan,
        simulation=simulation,
        execution=execution,
        observation=observation,
    )
    # The five remaining phase objects exist before their verdicts do; the verdicts are then
    # measured over the complete object set, which is what registers 09-11 report on.
    validation = validate_evolution(chain, authority, substrate)
    chain = chain.with_objects((*chain.objects, validation_object(chain, validation, authority)))
    verification = verify_evolution(chain, authority, substrate)
    chain = chain.with_objects(
        (*chain.objects, verification_object(chain, verification, authority))
    )
    certification = certify_evolution(chain, authority)
    chain = chain.with_objects(
        (*chain.objects, certification_object(chain, certification, authority))
    )
    chain = chain.with_objects((*chain.objects, learning_object(chain, authority)))
    chain = chain.with_objects((*chain.objects, state_transition_object(chain, authority)))

    for _ in range(rounds):
        chain = chain.with_verdicts(
            validation=validate_evolution(chain, authority, substrate),
            verification=verify_evolution(chain, authority, substrate),
        )
        chain = chain.sealed()
        chain = chain.with_verdicts(certification=certify_evolution(chain, authority))
        chain = chain.sealed()
    return chain


@pytest.fixture(scope="module")
def unknown(candidates) -> EvolutionCandidate:
    return next(
        entry for entry in candidates.candidates if entry.candidate_class == "UNKNOWN_OBJECT"
    )


@pytest.fixture(scope="module")
def unknown_chain(
    unknown: EvolutionCandidate, wired_authority: EvolutionAuthority, wired: Substrate
) -> EvolutionChain:
    return traverse(unknown, wired_authority, wired)


# --------------------------------------------------------------------------------------
# 1. Unknown evolution candidate
# --------------------------------------------------------------------------------------


def test_the_declared_unknown_probe_is_discovered(
    unknown: EvolutionCandidate, authority: EvolutionAuthority
) -> None:
    assert unknown.subject_identity == authority.unknown_probe.subject
    assert unknown.evidence, "the probe must carry evidence like any other candidate"


def test_the_unknown_object_traverses_every_phase(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    assert len(unknown_chain.objects) == len(wired_authority.phases)
    assert [entry.phase for entry in unknown_chain.objects] == [
        phase.identifier for phase in wired_authority.phases
    ]


def test_the_unknown_object_needs_no_new_registry_authority_or_schema(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    """Every object of the unknown chain resolves under an owner that predates this programme."""
    homes = {entry.home for entry in wired_authority.ownership}
    for obj in unknown_chain.objects:
        assert obj.authority, obj.object_kind
        assert set(obj.dependencies) & (homes | {p.identifier for p in wired_authority.phases})


def test_no_phase_branches_on_the_subject_class(
    candidates, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    """Two candidates of different classes produce structurally identical chains."""
    by_class: dict[str, EvolutionCandidate] = {}
    for entry in candidates.candidates:
        by_class.setdefault(entry.candidate_class, entry)
    picked = [by_class["UNKNOWN_OBJECT"], by_class["CAPABILITY_GAP"], by_class["KNOWLEDGE_GAP"]]
    shapes = {
        tuple(obj.phase for obj in traverse(entry, wired_authority, wired).objects)
        for entry in picked
    }
    assert len(shapes) == 1, "the loop shape must not depend on what the subject is"


# --------------------------------------------------------------------------------------
# 2. Missing evidence rejection
# --------------------------------------------------------------------------------------


def test_an_object_cannot_be_derived_without_evidence(
    unknown: EvolutionCandidate, authority: EvolutionAuthority
) -> None:
    with pytest.raises(EvolutionAuthorityError, match="at least one resolving evidence"):
        EvolutionObject.derive(
            rule=authority.identity,
            candidate=unknown,
            object_kind="AUE-OBJ-01",
            phase="AUE-P-01",
            lifecycle_state="observe",
            dependencies=(),
            evidence=(),
            authority="test",
        )


def test_a_candidate_with_no_resolving_evidence_cannot_be_understood(
    unknown: EvolutionCandidate, authority: EvolutionAuthority
) -> None:
    orphan = replace(unknown, evidence=("does/not/exist.json",))
    with pytest.raises(EvolutionAuthorityError, match="no resolving evidence"):
        understand_evolution(orphan, authority)


def test_discovery_drops_a_source_whose_artifact_does_not_resolve(
    authority: EvolutionAuthority, tmp_path: Path
) -> None:
    """In an empty tree no artifact resolves, so no artifact-backed candidate may be emitted.

    The internal sources still speak: with no owner home present, every declared authority
    surface reads as unbound, which is exactly the self-detection the register is for. What must
    not happen is a candidate carrying evidence that does not exist.
    """
    report = discover_evolution_candidates(authority, Substrate(tmp_path))
    assert report.unresolved_sources
    assert report.findings
    artifact_backed = {
        entry.candidate_class
        for entry in report.candidates
        if entry.candidate_class in {"CAPABILITY_GAP", "KNOWLEDGE_GAP", "VALIDATION_GAP"}
    }
    assert not artifact_backed
    for entry in report.candidates:
        assert entry.evidence, "no candidate may be emitted without evidence"


def test_evidence_integrity_fails_when_an_object_loses_its_evidence(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    broken = unknown_chain.with_objects(
        (
            replace(unknown_chain.objects[0], evidence=("nowhere/at/all.json",)),
            *unknown_chain.objects[1:],
        )
    )
    verdict = verify_evolution(broken, wired_authority, wired)
    failed = [entry.identifier for entry in verdict.blocking_failures]
    assert failed, "an object with no resolving evidence must fail verification"


# --------------------------------------------------------------------------------------
# 3. Missing identity rejection
# --------------------------------------------------------------------------------------


def test_an_empty_identity_input_is_refused(authority: EvolutionAuthority) -> None:
    with pytest.raises(EvolutionAuthorityError, match="cannot be identified"):
        derive_identity(authority.identity, dict.fromkeys(authority.identity.inputs, ""))


def test_identity_is_derived_not_minted(authority: EvolutionAuthority) -> None:
    inputs = dict.fromkeys(authority.identity.inputs, "x")
    first = derive_identity(authority.identity, inputs)
    assert first.startswith(authority.identity.prefix)
    assert len(first) == len(authority.identity.prefix) + authority.identity.width
    assert first == derive_identity(authority.identity, inputs)


def test_the_same_candidate_rediscovered_yields_the_same_identity(
    authority: EvolutionAuthority,
) -> None:
    first = discover_evolution_candidates(authority)
    second = discover_evolution_candidates(authority)
    assert [entry.evolution_id for entry in first.candidates] == [
        entry.evolution_id for entry in second.candidates
    ]


def test_distinct_phases_of_one_candidate_have_distinct_identities(
    unknown_chain: EvolutionChain,
) -> None:
    identities = [entry.evolution_id for entry in unknown_chain.objects]
    assert len(set(identities)) == len(identities)


def test_a_forged_identity_fails_correctness_and_identity_integrity(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    forged = unknown_chain.with_objects(
        (
            replace(unknown_chain.objects[0], evolution_id="UCOS-EVO-000000000000"),
            *unknown_chain.objects[1:],
        )
    )
    assert not validate_evolution(forged, wired_authority, wired).passed
    assert not verify_evolution(forged, wired_authority, wired).passed


def test_an_object_with_an_empty_subject_is_anonymous(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    anonymous = unknown_chain.with_objects(
        (replace(unknown_chain.objects[0], subject_identity=" "), *unknown_chain.objects[1:])
    )
    verdict = verify_evolution(anonymous, wired_authority, wired)
    assert any("anonymous" in entry.detail for entry in verdict.blocking_failures)


# --------------------------------------------------------------------------------------
# 4. Dependency failure
# --------------------------------------------------------------------------------------


def test_an_unresolvable_dependency_makes_the_simulation_non_executable(
    unknown: EvolutionCandidate, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    understanding = understand_evolution(unknown, wired_authority, wired)
    plan = create_evolution_plan(understanding, wired_authority)
    broken = replace(plan, dependencies=(*plan.dependencies, "engine/does/not/exist.py"))
    simulation = simulate_evolution(broken, wired_authority, wired)
    assert "engine/does/not/exist.py" in simulation.unresolved_dependencies
    assert not simulation.executable


def test_a_non_executable_simulation_refuses_execution(
    unknown: EvolutionCandidate, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    understanding = understand_evolution(unknown, wired_authority, wired)
    plan = create_evolution_plan(understanding, wired_authority)
    broken = replace(plan, dependencies=(*plan.dependencies, "engine/absent.py"))
    execution = execute_evolution(
        simulate_evolution(broken, wired_authority, wired), wired_authority, wired
    )
    assert not execution.authorised
    assert any("simulation did not authorise" in entry for entry in execution.refusals)


def test_the_loop_has_no_backward_dependency_edge(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    verdict = verify_evolution(unknown_chain, wired_authority, wired)
    outcome = next(
        entry for entry in verdict.outcomes if entry.subject.lower().startswith("dependency")
    )
    assert outcome.satisfied, outcome.detail


def test_a_plan_step_without_a_located_owner_is_refused(
    declaration: dict[str, Any], authority: EvolutionAuthority, wired: Substrate
) -> None:
    mutable = copy.deepcopy(declaration)
    mutable["phases"][3]["owners"] = []
    unowned = load_evolution_authority(DeclarationReader.from_document(mutable), wired)
    report = discover_evolution_candidates(unowned, wired)
    candidate = report.candidates[0]
    understanding = understand_evolution(candidate, unowned, wired)
    with pytest.raises(EvolutionAuthorityError, match="no located owner"):
        create_evolution_plan(understanding, unowned)


# --------------------------------------------------------------------------------------
# 5. Validation failure
# --------------------------------------------------------------------------------------


def test_an_unsealed_chain_fails_completeness(
    unknown: EvolutionCandidate, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    """Before sealing, early objects carry no verdict, so a mandated field is empty."""
    understanding = understand_evolution(unknown, wired_authority, wired)
    chain = EvolutionChain(
        candidate=unknown,
        objects=(_first_object(wired_authority, unknown), understanding.obj),
        understanding=understanding,
    )
    verdict = validate_evolution(chain, wired_authority, wired)
    completeness = next(
        entry for entry in verdict.outcomes if entry.subject.lower() == "completeness"
    )
    assert not completeness.satisfied
    assert not verdict.passed


def test_a_short_chain_fails_traceability(
    unknown: EvolutionCandidate, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    chain = EvolutionChain(candidate=unknown, objects=(_first_object(wired_authority, unknown),))
    verdict = validate_evolution(chain, wired_authority, wired)
    traceability = next(
        entry for entry in verdict.outcomes if entry.subject.lower() == "traceability"
    )
    assert not traceability.satisfied
    assert "mandated object kinds not produced" in traceability.detail


def test_a_candidate_from_an_undeclared_source_fails_traceability(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    forged = EvolutionChain(
        candidate=replace(unknown_chain.candidate, source="AUE-SRC-99"),
        objects=unknown_chain.objects,
        understanding=unknown_chain.understanding,
        plan=unknown_chain.plan,
    )
    verdict = validate_evolution(forged, wired_authority, wired)
    traceability = next(
        entry for entry in verdict.outcomes if entry.subject.lower() == "traceability"
    )
    assert not traceability.satisfied


def test_every_declared_validation_dimension_is_measured(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    verdict = validate_evolution(unknown_chain, wired_authority, wired)
    assert len(verdict.outcomes) == len(wired_authority.validations)
    assert all(entry.detail for entry in verdict.outcomes)
    assert all(entry.owner for entry in verdict.outcomes)


def test_a_validation_dimension_the_engine_cannot_measure_is_not_silently_satisfied(
    declaration: dict[str, Any], wired: Substrate, unknown_chain: EvolutionChain
) -> None:
    mutable = copy.deepcopy(declaration)
    mutable["validations"].append(
        {
            "id": "AUE-VAL-99",
            "dimension": "Telepathy",
            "obligation": "the engine guesses correctly",
            "blocking": True,
        }
    )
    extended = load_evolution_authority(DeclarationReader.from_document(mutable), wired)
    verdict = validate_evolution(unknown_chain, extended, wired)
    added = next(entry for entry in verdict.outcomes if entry.identifier == "AUE-VAL-99")
    assert not added.satisfied
    assert "cannot measure" in added.detail


def test_an_unwired_gate_fails_governance_verification(
    unknown_chain: EvolutionChain, authority: EvolutionAuthority
) -> None:
    """A dimension bound to a gate nothing discharges must fail, not pass.

    Until Epoch 4 this was measurable against the real tree, because the register's own declared
    gate was not in the Makefile. Wiring it closed that gap — so the condition is now constructed,
    by measuring against a tree that declares no gate at all. The gate whose absence is asserted is
    read from the declaration rather than named here, so a renamed gate does not silently turn this
    into a test of nothing.
    """

    class Ungated(Substrate):
        """The real tree, with the final position's declared gate treated as absent."""

        def make_targets(self) -> frozenset[str]:
            return super().make_targets() - {target}

    command = authority.phases[-1].gate.command
    target = command.removeprefix("make ").strip()
    verdict = verify_evolution(unknown_chain, authority, Ungated())
    governance = next(
        entry for entry in verdict.outcomes if entry.subject.lower().startswith("governance")
    )
    assert not governance.satisfied
    assert target in governance.detail


def test_the_governance_dimension_is_satisfied_against_repository_truth(
    unknown_chain: EvolutionChain, authority: EvolutionAuthority
) -> None:
    """The complement, and the property Epoch 4 delivered: every declared gate is now wired."""
    verdict = verify_evolution(unknown_chain, authority, Substrate())
    governance = next(
        entry for entry in verdict.outcomes if entry.subject.lower().startswith("governance")
    )
    assert governance.satisfied, governance.detail
    assert all(phase.gate.wired for phase in authority.phases)


# --------------------------------------------------------------------------------------
# 6. Certification failure
# --------------------------------------------------------------------------------------


def test_certification_fails_without_an_understanding_object(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    chain = EvolutionChain(candidate=unknown_chain.candidate, objects=unknown_chain.objects)
    verdict = certify_evolution(chain, wired_authority)
    failures = {entry.subject for entry in verdict.blocking_failures}
    assert "was understood" in failures
    assert "was planned" in failures


def test_certification_fails_when_execution_was_refused(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    refused = replace(unknown_chain.execution, authorised=False, refusals=("test-induced refusal",))
    chain = EvolutionChain(
        candidate=unknown_chain.candidate,
        objects=unknown_chain.objects,
        understanding=unknown_chain.understanding,
        plan=unknown_chain.plan,
        simulation=unknown_chain.simulation,
        execution=refused,
        observation=unknown_chain.observation,
        validation=unknown_chain.validation,
        verification=unknown_chain.verification,
    )
    verdict = certify_evolution(chain, wired_authority)
    assert "was executed correctly" in {entry.subject for entry in verdict.blocking_failures}


def test_certification_refuses_a_claimed_mutation(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    """If anything ever set mutation_performed, certification must refuse it."""
    claimed = replace(unknown_chain.execution, mutation_performed=True)
    chain = EvolutionChain(
        candidate=unknown_chain.candidate,
        objects=unknown_chain.objects,
        understanding=unknown_chain.understanding,
        plan=unknown_chain.plan,
        execution=claimed,
        validation=unknown_chain.validation,
        verification=unknown_chain.verification,
    )
    verdict = certify_evolution(chain, wired_authority)
    outcome = next(entry for entry in verdict.outcomes if entry.subject == "was executed correctly")
    assert not outcome.satisfied
    assert "claims a mutation" in outcome.detail


def test_certification_fails_without_a_measured_validation_verdict(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    chain = unknown_chain.with_verdicts()
    stripped = EvolutionChain(
        candidate=chain.candidate,
        objects=chain.objects,
        understanding=chain.understanding,
        plan=chain.plan,
        simulation=chain.simulation,
        execution=chain.execution,
        observation=chain.observation,
    )
    verdict = certify_evolution(stripped, wired_authority)
    failures = {entry.subject for entry in verdict.blocking_failures}
    assert {"has validation", "has verification"} <= failures


def test_certification_fails_when_the_history_cannot_be_projected(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    short = EvolutionChain(
        candidate=unknown_chain.candidate,
        objects=unknown_chain.objects[:4],
        understanding=unknown_chain.understanding,
        plan=unknown_chain.plan,
        validation=unknown_chain.validation,
        verification=unknown_chain.verification,
    )
    outcome = next(
        entry
        for entry in certify_evolution(short, wired_authority).outcomes
        if entry.subject == "has history"
    )
    assert not outcome.satisfied


def test_every_declared_certification_proof_is_measured(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    verdict = certify_evolution(unknown_chain, wired_authority)
    assert len(verdict.outcomes) == len(wired_authority.certifications)
    assert all(entry.detail for entry in verdict.outcomes)


# --------------------------------------------------------------------------------------
# 7. Successful evolution path
# --------------------------------------------------------------------------------------


def test_the_unknown_object_is_validated_verified_and_certified(
    unknown_chain: EvolutionChain,
) -> None:
    assert unknown_chain.validation is not None and unknown_chain.validation.passed, (
        unknown_chain.validation.summary if unknown_chain.validation else "no validation"
    )
    assert unknown_chain.verification is not None and unknown_chain.verification.passed, (
        [entry.detail for entry in unknown_chain.verification.blocking_failures]
        if unknown_chain.verification
        else "no verification"
    )
    assert unknown_chain.certification is not None and unknown_chain.certification.passed, (
        [entry.detail for entry in unknown_chain.certification.blocking_failures]
        if unknown_chain.certification
        else "no certification"
    )


def test_the_successful_path_authorises_execution_without_mutating(
    unknown_chain: EvolutionChain,
) -> None:
    assert unknown_chain.execution is not None
    assert unknown_chain.execution.authorised
    assert unknown_chain.execution.mutation_performed is False
    assert unknown_chain.execution.refusals == ()


def test_the_successful_path_produces_every_mandated_object_kind(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    produced = set(unknown_chain.kinds())
    for kind in wired_authority.mandated_kinds():
        assert kind.identifier in produced


def test_a_sealed_chain_carries_every_mandated_field_non_empty(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    for obj in unknown_chain.objects:
        for mandated in wired_authority.required_fields:
            if mandated.non_empty:
                assert obj.field_value(
                    mandated.field_name
                ), f"{obj.object_kind}.{mandated.field_name}"


def test_sealing_does_not_change_any_identity(unknown_chain: EvolutionChain) -> None:
    before = [entry.evolution_id for entry in unknown_chain.objects]
    after = [entry.evolution_id for entry in unknown_chain.sealed().objects]
    assert before == after


def test_observation_records_no_deviation_on_the_successful_path(
    unknown_chain: EvolutionChain,
) -> None:
    assert unknown_chain.observation is not None
    assert unknown_chain.observation.matches
    assert unknown_chain.observation.measured_by


def test_many_real_candidates_traverse_the_loop(
    candidates, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    """Not one hand-picked subject: a sample across every discovered class certifies."""
    sample: dict[str, EvolutionCandidate] = {}
    for entry in candidates.candidates:
        sample.setdefault(entry.candidate_class, entry)
    assert len(sample) >= 6
    for entry in sample.values():
        chain = traverse(entry, wired_authority, wired)
        assert chain.validation.passed, (entry.candidate_class, chain.validation.summary)
        assert chain.certification.passed, (
            entry.candidate_class,
            [failure.detail for failure in chain.certification.blocking_failures],
        )


# --------------------------------------------------------------------------------------
# 8. Deterministic replay
# --------------------------------------------------------------------------------------


def test_two_traversals_of_one_candidate_are_byte_identical(
    unknown: EvolutionCandidate, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    first = traverse(unknown, wired_authority, wired)
    second = traverse(unknown, wired_authority, wired)
    assert first.digest() == second.digest()
    assert first.to_dict() == second.to_dict()


def test_two_history_projections_are_byte_identical(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    first = project_history(unknown_chain, wired_authority)
    second = project_history(unknown_chain, wired_authority)
    assert first == second


def test_the_history_carries_no_wall_clock_time(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    """Logical time only: a timestamp would make two projections of one state differ."""
    records = history_records(unknown_chain, wired_authority)
    when = [
        finding for record in records for finding in record.findings if finding.startswith("when=")
    ]
    assert when and all("cycle=" in entry and "stage=" in entry for entry in when)
    assert not any(":" in entry.split("=", 1)[1] for entry in when)


def test_the_history_projects_one_record_per_canonical_stage(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    records = history_records(unknown_chain, wired_authority)
    assert len(records) == len(wired_authority.lifecycle_states)
    assert [record.stage.value for record in records] == [
        state.name for state in wired_authority.lifecycle_states
    ]


def test_the_history_rehydrates_through_the_ledger_that_owns_its_rules(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    document = project_history(unknown_chain, wired_authority)
    ledger = rehydrate_history(document)
    assert len(ledger) == len(wired_authority.lifecycle_states)
    assert ledger.is_terminated() is False
    assert ledger.fingerprint() == rehydrate_history(document).fingerprint()


def test_a_reordered_history_is_refused_on_read(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    document = project_history(unknown_chain, wired_authority)
    records = document["ledger"]["records"]
    records[3], records[4] = records[4], records[3]
    with pytest.raises(EvolutionError):
        rehydrate_history(document)


def test_a_truncated_history_is_refused_on_read(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    document = project_history(unknown_chain, wired_authority)
    del document["ledger"]["records"][6]
    with pytest.raises(EvolutionError):
        rehydrate_history(document)


def test_a_history_document_without_the_ledger_is_refused(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    document = project_history(unknown_chain, wired_authority)
    del document["ledger"]
    with pytest.raises(EvolutionAuthorityError, match="nest the Article 14 ledger"):
        rehydrate_history(document)


def test_a_history_not_declaring_itself_append_only_is_refused(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    document = project_history(unknown_chain, wired_authority)
    document["append_only"] = False
    with pytest.raises(EvolutionAuthorityError, match="append-only"):
        rehydrate_history(document)


def test_two_chains_occupy_two_cycles_and_the_loop_never_terminates(
    candidates, wired_authority: EvolutionAuthority, wired: Substrate
) -> None:
    picked = [
        entry for entry in candidates.candidates if entry.candidate_class == "UNKNOWN_OBJECT"
    ] + [entry for entry in candidates.candidates if entry.candidate_class == "CAPABILITY_GAP"][:1]
    chains = [traverse(entry, wired_authority, wired) for entry in picked]
    ledger = build_ledger(chains, wired_authority)
    assert len(ledger) == 2 * len(wired_authority.lifecycle_states)
    assert ledger.completed_cycles() == 2
    assert ledger.is_terminated() is False


def test_a_chain_missing_a_phase_object_cannot_project_a_history(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    short = unknown_chain.with_objects(unknown_chain.objects[:-1])
    with pytest.raises(EvolutionAuthorityError, match="would skip a stage"):
        history_records(short, wired_authority)


def test_the_history_is_queryable_only_by_declared_keys(
    unknown_chain: EvolutionChain, wired_authority: EvolutionAuthority
) -> None:
    document = project_history(unknown_chain, wired_authority)
    found = query_history(document, "evolution_id", unknown_chain.objects[0].evolution_id)
    assert found
    with pytest.raises(EvolutionAuthorityError, match="not declared queryable"):
        query_history(document, "colour", "blue")


def test_discovery_is_deterministic(authority: EvolutionAuthority) -> None:
    assert (
        discover_evolution_candidates(authority).digest()
        == discover_evolution_candidates(authority).digest()
    )


# --------------------------------------------------------------------------------------
# Non-duplication: the engine names no phase, register or stage
# --------------------------------------------------------------------------------------


def _code_literals(path: Path) -> tuple[tuple[int, str], ...]:
    """Every string literal in a module that is not a docstring.

    Prose may name a phase, a register or a stage — the modules explain what they realise, and a
    docstring that could not say so would be useless. What must not appear is a *code* literal,
    because that is the form a hard-coded declaration takes.
    """
    import ast

    tree = ast.parse(path.read_text("utf-8"))
    docstrings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                docstrings.add(doc)
    return tuple(
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    )


def test_no_engine_module_names_a_register_or_a_phase(
    authority: EvolutionAuthority,
) -> None:
    registers = {entry.file for entry in authority.registers}
    phases = {entry.identifier for entry in authority.phases}
    for path in UAUE_PACKAGE.glob("*.py"):
        for line, literal in _code_literals(path):
            assert literal not in registers, f"{path.name}:{line} names a register"
            assert literal not in phases, f"{path.name}:{line} names a phase"


def test_no_engine_module_enumerates_the_canonical_stage_set(
    authority: EvolutionAuthority,
) -> None:
    """No module may carry a stage *collection*; the stage set has exactly one home.

    Measured structurally, over list/tuple/set literals, rather than over every string in the
    file — and the distinction is necessary, not a convenience. Several document keys and declared
    field names collide incidentally with stage names: ``"reason"`` is a declared identity input,
    ``"validation"``/``"verification"``/``"certification"`` are keys of the chain document and
    prefixes of declared dimension names. None of those is a stage list. What would be a stage
    list is a literal sequence of stage names, and that is what this refuses.
    """
    import ast

    stages = {state.name for state in authority.lifecycle_states}
    for path in UAUE_PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.List | ast.Tuple | ast.Set):
                continue
            literals = {
                element.value
                for element in node.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            }
            named = literals & stages
            assert len(named) < 2, f"{path.name}:{node.lineno} enumerates stages {sorted(named)}"


def test_the_stage_set_is_imported_from_its_owner_not_restated() -> None:
    """Exactly one module reaches the canonical cycle, and it does so by import."""
    import ast

    importers: set[str] = set()
    for path in UAUE_PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "engine.uckp.evolution":
                importers.add(path.name)
    assert importers, "the stage set must be imported from the Article 14 authority"
    assert importers <= {"authority.py", "history.py"}, importers


def test_no_engine_module_names_a_discovery_source_or_object_kind(
    authority: EvolutionAuthority,
) -> None:
    forbidden = {entry.identifier for entry in authority.discovery_sources} | {
        entry.identifier for entry in authority.object_kinds
    }
    for path in UAUE_PACKAGE.glob("*.py"):
        for line, literal in _code_literals(path):
            assert literal not in forbidden, f"{path.name}:{line} names a declared identifier"


def test_no_lifecycle_module_writes_to_the_repository() -> None:
    """The lifecycle engine is a measurement. No write, no open-for-write, no unlink.

    Scoped to the lifecycle modules. Exactly one module of this package writes — the gate, which
    renders the declared history projection and the declared register surface — and it is excluded
    here and held to two stricter obligations, by
    :func:`test_the_only_writer_writes_only_inside_the_programme_home` and
    :func:`test_the_whole_rendered_surface_writes_only_declared_files_inside_the_home`: a
    projection has to be produced by something, and the honest way to say so is to name the single
    producer and bound where it may write, not to pretend nothing writes.

    This is why :mod:`engine.uaue.registers` returns rendered bodies instead of writing them. It
    renders eighteen files and reaches no path: ``rendered_surface`` hands the gate a
    file-name-to-body mapping and the gate performs every write. The alternative — eighteen
    renderers each holding a destination — would make "what may this programme mutate, and where"
    a question answered by reading every renderer, which is the same as having no answer.
    """
    import ast

    forbidden = {"write_text", "write_bytes", "mkdir", "unlink", "rmtree", "rename", "touch"}
    for path in UAUE_PACKAGE.glob("*.py"):
        if path.name == "gate.py":
            continue
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden:
                raise AssertionError(f"{path.name}:{node.lineno} calls {node.attr}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "open", f"{path.name}:{node.lineno} calls open()"


def test_the_only_writer_writes_only_inside_the_programme_home(tmp_path: Path) -> None:
    """The single writing module may write one declared file, inside its own home, and no other.

    The write-scope guard every rendering programme in this repository carries. Measured by
    rendering into a temporary tree and requiring that the only path touched is the file the
    declaration names, under the operational home the declaration names.
    """
    from engine.uaue.gate import history_path, measure, render
    from engine.uaue.resolution import PROGRAMME_HOME

    report = measure()
    target = tmp_path / PROGRAMME_HOME / report.context.authority.history.file
    written = render(report, target)
    assert written == target
    assert written.is_file()
    produced = sorted(entry.relative_to(tmp_path).as_posix() for entry in tmp_path.rglob("*"))
    assert produced == [
        "00-MASTER",
        PROGRAMME_HOME,
        f"{PROGRAMME_HOME}/{report.context.authority.history.file}",
    ]
    # And the canonical destination is inside the same home, not merely the temporary one.
    assert history_path(report.context).parent.as_posix().endswith(PROGRAMME_HOME)


def test_the_whole_rendered_surface_writes_only_declared_files_inside_the_home(
    tmp_path: Path,
) -> None:
    """The full surface — history plus every declared register — is bounded by the same rule.

    The register writes were moved out of the renderer and into the gate, which moved them *under*
    this bound rather than out of it: the guard above measures the history write in isolation, and
    this one measures everything the render command actually performs. Without it, moving a write
    into the one module the write guard exempts would be a way to acquire an unbounded write.

    Every written name must be a name the declaration chose. A register file the declaration does
    not name is a file nobody governs, and the count is compared as well as the set, because two
    declared registers resolving to one path would silently render seventeen files and report
    eighteen.
    """
    from engine.uaue.gate import measure, render_surface
    from engine.uaue.resolution import PROGRAMME_HOME

    report = measure()
    authority = report.context.authority
    declared = {authority.history.file} | {entry.file for entry in authority.registers}
    assert len(declared) == 1 + len(authority.registers), "two declared files share one name"

    written = render_surface(report, tmp_path)
    assert len(written) == len(declared)
    assert {path.name for path in written} == declared
    assert all(path.is_file() for path in written)
    produced = sorted(entry.relative_to(tmp_path).as_posix() for entry in tmp_path.rglob("*"))
    assert produced == sorted(
        ["00-MASTER", PROGRAMME_HOME] + [f"{PROGRAMME_HOME}/{name}" for name in declared]
    )


def test_the_engine_imports_no_platform_or_intelligence_module() -> None:
    """Layering: engine must not depend on platform or intelligence."""
    import ast

    for path in UAUE_PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(
                    ("platform", "intelligence")
                ), f"{path.name} imports {node.module}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(
                        ("platform", "intelligence")
                    ), f"{path.name} imports {alias.name}"


def test_context_is_canonical_and_hashable() -> None:
    first = as_context({"b": 2, "a": 1})
    assert first == (("a", "1"), ("b", "2"))
    assert hash(first)
