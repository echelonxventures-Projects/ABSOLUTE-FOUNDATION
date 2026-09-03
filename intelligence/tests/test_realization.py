"""URI-000001 validation tests — Universal Realization Intelligence.

Proves the constitutional claims the subsystem makes:

  * deterministic          — identical canonical knowledge ⇒ byte-identical artifacts
  * knowledge-derived      — every artifact is anchored to canonical objects, and every
                             realizable canonical object reaches an artifact
  * governed               — twelve fail-closed gates, no vacuous pass, rejection blocks
                             materialization
  * traceable              — closure verified in both directions
  * additive + safe        — frozen corpus and path traversal are refused; re-running is
                             a byte-stable no-op; written bytes are verified
  * really generated       — the emitted Python compiles and the emitted runtime boots

Run: .ec1-venv/bin/python -m pytest intelligence/tests/test_realization.py -q
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from engine.knowledge.cko import CanonicalKnowledgeObject
from engine.knowledge.model import KnowledgeAuthority, KnowledgeKind, Lifecycle
from engine.knowledge.store import KnowledgeBase
from intelligence.realization import (
    FAMILY_ORDER,
    GATES,
    VERDICT_GOVERNED,
    ArtifactFamily,
    CompositionEngine,
    GeneratedArtifact,
    GenerationEngine,
    GenerationManifest,
    ImplementationEngine,
    KnowledgeIntake,
    MediaKind,
    PlanningEngine,
    Provenance,
    RealizationConfig,
    RealizationGovernor,
    RealizationIntelligenceEngine,
    TraceabilityEngine,
    build_evidence,
    enforce_realization,
    materialize_artifacts,
    registry_manifest,
    verify_bundle,
)
from intelligence.realization.cli import main as cli_main
from intelligence.realization.errors import (
    FrozenSurfaceError,
    GovernanceRejectedError,
    ImplementationError,
    KnowledgeIntakeError,
)

REPO = RealizationConfig.create().repo_root


# --------------------------------------------------------------------------- #
# fixtures                                                                    #
# --------------------------------------------------------------------------- #


def _config(tmp_path) -> RealizationConfig:
    """A configuration writing into a throwaway tree (never the repository)."""
    return RealizationConfig.create(
        REPO,
        artifact_root=tmp_path / "realization",
        evidence_dir=tmp_path / "evidence",
    )


@pytest.fixture
def engine(tmp_path) -> RealizationIntelligenceEngine:
    return RealizationIntelligenceEngine(_config(tmp_path))


@pytest.fixture(scope="module")
def pipeline():
    """The pure prefix of the pipeline over the repository's canonical knowledge."""
    eng = RealizationIntelligenceEngine()
    return eng.generate()


def _object(cko_id: str, **overrides) -> CanonicalKnowledgeObject:
    fields = {
        "cko_id": cko_id,
        "kind": KnowledgeKind.RULE,
        "title": f"Test object {cko_id}",
        "statement": f"Statement for {cko_id}.",
        "universe": "TESTING",
        "authority": KnowledgeAuthority.ENGINEERING,
        "owner": "UCOS-TEST",
        "lifecycle": Lifecycle.OPERATIONAL,
        "version": "1.0.0",
    }
    fields.update(overrides)
    return CanonicalKnowledgeObject.create(**fields)


def _synthetic_intake(*objects: CanonicalKnowledgeObject) -> KnowledgeIntake:
    return KnowledgeIntake.from_base(KnowledgeBase(objects), source="test")


# --------------------------------------------------------------------------- #
# canonical knowledge intake                                                  #
# --------------------------------------------------------------------------- #


def test_intake_loads_and_verifies_repository_canonical_knowledge() -> None:
    intake = KnowledgeIntake.load()
    assert intake.base.objects()
    assert all(record["verified"] for record in intake.integrity)
    assert intake.knowledge_seal
    assert intake.targets


def test_intake_derives_one_target_per_knowledge_universe() -> None:
    intake = KnowledgeIntake.load()
    universes = {obj.universe for obj in intake.base.objects()}
    assert {target.universe for target in intake.targets} == universes


