"""UVI-000001 — the Universal Verification Intelligence, measured.

What these tests are for
------------------------
A verification selector's dangerous failure is not slowness. It is a green run that
skipped the affected test, because the symptom of that is indistinguishable from
success. So the tests below are weighted toward the refusals rather than the happy path:
every one of them is a way the intelligence could make a run report more than it
measured, pinned so it fails here instead of shipping as a faster green run.

The four that matter most:

* :func:`test_an_unbounded_change_always_widens` — the fail-wide asymmetry, over every
  class of change no graph in this repository can bound.
* :func:`test_a_partition_never_loses_a_test_object` — topology neutrality at every
  worker count, including the split-file case where a unit is a node rather than a file.
* :func:`test_a_certification_mode_can_never_reach_a_reuse_decision` — a certification
  that reuses a result certifies a cache.
* :func:`test_the_baseline_contract_is_a_ratchet` — every gate the certification default
  ran before this rework is still declared and still admitted by every certifying mode.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from engine.verification_intelligence import gate as uvi_gate
from engine.verification_intelligence.constitution import (
    execution_contract,
    load_constitution,
    load_declaration,
    repo_root,
    verify_source,
)
from engine.verification_intelligence.evidence import (
    EVIDENCE_VERSION,
    decide,
    input_digest,
    lookup,
    record,
    resolve_prefix,
)
from engine.verification_intelligence.execution import (
    assert_topology_neutral,
    plan_shards,
    resolve_workers,
    unit_file,
)
from engine.verification_intelligence.gate import every_declared_read_set_resolves
from engine.verification_intelligence.model import (
    Action,
    Coverage,
    Selection,
    Shard,
    VerificationIntelligenceError,
)
from engine.verification_intelligence.plan import (
    build_plan,
    plan_digest,
    plan_json,
    plan_tsv,
)
from engine.verification_intelligence.registry import (
    build_test_registry,
    collection_roots,
    is_collectible,
    load_substrates,
)
from engine.verification_intelligence.selection import select

REPO = repo_root()


@pytest.fixture(scope="module")
def substrates():
    return load_substrates()


@pytest.fixture(scope="module")
def tests_registry(substrates):
    return build_test_registry(substrates)


@pytest.fixture(scope="module")
def constitution():
    return load_constitution(checks=frozenset(uvi_gate.CHECKS))


# --- the constitution ---------------------------------------------------------------


def test_the_declaration_constructs_and_binds_every_law_to_a_check(constitution) -> None:
    """A law naming a check nothing implements would be governance by assertion."""
    assert constitution.artifact_id == "UVI-000001"
    assert {law.check for law in constitution.laws} == set(uvi_gate.CHECKS)


def test_a_law_naming_a_missing_check_refuses_to_construct(tmp_path) -> None:
    document = load_declaration()
    document["laws"].append(
        {"id": "X", "title": "t", "statement": "s", "check": "no_such_check_exists"}
    )
    path = tmp_path / "declaration.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(VerificationIntelligenceError, match="not implemented"):
        load_constitution(str(path), checks=frozenset(uvi_gate.CHECKS))


def test_a_reusable_stage_with_no_declared_inputs_refuses_to_construct(tmp_path) -> None:
    """A cache key covering nothing is a permanent false hit, so it is refused up front."""
    document = load_declaration()
    for stage in document["stage_registry"]["stages"]:
        stage["reusable"] = True
        stage.pop("reuse_inputs", None)
    path = tmp_path / "declaration.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(VerificationIntelligenceError, match="reuse_inputs"):
        load_constitution(str(path))


def test_two_stages_may_not_share_one_label(tmp_path) -> None:
    """The label is the join key to verify.sh and to the canonical validation record."""
    document = load_declaration()
    stages = document["stage_registry"]["stages"]
    stages[1]["label"] = stages[0]["label"]
    path = tmp_path / "declaration.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(VerificationIntelligenceError, match="label"):
        load_constitution(str(path))


def test_a_mode_listing_an_undeclared_stage_is_refused(tmp_path, constitution) -> None:
    document = load_declaration()
    for mode in document["mode_constitution"]["modes"]:
        mode["stages"] = ["a-stage-that-does-not-exist"]
    path = tmp_path / "declaration.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    broken = load_constitution(str(path))
    with pytest.raises(VerificationIntelligenceError, match="undeclared stage"):
        broken.stages_for(broken.mode("fast"))


def test_an_absent_declaration_is_a_fault_and_not_a_default(tmp_path) -> None:
    """There is deliberately no fallback constitution; one would be a second constitution."""
    with pytest.raises(VerificationIntelligenceError, match="unreadable"):
        load_constitution(str(tmp_path / "absent.json"))


def test_every_certification_mode_runs_the_whole_suite_under_the_floor(constitution) -> None:
    for mode in constitution.modes:
        if mode.certification_eligible:
            assert mode.selection is Selection.WHOLE_SUITE
            assert mode.coverage is Coverage.FLOOR_90
            assert not mode.evidence_reuse
        else:
            assert mode.claims_not, f"--{mode.mode_id} states nothing it does not claim"


# --- the Test Object Registry -------------------------------------------------------


def test_the_registry_projects_exactly_what_pytest_collects(tests_registry) -> None:
    roots = collection_roots()
    for path in tests_registry.paths:
        assert is_collectible(path, roots)
    assert tests_registry.objects, "the projection is empty"


def test_a_test_object_that_pytest_would_not_collect_is_not_selectable() -> None:
    roots = ("engine/tests",)
    assert is_collectible("engine/tests/unit/test_x.py", roots)
    assert not is_collectible("engine/tests/unit/helpers.py", roots)
    assert not is_collectible("engine/tests/unit/__init__.py", roots)
    assert not is_collectible("platform/tests/test_x.py", roots)
    assert not is_collectible("engine/tests/unit/test_x.txt", roots)


def test_an_unmeasured_object_is_over_priced_rather_than_assumed_cheap(tests_registry) -> None:
    """Under-pricing an unknown packs it into a shard the whole run then waits on."""
    from engine.verification_intelligence.registry import DEFAULT_COST_SECONDS

    assert tests_registry.cost_of("engine/tests/unit/a_file_nobody_measured.py") == (
        DEFAULT_COST_SECONDS
    )


# --- selection ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("description", "path"),
    [
        ("a registry or declaration with no import edges", "00-BOOK/DATA/uvi-probe.json"),
        ("a file type carrying no edges at all", "docs/uvi-probe.md"),
        ("a Python file absent from the executable registry", "engine/uvi_probe.py"),
        ("the selector's own substrate", "00-MASTER/UCOS-UGA-001/uvi-probe.py"),
        ("the build contract", "pyproject.toml"),
    ],
)
def test_an_unbounded_change_always_widens(description, path, substrates, tests_registry) -> None:
    """THE asymmetry. Every path no graph can bound runs the whole suite, and says why."""
    result = select((path,), substrates=substrates, tests=tests_registry)
    assert result.selection is Selection.WHOLE_SUITE, description
    assert result.test_paths == tests_registry.paths
    assert result.escalations, "it widened without naming a reason"


def test_a_bounded_change_selects_a_proper_subset(substrates, tests_registry) -> None:
    """A change with resolvable edges must not run everything, or selection is theatre."""
    result = select(("engine/uaue/gate.py",), substrates=substrates, tests=tests_registry)
    assert result.selection is Selection.IMPACT
    assert 0 < len(result.test_paths) < len(tests_registry.paths)
    assert not result.escalations


def test_the_selection_reaches_the_test_that_imports_the_change(substrates, tests_registry) -> None:
    result = select(("engine/uaue/gate.py",), substrates=substrates, tests=tests_registry)
    assert "engine/tests/unit/test_uaue_controller.py" in result.test_paths


def test_every_declared_substrate_layer_is_reported(substrates, tests_registry) -> None:
    """A layer that runs but reports nothing cannot be audited for over- or under-reach."""
    result = select(("engine/uaue/gate.py",), substrates=substrates, tests=tests_registry)
    assert [name for name, _ in result.layers] == [
        "IDENTITY",
        "DEPENDENCY",
        "OWNERSHIP",
        "CAPABILITY",
        "RELATIONSHIP",
    ]


def test_no_change_selects_nothing_and_claims_nothing(substrates, tests_registry) -> None:
    result = select((), substrates=substrates, tests=tests_registry)
    assert result.test_paths == ()
    assert result.selection is Selection.IMPACT


def test_a_change_to_the_selector_itself_escalates(substrates, tests_registry) -> None:
    """Self-application: the selector cannot be verified by asking it what to verify."""
    result = select(
        ("engine/verification_intelligence/selection.py",),
        substrates=substrates,
        tests=tests_registry,
    )
    assert result.selection is Selection.WHOLE_SUITE
    assert any("selector" in reason for reason in result.escalations)


# --- sharding and topology ----------------------------------------------------------


@pytest.mark.parametrize("workers", [1, 2, 3, 5, 12, 64])
def test_a_partition_never_loses_a_test_object(workers, tests_registry) -> None:
    """The failure that could turn a green run into a false one, at every worker count."""
    units = tests_registry.units_for(tests_registry.paths)
    shards = plan_shards(units, tests_registry, workers)
    placed = [unit for shard in shards for unit in shard.test_paths]
    assert len(placed) == len(set(placed)), "a unit was placed twice"
    assert sorted({unit_file(unit) for unit in placed}) == sorted(tests_registry.paths)


def test_partitioning_twice_produces_identical_shards(tests_registry) -> None:
    units = tests_registry.units_for(tests_registry.paths)
    first = plan_shards(units, tests_registry, 7)
    second = plan_shards(units, tests_registry, 7)
    assert [shard.test_paths for shard in first] == [shard.test_paths for shard in second]


def test_an_oversized_test_object_is_split_into_its_nodes(tests_registry) -> None:
    """One file was 46% of the whole suite; no shard count can finish sooner than that."""
    if not tests_registry.splittable:
        pytest.skip("no measured object exceeds the declared split threshold")
    split = sorted(tests_registry.splittable)[0]
    units = tests_registry.units_for((split,))
    assert len(units) > 1
    assert all(unit.startswith(f"{split}::") for unit in units)
    assert all(unit_file(unit) == split for unit in units)


def test_a_partition_that_splits_a_file_without_a_remainder_shard_is_refused() -> None:
    """Nodes in one shard and no remainder means the file's unmeasured tests run nowhere."""
    shards = (
        Shard(index=0, test_paths=("a/test_x.py::test_one",), cost_seconds=1.0),
        Shard(index=1, test_paths=("a/test_y.py",), cost_seconds=1.0),
    )
    with pytest.raises(VerificationIntelligenceError, match="would run twice"):
        assert_topology_neutral(shards, ("a/test_x.py", "a/test_y.py"))


