"""Verification Impact Engine tests.

The suite is weighted toward proving the engine **fails wide**, because that is the
property that makes it safe to select verification with. A selector that errs narrow
produces a green run which skipped the affected test, so every test named
``*_escalates_*`` is guarding against the dangerous direction, not the annoying one.
"""

from __future__ import annotations

import json

import pytest

from engine.verification_impact import (
    IMPACT_CONTRACT,
    ImpactError,
    ImpactGraph,
    ObjectRecord,
    Scope,
    analyse,
    load_graph,
    plan,
)
from engine.verification_impact.cli import EXIT_BOUNDED, EXIT_ESCALATED, main
from engine.verification_impact.graph import CODE_CLASSES, repo_root


def _record(path: str, cls: str = "EXECUTABLE_OBJECT", deps=(), owner="own") -> ObjectRecord:
    return ObjectRecord(
        path=path,
        universal_id=f"UCOS-X-{abs(hash(path)) % 1000000:06d}",
        object_class=cls,
        owner=owner,
        dependencies=tuple(deps),
        produces=(),
        evidence_class="VALIDATION",
        certification_status="GOVERNED",
        content_hash="deadbeef",
    )


def _graph(*records: ObjectRecord) -> ImpactGraph:
    graph = ImpactGraph()
    for record in records:
        graph.objects[record.path] = record
        graph.owners[record.owner].add(record.path)
        for dep in record.dependencies:
            graph.dependents[dep].add(record.path)
    return graph


# --------------------------------------------------------------------- substrate


def test_the_engine_builds_no_new_graph() -> None:
    assert IMPACT_CONTRACT["builds_new_graph"] is False
    assert IMPACT_CONTRACT["fails_wide"] is True


def test_the_committed_registry_loads_with_real_edges() -> None:
    graph = load_graph()
    assert len(graph.objects) > 4000
    assert len(graph.tests) > 700
    assert len(graph.dependents) > 500


def test_load_fails_closed_on_a_missing_registry(tmp_path) -> None:
    with pytest.raises(ImpactError, match="unreadable"):
        load_graph(str(tmp_path))


def test_load_fails_closed_on_an_empty_registry(tmp_path) -> None:
    target = tmp_path / "00-MASTER" / "UCOS-UGA-001"
    target.mkdir(parents=True)
    (target / "01-EXECUTABLE-OBJECT-REGISTRY.json").write_text(json.dumps({"entries": []}))
    with pytest.raises(ImpactError, match="holds no entries"):
        load_graph(str(tmp_path))


def test_load_fails_closed_when_no_edges_exist(tmp_path) -> None:
    """A registry with objects but no edges cannot answer an impact question."""
    target = tmp_path / "00-MASTER" / "UCOS-UGA-001"
    target.mkdir(parents=True)
    (target / "01-EXECUTABLE-OBJECT-REGISTRY.json").write_text(
        json.dumps({"entries": [{"path": "a.py", "object_class": "EXECUTABLE_OBJECT"}]})
    )
    with pytest.raises(ImpactError, match="no dependency edges"):
        load_graph(str(tmp_path))


def test_malformed_entries_are_skipped_not_fatal(tmp_path) -> None:
    target = tmp_path / "00-MASTER" / "UCOS-UGA-001"
    target.mkdir(parents=True)
    (target / "01-EXECUTABLE-OBJECT-REGISTRY.json").write_text(
        json.dumps(
            {
                "entries": [
                    "not-a-mapping",
                    {"no_path": True},
                    {"path": "b.py", "object_class": "TEST_OBJECT", "dependencies": ["a.py"]},
                ]
            }
        )
    )
    graph = load_graph(str(tmp_path))
    assert graph.tests == ("b.py",)


def test_repo_root_resolves_to_a_real_checkout() -> None:
    import os

    assert os.path.isdir(os.path.join(repo_root(), "00-MASTER"))


def test_code_classes_cover_the_executable_kinds() -> None:
    assert "TEST_OBJECT" in CODE_CLASSES and "EXECUTABLE_OBJECT" in CODE_CLASSES