def test_intake_refuses_mutated_canonical_knowledge() -> None:
    """A record whose hash no longer matches must fail intake, not propagate."""
    import dataclasses

    good = _object("UCKO-TEST-0001")
    tampered = dataclasses.replace(good, statement="mutated after sealing")
    with pytest.raises(KnowledgeIntakeError) as excinfo:
        _synthetic_intake(tampered)
    assert "UCKO-TEST-0001" in excinfo.value.context["failed"]


def test_intake_refuses_an_empty_canonical_store() -> None:
    with pytest.raises(KnowledgeIntakeError):
        KnowledgeIntake.from_base(KnowledgeBase(()), source="test")


def test_knowledge_seal_is_a_pure_function_of_canonical_knowledge() -> None:
    first = KnowledgeIntake.load()
    second = KnowledgeIntake.load()
    assert first.knowledge_seal == second.knowledge_seal


# --------------------------------------------------------------------------- #
# planning                                                                    #
# --------------------------------------------------------------------------- #


def test_plan_realizes_every_target_into_every_family(pipeline) -> None:
    _intake, plan, _composition, _findings, _manifest = pipeline
    for target in plan.targets:
        families = {step.family for step in plan.steps_for(target.target_id)}
        assert families == set(FAMILY_ORDER)


def test_plan_waves_cover_every_step_and_respect_dependencies(pipeline) -> None:
    _intake, plan, _composition, _findings, _manifest = pipeline
    waved = [step_id for wave in plan.waves for step_id in wave]
    assert sorted(waved) == sorted(step.step_id for step in plan.steps)
    level = {sid: idx for idx, wave in enumerate(plan.waves) for sid in wave}
    for step in plan.steps:
        for dependency in step.depends_on:
            assert level[dependency] < level[step.step_id]


def test_plan_has_no_coverage_gap_over_repository_knowledge(pipeline) -> None:
    _intake, plan, _composition, _findings, _manifest = pipeline
    assert plan.coverage_gaps == ()


def test_plan_is_deterministic() -> None:
    intake = KnowledgeIntake.load()
    planner = PlanningEngine()
    assert planner.plan(intake).seal == planner.plan(intake).seal


# --------------------------------------------------------------------------- #
# composition                                                                 #
# --------------------------------------------------------------------------- #


def test_composition_is_clean_and_ordered(pipeline) -> None:
    _intake, _plan, composition, findings, _manifest = pipeline
    assert findings.clean
    position = {unit_id: idx for idx, unit_id in enumerate(composition.order)}
    for unit in composition.units:
        for upstream in unit.upstream_units:
            assert position[upstream] < position[unit.unit_id]


def test_composition_detects_declared_conflicts() -> None:
    """Two canonical objects that conflict may not be composed into one unit."""
    left = _object("UCKO-TEST-C1", conflicts_with=("UCKO-TEST-C2",))
    right = _object("UCKO-TEST-C2", statement="A different statement.")
    intake = _synthetic_intake(left, right)
    plan = PlanningEngine().plan(intake)
    _composition, findings = CompositionEngine().compose(intake, plan)
    assert ("UCKO-TEST-C1", "UCKO-TEST-C2") in findings.conflicts
    assert not findings.clean


def test_composition_detects_duplicate_knowledge() -> None:
    """Identical knowledge under two identities violates the Knowledge Once Principle."""
    intake = _synthetic_intake(
        _object("UCKO-TEST-D1", statement="The very same statement."),
        _object("UCKO-TEST-D2", statement="The very same statement."),
    )
    plan = PlanningEngine().plan(intake)
    _composition, findings = CompositionEngine().compose(intake, plan)
    assert ("UCKO-TEST-D1", "UCKO-TEST-D2") in findings.duplicate_knowledge
    assert not findings.clean


# --------------------------------------------------------------------------- #
# generation                                                                  #
# --------------------------------------------------------------------------- #


def test_generation_is_byte_identical_across_two_passes(pipeline) -> None:
    intake, plan, composition, _findings, _manifest = pipeline
    proof = GenerationEngine().verify_determinism(intake, plan, composition)
    assert proof["deterministic"] is True
    assert proof["mismatches"] == []