def test_a_partition_whose_deselects_do_not_match_its_nodes_is_refused() -> None:
    """A node both deselected and unplaced runs nowhere; one placed twice runs twice."""
    shards = (
        Shard(index=0, test_paths=("a/test_x.py",), cost_seconds=1.0, deselect=("a/test_x.py::b",)),
        Shard(index=1, test_paths=("a/test_x.py::c",), cost_seconds=1.0),
    )
    with pytest.raises(VerificationIntelligenceError, match="run nowhere"):
        assert_topology_neutral(shards, ("a/test_x.py",))


def test_a_split_file_with_a_remainder_shard_is_accepted() -> None:
    """The legitimate shape: one shard holds the file minus exactly what the others took."""
    shards = (
        Shard(
            index=0,
            test_paths=("a/test_x.py",),
            cost_seconds=1.0,
            deselect=("a/test_x.py::two",),
        ),
        Shard(index=1, test_paths=("a/test_x.py::two",), cost_seconds=1.0),
    )
    assert_topology_neutral(shards, ("a/test_x.py",))


def test_a_partition_that_drops_a_test_object_is_refused() -> None:
    shards = (Shard(index=0, test_paths=("a/test_x.py",), cost_seconds=1.0),)
    with pytest.raises(VerificationIntelligenceError, match="missing"):
        assert_topology_neutral(shards, ("a/test_x.py", "a/test_y.py"))


def test_a_partition_that_duplicates_a_unit_is_refused() -> None:
    shards = (
        Shard(index=0, test_paths=("a/test_x.py",), cost_seconds=1.0),
        Shard(index=1, test_paths=("a/test_x.py",), cost_seconds=1.0),
    )
    with pytest.raises(VerificationIntelligenceError, match="more than once"):
        assert_topology_neutral(shards, ("a/test_x.py",))


def test_worker_resolution_never_exceeds_the_work_or_the_ceiling() -> None:
    assert resolve_workers(3, max_workers=12) <= 3
    assert resolve_workers(1000, max_workers=4) == 4
    assert resolve_workers(0, max_workers=4) == 1
    assert resolve_workers(1000, max_workers=4, override="2") == 2
    with pytest.raises(VerificationIntelligenceError):
        resolve_workers(10, max_workers=4, override="not-a-number")
    with pytest.raises(VerificationIntelligenceError):
        resolve_workers(10, max_workers=4, override="0")


def test_a_shard_plan_with_no_workers_is_refused(tests_registry) -> None:
    with pytest.raises(VerificationIntelligenceError, match="at least one worker"):
        plan_shards(tests_registry.paths, tests_registry, 0)


# --- evidence -----------------------------------------------------------------------


def test_a_certification_mode_can_never_reach_a_reuse_decision(
    constitution, substrates, tmp_path
) -> None:
    """A certification that reuses a result certifies a cache."""
    for mode in constitution.modes:
        if not mode.certification_eligible:
            continue
        for stage in constitution.stages_for(mode):
            reuse, reason, digest = decide(mode, stage, substrates, home=str(tmp_path))
            assert reuse is False
            assert digest is None
            assert "never reuses" in reason


def test_a_recorded_pass_is_reused_and_a_changed_input_is_not(
    constitution, substrates, tmp_path
) -> None:
    mode = constitution.mode("change")
    stage = next(s for s in constitution.stages_for(mode) if s.reusable)
    digest = input_digest(stage, substrates, contract=execution_contract(stage.label))
    assert digest is not None

    reuse, _, _ = decide(mode, stage, substrates, home=str(tmp_path))
    assert reuse is False, "an empty store must not be a hit"

    record(str(tmp_path), stage.stage_id, digest, "PASS")
    reuse, reason, hit = decide(mode, stage, substrates, home=str(tmp_path))
    assert reuse is True and hit == digest and "already passed" in reason

    # A different input is a different key, and therefore a miss.
    assert lookup(str(tmp_path), stage.stage_id, "0" * 64) is None


def test_a_recorded_failure_is_never_reused(constitution, substrates, tmp_path) -> None:
    mode = constitution.mode("change")
    stage = next(s for s in constitution.stages_for(mode) if s.reusable)
    digest = input_digest(stage, substrates, contract=execution_contract(stage.label))
    record(str(tmp_path), stage.stage_id, digest, "FAIL")
    reuse, reason, _ = decide(mode, stage, substrates, home=str(tmp_path))
    assert reuse is False and "not PASS" in reason


def test_an_entry_from_another_engine_version_is_not_a_hit(
    constitution, substrates, tmp_path
) -> None:
    """A result produced under a different execution contract answers a different question."""
    stage = next(s for s in constitution.stages if s.reusable)
    digest = input_digest(stage, substrates, contract=execution_contract(stage.label))
    record(str(tmp_path), stage.stage_id, digest, "PASS")
    target = os.path.join(str(tmp_path), stage.stage_id, f"{digest}.json")
    document = json.loads(open(target, encoding="utf-8").read())
    document["engine_version"] = f"{EVIDENCE_VERSION}-other"
    open(target, "w", encoding="utf-8").write(json.dumps(document))
    assert lookup(str(tmp_path), stage.stage_id, digest) is None


def test_a_non_reusable_stage_takes_no_digest(constitution, substrates) -> None:
    stage = next(s for s in constitution.stages if not s.reusable)
    assert input_digest(stage, substrates, contract=execution_contract(stage.label)) is None


def test_a_prefix_matching_no_registered_object_takes_no_digest(constitution, substrates) -> None:
    """A key that covers nothing would be a hit on every run, forever."""
    from dataclasses import replace

    stage = replace(
        next(s for s in constitution.stages if s.reusable),
        reuse_inputs=("a/path/that/is/not/registered/",),
    )
    assert input_digest(stage, substrates, contract=("x",)) is None


# --- read-set resolution and withheld hashes (A5 / A6) -------------------------------


def test_A6_the_read_set_resolves_against_the_universal_registry(substrates) -> None:
    """A6 — the executable projection is a subset, and a read-set is not confined to it.

    01 omits every DOCUMENT_ARTIFACT. Two declared prefixes name trees made entirely of
    documents, so against 01 they matched nothing at all while the objects sat, tracked
    and hashed, in 02.
    """
    assert len(substrates.universal) > len(substrates.objects)
    assert set(substrates.objects) <= set(substrates.universal), "02 must be a superset of 01"
    for prefix in ("00-SOURCE/", "00-BOOK/SCHEMAS/"):
        in_executable = [p for p in substrates.objects if p.startswith(prefix)]
        resolved = resolve_prefix(substrates, prefix)
        assert not in_executable, "fixture assumption: these are documents, absent from 01"
        assert resolved, f"{prefix} must resolve against the universal registry"


def test_A6_every_reusable_stage_now_takes_a_key(constitution, substrates) -> None:
    """A6 — the three permanently-keyless stages are keyless no longer.

    governance-pre, registry-validate and meta-constitutional could never compute a key.
    Every stage the declaration calls reusable must now produce one, or reuse is a
    promise the engine cannot keep.
    """
    source = verify_source()
    keyless = [
        stage.stage_id
        for stage in constitution.stages
        if stage.reusable
        and input_digest(stage, substrates, contract=execution_contract(stage.label, source=source))
        is None
    ]
    assert keyless == [], f"stages declared reusable but unable to key: {keyless}"


def test_A5_a_withheld_hash_contributes_a_constant_rather_than_refusing(
    constitution, substrates
) -> None:
    """A5 — withheld is a declared property of the object, not an absent measurement.

    Eleven surfaces carry ``content_hash_withheld: SELF_REFERENTIAL`` because a file
    cannot contain its own hash. Treating that as "unmeasured" refused the key for every
    stage whose read-set contained one, permanently and silently.
    """
    withheld = {
        path: entry
        for path, entry in substrates.universal.items()
        if not entry.get("content_hash") and entry.get("content_hash_withheld")
    }
    assert withheld, "fixture assumption: the registry declares withheld hashes"

    # No object may carry neither a hash nor a declared reason — that is the case that
    # must still refuse, and it must not exist in a healthy registry.
    unexplained = [
        path
        for path, entry in substrates.universal.items()
        if not entry.get("content_hash") and not entry.get("content_hash_withheld")
    ]
    assert unexplained == [], f"objects with no hash and no declared reason: {unexplained[:5]}"

    # meta-constitutional reads 00-BOOK/DATA/, which contains a withheld object.
    stage = next(s for s in constitution.stages if s.stage_id == "meta-constitutional")
    assert any(p in withheld for p in resolve_prefix(substrates, "00-BOOK/DATA/"))
    assert input_digest(stage, substrates, contract=execution_contract(stage.label)) is not None


