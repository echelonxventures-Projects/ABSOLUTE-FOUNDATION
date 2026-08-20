"""EX-016 — the classifier that makes EX-015's declared rules decidable.

The bar these tests hold is the one the register itself sets: a rule nobody evaluates is
prose, and prose is what let ``uisd-declaration.json`` be authored, owned, engine-consumed
and unclassified while six of its mutations were certified. So every declared rule is
exercised against a real subject, the terminal is exercised, and the two-sided coverage
check is exercised in both directions.

``UNRESOLVED`` is asserted to be diagnostic — never a class, never an authority, never a
default — because a permissive default is precisely how two mutation classes came to be
missing in the first place.
"""

from __future__ import annotations

from pathlib import Path
from platform.repository_intelligence import mutation_classification as mc

import pytest

REPO = Path(__file__).resolve().parents[2]

UISD = "00-MASTER/UISD-000001/uisd-declaration.json"


@pytest.fixture(scope="module")
def repo() -> mc.Repository:
    return mc.Repository(REPO)


@pytest.fixture(scope="module")
def boundary(repo: mc.Repository) -> dict:
    return mc.load_boundary(repo.root)


# ------------------------------------------------------------------ rule coverage


def test_every_declared_rule_has_a_predicate_and_every_predicate_a_rule(boundary: dict) -> None:
    """Two-sided, exactly like LAW_CHECKS: neither direction may drift."""
    assert mc.validate_rule_coverage(boundary) == ()


def test_a_declared_rule_with_no_predicate_is_refused(boundary: dict) -> None:
    doc = {"classification_rules": {"rules": [{"id": "R-99", "class": "X"}]}}
    problems = mc.validate_rule_coverage(doc)
    assert any("no predicate implements it" in p for p in problems)


def test_a_predicate_no_rule_declares_is_refused() -> None:
    doc = {"classification_rules": {"rules": [{"id": "R-01", "class": "REPOSITORY_STATE"}]}}
    problems = mc.validate_rule_coverage(doc)
    assert any("no rule declares it" in p for p in problems)


# ------------------------------------------------------- classes 0..5, each resolved


def test_class_0_constitutional_truth_resolves_from_an_object_subject(
    repo: mc.Repository, boundary: dict
) -> None:
    result = mc.classify(mc.Subject.of_object("population/alpha", "Population"), repo, boundary)
    assert result.status == mc.CLASSIFIED
    assert result.mutation_class == "CONSTITUTIONAL_TRUTH"
    assert result.rule_id == "R-05"
    assert result.authority == "UCOS-CMG-EXEC-000001"


def test_class_0_is_an_object_predicate_not_a_path_predicate(
    repo: mc.Repository, boundary: dict
) -> None:
    """A path never satisfies R-05; the register states the domain and the code honours it."""
    result = mc.classify("engine/constitution/gateway.py", repo, boundary)
    assert result.mutation_class != "CONSTITUTIONAL_TRUTH"


def test_class_1_source_resolves(repo: mc.Repository, boundary: dict) -> None:
    for path in ("engine/nucleus/lifecycle.py", "verify.sh", "pyproject.toml"):
        result = mc.classify(path, repo, boundary)
        assert result.status == mc.CLASSIFIED, path
        assert result.mutation_class == "SOURCE", path
        assert result.rule_id == "R-07", path


def test_class_2_generated_artifact_resolves(repo: mc.Repository, boundary: dict) -> None:
    result = mc.classify("intelligence/UCOS-RIE-MODEL.json", repo, boundary)
    assert result.status == mc.CLASSIFIED
    assert result.mutation_class == "GENERATED_ARTIFACT"
    assert result.rule_id == "R-04"


def test_class_3_exclusion_resolves(repo: mc.Repository, boundary: dict) -> None:
    result = mc.classify(".gitignore", repo, boundary)
    assert result.status == mc.CLASSIFIED
    assert result.mutation_class == "EXCLUSION"
    assert result.rule_id == "R-02"


def test_class_4_repository_state_resolves(repo: mc.Repository, boundary: dict) -> None:
    result = mc.classify(".git/index", repo, boundary)
    assert result.status == mc.CLASSIFIED
    assert result.mutation_class == "REPOSITORY_STATE"
    assert result.rule_id == "R-01"


def test_class_5_corpus_registration_resolves(repo: mc.Repository, boundary: dict) -> None:
    for path in ("00-BOOK/DATA/id-ledger.json", "00-BOOK/DATA/artifacts.json"):
        result = mc.classify(path, repo, boundary)
        assert result.status == mc.CLASSIFIED, path
        assert result.mutation_class == "CORPUS_REGISTRATION", path
        assert result.rule_id == "R-03", path