def test_every_artifact_is_anchored_to_canonical_knowledge(pipeline) -> None:
    intake, _plan, _composition, _findings, manifest = pipeline
    known = set(intake.object_ids())
    assert manifest.artifacts
    for artifact in manifest.artifacts:
        assert artifact.provenance.source_ckos
        assert set(artifact.provenance.source_ckos) <= known


def test_every_artifact_carries_complete_provenance(pipeline) -> None:
    intake, _plan, _composition, _findings, manifest = pipeline
    for artifact in manifest.artifacts:
        provenance = artifact.provenance.to_dict()
        for field in (
            "generator",
            "generator_version",
            "capability",
            "plan_id",
            "step_id",
            "unit_id",
            "target_id",
            "knowledge_seal",
        ):
            assert provenance[field], f"{artifact.relative_path} missing {field}"
        assert provenance["knowledge_seal"] == intake.knowledge_seal
        assert provenance["authority"].startswith("NONE")


def test_all_seven_families_are_generated(pipeline) -> None:
    _intake, _plan, _composition, _findings, manifest = pipeline
    assert set(manifest.by_family()) == {family.value for family in FAMILY_ORDER}


def test_generated_python_artifacts_compile(pipeline) -> None:
    _intake, _plan, _composition, _findings, manifest = pipeline
    python_artifacts = [art for art in manifest.artifacts if art.media is MediaKind.PYTHON]
    assert python_artifacts
    for artifact in python_artifacts:
        compile(artifact.content, artifact.relative_path, "exec")


def test_generated_json_artifacts_parse_and_cite_the_knowledge_seal(pipeline) -> None:
    intake, _plan, _composition, _findings, manifest = pipeline
    json_artifacts = [art for art in manifest.artifacts if art.media is MediaKind.JSON]
    assert json_artifacts
    for artifact in json_artifacts:
        document = json.loads(artifact.content)
        assert document["knowledge_seal"] == intake.knowledge_seal
        assert document["provenance"]["knowledge_seal"] == intake.knowledge_seal


def test_generated_artifacts_carry_no_wall_clock(pipeline) -> None:
    """Identity is content, never time — no generated body may embed a timestamp."""
    _intake, _plan, _composition, _findings, manifest = pipeline
    for artifact in manifest.artifacts:
        if artifact.media is MediaKind.JSON:
            document = json.loads(artifact.content)
            assert "generated_at" not in document
            assert "timestamp" not in document


def test_generator_registry_is_complete_and_unambiguous() -> None:
    manifest = registry_manifest()
    assert len(manifest) == len(FAMILY_ORDER)
    assert [entry["family"] for entry in manifest] == [f.value for f in FAMILY_ORDER]
    assert len({entry["generator"] for entry in manifest}) == len(FAMILY_ORDER)


# --------------------------------------------------------------------------- #
# governance                                                                  #
# --------------------------------------------------------------------------- #


def test_repository_realization_is_governed() -> None:
    decision = RealizationIntelligenceEngine().govern()
    assert decision.verdict == VERDICT_GOVERNED, decision.blocking_reasons
    assert decision.passed_count == len(GATES)


def test_every_declared_gate_is_present_and_actually_exercised() -> None:
    decision = RealizationIntelligenceEngine().govern()
    assert sorted(gate.gate for gate in decision.gates) == sorted(GATES)
    for gate in decision.gates:
        assert gate.checked > 0, f"{gate.gate} passed vacuously"


def test_gates_fail_closed_when_evidence_is_absent(pipeline) -> None:
    """A gate with no evidence supplied must FAIL, never pass by default."""
    intake, plan, composition, findings, manifest = pipeline
    decision = RealizationGovernor().adjudicate(
        intake=intake,
        plan=plan,
        composition=composition,
        findings=findings,
        manifest=manifest,
        determinism=None,
        ledger=None,
    )
    assert not decision.governed
    failed = {gate.gate for gate in decision.gates if not gate.passed}
    assert failed == {"GENERATION_DETERMINISM", "TRACE_CLOSURE"}
    assert "GENERATION_DETERMINISM:unexercised" in decision.blocking_reasons