# --------------------------------------------------------------------- traversal


def test_dependents_are_found_transitively() -> None:
    graph = _graph(
        _record("core.py"),
        _record("mid.py", deps=["core.py"]),
        _record("test_top.py", cls="TEST_OBJECT", deps=["mid.py"]),
    )
    assert graph.dependents_of({"core.py"}) == {"mid.py", "test_top.py"}


def test_direct_only_traversal_stops_at_one_hop() -> None:
    graph = _graph(
        _record("core.py"),
        _record("mid.py", deps=["core.py"]),
        _record("test_top.py", cls="TEST_OBJECT", deps=["mid.py"]),
    )
    assert graph.dependents_of({"core.py"}, transitive=False) == {"mid.py"}


def test_a_dependency_cycle_terminates() -> None:
    """Import cycles exist in real trees; traversal must not spin."""
    graph = _graph(_record("a.py", deps=["b.py"]), _record("b.py", deps=["a.py"]))
    assert graph.dependents_of({"a.py"}) == {"a.py", "b.py"}


def test_ownership_lookup() -> None:
    graph = _graph(_record("x.py", owner="alpha"), _record("y.py", owner="alpha"))
    assert graph.owned_by("alpha") == ("x.py", "y.py")
    assert graph.owned_by("absent") == ()


def test_record_lookup_returns_none_for_an_unknown_path() -> None:
    assert _graph().record("nope.py") is None


# ------------------------------------------------------------------- bounded case


def test_a_bounded_change_selects_only_reachable_tests() -> None:
    graph = _graph(
        _record("core.py"),
        _record("test_core.py", cls="TEST_OBJECT", deps=["core.py"]),
        _record("test_unrelated.py", cls="TEST_OBJECT", deps=["other.py"]),
        _record("other.py"),
    )
    report = analyse(graph, ["core.py"])
    assert report.scope is Scope.CHANGED
    assert report.affected_tests == ("test_core.py",)
    assert "test_unrelated.py" not in report.affected_objects


def test_report_surfaces_evidence_certification_and_owners() -> None:
    graph = _graph(
        _record("core.py", owner="alpha"),
        _record("test_core.py", cls="TEST_OBJECT", deps=["core.py"], owner="alpha"),
    )
    report = analyse(graph, ["core.py"])
    assert report.affected_evidence == ("VALIDATION",)
    assert report.affected_certification == ("GOVERNED",)
    assert report.affected_owners == ("alpha",)


def test_plan_for_a_bounded_change_selects_paths() -> None:
    graph = _graph(
        _record("core.py"),
        _record("test_core.py", cls="TEST_OBJECT", deps=["core.py"]),
    )
    verification = plan(analyse(graph, ["core.py"]))
    assert verification.run_everything is False
    assert verification.test_paths == ("test_core.py",)


# ----------------------------------------------------------------- escalation


def test_no_changes_is_scope_none() -> None:
    report = analyse(_graph(), [])
    assert report.scope is Scope.NONE
    assert plan(report).run_everything is False
    assert plan(report).reason == "no changes to verify"


@pytest.mark.parametrize(
    "path",
    [
        "00-BOOK/DATA/id-ledger.json",
        "00-BOOK/SCHEMAS/artifact.schema.json",
        "00-BOOK/tools/ukb.py",
        "00-CMG/CMG-000001-x.md",
        "00-CEP/CEP-007-x.md",
        "pyproject.toml",
        "verify.sh",
        "Makefile",
        "scripts/ucos-env.sh",
    ],
)
def test_unbounded_paths_escalate_to_full(path: str) -> None:
    """A declaration drives engines no import graph connects to it."""
    report = analyse(_graph(_record("core.py")), [path])
    assert report.scope is Scope.FULL
    assert plan(report).run_everything is True


