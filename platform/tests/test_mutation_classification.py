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

import subprocess
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


# --------------------------------------------------------------- class 7, positive

ADR_DECIDERS = "adr/0003-constitutional-binding-of-ceu-and-ucxi.md"
CONSTITUTION_AUTHORITY = "00-CEP/CEP-002-CONSTITUTIONAL-GOVERNANCE-CONSTITUTION.md"
DETERMINATION_NO_AUTHORITY = "adr/0002-aeos-phase-1-architectural-determination.md"


def test_class_7_an_adr_using_the_deciders_convention_resolves(
    repo: mc.Repository, boundary: dict
) -> None:
    """Authored document classification — the ADR convention (Deciders, table form)."""
    result = mc.classify(ADR_DECIDERS, repo, boundary)
    assert result.status == mc.CLASSIFIED
    assert result.mutation_class == "AUTHORED_DOCUMENT"
    assert result.rule_id == "R-08"


def test_class_7_a_constitution_using_the_authority_convention_resolves(
    repo: mc.Repository, boundary: dict
) -> None:
    """Authored document classification — the constitution convention (AUTHORITY, table form,
    uppercase label — the field-name match is case-insensitive)."""
    result = mc.classify(CONSTITUTION_AUTHORITY, repo, boundary)
    assert result.status == mc.CLASSIFIED
    assert result.mutation_class == "AUTHORED_DOCUMENT"
    assert result.rule_id == "R-08"


def test_class_7_ownership_resolution_reads_the_documents_own_declaration(
    repo: mc.Repository,
) -> None:
    """Canonical owner: read from the artifact, Authority checked before Deciders."""
    assert mc.authored_document_owner(ADR_DECIDERS, repo) == "Constitutional Authority · UCOS Ω∞"
    owner = mc.authored_document_owner(CONSTITUTION_AUTHORITY, repo)
    assert owner.startswith("Supreme over all governance operation")


def test_class_7_authority_resolution_names_the_owner_parameterised_chain(
    repo: mc.Repository, boundary: dict
) -> None:
    """The fixed governance chain (Class 6's own pattern) plus the per-document owner."""
    result = mc.classify(ADR_DECIDERS, repo, boundary)
    assert "owner-parameterised" in result.authority
    assert "self-declared" in result.authority or "declares" in result.authority


def test_class_7_lifecycle_is_read_from_the_documents_own_status_field(
    repo: mc.Repository,
) -> None:
    """Lifecycle handling: open vocabulary, whatever the document states of itself."""
    assert mc.authored_document_lifecycle(ADR_DECIDERS, repo) == "Accepted"


def test_class_7_evaluates_criteria_and_never_matches_on_examples(
    repo: mc.Repository, boundary: dict
) -> None:
    """Examples are documentation, exactly like Class 6. Membership is the five criteria."""
    checks = mc.authored_document_checks(ADR_DECIDERS, repo)
    declared = next(
        e["membership_criteria"]
        for e in boundary["mutation_classes"]
        if e["class"] == "AUTHORED_DOCUMENT"
    )
    assert len(checks) == len(declared)
    assert all(checks.values()), checks


# --------------------------------------------------------------- class 7, negative
# and fail-closed classification


def test_class_7_a_document_declaring_no_authority_or_deciders_is_unresolved(
    repo: mc.Repository, boundary: dict
) -> None:
    """Fail-closed: a determination document that states 'AUTHORITY = NONE' inline prose,
    not as a self-declared Authority/Deciders field, earns no class rather than one by
    default — the same discipline GOVERNED_DECLARATION applies to an ownerless JSON file."""
    checks = mc.authored_document_checks(DETERMINATION_NO_AUTHORITY, repo)
    assert checks["self-declared-authority"] is False
    result = mc.classify(DETERMINATION_NO_AUTHORITY, repo, boundary)
    assert result.mutation_class != "AUTHORED_DOCUMENT"
    assert result.status == mc.UNRESOLVED