def test_enforcement_raises_on_a_rejected_decision(pipeline) -> None:
    intake, plan, composition, findings, manifest = pipeline
    decision = RealizationGovernor().adjudicate(
        intake=intake,
        plan=plan,
        composition=composition,
        findings=findings,
        manifest=manifest,
    )
    with pytest.raises(GovernanceRejectedError):
        enforce_realization(decision)


def test_duplicate_knowledge_rejects_the_run() -> None:
    intake = _synthetic_intake(
        _object("UCKO-TEST-D1", statement="The very same statement."),
        _object("UCKO-TEST-D2", statement="The very same statement."),
    )
    plan = PlanningEngine().plan(intake)
    composition, findings = CompositionEngine().compose(intake, plan)
    manifest = GenerationEngine().generate(intake, plan, composition)
    determinism = GenerationEngine().verify_determinism(intake, plan, composition)
    ledger = TraceabilityEngine().build(intake, plan, composition, manifest)
    decision = RealizationGovernor().adjudicate(
        intake=intake,
        plan=plan,
        composition=composition,
        findings=findings,
        manifest=manifest,
        determinism=determinism,
        ledger=ledger,
    )
    assert not decision.governed
    assert any(
        reason.startswith("COMPOSITION_NO_DUPLICATE_KNOWLEDGE")
        for reason in decision.blocking_reasons
    )


def test_decision_is_sealed_and_deterministic() -> None:
    engine = RealizationIntelligenceEngine()
    assert engine.govern().seal == engine.govern().seal


# --------------------------------------------------------------------------- #
# traceability                                                                #
# --------------------------------------------------------------------------- #


def test_traceability_is_closed_in_both_directions(pipeline) -> None:
    intake, plan, composition, _findings, manifest = pipeline
    ledger = TraceabilityEngine().build(intake, plan, composition, manifest)
    assert ledger.forward_gaps == ()
    assert ledger.orphan_artifacts == ()
    assert ledger.closed


def test_trace_chain_reaches_artifacts_from_a_canonical_object(pipeline) -> None:
    intake, plan, composition, _findings, manifest = pipeline
    ledger = TraceabilityEngine().build(intake, plan, composition, manifest)
    cko_id = intake.object_ids()[0]
    chain = ledger.chain(cko_id)
    assert chain["canonical-object->target"]
    assert chain["target->step"]
    assert chain["step->unit"]
    assert chain["unit->artifact"]


def test_orphan_artifact_breaks_closure(pipeline) -> None:
    """An artifact with no canonical ancestor must be reported, not tolerated."""
    intake, plan, composition, _findings, manifest = pipeline
    orphan = GeneratedArtifact(
        relative_path="orphan/invented.json",
        family=ArtifactFamily.ARCHITECTURE,
        media=MediaKind.JSON,
        content="{}\n",
        provenance=Provenance(
            generator="test.orphan",
            generator_version="0.0.0",
            capability="URI-000001",
            plan_id=plan.plan_id,
            step_id="STEP",
            unit_id="UNIT",
            target_id="TARGET",
            knowledge_seal=intake.knowledge_seal,
            source_ckos=(),
        ),
    )
    polluted = GenerationManifest(
        composition_id=manifest.composition_id,
        composition_seal=manifest.composition_seal,
        plan_id=manifest.plan_id,
        knowledge_seal=manifest.knowledge_seal,
        artifacts=(*manifest.artifacts, orphan),
    )
    ledger = TraceabilityEngine().build(intake, plan, composition, polluted)
    assert "orphan/invented.json" in ledger.orphan_artifacts
    assert not ledger.closed


# --------------------------------------------------------------------------- #
# implementation safety                                                       #
# --------------------------------------------------------------------------- #


def _manifest_with(path: str, pipeline) -> GenerationManifest:
    intake, plan, _composition, _findings, manifest = pipeline
    artifact = GeneratedArtifact(
        relative_path=path,
        family=ArtifactFamily.ARCHITECTURE,
        media=MediaKind.JSON,
        content="{}\n",
        provenance=Provenance(
            generator="test",
            generator_version="0.0.0",
            capability="URI-000001",
            plan_id=plan.plan_id,
            step_id="STEP",
            unit_id="UNIT",
            target_id="TARGET",
            knowledge_seal=intake.knowledge_seal,
            source_ckos=(intake.object_ids()[0],),
        ),
    )
    return GenerationManifest(
        composition_id=manifest.composition_id,
        composition_seal=manifest.composition_seal,
        plan_id=manifest.plan_id,
        knowledge_seal=manifest.knowledge_seal,
        artifacts=(artifact,),
    )