def test_A5_an_unexplained_missing_hash_still_refuses(constitution, substrates) -> None:
    """A5 — the distinction is withheld vs MISSING, and missing must still refuse."""
    from dataclasses import replace

    stage = replace(
        next(s for s in constitution.stages if s.reusable),
        reuse_inputs=("engine/verification_intelligence/",),
    )
    contract = execution_contract(stage.label)
    assert input_digest(stage, substrates, contract=contract) is not None

    victim = next(iter(resolve_prefix(substrates, "engine/verification_intelligence/")))
    original = substrates.universal[victim]
    substrates.universal[victim] = {
        k: v for k, v in original.items() if k not in ("content_hash", "content_hash_withheld")
    }
    try:
        assert input_digest(stage, substrates, contract=contract) is None
    finally:
        substrates.universal[victim] = original


def test_A5_withheld_and_hashed_are_not_the_same_key(constitution, substrates) -> None:
    """A5 — a withheld marker must not collide with a real hash of the same text."""
    from dataclasses import replace

    stage = replace(
        next(s for s in constitution.stages if s.reusable),
        reuse_inputs=("engine/verification_intelligence/",),
    )
    contract = execution_contract(stage.label)
    victim = next(iter(resolve_prefix(substrates, "engine/verification_intelligence/")))
    original = substrates.universal[victim]
    marker = "SELF_REFERENTIAL"
    try:
        substrates.universal[victim] = {**original, "content_hash": marker}
        as_hash = input_digest(stage, substrates, contract=contract)
        substrates.universal[victim] = {
            **{k: v for k, v in original.items() if k != "content_hash"},
            "content_hash_withheld": marker,
        }
        as_withheld = input_digest(stage, substrates, contract=contract)
        assert as_hash != as_withheld
    finally:
        substrates.universal[victim] = original


def test_UVI_L_11_fires_on_a_read_set_that_resolves_to_nothing(substrates) -> None:
    """UVI-L-11 — mutation proof: the law must fail when the condition it names is present."""
    ctx = uvi_gate._Context()
    assert every_declared_read_set_resolves(ctx) == [], "the law must hold as the tree stands"

    from dataclasses import replace

    bogus = replace(ctx.constitution.stages[0], reuse_inputs=("no/such/tree/",))
    ctx.constitution = replace(ctx.constitution, stages=(bogus, *ctx.constitution.stages[1:]))
    findings = every_declared_read_set_resolves(ctx)
    assert findings, "the law did not fire on an unresolvable read-set"
    assert "no/such/tree/" in findings[0]


# --- the execution contract in the evidence key (Step 1) ----------------------------
#
# The key used to cover what a stage READS but not what it RUNS. A stage is both, and a
# cache keyed on only one of them answers a question nobody asked. Every test below
# computes a real key from the real declaration and the real script; none asserts a
# hardcoded digest, because a hardcoded digest would freeze the composition rather than
# measure it.


def _reusable_keyable(constitution, substrates):
    """A declared stage that is reusable AND whose declared inputs actually resolve."""
    for stage in constitution.stages:
        if not stage.reusable:
            continue
        contract = execution_contract(stage.label)
        if contract and input_digest(stage, substrates, contract=contract):
            return stage, contract
    raise AssertionError("no reusable stage takes a digest; the fixture cannot measure reuse")


def test_the_contract_of_every_declared_stage_resolves(constitution) -> None:
    """A stage whose command cannot be read has no identity to key on."""
    source = verify_source()
    for stage in constitution.stages:
        contract = execution_contract(stage.label, source=source)
        assert contract, f"no execution contract resolved for {stage.stage_id}"
        assert all(token for token in contract), f"empty argv token in {stage.stage_id}"


def test_A_same_inputs_same_command_is_one_key_and_a_hit(
    constitution, substrates, tmp_path
) -> None:
    """A — identical inputs and identical command: identical key, reuse allowed."""
    stage, contract = _reusable_keyable(constitution, substrates)
    first = input_digest(stage, substrates, contract=contract)
    second = input_digest(stage, substrates, contract=contract)
    assert first == second, "the same contract must produce the same key"

    mode = constitution.mode("change")
    record(str(tmp_path), stage.stage_id, first, "PASS")
    reuse, reason, hit = decide(mode, stage, substrates, home=str(tmp_path), verify=verify_source())
    assert reuse is True and hit == first and "already passed" in reason


def test_B_a_changed_command_is_a_different_key_and_a_miss(
    constitution, substrates, tmp_path
) -> None:
    """B — same inputs, changed command: different key, and the recorded PASS is unreachable.

    This is the defect the step closes, performed rather than described: the entry is
    recorded under the real contract, the command is then edited exactly as a maintainer
    would edit it, and the edited stage must NOT reach that entry.
    """
    stage, contract = _reusable_keyable(constitution, substrates)
    original = input_digest(stage, substrates, contract=contract)
    record(str(tmp_path), stage.stage_id, original, "PASS")

    mutations = (
        contract + ("--newly-added-flag",),
        contract[:-1],
        ("different-interpreter",) + contract[1:],
    )
    for mutated in mutations:
        assert mutated != contract
        key = input_digest(stage, substrates, contract=mutated)
        assert key is not None
        assert key != original, f"a changed command produced the same key: {mutated}"
        assert (
            lookup(str(tmp_path), stage.stage_id, key) is None
        ), "a changed command reached a result it never produced"


def test_C_argument_order_is_significant(constitution, substrates) -> None:
    """C — reordering arguments changes the key.

    A shell passes argv in the order written. Nothing here may assume the receiving
    parser is order-insensitive, so order is part of the identity.
    """
    stage, contract = _reusable_keyable(constitution, substrates)
    flagged = contract + ("--alpha", "--beta")
    swapped = contract + ("--beta", "--alpha")
    assert input_digest(stage, substrates, contract=flagged) != input_digest(
        stage, substrates, contract=swapped
    )


def test_C_token_boundaries_cannot_be_forged(constitution, substrates) -> None:
    """C — two tokens are never the same key as the one token that concatenates them."""
    stage, contract = _reusable_keyable(constitution, substrates)
    split = contract + ("--gate", "--quiet")
    joined = contract + ("--gate --quiet",)
    assert input_digest(stage, substrates, contract=split) != input_digest(
        stage, substrates, contract=joined
    )


def test_D_equivalent_serialisations_of_one_command_are_one_key(constitution, substrates) -> None:
    """D — how the invocation is WRITTEN does not change the key; what it RUNS does.

    Line-wrapping, indentation, repeated spaces and quoting style are all serialisation.
    A maintainer who re-wraps a long invocation must not invalidate its evidence.
    """
    stage, _ = _reusable_keyable(constitution, substrates)
    label = stage.label
    variants = (
        f'run_stage "{label}" "$PY" -m pkg.mod --gate --quiet\n',
        f'run_stage "{label}" \\\n  "$PY" -m pkg.mod --gate --quiet\n',
        f'run_stage "{label}"    $PY    -m   pkg.mod   --gate   --quiet\n',
        f'run_stage "{label}" \\\n    "$PY" \\\n    -m pkg.mod \\\n    --gate --quiet\n',
    )
    contracts = {execution_contract(label, source=v) for v in variants}
    assert len(contracts) == 1, f"serialisation changed the contract: {contracts}"
    keys = {input_digest(stage, substrates, contract=c) for c in contracts}
    assert len(keys) == 1


def test_E_no_clock_host_path_or_environment_reaches_the_key(constitution, substrates) -> None:
    """E — the key carries no observation of the machine that computed it.

    The contract is taken from the script's SOURCE TEXT, so ``"$PY"`` stays the literal
    ``$PY`` and never becomes this checkout's absolute venv path. Were it otherwise the
    key would differ between two machines verifying identical trees, and UVI-L-10's
    prohibition on an absolute path reaching a plan would be broken by the field added
    to make the plan honest.
    """
    source = verify_source()
    for stage in constitution.stages:
        contract = execution_contract(stage.label, source=source)
        assert contract is not None
        for token in contract:
            assert not os.path.isabs(token), f"absolute path in contract: {token}"
            assert repo_root() not in token, f"checkout path in contract: {token}"
            assert not token.startswith("~"), f"home-relative path in contract: {token}"
            assert "\n" not in token

    # The key is a pure function of (declaration, registry, script). Recomputing it in a
    # second process must land on the same value: nothing observed at runtime enters it.
    stage, contract = _reusable_keyable(constitution, substrates)
    expected = input_digest(stage, substrates, contract=contract)
    program = (
        "from engine.verification_intelligence.constitution import "
        "load_constitution, execution_contract\n"
        "from engine.verification_intelligence.registry import load_substrates\n"
        "from engine.verification_intelligence.evidence import input_digest\n"
        "c = load_constitution(); s = load_substrates()\n"
        f"st = next(x for x in c.stages if x.stage_id == {stage.stage_id!r})\n"
        "print(input_digest(st, s, contract=execution_contract(st.label)))\n"
    )
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", program],
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == expected