def test_class_7_a_json_declaration_is_never_also_an_authored_document(
    repo: mc.Repository, boundary: dict
) -> None:
    """Structural exclusivity: R-06 (JSON declaration) precedes R-08, and a JSON path never
    satisfies the markdown criterion — the two classes cannot both claim one subject."""
    assert mc.authored_document_checks(UISD, repo)["markdown"] is False
    result = mc.classify(UISD, repo, boundary)
    assert result.mutation_class == "GOVERNED_DECLARATION"


def test_class_7_a_source_file_is_never_an_authored_document(
    repo: mc.Repository, boundary: dict
) -> None:
    checks = mc.authored_document_checks("engine/nucleus/lifecycle.py", repo)
    assert checks["markdown"] is False
    assert mc.classify("engine/nucleus/lifecycle.py", repo, boundary).mutation_class == "SOURCE"


def test_class_7_an_untracked_markdown_document_is_refused(repo: mc.Repository) -> None:
    checks = mc.authored_document_checks("nowhere/orphan.md", repo)
    assert checks["repository-controlled"] is False


def test_class_7_no_duplicate_mutation_authority_with_class_6(boundary: dict) -> None:
    """The invariant test_2 in test_mutation_governance_boundary.py checks this at the
    register level; this checks it at the classifier level — the two owner-parameterised
    classes (6 and 7) never resolve the same subject, and their governed_by chains, while
    both owner-parameterised, are declared as two distinct class entries, never one merged
    authority."""
    classes = [e["class"] for e in boundary["mutation_classes"]]
    assert classes.count("GOVERNED_DECLARATION") == 1
    assert classes.count("AUTHORED_DOCUMENT") == 1
    governed_decl = mc.authority_for(boundary, "GOVERNED_DECLARATION")
    authored_doc = mc.authority_for(boundary, "AUTHORED_DOCUMENT")
    assert governed_decl != authored_doc


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


# ------------------------------------------------- version-control path fidelity
# Regression cover for the tracked-path parsing defect: `git ls-files` C-quotes and
# octal-escapes any path holding a non-ASCII byte, so a tracked `…UCOS-Ω∞-…` artifact
# arrived as `"…UCOS-\316\251\342\210\236-…"` and never equalled its own path. It then
# tested as untracked, and because R-01 claims any existing path absent from `tracked`,
# 117 real artifacts were absorbed into REPOSITORY_STATE before the rule that owns them
# was ever evaluated — a WRONG authority, strictly worse than the fail-closed terminal.
#
# Every test above this line drives `Repository` through `_overrides["tracked"]` with
# ASCII-only fixtures, which is precisely why none of them could see the defect. These
# drive the real `git ls-files` subprocess against real non-ASCII names.

#: Tracked, non-generated, non-ASCII. Declares no Authority/Deciders field, so Class 7
#: correctly refuses it and it fails closed — the point is that it is not REPOSITORY_STATE.
OMEGA_NO_AUTHORITY = "02-MASTER/UCOS-Ω∞-TECHNOLOGY-CONSTITUTION.md"

#: Tracked, non-generated, non-ASCII, and self-declaring an Authority — resolves to Class 7.
OMEGA_AUTHORED = "02-MASTER/UCOS-Ω∞-ABSOLUTE-IDENTITY-FEDERATION-AND-CONTINUITY-CONSTITUTION.md"


def _git_repo_with(tmp_path: Path, *names: str) -> Path:
    """A real git work tree holding real files, staged. Index alone drives `ls-files`."""
    subprocess.run(  # noqa: S603
        ["git", "init", "-q"],  # noqa: S607 — resolved from PATH, as the module under test does
        cwd=tmp_path,
        check=True,
    )
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# fixture\n", encoding="utf-8")
    subprocess.run(  # noqa: S603
        ["git", "add", "-A"],  # noqa: S607 — resolved from PATH, as the module under test does
        cwd=tmp_path,
        check=True,
    )
    return tmp_path


