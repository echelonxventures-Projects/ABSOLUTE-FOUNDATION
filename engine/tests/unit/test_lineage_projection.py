"""ULP — the Universal Lineage Projection, measured.

Lineage answers "how did this become this?". These tests hold the four properties that make
a derived answer trustworthy — it is composed rather than stored, it is deterministic, each
family keeps its own meaning, and every answer cites its source — and they exercise the
refusals that make those properties non-vacuous.

The F-1 failure pattern is reconstructed here too: a projected structural ancestor that is
not the declared parent must fail, at the projection layer as well as at `ukb validate`.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from engine.lineage import query
from engine.lineage.model import Classification, LineageEdge, LineageError, LineageProjection
from engine.lineage.projection import (
    build,
    digest,
    load_classification,
    rendered,
    to_document,
    validate,
    verify,
)
from engine.lineage.sources import (
    SOURCE_FILES,
    declared_relations,
    load_sources,
    repo_root,
)


@pytest.fixture(scope="module", name="projection")
def _projection() -> LineageProjection:
    return build()


@pytest.fixture(scope="module", name="classification")
def _classification() -> Classification:
    return load_classification()


@pytest.fixture(name="document")
def _document() -> dict:
    import os

    with open(
        os.path.join(repo_root(), "engine", "lineage", "families.json"), encoding="utf-8"
    ) as h:
        return json.load(h)


# --- composition, not storage -----------------------------------------------------------


def test_the_projection_builds_over_every_declared_source(projection) -> None:
    assert set(projection.sources) == {
        "artifacts",
        "births",
        "change_events",
        "change_lineage",
        "generated",
        "identity_history",
        "typed_edges",
    }
    assert all(count > 0 for count in projection.sources.values())


def test_every_declared_source_file_exists() -> None:
    import os

    missing = [p for p in SOURCE_FILES if not os.path.exists(os.path.join(repo_root(), p))]
    assert missing == []


def test_the_projection_writes_nothing(tmp_path) -> None:
    """A lineage store is what UCI-001 XVI.5 forbids."""
    import subprocess

    before = subprocess.run(  # noqa: S603
        ["git", "status", "--porcelain"],  # noqa: S607
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    build()
    verify()
    after = subprocess.run(  # noqa: S603
        ["git", "status", "--porcelain"],  # noqa: S607
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    assert before == after, "building the projection moved something in the tree"


def test_the_document_claims_no_authority(projection) -> None:
    assert to_document(projection)["authority"].startswith("NONE")


def test_the_document_stays_open(projection) -> None:
    document = to_document(projection)
    assert document["closed_set"] is False
    assert document["upper_limit"] is None


# --- determinism ------------------------------------------------------------------------


def test_two_builds_are_byte_identical() -> None:
    assert rendered(build()) == rendered(build())


def test_the_digest_is_stable_across_builds() -> None:
    assert digest(build()) == digest(build())


def test_verify_reports_determinism_and_passes() -> None:
    report = verify()
    assert report["deterministic"] is True
    assert report["status"] == "PASS", report["problems"]
    assert report["problems"] == []


def test_no_wall_clock_enters_the_document(projection) -> None:
    """A timestamp would make two builds of one state differ."""
    import re

    document = to_document(projection)
    document.pop("edges")
    assert re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", json.dumps(document)) == []


# --- the four families keep distinct meanings -------------------------------------------


def test_the_four_lineage_families_are_populated(projection) -> None:
    counts = projection.by_family()
    assert set(counts) == {"structure", "dependency", "derivation", "supersession"}
    assert all(count > 0 for count in counts.values())


def test_structural_edges_equal_the_declared_containment_facts(projection) -> None:
    """One containment fact, one edge — not one per direction."""
    sources = load_sources()
    declared = sum(1 for a in sources["artifacts"] if a.get("parent"))
    assert projection.by_family()["structure"] == declared


def test_each_relation_belongs_to_exactly_one_family(classification) -> None:
    seen: dict[str, str] = {}
    for family in classification.families:
        for rule in family.relations:
            assert rule.relation not in seen, f"{rule.relation} in two families"
            seen[rule.relation] = family.name


def test_transformation_is_events_and_never_edges(projection) -> None:
    """The meaning-collapse the architecture forbids (P-2)."""
    assert "transformation" not in projection.by_family()
    assert projection.events, "the event stream is empty"
    assert all(isinstance(e.sequence, int) for e in projection.events)


def test_derivation_comes_from_the_generated_artifact_registry(projection) -> None:
    sources = {e.source for e in projection.edges if e.family == "derivation"}
    assert sources == {"00-BOOK/DATA/generated-artifact-registry.json"}


def test_supersession_comes_from_the_change_ledger_and_the_typed_graph(projection) -> None:
    sources = {e.source for e in projection.edges if e.family == "supersession"}
    assert "00-BOOK/DATA/change-ledger.json" in sources


# --- every edge cites its source ---------------------------------------------------------


def test_every_edge_names_a_declared_source(projection) -> None:
    allowed = set(SOURCE_FILES)
    assert {e.source for e in projection.edges} <= allowed


def test_every_edge_relation_is_declared_by_the_vocabulary_owner(projection) -> None:
    declared = declared_relations()
    assert {e.relation for e in projection.edges} <= declared


def test_within_one_source_a_fact_is_carried_once(projection) -> None:
    """One source states one ancestry fact with one relation — the inverse is collapsed."""
    facts: dict[tuple[str, str, str, str], set[str]] = {}
    for edge in projection.edges:
        key = (edge.family, edge.descendant, edge.ancestor, edge.source)
        facts.setdefault(key, set()).add(edge.relation)
    doubled = {k: v for k, v in facts.items() if len(v) > 1}
    assert doubled == {}, f"one source carried a fact under two relations: {doubled}"


def test_two_sources_may_attest_one_fact_and_each_cites_itself(projection) -> None:
    """Multi-source attestation is kept, not collapsed — and it is measured, not assumed.

    The change ledger records `UCOS-UMB-000024` as SUPERSEDING `…000023`; the typed graph
    records the same pair as EVOLVES-FROM. Two governed sources describing one ancestry in
    their own vocabulary is not duplication, and silently dropping one would discard an
    attestation the repository actually holds. Each edge names the source that made it, so
    a caller can tell the two apart.
    """
    facts: dict[tuple[str, str, str], set[str]] = {}
    for edge in projection.edges:
        facts.setdefault((edge.family, edge.descendant, edge.ancestor), set()).add(edge.source)
    multi = {k: v for k, v in facts.items() if len(v) > 1}
    assert multi, "expected at least one multi-source ancestry attestation"
    for key, sources in multi.items():
        assert len(sources) == len(set(sources)), key


# --- the query surface -------------------------------------------------------------------


def test_the_query_answers_the_six_questions(projection) -> None:
    sources = load_sources()
    node = next(iter(sorted(sources["artifacts_by_id"])))
    answer = query.answer(node, projection)
    assert set(answer) == {
        "node",
        "what_is_this",
        "who_owns_this",
        "where_did_it_come_from",
        "when_was_it_created",
        "what_has_it_become",
        "what_depends_on_it",
    }


def test_every_origin_answer_cites_its_source(projection) -> None:
    sources = load_sources()
    subject = next(e.descendant for e in projection.edges if e.family == "structure")
    for found in query.origin_of(subject, projection, sources):
        assert found["source"], "an answer without a source is not returned"
        assert found["family"]


def test_an_unknown_node_answers_empty_rather_than_guessing(projection) -> None:
    answer = query.answer("UCOS-NOT-A-REAL-ID", projection)
    assert answer["what_is_this"] == {}
    assert answer["who_owns_this"] == {}
    assert answer["where_did_it_come_from"] == []


# --- refusals ----------------------------------------------------------------------------


def test_the_f1_pattern_is_refused_by_the_projection(projection) -> None:
    """A structural ancestor that is not the declared parent must fail."""
    sources = load_sources()
    subject = next(e.descendant for e in projection.edges if e.family == "structure")
    forged = dataclasses.replace(
        projection,
        edges=(
            *projection.edges,
            LineageEdge(
                descendant=subject,
                ancestor="UCOS-USIS-000017",
                relation="Parent",
                family="structure",
                source="00-BOOK/DATA/relationships.json",
            ),
        ),
    )
    problems = validate(forged)
    assert any("is not the declared parent" in p for p in problems)
    assert any("conflicting structural ancestry" in p for p in problems)
    del sources


def test_a_cycle_in_an_acyclic_family_is_refused(projection) -> None:
    forged = dataclasses.replace(
        projection,
        edges=(
            LineageEdge("A", "B", "Depends-On", "dependency", "00-BOOK/DATA/relationships.json"),
            LineageEdge("B", "A", "Depends-On", "dependency", "00-BOOK/DATA/relationships.json"),
        ),
    )
    assert any("not acyclic" in p for p in validate(forged))


def test_an_undeclared_relation_is_refused(projection) -> None:
    forged = dataclasses.replace(
        projection,
        edges=(
            LineageEdge(
                "A", "B", "Invented-Relation", "dependency", "00-BOOK/DATA/relationships.json"
            ),
        ),
    )
    assert any("is not a declared relation" in p for p in validate(forged))


# --- the classification refuses an unusable declaration ----------------------------------


def test_a_relation_the_owner_does_not_declare_is_refused(tmp_path, document) -> None:
    document["families"][0]["types"].append({"type": "Invented-Relation", "ancestor": "to"})
    path = tmp_path / "families.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(LineageError, match="does not declare|do not declare"):
        load_classification(str(path))


def test_leaving_a_declared_relation_unclassified_is_refused(tmp_path, document) -> None:
    document["non_lineage"] = document["non_lineage"][:-1]
    path = tmp_path / "families.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(LineageError, match="neither as lineage nor"):
        load_classification(str(path))


def test_a_relation_classified_twice_is_refused(document) -> None:
    document["families"][1]["types"].append(document["families"][0]["types"][0])
    with pytest.raises(LineageError, match="two families"):
        Classification.of(document)


def test_a_relation_both_lineage_and_non_lineage_is_refused(document) -> None:
    document["non_lineage"].append(
        {"type": document["families"][0]["types"][0]["type"], "reason": "claimed twice"}
    )
    with pytest.raises(LineageError, match="both lineage and non-lineage"):
        Classification.of(document)


# --- an exclusion argues itself, or it is not an exclusion --------------------------------
#
# Listing a relation as non-lineage stops it being silently ignored, but a bare name leaves the
# exclusion asserted rather than measured — and an unexplained exclusion is indistinguishable
# from an oversight to every later reader. These three make the reason load-bearing.


def test_a_non_lineage_relation_named_without_a_reason_is_refused(document) -> None:
    document["non_lineage"][0] = {"type": document["non_lineage"][0]["type"]}
    with pytest.raises(LineageError, match="reason"):
        Classification.of(document)


def test_a_bare_relation_name_is_not_an_exclusion(document) -> None:
    document["non_lineage"][0] = document["non_lineage"][0]["type"]
    with pytest.raises(LineageError, match="not a bare name"):
        Classification.of(document)


def test_the_same_relation_excluded_twice_is_refused(document) -> None:
    document["non_lineage"].append(dict(document["non_lineage"][0]))
    with pytest.raises(LineageError, match="more than once"):
        Classification.of(document)


def test_every_excluded_relation_carries_its_reason(classification) -> None:
    """The live classification, not a fixture: each exclusion says why it is not ancestry."""
    assert set(classification.exclusions) == set(classification.non_lineage)
    assert all(len(reason) > 40 for reason in classification.exclusions.values())


def test_an_unknown_ancestor_direction_is_refused(document) -> None:
    document["families"][0]["types"][0]["ancestor"] = "sideways"
    with pytest.raises(LineageError, match="edge endpoint"):
        Classification.of(document)


def test_a_missing_section_is_refused(document) -> None:
    document.pop("families")
    with pytest.raises(LineageError):
        Classification.of(document)


def test_a_missing_classification_file_is_a_fault(tmp_path) -> None:
    with pytest.raises(LineageError, match="absent"):
        load_classification(str(tmp_path / "nope.json"))


def test_an_unparseable_classification_is_a_fault(tmp_path) -> None:
    path = tmp_path / "families.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(LineageError, match="valid JSON"):
        load_classification(str(path))


# --- no hard-coded reality ----------------------------------------------------------------


def test_the_classification_is_data_not_code(classification) -> None:
    """Family and relation names live in families.json, checked against the owner."""
    import ast
    import pathlib

    source = (pathlib.Path(repo_root()) / "engine" / "lineage" / "model.py").read_text("utf-8")
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    literals = [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings
    ]
    names = {f.name for f in classification.families} | set(classification.rules)
    for literal in literals:
        assert literal not in names, f"model.py hard-codes {literal!r}"