def test_non_python_changes_escalate_to_full() -> None:
    report = analyse(_graph(_record("core.py")), ["00-MASTER/X/register.md"])
    assert report.scope is Scope.FULL
    assert any("no dependency edges exist" in e for e in report.escalations)


def test_an_unregistered_python_file_escalates_and_is_named() -> None:
    """A new file absent from the registry has unknown dependents."""
    report = analyse(_graph(_record("core.py")), ["engine/brand_new.py"])
    assert report.scope is Scope.FULL
    assert report.unregistered == ("engine/brand_new.py",)


def test_a_bounded_change_reaching_no_test_widens_rather_than_skipping() -> None:
    """Code nothing exercises is a coverage question, not a licence to skip."""
    report = analyse(_graph(_record("orphan.py")), ["orphan.py"])
    assert report.scope is Scope.INTEGRATION
    assert any("reaches no test object" in e for e in report.escalations)
    assert plan(report).run_everything is True


def test_a_broad_blast_radius_widens_to_integration() -> None:
    graph = _graph(
        _record("core.py"),
        *[
            _record(f"test_{n}.py", cls="TEST_OBJECT", deps=["core.py"], owner=f"own{n}")
            for n in range(5)
        ],
    )
    report = analyse(graph, ["core.py"])
    assert report.scope is Scope.INTEGRATION
    assert any("subsystem-level blast radius" in e for e in report.escalations)


def test_mixed_changes_take_the_broader_scope() -> None:
    graph = _graph(
        _record("core.py"),
        _record("test_core.py", cls="TEST_OBJECT", deps=["core.py"]),
    )
    report = analyse(graph, ["core.py", "pyproject.toml"])
    assert report.scope is Scope.FULL


def test_scope_widen_is_monotonic() -> None:
    assert Scope.CHANGED.widen(Scope.FULL) is Scope.FULL
    assert Scope.FULL.widen(Scope.CHANGED) is Scope.FULL
    assert Scope.NONE.widen(Scope.NONE) is Scope.NONE
    assert Scope.INTEGRATION.widen(Scope.CHANGED) is Scope.INTEGRATION


def test_report_serialises_with_counts() -> None:
    graph = _graph(
        _record("core.py"),
        _record("test_core.py", cls="TEST_OBJECT", deps=["core.py"]),
    )
    body = analyse(graph, ["core.py"]).to_dict()
    assert body["counts"]["affected_tests"] == 1
    assert body["scope"] == "changed"


def test_is_full_predicate() -> None:
    assert analyse(_graph(), ["verify.sh"]).is_full is True


# ------------------------------------------------------------------------- CLI


def test_cli_bounded_change_exits_zero(capsys) -> None:
    assert main(["--path", "engine/temporal/coordinate.py", "--quiet"]) == EXIT_BOUNDED


def test_cli_selects_the_temporal_tests(capsys) -> None:
    """Live registry: a temporal change must reach its own suite."""
    main(["--path", "engine/temporal/coordinate.py", "--print-tests"])
    out = capsys.readouterr().out
    assert "engine/tests/unit/test_temporal_contract.py" in out


def test_cli_escalation_exits_two(capsys) -> None:
    assert main(["--path", "00-BOOK/DATA/id-ledger.json", "--quiet"]) == EXIT_ESCALATED


def test_cli_print_tests_is_empty_when_escalated(capsys) -> None:
    """Silence plus exit 2 — never silence plus exit 0."""
    code = main(["--path", "verify.sh", "--print-tests"])
    assert code == EXIT_ESCALATED
    assert capsys.readouterr().out.strip() == ""


def test_cli_emits_json(capsys) -> None:
    main(["--path", "engine/temporal/coordinate.py", "--json"])
    body = json.loads(capsys.readouterr().out)
    assert body["plan"]["scope"] == "changed"
    assert body["impact"]["counts"]["changed"] == 1


def test_cli_renders_a_report(capsys) -> None:
    main(["--path", "engine/temporal/coordinate.py"])
    assert "VERIFICATION IMPACT" in capsys.readouterr().out