def test_a_non_ascii_tracked_path_is_read_unescaped_from_version_control(
    tmp_path: Path,
) -> None:
    """The parsing correction itself, against the real subprocess.

    Asserted on the *real path*, and on the absence of any escaped form — a fix that
    merely unquoted the outer quotes would still leave the octal escapes behind.
    """
    root = _git_repo_with(tmp_path, "UCOS-Ω∞-FIXTURE.md", "plain-ascii.md")
    tracked = mc.Repository(root).tracked

    assert "UCOS-Ω∞-FIXTURE.md" in tracked
    assert "plain-ascii.md" in tracked, "ASCII paths must be unaffected by the correction"
    assert not any(p.startswith('"') for p in tracked), f"a quoted path survived: {tracked}"
    assert not any("\\316" in p or "\\342" in p for p in tracked), (
        f"an octal-escaped path survived: {tracked}"
    )


def test_an_omega_infinity_document_is_not_absorbed_into_repository_state(
    repo: mc.Repository, boundary: dict
) -> None:
    """The defect's actual consequence, on a real repository artifact.

    Before the correction this resolved to REPOSITORY_STATE via R-01 — governed by
    UCOS-RIB-001 GATE-02/12 rather than by its own authority. It declares no
    Authority/Deciders field, so the correct outcome is the fail-closed terminal: no
    authority, rather than someone else's.
    """
    assert OMEGA_NO_AUTHORITY in repo.tracked

    result = mc.classify(OMEGA_NO_AUTHORITY, repo, boundary)
    assert result.mutation_class != "REPOSITORY_STATE"
    assert result.status == mc.UNRESOLVED
    assert result.authority == "", "the terminal confers no authority"


def test_an_omega_infinity_authored_document_resolves_to_class_7(
    repo: mc.Repository, boundary: dict
) -> None:
    """Authored-document detection survives the correction for non-ASCII paths.

    R-08 requires `repository-controlled`, which is exactly the criterion the defect
    falsified — so a self-declaring Ω∞ constitution could never reach Class 7 before.
    """
    checks = mc.authored_document_checks(OMEGA_AUTHORED, repo)
    assert checks["repository-controlled"] is True
    assert all(checks.values()), checks

    result = mc.classify(OMEGA_AUTHORED, repo, boundary)
    assert result.status == mc.CLASSIFIED
    assert result.mutation_class == "AUTHORED_DOCUMENT"
    assert result.rule_id == "R-08"
    assert mc.authored_document_owner(OMEGA_AUTHORED, repo) != ""


def test_an_untracked_path_is_still_detected_as_untracked(tmp_path: Path) -> None:
    """The correction must not weaken the check it repairs.

    A path git does not carry must stay outside `tracked` — in a synthetic tree and in
    the real repository — or R-01's precedence and Class 6/7's `repository-controlled`
    criterion would both silently become permissive.
    """
    root = _git_repo_with(tmp_path, "UCOS-Ω∞-STAGED.md")
    (root / "UCOS-Ω∞-UNSTAGED.md").write_text("# not added\n", encoding="utf-8")
    tracked = mc.Repository(root).tracked

    assert "UCOS-Ω∞-STAGED.md" in tracked
    assert "UCOS-Ω∞-UNSTAGED.md" not in tracked

    real = mc.Repository(REPO)
    assert "nowhere/orphan.md" not in real.tracked
    assert "02-MASTER/UCOS-Ω∞-DOES-NOT-EXIST.md" not in real.tracked


def test_repository_state_claims_only_genuinely_untracked_paths(
    repo: mc.Repository, boundary: dict
) -> None:
    """R-01 precedence, both directions.

    R-01 runs first, so if it over-claims nothing downstream is ever consulted. It must
    claim an existing-but-untracked path, and must NOT claim a tracked one — including a
    tracked non-ASCII one, which is the case the defect inverted.
    """
    subject = mc.Subject.of_path(OMEGA_NO_AUTHORITY)
    assert mc._r01_repository_state(subject, repo, boundary) is False

    untracked = mc.Subject.of_path(".git/HEAD")
    assert mc._r01_repository_state(untracked, repo, boundary) is True
    assert mc.classify(untracked, repo, boundary).mutation_class == "REPOSITORY_STATE"

    for path in (OMEGA_NO_AUTHORITY, OMEGA_AUTHORED):
        assert mc.classify(path, repo, boundary).mutation_class != "REPOSITORY_STATE"