# --------------------------------------------------------------- class 6, positive


def test_class_6_the_uisd_declaration_resolves_to_governed_declaration(
    repo: mc.Repository, boundary: dict
) -> None:
    """The artifact whose unclassifiability was the whole reason for EX-015 and EX-016."""
    result = mc.classify(UISD, repo, boundary)
    assert result.status == mc.CLASSIFIED
    assert result.mutation_class == "GOVERNED_DECLARATION"
    assert result.rule_id == "R-06"
    assert "owning programme" in result.authority


def test_class_6_every_declared_example_resolves(repo: mc.Repository, boundary: dict) -> None:
    examples = next(
        e["examples"] for e in boundary["mutation_classes"] if e["class"] == "GOVERNED_DECLARATION"
    )
    assert examples, "the class declares no example, so this test would be vacuous"
    for path in examples:
        result = mc.classify(path, repo, boundary)
        assert result.mutation_class == "GOVERNED_DECLARATION", f"{path}: {result.reason}"


def test_class_6_evaluates_criteria_and_never_matches_on_examples(
    repo: mc.Repository, boundary: dict
) -> None:
    """Examples are documentation. Membership is the seven criteria, each computed."""
    checks = mc.governed_declaration_checks(UISD, repo.declaration_document(UISD), repo)
    declared = next(
        e["membership_criteria"]
        for e in boundary["mutation_classes"]
        if e["class"] == "GOVERNED_DECLARATION"
    )
    assert len(checks) == len(declared)
    assert all(checks.values()), checks


# --------------------------------------------------------------- class 6, negative


def test_executable_source_is_not_a_governed_declaration(
    repo: mc.Repository, boundary: dict
) -> None:
    checks = mc.governed_declaration_checks("engine/nucleus/lifecycle.py", None, repo)
    assert checks["non-executable"] is False
    assert mc.classify("engine/nucleus/lifecycle.py", repo, boundary).mutation_class == "SOURCE"


def test_a_generated_artifact_is_not_a_governed_declaration(
    repo: mc.Repository, boundary: dict
) -> None:
    path = "intelligence/UCOS-RIE-MODEL.json"
    checks = mc.governed_declaration_checks(path, repo.declaration_document(path), repo)
    assert checks["non-generated"] is False
    assert mc.classify(path, repo, boundary).mutation_class == "GENERATED_ARTIFACT"


def test_an_artifact_with_no_owning_programme_is_not_a_governed_declaration(
    repo: mc.Repository, tmp_path: Path
) -> None:
    """Criterion 4 fails closed: no owner, no class. CEP-009 I.3 keeps ownership single."""
    document = {"laws": [{"id": "X"}]}
    checks = mc.governed_declaration_checks("nowhere/orphan.json", document, repo)
    assert checks["programme-owned"] is False


def test_a_declaration_bearing_file_outside_version_control_is_refused(
    repo: mc.Repository,
) -> None:
    checks = mc.governed_declaration_checks(
        "00-MASTER/NOT-TRACKED/x.json", {"programme": {"id": "P"}}, repo
    )
    assert checks["repository-controlled"] is False


# ------------------------------------------------------------------- the terminal


def test_an_unknown_artifact_returns_unresolved(repo: mc.Repository, boundary: dict) -> None:
    result = mc.classify("README.md", repo, boundary)
    assert result.status == mc.UNRESOLVED
    assert result.mutation_class == ""
    assert result.rule_id == ""
    assert result.authority == ""
    assert "FAILS CLOSED" in result.reason


def test_unresolved_confers_no_class_and_no_authority(repo: mc.Repository, boundary: dict) -> None:
    """UNRESOLVED is diagnostic. It must never read as a permissive default."""
    declared = {e["class"] for e in boundary["mutation_classes"]}
    result = mc.classify("README.md", repo, boundary)
    assert result.mutation_class not in declared
    assert mc.UNRESOLVED not in declared


def test_unresolved_reports_the_subjects_for_a_fail_closed_consumer(
    repo: mc.Repository,
) -> None:
    results = mc.classify_all(["README.md", UISD], repo)
    assert mc.unresolved(results) == ("README.md",)


# -------------------------------------------------------------------- determinism


def test_repeated_evaluation_is_identical(repo: mc.Repository, boundary: dict) -> None:
    for path in (UISD, "engine/nucleus/lifecycle.py", "README.md", ".gitignore"):
        first = mc.classify(path, repo, boundary)
        second = mc.classify(path, repo, boundary)
        assert first == second, path