def test_materialization_refuses_the_frozen_corpus(pipeline) -> None:
    frozen_config = RealizationConfig.create(REPO, artifact_root=REPO / "00-BOOK")
    implementer = ImplementationEngine(frozen_config)
    with pytest.raises(FrozenSurfaceError):
        implementer.preflight(_manifest_with("uri-should-never-exist.json", pipeline))


def test_materialization_refuses_path_traversal(tmp_path, pipeline) -> None:
    implementer = ImplementationEngine(_config(tmp_path))
    with pytest.raises(ImplementationError):
        implementer.preflight(_manifest_with("../escaped.json", pipeline))


def test_materialization_refuses_an_absolute_path(tmp_path, pipeline) -> None:
    implementer = ImplementationEngine(_config(tmp_path))
    with pytest.raises(ImplementationError):
        implementer.preflight(_manifest_with("/etc/uri-escape.json", pipeline))


def test_materialization_refuses_an_empty_manifest(tmp_path, pipeline) -> None:
    _intake, _plan, _composition, _findings, manifest = pipeline
    empty = GenerationManifest(
        composition_id=manifest.composition_id,
        composition_seal=manifest.composition_seal,
        plan_id=manifest.plan_id,
        knowledge_seal=manifest.knowledge_seal,
        artifacts=(),
    )
    with pytest.raises(ImplementationError):
        ImplementationEngine(_config(tmp_path)).materialize(empty)


def test_dry_run_writes_nothing(engine) -> None:
    result = engine.realize(dry_run=True, emit=False)
    assert result.governed
    assert result.record is not None
    assert result.record.dry_run is True
    assert not engine.config.artifact_root.exists()


# --------------------------------------------------------------------------- #
# end-to-end realization                                                      #
# --------------------------------------------------------------------------- #


def test_realize_materializes_and_verifies_every_artifact(engine) -> None:
    result = engine.realize()
    assert result.governed
    assert result.record is not None
    assert result.record.verified is True
    assert len(result.record.files) == len(result.manifest.artifacts)
    for item in result.record.files:
        path = engine.config.artifact_root / item.relative_path
        assert path.is_file()


def test_realize_is_idempotent(engine) -> None:
    engine.realize()
    second = engine.realize()
    assert second.record is not None
    assert set(second.record.actions()) == {"unchanged"}


def test_realize_emits_the_complete_evidence_bundle(engine) -> None:
    from intelligence.realization.evidence import REQUIRED_FILES

    result = engine.realize()
    assert result.evidence.missing() == ()
    assert sorted(result.emitted) == sorted(REQUIRED_FILES)
    report = verify_bundle(engine.config)
    assert report["complete"] is True
    assert report["checked"] == len(REQUIRED_FILES)
    assert report["failed"] == []


def test_evidence_documents_are_individually_sealed(engine) -> None:
    from intelligence.realization.canonical import verify_seal

    result = engine.realize()
    for name, path in result.emitted.items():
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
        assert verify_seal(document), f"{name} seal mismatch"