def test_a_certification_mode_never_resolves_a_contract_at_all(
    constitution, substrates, tmp_path
) -> None:
    """UVI-L-09 is evaluated BEFORE the contract, and this step did not move it.

    A certification-eligible mode must return without reading the script, the store or a
    digest. Passing a deliberately broken script proves the refusal happens first: if the
    contract were resolved before the mode check, this would raise or return a digest.
    """
    for mode in constitution.modes:
        if not mode.certification_eligible:
            continue
        for stage in constitution.stages_for(mode):
            reuse, reason, digest = decide(
                mode, stage, substrates, home=str(tmp_path), verify="not a shell script at all"
            )
            assert reuse is False
            assert digest is None
            assert "never reuses" in reason


def test_an_unresolvable_contract_refuses_the_key_rather_than_guessing(
    constitution, substrates, tmp_path
) -> None:
    """Unknown widens. A label the script does not declare exactly once has no contract."""
    stage, _ = _reusable_keyable(constitution, substrates)
    assert execution_contract(stage.label, source="") is None
    duplicated = f'run_stage "{stage.label}" a\n' f'run_stage "{stage.label}" b\n'
    assert execution_contract(stage.label, source=duplicated) is None
    unbalanced = f'run_stage "{stage.label}" "never-closed\n'
    assert execution_contract(stage.label, source=unbalanced) is None

    mode = constitution.mode("change")
    reuse, reason, digest = decide(mode, stage, substrates, home=str(tmp_path), verify="")
    assert reuse is False and digest is None
    assert "execution contract" in reason


# --- the plan -----------------------------------------------------------------------


@pytest.mark.parametrize("mode_id", ["fast", "change", "integration", "full"])
def test_planning_twice_produces_identical_bytes(mode_id, constitution, substrates, tests_registry):
    first = build_plan(
        mode_id, constitution=constitution, substrates=substrates, tests=tests_registry, changed=()
    )
    second = build_plan(
        mode_id, constitution=constitution, substrates=substrates, tests=tests_registry, changed=()
    )
    assert plan_json(first) == plan_json(second)
    assert plan_digest(first) == plan_digest(second)


@pytest.mark.parametrize("mode_id", ["fast", "change", "integration", "full"])
def test_a_plan_carries_no_observation_of_the_run(
    mode_id, constitution, substrates, tests_registry
) -> None:
    """A clock or a machine path would make two plans of one state differ."""
    import re

    body = plan_json(
        build_plan(
            mode_id,
            constitution=constitution,
            substrates=substrates,
            tests=tests_registry,
            changed=(),
        )
    )
    assert not re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", body)
    assert REPO not in body


def test_every_declared_stage_appears_in_every_plan(constitution, substrates, tests_registry):
    """A stage absent from the plan would be executed by the shell's fail-safe default."""
    for mode in constitution.modes:
        plan = build_plan(
            mode.mode_id,
            constitution=constitution,
            substrates=substrates,
            tests=tests_registry,
            changed=(),
        )
        assert [entry.stage.label for entry in plan.stages] == list(constitution.stage_labels)


def test_a_developer_mode_that_escalates_is_run_under_the_floor(
    constitution, substrates, tests_registry
) -> None:
    """Running the whole suite WITHOUT the floor would be less than the old default did."""
    plan = build_plan(
        "change",
        constitution=constitution,
        substrates=substrates,
        tests=tests_registry,
        changed=("00-BOOK/DATA/uvi-probe.json",),
    )
    assert plan.selection.escalated
    assert plan.coverage is Coverage.FLOOR_90
    assert plan.escalated_coverage
    coverage_report = next(e for e in plan.stages if e.stage.stage_id == "coverage-report")
    assert coverage_report.action is Action.RUN


def test_a_developer_mode_that_does_not_escalate_owns_no_floor(
    constitution, substrates, tests_registry
) -> None:
    plan = build_plan(
        "change",
        constitution=constitution,
        substrates=substrates,
        tests=tests_registry,
        changed=("engine/uaue/gate.py",),
    )
    assert plan.coverage is Coverage.NOT_EVALUATED
    coverage_report = next(e for e in plan.stages if e.stage.stage_id == "coverage-report")
    assert coverage_report.action is Action.SKIP


def test_only_full_admits_the_registration_observation(
    constitution, substrates, tests_registry
) -> None:
    for mode in constitution.modes:
        plan = build_plan(
            mode.mode_id,
            constitution=constitution,
            substrates=substrates,
            tests=tests_registry,
            changed=(),
        )
        entry = next(e for e in plan.stages if e.stage.stage_id == "registration-observation")
        expected = Action.RUN if mode.mode_id == "full" else Action.SKIP
        assert entry.action is expected


def test_the_plan_the_shell_reads_is_looked_up_by_the_stage_label(
    constitution, substrates, tests_registry
) -> None:
    """One string identifies a stage in verify.sh, in the record, and in the plan."""
    plan = build_plan(
        "full", constitution=constitution, substrates=substrates, tests=tests_registry, changed=()
    )
    rows = [line.split("\t") for line in plan_tsv(plan).strip().splitlines()]
    assert [row[3] for row in rows] == list(constitution.stage_labels)
    assert all(row[0] in {"RUN", "SKIP", "REUSE"} for row in rows)
    assert all("\t" not in row[3] for row in rows)


def test_a_selection_fault_is_answered_with_the_whole_suite(
    constitution, substrates, tests_registry, monkeypatch
) -> None:
    """The caller's alternative to a wide plan is no plan at all, never a narrow one."""

    def _fault(*args, **kwargs):
        raise VerificationIntelligenceError("the substrate is unreadable")

    monkeypatch.setattr("engine.verification_intelligence.plan.select", _fault)
    plan = build_plan(
        "change", constitution=constitution, substrates=substrates, tests=tests_registry
    )
    assert plan.selection.selection is Selection.WHOLE_SUITE
    assert plan.selection.test_paths == tests_registry.paths


# --- the gate -----------------------------------------------------------------------


def test_every_law_holds_over_the_live_repository() -> None:
    """The gate verify.sh runs, run here so a refusal is a test failure with a name."""
    report = uvi_gate.measure()
    refused = [law for law in report["laws"] if not law["holds"]]
    assert refused == [], "refused laws:\n" + "\n".join(
        f"  {law['law_id']} {law['title']}: {law['violations']}" for law in refused
    )
    assert report["verdict"] == "COHERENT"


def test_the_baseline_contract_is_a_ratchet() -> None:
    """Every gate the certification default ran before this rework must still run."""
    document = load_declaration()
    baseline = document["no_assurance_reduction"]["baseline_stages"]
    assert baseline, "no baseline contract is declared"
    constitution = load_constitution()
    for mode in constitution.modes:
        if not mode.certification_eligible:
            continue
        admitted = {stage.label for stage in constitution.stages_for(mode)}
        assert set(baseline) <= admitted, f"--{mode.mode_id} dropped a baseline gate"


def test_the_stage_registry_and_the_script_declare_the_same_contract() -> None:
    source = open(os.path.join(REPO, "verify.sh"), encoding="utf-8").read()
    assert uvi_gate._declared_stage_labels(source) == list(load_constitution().stage_labels)


def test_the_script_accepts_exactly_the_declared_modes() -> None:
    source = open(os.path.join(REPO, "verify.sh"), encoding="utf-8").read()
    assert uvi_gate._accepted_flags(source) == set(load_constitution().flags)


def test_the_bare_invocation_is_the_declared_default() -> None:
    source = open(os.path.join(REPO, "verify.sh"), encoding="utf-8").read()
    assert f'MODE="{load_constitution().default_mode_id}"' in source


def test_the_gate_reports_a_fault_rather_than_a_verdict_on_a_broken_declaration(tmp_path) -> None:
    """'A law was refused' and 'the declaration is unreadable' are different facts."""
    path = tmp_path / "declaration.json"
    path.write_text("{not json", encoding="utf-8")
    assert uvi_gate.main(["--gate", "--quiet", "--declaration", str(path)]) == uvi_gate.EXIT_FAULT


def test_the_gate_exits_zero_when_every_law_holds() -> None:
    assert uvi_gate.main(["--gate", "--quiet"]) == uvi_gate.EXIT_COHERENT


def test_the_gate_emits_json_and_a_rendered_report(capsys) -> None:
    assert uvi_gate.main(["--json"]) == uvi_gate.EXIT_COHERENT
    report = json.loads(capsys.readouterr().out)
    declared = len(load_declaration()["laws"])
    assert report["laws_measured"] == len(report["laws"]) == declared
    assert uvi_gate.main([]) == uvi_gate.EXIT_COHERENT
    assert "VERDICT" in capsys.readouterr().out