def test_result_is_independent_of_the_order_subjects_are_presented(
    repo: mc.Repository,
) -> None:
    forward = mc.classify_all([UISD, "README.md", ".gitignore"], repo)
    reverse = mc.classify_all([".gitignore", "README.md", UISD], repo)
    assert forward == reverse


def test_a_second_repository_view_of_the_same_state_agrees(boundary: dict) -> None:
    """No cached state leaks between views; the result is a function of the repository."""
    a, b = mc.Repository(REPO), mc.Repository(REPO)
    assert mc.classify(UISD, a, boundary) == mc.classify(UISD, b, boundary)


def test_the_result_carries_no_clock_or_environment(repo: mc.Repository, boundary: dict) -> None:
    payload = mc.classify(UISD, repo, boundary).to_dict()
    assert set(payload) == {
        "artifact",
        "mutation_class",
        "rule_id",
        "authority",
        "status",
        "reason",
    }


# ------------------------------------------------------------------------- faults


def test_an_unreadable_boundary_is_an_error_not_a_classification(tmp_path: Path) -> None:
    result = mc.classify("anything", mc.Repository(tmp_path))
    assert result.status == mc.ERROR
    assert result.mutation_class == ""


def test_a_boundary_without_classification_rules_fails_closed(tmp_path: Path) -> None:
    target = tmp_path / "00-BOOK" / "DATA"
    target.mkdir(parents=True)
    (target / "mutation-governance-boundary.json").write_text("{}", encoding="utf-8")
    with pytest.raises(mc.ClassificationError):
        mc.load_boundary(tmp_path)


# ------------------------------------------------- hermetic views and fault paths
#
# Repository._overrides exists so a test can state a repository rather than discover one.
# Exercising it here is what keeps these cases hermetic: no git, no filesystem walk, and a
# subject whose classification depends only on the stated view.


def _view(**overrides: object) -> mc.Repository:
    base: dict[str, object] = {
        "tracked": set(),
        "generated": set(),
        "producer_homes": set(),
        "python_corpus": "",
    }
    base.update(overrides)
    return mc.Repository(REPO, base)


def test_a_stated_view_drives_classification_without_touching_git(boundary: dict) -> None:
    view = _view(
        tracked={"00-MASTER/X-000001/x-declaration.json"}, python_corpus='"x-declaration.json"'
    )
    result = mc.classify("00-MASTER/X-000001/x-declaration.json", view, boundary)
    assert result.status in {mc.CLASSIFIED, mc.UNRESOLVED}
    assert view.tracked == {"00-MASTER/X-000001/x-declaration.json"}
    assert view.generated == frozenset()
    assert view.producer_homes == frozenset()


def test_a_generated_path_in_the_stated_view_wins_precedence(boundary: dict) -> None:
    view = _view(generated={"00-MASTER/X-000001/x-declaration.json"})
    result = mc.classify("00-MASTER/X-000001/x-declaration.json", view, boundary)
    assert result.mutation_class == "GENERATED_ARTIFACT"
    assert result.rule_id == "R-04"


def test_an_unparseable_json_artifact_is_not_declaration_bearing(repo: mc.Repository) -> None:
    assert repo.declaration_document("engine/nucleus/lifecycle.py") is None
    assert repo.declaration_document("00-BOOK/DATA/does-not-exist.json") is None


def test_object_subjects_are_refused_by_path_only_rules(
    repo: mc.Repository, boundary: dict
) -> None:
    """R-01 and R-06 are path predicates; an object subject must fall through them."""
    subject = mc.Subject.of_object("population/beta", "NotAConstitutionalType")
    result = mc.classify(subject, repo, boundary)
    assert result.status == mc.UNRESOLVED


def test_a_boundary_whose_rules_do_not_match_the_predicates_is_an_error(
    repo: mc.Repository,
) -> None:
    doc = {"classification_rules": {"rules": [{"id": "R-01", "class": "REPOSITORY_STATE"}]}}
    result = mc.classify("anything", repo, doc)
    assert result.status == mc.ERROR
    assert "no rule declares it" in result.reason


def test_a_predicate_that_raises_is_reported_as_a_fault_not_a_class(
    repo: mc.Repository, boundary: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(subject, repository, doc):  # noqa: ANN001, ANN202
        raise RuntimeError("predicate is unevaluable")

    monkeypatch.setitem(mc.RULE_PREDICATES, "R-01", explode)
    result = mc.classify("anything", repo, boundary)
    assert result.status == mc.ERROR
    assert result.rule_id == "R-01"
    assert "RuntimeError" in result.reason


def test_authority_for_an_unknown_class_is_empty(boundary: dict) -> None:
    assert mc.authority_for(boundary, "NO_SUCH_CLASS") == ""