def test_evidence_varies_only_where_the_materialization_pass_differs(engine) -> None:
    """Re-running changes exactly one fact: what the materialization pass did.

    The first pass creates files; the second finds them byte-identical and reports
    ``unchanged``. Exactly two documents may reflect that — the implementation record
    that states the observation, and the evidence record that seals it. Every
    knowledge-derived document must be byte-identical.

    The governance decision is NO LONGER among them. It varied only because it cites
    ``implementation_id``, and that id was sealed over the per-file ``action`` — so a
    pristine clone reporting ``created`` and every later pass reporting ``unchanged``
    produced two different implementation identities from identical canonical
    knowledge. ``realization/UCOS-URI-MANIFEST.json`` therefore had no fixed point,
    which is why ``intelligence/realization/engine.py`` could not be added to
    scripts/generate-prerequisites.sh and ``realization/`` stayed the one open
    bootstrap gap in the generated-artifact registry.

    ``action`` is now excluded from the seal and from the manifest (UAKOS-CLOSURE-008:
    an execution transcript is evidence, never identity). The observation is preserved
    where it belongs — on the returned record, in the structured log, and in these two
    evidence documents.
    """
    from intelligence.realization.evidence import (
        GOVERNANCE_FILE,
        IMPLEMENTATION_FILE,
        RECORD_FILE,
    )

    first = engine.realize()
    second = engine.realize()
    assert first.record is not None and second.record is not None
    assert set(first.record.actions()) == {"created"}
    assert set(second.record.actions()) == {"unchanged"}
    varied = {
        name
        for name in first.evidence.documents
        if first.evidence.documents[name] != second.evidence.documents[name]
    }
    assert varied == {IMPLEMENTATION_FILE, RECORD_FILE}
    # The implementation IDENTITY is now a function of what was materialized, not of
    # what the filesystem held first — so the same knowledge yields one id, always.
    assert first.record.seal == second.record.seal
    assert first.record.implementation_id == second.record.implementation_id
    assert first.evidence.documents[GOVERNANCE_FILE] == second.evidence.documents[GOVERNANCE_FILE]
    # The governance verdict itself is unchanged — only the id it cites moved.
    assert first.decision.verdict == second.decision.verdict == VERDICT_GOVERNED
    assert [gate.to_dict() for gate in first.decision.gates] == [
        gate.to_dict() for gate in second.decision.gates
    ]


def test_knowledge_derived_evidence_is_independent_of_the_output_location(engine, tmp_path) -> None:
    """The knowledge-derived documents must not depend on where output happens to land.

    Only the implementation record legitimately differs between two output roots — it
    records the path it actually wrote to. Everything upstream of materialization is a
    pure function of canonical knowledge and must be byte-identical.
    """
    from intelligence.realization.evidence import (
        COMPOSITION_FILE,
        GENERATION_FILE,
        INTAKE_FILE,
        PLAN_FILE,
        TRACEABILITY_FILE,
    )

    first = engine.realize()
    other = RealizationIntelligenceEngine(_config(tmp_path / "elsewhere"))
    second = other.realize()
    for name in (
        INTAKE_FILE,
        PLAN_FILE,
        COMPOSITION_FILE,
        GENERATION_FILE,
        TRACEABILITY_FILE,
    ):
        assert (
            first.evidence.documents[name] == second.evidence.documents[name]
        ), f"{name} depends on the output location"
    assert first.manifest.seal == second.manifest.seal
    assert first.plan.seal == second.plan.seal


def test_verify_reports_a_corrupted_artifact(engine) -> None:
    result = engine.realize()
    victim = engine.config.artifact_root / result.manifest.artifacts[0].relative_path
    victim.write_text("tampered\n", encoding="utf-8")
    report = engine.implementer.verify(result.manifest)
    assert report["verified"] is False
    assert report["failed"]