def test_the_gate_writes_nothing(tmp_path) -> None:
    """OBSERVE MODE. A gate that writes can drift, and this one measures drift."""
    import subprocess
    import sys

    before = subprocess.run(  # noqa: S603
        ["git", "status", "--porcelain"],  # noqa: S607
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    subprocess.run(  # noqa: S603
        [sys.executable, "-m", "engine.verification_intelligence.gate", "--quiet"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    after = subprocess.run(  # noqa: S603
        ["git", "status", "--porcelain"],  # noqa: S607
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    assert before == after


# --- the CLI ------------------------------------------------------------------------


def test_the_cli_emits_a_plan_the_shell_can_read(tmp_path) -> None:
    from engine.verification_intelligence.cli import main

    out = tmp_path / "plan.tsv"
    assert main(["plan", "--mode", "full", "--tsv", "--out", str(out), "--path", "README.md"]) == 0
    rows = [line.split("\t") for line in out.read_text(encoding="utf-8").strip().splitlines()]
    assert rows and all(len(row) == 4 for row in rows)


def test_the_cli_refuses_to_record_against_an_undeclared_stage() -> None:
    from engine.verification_intelligence.cli import main

    assert (
        main(["record", "--stage-label", "no such stage", "--result", "PASS", "--digest", "x"]) == 2
    )


# --- execution, actually executed ---------------------------------------------------
#
# The section that matters most and is easiest to skip. plan_shards and the neutrality
# assertion above are pure and cheap to test; run_tests spawns processes, and it is the
# code that could report a pass over tests that never ran. So it is exercised here for
# real, over a throwaway suite, rather than described.


def _throwaway_suite(tmp_path, *, failing: bool = False) -> tuple:
    """A tiny real pytest suite in a scratch directory, plus shards over it."""
    (tmp_path / "test_alpha.py").write_text(
        "def test_alpha():\n    assert True\n", encoding="utf-8"
    )
    (tmp_path / "test_beta.py").write_text(
        "def test_beta():\n    assert %s\n" % ("False" if failing else "True"), encoding="utf-8"
    )
    return (
        Shard(index=0, test_paths=("test_alpha.py",), cost_seconds=0.1),
        Shard(index=1, test_paths=("test_beta.py",), cost_seconds=0.1),
    )


def test_run_tests_executes_every_shard_and_passes_when_they_pass(tmp_path) -> None:
    import io
    import sys

    from engine.verification_intelligence.execution import run_tests

    shards = _throwaway_suite(tmp_path)
    stream = io.StringIO()
    code = run_tests(
        shards,
        Coverage.NOT_EVALUATED,
        root=str(tmp_path),
        python=sys.executable,
        selection=("test_alpha.py", "test_beta.py"),
        stream=stream,
    )
    assert code == 0
    body = stream.getvalue()
    assert "shard 0" in body and "shard 1" in body
    assert "2 shard(s) running concurrently" in body


def test_run_tests_fails_when_any_shard_fails(tmp_path) -> None:
    import io
    import sys

    from engine.verification_intelligence.execution import run_tests

    shards = _throwaway_suite(tmp_path, failing=True)
    stream = io.StringIO()
    code = run_tests(
        shards,
        Coverage.NOT_EVALUATED,
        root=str(tmp_path),
        python=sys.executable,
        selection=("test_alpha.py", "test_beta.py"),
        stream=stream,
    )
    assert code == 1
    assert "shard(s) FAILED: [1]" in stream.getvalue()


def test_run_tests_refuses_a_partition_that_is_not_the_selection(tmp_path) -> None:
    """The check that stands between a dropped shard and a green run."""
    import io
    import sys

    from engine.verification_intelligence.execution import run_tests

    shards = _throwaway_suite(tmp_path)[:1]
    with pytest.raises(VerificationIntelligenceError, match="missing"):
        run_tests(
            shards,
            Coverage.NOT_EVALUATED,
            root=str(tmp_path),
            python=sys.executable,
            selection=("test_alpha.py", "test_beta.py"),
            stream=io.StringIO(),
        )


def test_run_tests_refuses_to_report_a_pass_over_nothing(tmp_path) -> None:
    """An empty partition is the one thing that must never look like success."""
    import io
    import sys

    from engine.verification_intelligence.execution import run_tests

    stream = io.StringIO()
    assert (
        run_tests(
            (), Coverage.NOT_EVALUATED, root=str(tmp_path), python=sys.executable, stream=stream
        )
        == 1
    )
    assert "refusing to report a pass" in stream.getvalue()


def test_the_floor_is_evaluated_over_combined_data_and_refuses_when_there_is_none(
    tmp_path,
) -> None:
    """No coverage data cannot be answered with a pass; the floor would be a claim about air."""
    import io
    import sys

    from engine.verification_intelligence.execution import _combine_and_evaluate

    stream = io.StringIO()
    empty = tmp_path / "no-data"
    empty.mkdir()
    assert _combine_and_evaluate(sys.executable, str(tmp_path), str(empty), stream) == 1
    assert "no coverage data" in stream.getvalue()


def test_the_shard_command_keeps_addopts_under_the_floor_and_drops_them_without_it() -> None:
    """The denominator must not depend on how the run was scheduled."""
    from engine.verification_intelligence.execution import _shard_argv

    shard = Shard(index=0, test_paths=("a/test_x.py",), cost_seconds=1.0)
    under_floor = _shard_argv("py", shard, Coverage.FLOOR_90)
    assert "-o" not in under_floor, "clearing addopts would drop every --cov argument"
    assert "--cov-fail-under=0" in under_floor, "the floor is evaluated once, over combined data"
    assert "--cov-report=" in under_floor
    assert under_floor[-1] == "a/test_x.py"

    without = _shard_argv("py", shard, Coverage.NOT_EVALUATED)
    assert without[3:5] == ["-o", "addopts="] and "--no-cov" in without


# --- every law must be able to refuse -----------------------------------------------
#
# A check that cannot fail is not a check. Each test below breaks exactly one declared
# property and asserts that the law responsible names it — so a law that silently stopped
# measuring anything fails here rather than reporting COHERENT forever.


def _ctx(tmp_path, mutate) -> object:
    document = load_declaration()
    mutate(document)
    path = tmp_path / "declaration.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return uvi_gate._Context(declaration=str(path))


def test_l01_refuses_a_mode_the_script_does_not_accept(tmp_path) -> None:
    def mutate(document):
        document["mode_constitution"]["modes"][0]["flag"] = "--nonexistent"

    findings = uvi_gate.mode_constitution_completeness(_ctx(tmp_path, mutate))
    assert any("does not accept it" in f for f in findings)


def test_l02_refuses_a_default_the_script_does_not_resolve_to(tmp_path) -> None:
    def mutate(document):
        document["mode_constitution"]["default_mode"] = "integration"

    findings = uvi_gate.exactly_one_default(_ctx(tmp_path, mutate))
    assert any("defaults to" in f for f in findings)


def test_l03_refuses_a_stage_the_script_does_not_declare(tmp_path) -> None:
    def mutate(document):
        document["stage_registry"]["stages"][0]["label"] = "a stage nothing declares"

    findings = uvi_gate.stage_registry_reconciliation(_ctx(tmp_path, mutate))
    assert any("does not declare" in f for f in findings)
    assert any("does not classify" in f for f in findings)


def test_l03_refuses_a_reordered_contract(tmp_path) -> None:
    """Order is part of the contract the canonical validation record digests."""

    def mutate(document):
        stages = document["stage_registry"]["stages"]
        stages[0], stages[1] = stages[1], stages[0]

    findings = uvi_gate.stage_registry_reconciliation(_ctx(tmp_path, mutate))
    assert any("DIFFERENT order" in f for f in findings)


def test_l04_refuses_dropping_a_baseline_gate_from_a_certifying_mode(tmp_path) -> None:
    """THE ratchet. Removing a gate from --full must fail here, not be noticed later."""

    def mutate(document):
        baseline = document["no_assurance_reduction"]["baseline_stages"][0]
        for stage in document["stage_registry"]["stages"]:
            if stage["label"] == baseline:
                stage["modes"] = ["fast"]

    findings = uvi_gate.no_assurance_reduction(_ctx(tmp_path, mutate))
    assert any("no longer runs a baseline gate" in f for f in findings)


def test_l04_refuses_deleting_a_baseline_gate_outright(tmp_path) -> None:
    def mutate(document):
        baseline = document["no_assurance_reduction"]["baseline_stages"][0]
        document["stage_registry"]["stages"] = [
            stage for stage in document["stage_registry"]["stages"] if stage["label"] != baseline
        ]

    findings = uvi_gate.no_assurance_reduction(_ctx(tmp_path, mutate))
    assert any("no longer a declared stage" in f for f in findings)


def test_l04_refuses_a_repository_where_nothing_certifies(tmp_path) -> None:
    def mutate(document):
        for mode in document["mode_constitution"]["modes"]:
            mode["certification_eligible"] = False

    findings = uvi_gate.no_assurance_reduction(_ctx(tmp_path, mutate))
    assert any("owned by nothing" in f for f in findings)


def test_l05_refuses_a_mode_that_certifies_a_subset(tmp_path) -> None:
    def mutate(document):
        for mode in document["mode_constitution"]["modes"]:
            if mode["id"] == "change":
                mode["certification_eligible"] = True

    findings = uvi_gate.no_mode_claims_more_than_it_measures(_ctx(tmp_path, mutate))
    assert any("would certify a subset" in f for f in findings)
    assert any("does not evaluate the floor" in f for f in findings)
    assert any("could certify a cache" in f for f in findings)


def test_l05_refuses_a_second_owner_of_the_floor(tmp_path) -> None:
    def mutate(document):
        for mode in document["mode_constitution"]["modes"]:
            if mode["id"] == "fast":
                mode["coverage"] = "FLOOR_90"

    findings = uvi_gate.no_mode_claims_more_than_it_measures(_ctx(tmp_path, mutate))
    assert any("two owners" in f for f in findings)


def test_l05_refuses_a_mode_that_states_nothing_it_does_not_claim(tmp_path) -> None:
    def mutate(document):
        for mode in document["mode_constitution"]["modes"]:
            if mode["id"] == "fast":
                mode["claims_not"] = []

    findings = uvi_gate.no_mode_claims_more_than_it_measures(_ctx(tmp_path, mutate))
    assert any("does not claim" in f for f in findings)


def test_l06_refuses_a_declared_substrate_that_nothing_reads(tmp_path) -> None:
    """A declaration claiming a derivation that does not happen is worse than silence."""

    def mutate(document):
        document["selection"]["substrates"].append(
            {"id": "invented", "source": "00-BOOK/DATA/a-substrate-nothing-reads.json"}
        )

    findings = uvi_gate.selection_is_derived(_ctx(tmp_path, mutate))
    assert any("no module reads it" in f for f in findings)


def test_l06_refuses_an_authored_test_path_in_the_declaration(tmp_path) -> None:
    def mutate(document):
        document["selection"]["layers"][0]["rule"] = "run engine/tests/unit/test_something.py"

    findings = uvi_gate.selection_is_derived(_ctx(tmp_path, mutate))
    assert any("names a specific test file" in f for f in findings)


def test_l06_ignores_a_test_path_inside_declared_rationale(tmp_path) -> None:
    """A `$`-prefixed key is prose. Prose may discuss a test file; a declaration may not."""

    def mutate(document):
        document["selection"]["$example"] = "for instance engine/tests/unit/test_thing.py"

    assert not [
        f for f in uvi_gate.selection_is_derived(_ctx(tmp_path, mutate)) if "test_thing" in f
    ]


def test_l09_refuses_reuse_conditions_that_omit_the_digest_or_the_result(tmp_path) -> None:
    def mutate(document):
        document["evidence_registry"]["reuse_conditions"] = ["the stage feels fine"]

    findings = uvi_gate.evidence_reuse_integrity(_ctx(tmp_path, mutate))
    assert any("input digest" in f for f in findings)
    assert any("PASS" in f for f in findings)


def test_l10_refuses_a_plan_that_is_not_reproducible(tmp_path, monkeypatch) -> None:
    """The law must be able to see non-determinism, or it is decoration."""
    import itertools

    counter = itertools.count()
    real = uvi_gate.build_plan

    def _drifting(*args, **kwargs):
        plan = real(*args, **kwargs)
        from dataclasses import replace

        return replace(plan, notes=(f"run {next(counter)}",))

    monkeypatch.setattr(uvi_gate, "build_plan", _drifting)
    findings = uvi_gate.deterministic_planning(uvi_gate._Context())
    assert any("different bytes" in f for f in findings)


def test_the_gate_exits_one_when_a_law_is_refused(tmp_path) -> None:
    document = load_declaration()
    document["mode_constitution"]["default_mode"] = "integration"
    path = tmp_path / "declaration.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    assert (
        uvi_gate.main(["--gate", "--quiet", "--declaration", str(path)]) == uvi_gate.EXIT_INCOHERENT
    )


def test_without_the_gate_flag_a_refusal_is_reported_but_does_not_fail(tmp_path) -> None:
    """`--gate` is what makes it fail closed; without it the gate is a measurement."""
    document = load_declaration()
    document["mode_constitution"]["default_mode"] = "integration"
    path = tmp_path / "declaration.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    assert uvi_gate.main(["--quiet", "--declaration", str(path)]) == uvi_gate.EXIT_COHERENT


# --- the surfaces the shell actually calls ------------------------------------------


def test_the_report_surface_explains_the_plan_it_would_execute(capsys) -> None:
    """`--explain` is only useful if it shows the same decision run-tests will act on."""
    from engine.verification_intelligence.cli import main

    assert main(["report", "--mode", "change", "--path", "engine/uaue/gate.py"]) == 0
    body = capsys.readouterr().out
    assert "VERIFICATION PLAN" in body
    assert "mode                  : --change" in body
    assert "selection layers:" in body
    for label in load_constitution().stage_labels:
        assert label in body


def test_the_report_names_every_escalation_it_widened_on(capsys) -> None:
    from engine.verification_intelligence.cli import main

    assert main(["report", "--mode", "change", "--path", "00-BOOK/DATA/uvi-probe.json"]) == 0
    body = capsys.readouterr().out
    assert "escalations:" in body
    assert "WHOLE_SUITE" in body


def test_the_plan_surface_emits_json_and_a_rendered_form(capsys) -> None:
    from engine.verification_intelligence.cli import main

    assert main(["plan", "--mode", "full", "--json", "--path", "README.md"]) == 0
    document = json.loads(capsys.readouterr().out)
    assert document["artifact_id"] == "UVI-000001"
    assert document["mode"]["id"] == "full"
    assert main(["plan", "--mode", "fast", "--path", "README.md"]) == 0
    assert "VERIFICATION PLAN" in capsys.readouterr().out


def test_the_cli_reports_a_fault_rather_than_a_narrow_plan(monkeypatch, capsys) -> None:
    from engine.verification_intelligence import cli

    def _fault(*args, **kwargs):
        raise VerificationIntelligenceError("the substrate is unreadable")

    monkeypatch.setattr(cli, "build_plan", _fault)
    assert cli.main(["plan", "--mode", "fast"]) == 2
    assert "UVI FAULT" in capsys.readouterr().err


def test_recording_a_result_round_trips_through_the_declared_store(tmp_path, monkeypatch) -> None:
    from engine.verification_intelligence import cli, evidence

    monkeypatch.setattr(evidence, "store_home", lambda *a, **k: str(tmp_path))
    monkeypatch.setattr(cli, "store_home", lambda *a, **k: str(tmp_path))
    constitution = load_constitution()
    stage = next(s for s in constitution.stages if s.reusable)
    assert (
        cli.main(["record", "--stage-label", stage.label, "--result", "PASS", "--digest", "a" * 64])
        == 0
    )
    entry = lookup(str(tmp_path), stage.stage_id, "a" * 64)
    assert entry is not None and entry.passed


def test_a_store_that_cannot_be_written_does_not_fail_a_verification(tmp_path) -> None:
    """A cache is an optimisation. It may never be the reason a run fails."""
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("", encoding="utf-8")
    record(str(blocked), "some-stage", "b" * 64, "PASS")
    assert lookup(str(blocked), "some-stage", "b" * 64) is None


# --- fail-closed substrate handling -------------------------------------------------


def test_an_unreadable_registry_is_a_fault_and_never_an_empty_selection(tmp_path) -> None:
    """The most dangerous possible failure is 'nothing to verify'. It must be impossible."""
    with pytest.raises(VerificationIntelligenceError, match="unreadable"):
        load_substrates(str(tmp_path))


def test_a_registry_with_no_dependency_edges_is_refused(tmp_path) -> None:
    from engine.verification_intelligence.registry import EXECUTABLE_REGISTRY

    target = tmp_path / EXECUTABLE_REGISTRY
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps({"entries": [{"path": "a.py", "object_class": "EXECUTABLE_OBJECT"}]}),
        encoding="utf-8",
    )
    with pytest.raises(VerificationIntelligenceError, match="no dependency edges"):
        load_substrates(str(tmp_path))


def test_a_registry_holding_no_entries_is_refused(tmp_path) -> None:
    from engine.verification_intelligence.registry import EXECUTABLE_REGISTRY

    target = tmp_path / EXECUTABLE_REGISTRY
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({"entries": []}), encoding="utf-8")
    with pytest.raises(VerificationIntelligenceError, match="no entries"):
        load_substrates(str(tmp_path))


def test_a_pytest_configuration_declaring_no_testpaths_is_refused(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    with pytest.raises(VerificationIntelligenceError, match="no testpaths"):
        collection_roots(str(tmp_path))


def test_an_absent_cost_model_prices_everything_at_the_default(tmp_path, substrates) -> None:
    """A missing measurement makes a plan slower, never wrong."""
    from engine.verification_intelligence.registry import load_cost_model

    costs, split, threshold = load_cost_model(str(tmp_path))
    assert costs == {} and split == {} and threshold == 0.0


def test_a_corrupt_cost_model_is_ignored_rather_than_fatal(tmp_path) -> None:
    from engine.verification_intelligence.constitution import COST_MODEL
    from engine.verification_intelligence.registry import load_cost_model

    target = tmp_path / COST_MODEL
    target.parent.mkdir(parents=True)
    target.write_text("{not json", encoding="utf-8")
    assert load_cost_model(str(tmp_path)) == ({}, {}, 0.0)


def test_a_split_entry_whose_content_hash_moved_falls_back_to_the_whole_file(
    substrates, monkeypatch
) -> None:
    """Stale node ids would fail a run; whole-file placement is slower and always correct."""
    from engine.verification_intelligence import registry as registry_module

    real = registry_module.load_cost_model

    def _stale(root=None):
        costs, split, threshold = real(root)
        for entry in split.values():
            entry["content_hash"] = "0" * 64
        return costs, split, threshold

    monkeypatch.setattr(registry_module, "load_cost_model", _stale)
    projected = registry_module.build_test_registry(substrates)
    assert projected.splittable == {}
    assert projected.units_for(projected.paths) == projected.paths


# --- the constitution refuses every incoherence it can compute -----------------------
#
# A declaration that cannot be constructed is a FAULT, deliberately not a verdict: an
# unreadable or self-contradictory constitution must not resolve to whichever answer
# happened to be convenient.


@pytest.mark.parametrize(
    ("what", "mutate", "message"),
    [
        (
            "a stage naming an undeclared phase",
            lambda d: d["stage_registry"]["stages"][0].update(phase="WHENEVER"),
            "undeclared phase",
        ),
        (
            "a stage naming an undeclared plane",
            lambda d: d["stage_registry"]["stages"][0].update(plane="SOMEWHERE"),
            "undeclared plane",
        ),
        (
            "a stage depending on a stage that does not exist",
            lambda d: d["stage_registry"]["stages"][0].update(depends_on=["not-a-stage"]),
            "undeclared stage",
        ),
        (
            "a stage admitting a mode that does not exist",
            lambda d: d["stage_registry"]["stages"][0].update(modes=["turbo"]),
            "undeclared mode",
        ),
        (
            "two stages sharing one id",
            lambda d: d["stage_registry"]["stages"][1].update(
                id=d["stage_registry"]["stages"][0]["id"]
            ),
            "share one id",
        ),
        (
            "two modes sharing one id",
            lambda d: d["mode_constitution"]["modes"][1].update(
                id=d["mode_constitution"]["modes"][0]["id"]
            ),
            "share one id",
        ),
        (
            "a default that is not a declared mode",
            lambda d: d["mode_constitution"].update(default_mode="turbo"),
            "not a declared mode",
        ),
        (
            "a mode selecting from an unknown vocabulary",
            lambda d: d["mode_constitution"]["modes"][0].update(selection="SOME_OF_IT"),
            "unknown vocabulary",
        ),
        (
            "a mode with no coverage decision at all",
            lambda d: d["mode_constitution"]["modes"][0].update(coverage=""),
            "missing or empty",
        ),
        (
            "no modes",
            lambda d: d["mode_constitution"].update(modes=[]),
            "declares no modes",
        ),
        (
            "no stages",
            lambda d: d["stage_registry"].update(stages=[]),
            "declares no stages",
        ),
        (
            "no laws",
            lambda d: d.update(laws=[]),
            "states no laws",
        ),
        (
            "no mode constitution at all",
            lambda d: d.pop("mode_constitution"),
            "no mode_constitution",
        ),
    ],
)
def test_an_incoherent_constitution_is_refused(what, mutate, message, tmp_path) -> None:
    document = load_declaration()
    mutate(document)
    path = tmp_path / "declaration.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(VerificationIntelligenceError, match=message):
        load_constitution(str(path))


def test_a_declaration_that_is_not_an_object_is_refused(tmp_path) -> None:
    path = tmp_path / "declaration.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(VerificationIntelligenceError, match="not an object"):
        load_declaration(str(path))


def test_a_check_no_law_claims_is_refused(tmp_path) -> None:
    """Both directions. An unclaimed check is a measurement nothing acts on."""
    path = tmp_path / "declaration.json"
    path.write_text(json.dumps(load_declaration()), encoding="utf-8")
    with pytest.raises(VerificationIntelligenceError, match="claimed by no law"):
        load_constitution(str(path), checks=frozenset({*uvi_gate.CHECKS, "an_orphan_check"}))


def test_asking_for_a_mode_or_stage_that_does_not_exist_is_refused(constitution) -> None:
    with pytest.raises(VerificationIntelligenceError, match="no such declared mode"):
        constitution.mode("turbo")
    with pytest.raises(VerificationIntelligenceError, match="no such declared stage"):
        constitution.stage("not-a-stage")


def test_a_mode_declaring_an_unknown_stage_selector_is_refused(tmp_path) -> None:
    document = load_declaration()
    document["mode_constitution"]["modes"][0]["stages"] = "EVERYTHING_PLEASE"
    path = tmp_path / "declaration.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    broken = load_constitution(str(path))
    with pytest.raises(VerificationIntelligenceError, match="unknown stage selector"):
        broken.stages_for(broken.modes[0])


# --- the floor, evaluated for real over combined shard data --------------------------


def test_the_floor_is_evaluated_once_over_the_union_of_the_shards(tmp_path) -> None:
    """Two shards, one combined total, one verdict — the property sharding must not break."""
    import io
    import sys
    import textwrap

    from engine.verification_intelligence.execution import run_tests

    (tmp_path / "measured.py").write_text(
        textwrap.dedent(
            """
            def covered_by_shard_one():
                return 1

            def covered_by_shard_two():
                return 2

            def covered_by_nobody():
                return 3
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_one.py").write_text(
        "import measured\n\ndef test_one():\n    assert measured.covered_by_shard_one() == 1\n",
        encoding="utf-8",
    )
    (tmp_path / "test_two.py").write_text(
        "import measured\n\ndef test_two():\n    assert measured.covered_by_shard_two() == 2\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [tool.pytest.ini_options]
            addopts = ["--cov=measured", "--cov-report=term", "--cov-fail-under=90"]

            [tool.coverage.run]
            source = ["."]
            omit = ["test_*.py"]

            [tool.coverage.report]
            fail_under = 90
            """
        ),
        encoding="utf-8",
    )
    shards = (
        Shard(index=0, test_paths=("test_one.py",), cost_seconds=0.1),
        Shard(index=1, test_paths=("test_two.py",), cost_seconds=0.1),
    )
    stream = io.StringIO()
    code = run_tests(
        shards,
        Coverage.FLOOR_90,
        root=str(tmp_path),
        python=sys.executable,
        selection=("test_one.py", "test_two.py"),
        stream=stream,
    )
    body = stream.getvalue()
    # One function is exercised by each shard and one by neither, so the combined total
    # must be below the floor — which is only true if the data was actually combined. A
    # per-shard evaluation would have failed for a different reason, and an uncombined
    # one would report a single shard's coverage as the whole.
    assert code == 1, body
    assert "below the declared floor" in body
    assert (tmp_path / "coverage.xml").is_file(), "the xml report must still be produced"


# --- capability resolution ------------------------------------------------------------


def test_an_owner_below_a_catalogued_capability_resolves_to_it(substrates) -> None:
    """A new subpackage under a known capability is attributed, not escalated."""
    from engine.verification_intelligence.selection import _capability_location

    catalogued = next(iter(sorted(substrates.capability_of_owner)))
    assert _capability_location(substrates, catalogued) == catalogued
    assert _capability_location(substrates, f"{catalogued}/a/new/subpackage") == catalogued
    assert _capability_location(substrates, "a-location-nothing-catalogues") is None


def test_the_test_mirror_is_derived_from_the_catalogue_shape() -> None:
    from engine.verification_intelligence.selection import _test_mirror

    assert _test_mirror("engine/uckp") == "engine/tests/uckp"
    assert _test_mirror("engine") == "engine/tests"
    assert _test_mirror("engine/tests") is None, "a test location has no test mirror"
    assert _test_mirror("engine/tests/uckp") is None


# --- exclusive execution --------------------------------------------------------------


def test_a_declared_isolated_object_runs_alone_and_first(constitution, tests_registry) -> None:
    """Alone because the other shards perturb it; FIRST so it sees the tree as found."""
    isolated = tuple(
        str(entry["prefix"])
        for entry in constitution.sharding.get("isolated") or ()
        if entry.get("prefix")
    )
    if not isolated:
        pytest.skip("no object is declared isolated")
    shards = plan_shards(
        tests_registry.units_for(tests_registry.paths), tests_registry, 8, isolated=isolated
    )
    first_wave = [shard for shard in shards if shard.wave == min(s.wave for s in shards)]
    assert len(first_wave) == 1, "an exclusive wave with two shards is not exclusive"
    assert all(unit_file(unit).startswith(isolated) for unit in first_wave[0].test_paths)
    body = [shard for shard in shards if shard.wave > first_wave[0].wave]
    assert body, "the concurrent body must follow the exclusive wave"
    for shard in body:
        assert not any(unit_file(unit).startswith(isolated) for unit in shard.test_paths)
    assert [shard.index for shard in shards] == list(range(len(shards)))


def test_isolation_changes_the_schedule_and_never_the_scope(tests_registry) -> None:
    """The covered set must be identical whether or not anything is isolated.

    Stated over test OBJECTS rather than over units, because which shard becomes the
    remainder for a split file legitimately depends on the partition — and the remainder
    holds the file where the others hold nodes.
    """
    units = tests_registry.units_for(tests_registry.paths)
    without = plan_shards(units, tests_registry, 8)
    with_isolation = plan_shards(units, tests_registry, 8, isolated=("platform/tests/",))
    covered = lambda shards: sorted(  # noqa: E731
        {unit_file(unit) for shard in shards for unit in shard.test_paths}
    )
    assert covered(without) == covered(with_isolation) == sorted(tests_registry.paths)
    assert any(shard.wave > 0 for shard in with_isolation)


def test_every_declared_isolated_prefix_states_why_it_is_isolated(constitution) -> None:
    """Isolation is expensive, so the bar for adding one is a measurement, not a suspicion."""
    for entry in constitution.sharding.get("isolated") or ():
        assert entry.get("prefix")
        assert entry.get("$measured"), f"{entry.get('prefix')} is isolated without a measurement"


def test_l06_refuses_an_isolation_entry_for_an_object_that_is_not_there(tmp_path) -> None:
    """A stale scheduling exception must fail, not sit inert."""

    def mutate(document):
        document["execution"]["test_sharding"]["isolated"] = [
            {"prefix": "platform/tests/test_a_file_that_was_deleted.py", "$measured": "why"}
        ]

    findings = uvi_gate.selection_is_derived(_ctx(tmp_path, mutate))
    assert any("matches no collectible test object" in f for f in findings)


def test_l06_refuses_an_isolation_entry_with_no_measurement(tmp_path, constitution) -> None:
    def mutate(document):
        for entry in document["execution"]["test_sharding"]["isolated"]:
            entry.pop("$measured", None)

    findings = uvi_gate.selection_is_derived(_ctx(tmp_path, mutate))
    assert any("no measurement justifying it" in f for f in findings)


def test_running_the_tests_leaves_nothing_in_the_repository(tmp_path) -> None:
    """A verification run must not be able to dirty the thing it is verifying."""
    import io
    import sys

    from engine.verification_intelligence.execution import run_tests

    shards = _throwaway_suite(tmp_path)
    before = sorted(os.listdir(tmp_path))
    run_tests(
        shards,
        Coverage.NOT_EVALUATED,
        root=str(tmp_path),
        python=sys.executable,
        selection=("test_alpha.py", "test_beta.py"),
        stream=io.StringIO(),
    )
    left = sorted(set(os.listdir(tmp_path)) - set(before))
    assert not [
        name for name in left if name.startswith("uvi-")
    ], f"the run left working directories behind: {left}"


def test_the_evidence_store_is_excluded_from_the_tracked_tree(constitution) -> None:
    """A cache inside the tree is a second answer to 'did this pass'."""
    ignored = {
        line.strip().rstrip("/")
        for line in open(os.path.join(REPO, ".gitignore"), encoding="utf-8")
        if not line.startswith("#")
    }
    assert constitution.evidence_home.rstrip("/") in ignored


def test_l06_refuses_an_evidence_store_that_would_be_tracked(tmp_path) -> None:
    def mutate(document):
        document["evidence_registry"]["home"] = ".a-store-nothing-ignores/"

    findings = uvi_gate.selection_is_derived(_ctx(tmp_path, mutate))
    assert any("not excluded by .gitignore" in f for f in findings)


def test_the_test_stage_runs_in_a_phase_of_its_own(constitution) -> None:
    """Read-only is not sufficient for concurrency — see the stage's own $phase note."""
    pytest_stage = constitution.stage("pytest")
    others = [s for s in constitution.stages if s.phase == pytest_stage.phase]
    assert others == [pytest_stage], (
        "the suite regenerates derived views and takes the git index lock, so nothing may "
        "read the tree beside it"
    )


def test_the_shards_collect_exactly_the_tests_the_whole_suite_collects() -> None:
    """THE test. Everything else about sharding is an optimisation; this is correctness.

    Every property the plan asserts about itself is asserted at the granularity the plan
    reasons in. This one asks pytest, at the granularity pytest reasons in: collect the
    whole suite, collect every shard, and require the two sets to be equal.

    It is here because the file-level version of this check passed while the run was
    losing tests. A test object above the split threshold is placed as its measured
    nodes, and ``--durations`` hides anything under 0.005s — so 54 tests that were too
    fast to be measured were in no shard at all, and the suite reported 11 706 of 11 760
    as a pass. No amount of reasoning about the cost model would have found that; only
    asking the collector did.
    """
    import subprocess
    import sys

    from engine.verification_intelligence.execution import _shard_argv

    def _collect(argv: list[str]) -> set[str]:
        result = subprocess.run(  # noqa: S603
            [*argv[: argv.index("-q") + 1], "--collect-only", *argv[argv.index("-q") + 1 :]],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            line.strip()
            for line in result.stdout.splitlines()
            if "::" in line and not line.startswith(" ")
        }

    serial = _collect([sys.executable, "-m", "pytest", "-o", "addopts=", "--no-cov", "-q"])
    assert serial, "the whole suite collected nothing; the comparison would be vacuous"

    plan = build_plan("integration")
    union: set[str] = set()
    placed = 0
    for shard in plan.shards:
        ids = _collect(_shard_argv(sys.executable, shard, Coverage.NOT_EVALUATED))
        placed += len(ids)
        union |= ids

    assert placed == len(union), f"{placed - len(union)} test(s) are collected by two shards"
    assert union == serial, (
        f"{len(serial - union)} test(s) are in no shard and would be silently skipped: "
        f"{sorted(serial - union)[:5]}; {len(union - serial)} are in a shard and not in the suite"
    )


# --- every substrate fails closed ----------------------------------------------------
#
# One shape per substrate. A selector missing one of its graphs must FAULT, because the
# alternative is that it silently reasons from the ones it still has and narrows a run.


def _substrate_fixture(tmp_path, **overrides):
    """A minimal but valid substrate tree, with one surface replaced by the caller."""
    from engine.verification_intelligence.registry import (
        CAPABILITY_CATALOG,
        EXECUTABLE_REGISTRY,
        RELATIONSHIP_GRAPH,
        UNIVERSAL_REGISTRY,
    )

    executable_entries = [
        {"path": "a.py", "object_class": "EXECUTABLE_OBJECT", "dependencies": []},
        {
            "path": "engine/tests/test_a.py",
            "object_class": "TEST_OBJECT",
            "owner": "engine/tests",
            "universal_id": "UCOS-TESTOBJ-000001",
            "dependencies": ["a.py"],
            "content_hash": "0" * 64,
        },
    ]
    surfaces = {
        EXECUTABLE_REGISTRY: {"entries": executable_entries},
        # 02 is a superset of 01 in the repository, so the fixture models it as one:
        # the executable objects plus a DOCUMENT_ARTIFACT that 01 never carries.
        UNIVERSAL_REGISTRY: {
            "entries": [
                *executable_entries,
                {
                    "path": "doc/a.md",
                    "object_class": "DOCUMENT_ARTIFACT",
                    "owner": "doc",
                    "universal_id": "UCOS-EXDOC-000001",
                    "content_hash": "1" * 64,
                },
            ]
        },
        RELATIONSHIP_GRAPH: {"relationships": [{"from": "UCOS-TESTOBJ-000001", "to": "a.py"}]},
        CAPABILITY_CATALOG: {
            "capabilities": [{"canonical_location": "engine", "canonical_name": "engine"}]
        },
    }
    surfaces.update(overrides)
    for name, document in surfaces.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(document), encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\ntestpaths = ["engine/tests"]\n', encoding="utf-8"
    )
    return tmp_path


def test_a_valid_substrate_tree_loads(tmp_path) -> None:
    """The control. Without it the refusals below could pass for the wrong reason."""
    root = _substrate_fixture(tmp_path)
    substrates = load_substrates(str(root))
    assert substrates.capability_of_owner == {"engine": "engine"}
    assert substrates.related_identities({"UCOS-TESTOBJ-000001"}) == {"a.py"}
    registry = build_test_registry(substrates, str(root))
    assert registry.paths == ("engine/tests/test_a.py",)


@pytest.mark.parametrize(
    ("surface", "document", "message"),
    [
        ("RELATIONSHIP_GRAPH", {"relationships": []}, "no relationships"),
        ("RELATIONSHIP_GRAPH", {"relationships": "not-a-list"}, "no relationships"),
        ("CAPABILITY_CATALOG", {"capabilities": []}, "no capabilities"),
        ("CAPABILITY_CATALOG", {"nothing": True}, "no capabilities"),
    ],
)
def test_an_unusable_substrate_is_a_fault(surface, document, message, tmp_path) -> None:
    from engine.verification_intelligence import registry as registry_module

    root = _substrate_fixture(tmp_path, **{getattr(registry_module, surface): document})
    with pytest.raises(VerificationIntelligenceError, match=message):
        load_substrates(str(root))


def test_a_surface_that_is_not_an_object_is_a_fault(tmp_path) -> None:
    from engine.verification_intelligence.registry import EXECUTABLE_REGISTRY

    root = _substrate_fixture(tmp_path)
    (root / EXECUTABLE_REGISTRY).write_text("[]", encoding="utf-8")
    with pytest.raises(VerificationIntelligenceError, match="not an object"):
        load_substrates(str(root))


def test_malformed_entries_are_skipped_rather_than_crashing(tmp_path) -> None:
    """A surface may carry a row this engine does not understand; it may not carry none."""
    from engine.verification_intelligence.registry import (
        CAPABILITY_CATALOG,
        EXECUTABLE_REGISTRY,
        RELATIONSHIP_GRAPH,
    )

    root = _substrate_fixture(
        tmp_path,
        **{
            EXECUTABLE_REGISTRY: {
                "entries": [
                    "not-a-dict",
                    {"no_path": True},
                    {
                        "path": "engine/tests/test_a.py",
                        "object_class": "TEST_OBJECT",
                        "owner": "engine/tests",
                        "dependencies": ["a.py"],
                    },
                ]
            },
            RELATIONSHIP_GRAPH: {
                "relationships": ["not-a-dict", {"from": "", "to": ""}, {"from": "x", "to": "y"}]
            },
            CAPABILITY_CATALOG: {
                "capabilities": [
                    "not-a-dict",
                    {"canonical_location": ""},
                    {"canonical_location": "engine"},
                ]
            },
        },
    )
    substrates = load_substrates(str(root))
    assert set(substrates.objects) == {"engine/tests/test_a.py"}
    assert substrates.capability_of_owner == {"engine": "engine"}


def test_a_tree_whose_registry_and_pytest_config_disagree_is_a_fault(tmp_path) -> None:
    root = _substrate_fixture(tmp_path)
    (root / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\ntestpaths = ["somewhere/else"]\n', encoding="utf-8"
    )
    with pytest.raises(VerificationIntelligenceError, match="no collectible test object"):
        build_test_registry(load_substrates(str(root)), str(root))


def test_an_unreadable_pytest_configuration_is_a_fault(tmp_path) -> None:
    root = _substrate_fixture(tmp_path)
    (root / "pyproject.toml").write_text("[tool.pytest\n", encoding="utf-8")
    with pytest.raises(VerificationIntelligenceError, match="unreadable"):
        collection_roots(str(root))


def test_total_cost_prices_the_whole_suite_by_default(tests_registry) -> None:
    assert tests_registry.total_cost() == pytest.approx(
        tests_registry.total_cost(tests_registry.paths)
    )
    assert tests_registry.total_cost(()) == 0