def test_cli_renders_escalations(capsys) -> None:
    main(["--path", "verify.sh"])
    assert "escalations:" in capsys.readouterr().out


def test_cli_faults_on_an_unresolvable_base(capsys) -> None:
    assert main(["--base", "not-a-real-ref-xyz", "--quiet"]) == EXIT_ESCALATED
    assert "IMPACT FAULT" in capsys.readouterr().err


# ------------------------------------------------------------------- changes


def test_working_tree_changes_returns_paths() -> None:
    from engine.verification_impact import working_tree_changes

    assert isinstance(working_tree_changes(), tuple)


def test_changed_paths_refuses_an_unresolvable_base() -> None:
    from engine.verification_impact import changed_paths

    with pytest.raises(ImpactError, match="does not resolve"):
        changed_paths("definitely-not-a-ref-abc123")


# ------------------------------------------------- diff-base resolution coverage
# The resolution chain is the part that must never return an empty set on failure,
# so each branch is exercised against a real throwaway repository rather than mocks.


@pytest.fixture(name="scratch_repo")
def _scratch_repo(tmp_path):
    """A real git repository with one commit, for base-resolution tests."""
    import subprocess

    root = tmp_path / "repo"
    root.mkdir()

    def git(*args: str):
        return subprocess.run(  # noqa: S603
            ["git", *args],  # noqa: S607 - resolved from PATH by design
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

    git("init", "-q")
    git("config", "user.email", "t@t.invalid")
    git("config", "user.name", "t")
    (root / "a.py").write_text("x = 1\n")
    git("add", "a.py")
    git("commit", "-q", "-m", "first")
    return root, git


def test_explicit_base_diffs_against_it(scratch_repo) -> None:
    from engine.verification_impact.changes import changed_paths

    root, git = scratch_repo
    (root / "b.py").write_text("y = 2\n")
    git("add", "b.py")
    git("commit", "-q", "-m", "second")
    assert changed_paths("HEAD^", root=str(root)) == ("b.py",)


def test_working_tree_changes_include_staged_unstaged_and_untracked(scratch_repo) -> None:
    from engine.verification_impact.changes import working_tree_changes

    root, git = scratch_repo
    (root / "a.py").write_text("x = 2\n")  # unstaged modification
    (root / "staged.py").write_text("z = 3\n")
    git("add", "staged.py")
    (root / "untracked.py").write_text("w = 4\n")
    found = working_tree_changes(root=str(root))
    assert set(found) == {"a.py", "staged.py", "untracked.py"}


def test_working_tree_changes_take_priority_over_history(scratch_repo) -> None:
    from engine.verification_impact.changes import changed_paths

    root, _ = scratch_repo
    (root / "dirty.py").write_text("d = 1\n")
    assert changed_paths(root=str(root)) == ("dirty.py",)


def test_head_parent_is_used_when_the_tree_is_clean(scratch_repo) -> None:
    from engine.verification_impact.changes import changed_paths

    root, git = scratch_repo
    (root / "c.py").write_text("c = 1\n")
    git("add", "c.py")
    git("commit", "-q", "-m", "third")
    assert changed_paths(root=str(root)) == ("c.py",)


def test_a_clean_single_commit_repo_refuses_rather_than_reporting_nothing(
    scratch_repo,
) -> None:
    """The dangerous case: no base, clean tree. Must raise, never return ()."""
    from engine.verification_impact.changes import changed_paths

    root, _ = scratch_repo  # one commit, no HEAD^, no upstream, clean
    with pytest.raises(ImpactError, match="no diff base could be resolved"):
        changed_paths(root=str(root))


def test_working_tree_changes_outside_a_repository_returns_empty(tmp_path) -> None:
    from engine.verification_impact.changes import working_tree_changes

    assert working_tree_changes(root=str(tmp_path)) == ()


def test_changed_paths_outside_a_repository_refuses(tmp_path) -> None:
    from engine.verification_impact.changes import changed_paths

    with pytest.raises(ImpactError):
        changed_paths(root=str(tmp_path))