def test_generated_runtime_boots_against_canonical_knowledge(engine) -> None:
    """The emitted runtime module is executable and enforces its own checks."""
    result = engine.realize()
    runtime_modules = [
        art.relative_path
        for art in result.manifest.artifacts
        if art.family is ArtifactFamily.RUNTIME and art.media is MediaKind.PYTHON
    ]
    assert runtime_modules
    for relative in runtime_modules:
        path = engine.config.artifact_root / relative
        spec = importlib.util.spec_from_file_location(f"uri_test_{path.stem}", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.boot(result.intake.base)
        assert report["ready"] is True, report["failed_checks"]


def test_generated_api_route_table_dispatches(engine) -> None:
    result = engine.realize()
    route_modules = [
        art.relative_path
        for art in result.manifest.artifacts
        if art.family is ArtifactFamily.API and art.media is MediaKind.PYTHON
    ]
    assert route_modules
    for relative in route_modules:
        path = engine.config.artifact_root / relative
        spec = importlib.util.spec_from_file_location(f"uri_routes_{path.stem}", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        records = module.list_objects(result.intake.base)
        assert records
        assert {record["universe"] for record in records} == {module.UNIVERSE}
        assert module.list_kinds(result.intake.base) == list(module.KINDS)


def test_result_summary_is_serialisable_and_deterministic(engine) -> None:
    summary = engine.realize().summary()
    encoded = json.dumps(summary, sort_keys=True)
    assert summary["verdict"] == VERDICT_GOVERNED
    assert summary["trace_closed"] is True
    assert summary["deterministic"] is True
    assert "URI-000001" in encoded


def test_evidence_build_is_pure(pipeline) -> None:
    """Building evidence writes nothing and is a function of the stage outputs."""
    intake, plan, composition, findings, manifest = pipeline
    determinism = GenerationEngine().verify_determinism(intake, plan, composition)
    ledger = TraceabilityEngine().build(intake, plan, composition, manifest)
    decision = RealizationGovernor().adjudicate(
        intake=intake,
        plan=plan,
        composition=composition,
        findings=findings,
        manifest=manifest,
        determinism=determinism,
        ledger=ledger,
    )
    kwargs = {
        "intake": intake,
        "plan": plan,
        "composition": composition,
        "findings": findings,
        "manifest": manifest,
        "decision": decision,
        "ledger": ledger,
        "determinism": determinism,
    }
    assert build_evidence(**kwargs).record_hash == build_evidence(**kwargs).record_hash


# --------------------------------------------------------------------------- #
# command surface                                                             #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "command",
    ["intake", "plan", "compose", "generate", "govern", "trace", "verify", "generators"],
)
def test_cli_read_only_commands_exit_zero(command, tmp_path, capsys) -> None:
    exit_code = cli_main(
        [
            "--repo",
            str(REPO),
            "--artifact-root",
            str(tmp_path / "realization"),
            "--evidence-dir",
            str(tmp_path / "evidence"),
            command,
        ]
    )
    captured = capsys.readouterr()
    if command == "verify":
        # verify inspects on-disk state, which is empty for a throwaway root.
        assert exit_code in (0, 1)
    else:
        assert exit_code == 0, captured.out
    assert json.loads(captured.out)


def test_cli_realize_writes_into_the_configured_roots(tmp_path, capsys) -> None:
    artifacts = tmp_path / "realization"
    evidence = tmp_path / "evidence"
    exit_code = cli_main(
        [
            "--repo",
            str(REPO),
            "--artifact-root",
            str(artifacts),
            "--evidence-dir",
            str(evidence),
            "realize",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["verdict"] == VERDICT_GOVERNED
    assert (artifacts / "UCOS-URI-MANIFEST.json").is_file()
    assert (evidence / "realization-evidence-record.json").is_file()


# --------------------------------------------------------------------------- #
# implementation: verification, pruning and the convenience entry point        #
#                                                                             #
# WHY THESE EXIST. Materialization was exercised end to end, so its happy path #
# was covered and none of its refusals were: the byte-level verification that  #
# catches an artifact edited after it was sealed, the bounded pruning of files #
# a previous pass generated, and the module-level entry point the CLI documents#
# were all unexecuted. A verifier nothing has caught out is not a verifier.    #
# --------------------------------------------------------------------------- #


def test_verify_reports_a_present_artifact_that_no_longer_matches_its_seal(
    tmp_path, pipeline
) -> None:
    manifest = _manifest_with("checked.json", pipeline)
    implementer = ImplementationEngine(_config(tmp_path))
    implementer.materialize(manifest)

    target = implementer.config.artifact_root / "checked.json"
    target.write_text('{"edited": true}\n', encoding="utf-8")

    report = implementer.verify(manifest)
    assert report["verified"] is False
    assert report["checked"] == 1
    assert report["failed"][0]["path"] == "checked.json"
    assert report["failed"][0]["present"] is True


def test_verify_reports_an_artifact_that_is_absent_entirely(tmp_path, pipeline) -> None:
    manifest = _manifest_with("never-written.json", pipeline)
    report = ImplementationEngine(_config(tmp_path)).verify(manifest)
    assert report["verified"] is False
    assert report["failed"][0]["actual"] is None
    assert report["failed"][0]["present"] is False


def test_materialization_raises_when_the_bytes_on_disk_disagree_with_the_seal(
    tmp_path, pipeline, monkeypatch
) -> None:
    """The raising verification inside ``materialize`` is the one that must never be
    skipped: it is what makes the returned record an attestation rather than a log. It
    is forged by corrupting the write, because a correct write cannot reach it."""
    manifest = _manifest_with("corrupted.json", pipeline)
    implementer = ImplementationEngine(_config(tmp_path))

    real_write = Path.write_text

    def _short_write(self, data, *args, **kwargs):
        if self.name == "corrupted.json":
            return real_write(self, "{}", *args, **kwargs)
        return real_write(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", _short_write)
    with pytest.raises(ImplementationError) as excinfo:
        implementer.materialize(manifest)
    assert "do not match" in str(excinfo.value)


def test_an_artifact_root_that_is_not_a_parent_of_the_resolved_path_is_refused(
    tmp_path, pipeline
) -> None:
    """A path that survives the traversal and absolute checks but still resolves outside
    the artifact root — here through a symlink — is refused by the containment check."""
    config = _config(tmp_path)
    config.artifact_root.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (config.artifact_root / "link").symlink_to(outside, target_is_directory=True)

    implementer = ImplementationEngine(config)
    with pytest.raises(ImplementationError, match="outside the artifact root"):
        implementer.preflight(_manifest_with("link", pipeline))


def test_nothing_is_stale_before_a_first_pass_has_written_a_manifest(tmp_path, pipeline) -> None:
    implementer = ImplementationEngine(_config(tmp_path))
    assert implementer.stale_artifacts(_manifest_with("a.json", pipeline)) == ()


def test_an_unreadable_manifest_of_record_yields_no_previous_paths(tmp_path, pipeline) -> None:
    """A corrupt manifest must not make pruning claim that every current artifact is
    stale; it yields nothing, which is the fail-safe direction for a delete."""
    implementer = ImplementationEngine(_config(tmp_path))
    implementer.manifest_path().parent.mkdir(parents=True, exist_ok=True)
    implementer.manifest_path().write_text("{ not json", encoding="utf-8")
    assert implementer.stale_artifacts(_manifest_with("a.json", pipeline)) == ()


def test_an_artifact_a_previous_pass_claimed_and_this_one_does_not_is_stale(
    tmp_path, pipeline
) -> None:
    implementer = ImplementationEngine(_config(tmp_path))
    implementer.materialize(_manifest_with("first.json", pipeline))

    current = _manifest_with("second.json", pipeline)
    assert implementer.stale_artifacts(current) == ("first.json",)


def test_pruning_is_a_dry_run_by_default_and_removes_nothing(tmp_path, pipeline) -> None:
    implementer = ImplementationEngine(_config(tmp_path))
    implementer.materialize(_manifest_with("first.json", pipeline))
    stale_path = implementer.config.artifact_root / "first.json"

    report = implementer.prune(_manifest_with("second.json", pipeline))
    assert report["dry_run"] is True
    assert report["stale"] == ["first.json"]
    assert report["removed"] == ["first.json"]
    assert stale_path.is_file()


def test_pruning_removes_the_stale_artifact_when_it_is_not_a_dry_run(tmp_path, pipeline) -> None:
    implementer = ImplementationEngine(_config(tmp_path))
    implementer.materialize(_manifest_with("first.json", pipeline))
    stale_path = implementer.config.artifact_root / "first.json"

    report = implementer.prune(_manifest_with("second.json", pipeline), dry_run=False)
    assert report["removed"] == ["first.json"]
    assert not stale_path.exists()


def test_a_stale_entry_whose_file_is_already_gone_is_not_reported_as_removed(
    tmp_path, pipeline
) -> None:
    implementer = ImplementationEngine(_config(tmp_path))
    implementer.materialize(_manifest_with("first.json", pipeline))
    (implementer.config.artifact_root / "first.json").unlink()

    report = implementer.prune(_manifest_with("second.json", pipeline), dry_run=False)
    assert report["stale"] == ["first.json"]
    assert report["removed"] == []


def test_the_convenience_entry_point_materializes_the_same_manifest(tmp_path, pipeline) -> None:
    config = _config(tmp_path)
    record = materialize_artifacts(_manifest_with("direct.json", pipeline), config)
    assert record.verified is True
    assert (config.artifact_root / "direct.json").is_file()
