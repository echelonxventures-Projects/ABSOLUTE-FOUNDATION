"""UCOS-NUC-001 — the lifecycle as infrastructure, the lineage ledger, evolution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.nucleus import lifecycle, lineage
from engine.nucleus.errors import EvolutionError, LifecycleError, NucleusError
from engine.nucleus.evolution import (
    Evolution,
    EvolutionLedger,
    always_valid,
    state_must_grow,
)
from engine.nucleus.lifecycle import Stage, StageStatus
from engine.nucleus.registry import build_seed_registry

REPO_ROOT = Path(__file__).resolve().parents[3]


# -- the lifecycle ----------------------------------------------------------- #


def test_the_declared_lifecycle_is_the_mandated_chain():
    assert len(lifecycle.STAGES) == 45
    names = [s.name for s in lifecycle.STAGES]
    assert names[0] == "Receive Goal"
    assert names[-1] == "Begin Next Elevated Engineering Cycle"
    assert "Reuse Before Create" in names
    assert "Deterministic Fixed Point" in names
    assert "Assign Universal Constitutional Identifier" in names


def test_stage_order_is_derived_total_and_acyclic():
    order = lifecycle.stage_order()
    assert len(order) == len(lifecycle.STAGES)
    assert order == [s.stage_id for s in lifecycle.STAGES]


def test_a_cyclic_stage_graph_has_no_order():
    cyclic = (
        Stage("A", "a", 1, "G", depends_on=("B",)),
        Stage("B", "b", 2, "G", depends_on=("A",)),
    )
    with pytest.raises(LifecycleError):
        lifecycle.stage_order(cyclic)


def test_stage_lookup_fails_closed():
    assert lifecycle.stage("UCL-S-0010").name == "Receive Goal"
    with pytest.raises(LifecycleError):
        lifecycle.stage("UCL-S-9999")


def test_the_in_engine_stages_do_not_diverge_from_the_declaration_that_owns_them():
    manifest_path = REPO_ROOT / "00-MASTER" / "UCL-000001" / "ucl-stage-manifest.json"
    if not manifest_path.exists():  # pragma: no cover - declaration present in this tree
        pytest.skip("stage manifest not present")
    manifest = json.loads(manifest_path.read_text("utf-8"))
    assert lifecycle.verify_manifest_alignment(manifest) == ()


def test_manifest_alignment_reports_divergence():
    assert lifecycle.verify_manifest_alignment({}) == ("manifest carries no 'nodes' list",)
    divergences = lifecycle.verify_manifest_alignment(
        {"nodes": [{"id": "UCL-S-0010", "stage": "Wrong", "ordinal": 99, "group": "X"}]}
    )
    assert any("stage" in d for d in divergences)
    assert any("absent from manifest" in d for d in divergences)
    assert lifecycle.verify_manifest_alignment({"nodes": ["nope"]})[0].startswith("manifest node")
    assert any(
        "absent from STAGES" in d
        for d in lifecycle.verify_manifest_alignment({"nodes": [{"id": "UCL-S-0011"}]})
    )


def test_execution_runs_every_stage_and_chains_them():
    execution = lifecycle.execute("UCOS-NUC-000000000001")
    assert execution.complete is True
    assert execution.status == "COMPLETE"
    assert len(execution.outcomes) == 45
    assert execution.chain_is_intact() is True
    assert execution.chain_head
    assert execution.failures == ()
    assert execution.to_dict()["declared_stage_count"] == 45


def test_execution_replays_to_a_deterministic_fixed_point():
    report = lifecycle.replay("UCOS-NUC-000000000001")
    assert report["fixed_point"] is True
    assert report["chain_intact"] is True
    assert report["first_digest"] == report["second_digest"]


def test_a_failing_stage_is_recorded_not_swallowed():
    def failing(subject: str, stage: Stage):
        if stage.stage_id == "UCL-S-0160":
            return StageStatus.FAILED, "probe", {"why": "deliberate"}
        return StageStatus.SATISFIED, "probe", {}

    execution = lifecycle.execute("subject", stage_function=failing)
    assert execution.complete is False
    assert execution.status == "INCOMPLETE"
    assert [o.stage_id for o in execution.failures] == ["UCL-S-0160"]


def test_not_applicable_is_a_first_class_status():
    def mixed(subject: str, stage: Stage):
        return StageStatus.NOT_APPLICABLE, "probe", {}

    execution = lifecycle.execute("subject", stage_function=mixed)
    assert execution.complete is True
    assert all(o.status is StageStatus.NOT_APPLICABLE for o in execution.outcomes)


def test_an_unknown_status_fails_closed():
    def bogus(subject: str, stage: Stage):
        return "elsewhere", "probe", {}

    with pytest.raises(LifecycleError):
        lifecycle.execute("subject", stage_function=bogus)


def test_an_unnamed_subject_cannot_execute():
    with pytest.raises(LifecycleError):
        lifecycle.execute("   ")


def test_a_tampered_chain_is_detected():
    execution = lifecycle.execute("subject")
    from engine.nucleus.lifecycle import LifecycleExecution, StageOutcome

    outcomes = list(execution.outcomes)
    first = outcomes[0]
    outcomes[0] = StageOutcome(
        stage_id=first.stage_id,
        name="tampered",
        group=first.group,
        status=first.status,
        evidence=first.evidence,
        detail=first.detail,
        prev_hash=first.prev_hash,
        entry_hash=first.entry_hash,
    )
    tampered = LifecycleExecution(
        subject=execution.subject,
        lifecycle_id=execution.lifecycle_id,
        outcomes=tuple(outcomes),
        order=execution.order,
    )
    assert tampered.chain_is_intact() is False


def test_the_lifecycle_applies_to_every_category_of_thing():
    registry = build_seed_registry()
    subjects = [s.universal_id for s in registry.subjects()][:6]
    subjects += [c.universal_id for c in registry.capabilities()][:3]
    for subject in subjects:
        execution = lifecycle.execute(subject)
        assert execution.complete
        assert execution.subject == subject


def test_lifecycle_document_declares_no_ceiling():
    document = lifecycle.to_document()
    assert document["stage_count"] == 45
    assert document["closed_set"] is False
    assert document["upper_limit"] is None
    assert lifecycle.digest() == lifecycle.digest()
    assert len(document["groups"]) >= 10


def test_an_appended_stage_needs_no_code_change():
    extended = (
        *lifecycle.STAGES,
        Stage("UCL-S-0460", "Federate Across Frames", 460, "ELEVATION", depends_on=("UCL-S-0450",)),
    )
    execution = lifecycle.execute("subject", stages=extended)
    assert len(execution.outcomes) == 46
    assert execution.outcomes[-1].name == "Federate Across Frames"


# -- lineage ----------------------------------------------------------------- #


def test_lineage_is_appended_hash_chained_and_intact():
    ledger = lineage.LineageLedger()
    first = ledger.record(lineage.GENESIS, subject_id="ID-1", subject_key="k1")
    second = ledger.record(lineage.REGISTERED, subject_id="ID-1", subject_key="k1")
    assert first.prev_hash == ""
    assert second.prev_hash == first.entry_hash
    assert ledger.head == second.entry_hash
    assert ledger.is_intact() is True
    assert len(ledger) == 2
    assert ledger.lineage_of("ID-1") == (lineage.GENESIS, lineage.REGISTERED)
    assert ledger.subjects() == ("ID-1",)


def test_lineage_refuses_an_unnamed_event_or_subject():
    ledger = lineage.LineageLedger()
    with pytest.raises(NucleusError):
        ledger.record("", subject_id="ID-1", subject_key="k")
    with pytest.raises(NucleusError):
        ledger.record("e", subject_id="", subject_key="k")
    with pytest.raises(NucleusError):
        ledger.record("e", subject_id="ID", subject_key="")


def test_a_rewritten_lineage_is_detected():
    ledger = lineage.LineageLedger()
    ledger.record(lineage.GENESIS, subject_id="ID-1", subject_key="k1")
    entries = list(ledger.entries())
    forged = lineage.LineageEntry(
        sequence=1,
        event="forged",
        subject_id="ID-1",
        subject_key="k1",
        prev_hash="",
        entry_hash=entries[0].entry_hash,
    )
    assert lineage.LineageLedger([forged]).is_intact() is False


def test_registry_lineage_covers_every_subject_and_assignment():
    registry = build_seed_registry()
    ledger = lineage.ledger_for(registry)
    known = [s.universal_id for s in registry.subjects()]
    assert ledger.is_intact()
    assert ledger.unrecorded(known) == ()
    assert ledger.orphans(known + [c.universal_id for c in registry.capabilities()]) == ()
    assert len(ledger) == len(known) * 2 + len(registry.assignments())
    document = ledger.to_document()
    assert document["intact"] is True
    assert ledger.digest() == lineage.ledger_for(build_seed_registry()).digest()


def test_lineage_filters_by_event():
    registry = build_seed_registry()
    ledger = lineage.ledger_for(registry)
    assigned = ledger.entries(event=lineage.OWNERSHIP_ASSIGNED)
    assert len(assigned) == len(registry.assignments())


def test_supersession_is_recorded_as_such():
    from engine.nucleus.model import CapabilityDeclaration, SubjectDeclaration
    from engine.nucleus.registry import NucleusRegistry

    fresh = NucleusRegistry()
    fresh.register_subject(SubjectDeclaration(key="payment", title="Payment", concept="payment"))
    fresh.register_subject(SubjectDeclaration(key="billing", title="Billing", concept="billing"))
    fresh.register_capability(
        CapabilityDeclaration(key="invoice", title="Invoice", owner="payment")
    )
    fresh.reassign_capability("invoice", new_owner="billing", authority="TEST")
    ledger = lineage.ledger_for(fresh)
    assert len(ledger.entries(event=lineage.OWNERSHIP_SUPERSEDED)) == 1


# -- evolution --------------------------------------------------------------- #


def test_evolution_is_generational_linked_and_evidenced():
    ledger = EvolutionLedger()
    first = ledger.evolve(
        subject_id="ID-1",
        subject_key="payment",
        change="c1",
        authority="A",
        state={"capability": 1},
    )
    second = ledger.evolve(
        subject_id="ID-1",
        subject_key="payment",
        change="c2",
        authority="A",
        state={"capability": 2},
    )
    assert first.generation == 1 and second.generation == 2
    assert second.supersedes == first.evolution_id
    assert ledger.generation_of("ID-1") == 2
    assert ledger.chain_is_unbroken("ID-1") is True
    assert ledger.unevidenced() == ()
    assert ledger.latest("ID-1") == second
    assert ledger.lineage.is_intact()


def test_capability_regression_is_refused():
    ledger = EvolutionLedger(validator=state_must_grow)
    ledger.evolve(
        subject_id="ID-1", subject_key="k", change="c1", authority="A", state={"capability": 5}
    )
    with pytest.raises(EvolutionError) as exc:
        ledger.evolve(
            subject_id="ID-1", subject_key="k", change="c2", authority="A", state={"capability": 4}
        )
    assert "regressed" in exc.value.detail["reason"]


def test_the_growth_validator_requires_a_reading():
    ledger = EvolutionLedger(validator=state_must_grow)
    with pytest.raises(EvolutionError):
        ledger.evolve(subject_id="ID-1", subject_key="k", change="c", authority="A")
    ok, reason = state_must_grow(
        Evolution(
            subject_id="ID",
            subject_key="k",
            generation=1,
            change="c",
            authority="A",
            state={"capability": "not-a-number", "previous_capability": 1},
        )
    )
    assert ok is False and "numeric" in reason


def test_evolution_requires_its_declarations():
    with pytest.raises(EvolutionError):
        Evolution(subject_id="", subject_key="k", generation=1, change="c", authority="A")
    with pytest.raises(EvolutionError):
        Evolution(subject_id="ID", subject_key="k", generation=0, change="c", authority="A")


def test_permissive_validator_still_records_lineage():
    ledger = EvolutionLedger(validator=always_valid)
    ledger.evolve(subject_id="ID-1", subject_key="k", change="c", authority="A")
    document = ledger.to_document()
    assert document["count"] == 1
    assert document["chains_unbroken"] is True
    assert document["lineage_intact"] is True
    assert document["closed_set"] is False
    assert ledger.digest() == ledger.digest()
    assert ledger.evolutions()[0].to_dict()["generation"] == 1


def test_everything_evolves_through_one_mechanism():
    registry = build_seed_registry()
    ledger = EvolutionLedger(lineage=lineage.ledger_for(registry), validator=state_must_grow)
    population = list(registry.subjects()) + list(registry.capabilities())
    for index, item in enumerate(population, start=1):
        ledger.evolve(
            subject_id=item.universal_id,
            subject_key=item.key,
            change="stage-0",
            authority="UCOS-NUC-LAW-0001",
            state={"capability": index},
        )
    assert len(ledger.evolutions()) == len(population)
    assert ledger.unevidenced() == ()
    assert all(ledger.chain_is_unbroken(s) for s in ledger.subjects())
