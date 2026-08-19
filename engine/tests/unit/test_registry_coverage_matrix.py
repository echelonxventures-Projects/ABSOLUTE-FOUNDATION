"""RCM — the Registry Coverage Matrix, measured.

The matrix answers where every governed object is registered and which registries declare
no authority. These tests hold the properties that make that answer trustworthy — it stores
nothing, the partition is exact, and each failure state is detectable — and they construct
each failure so that no state is asserted without ever having been produced.

The constraint under test throughout: the matrix must not become the 141st registry.
"""

from __future__ import annotations

import copy
import json

import pytest

from engine.registry_coverage.matrix import (
    COVERED,
    DUPLICATE_REGISTRATION,
    UNREGISTERED,
    CoverageError,
    Declarations,
    build,
    digest,
    load_declarations,
    rendered,
    repo_root,
    validate,
    verify,
)


@pytest.fixture(scope="module", name="matrix")
def _matrix() -> dict:
    return build()


@pytest.fixture(scope="module", name="declarations")
def _declarations() -> Declarations:
    return load_declarations()


@pytest.fixture(name="document")
def _document() -> dict:
    import os

    path = os.path.join(repo_root(), "engine", "registry_coverage", "declarations.json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


# --- it is not a registry ----------------------------------------------------------------


def test_the_matrix_stores_no_object_record(matrix) -> None:
    """Coverage counts, never a catalogue. A stored copy would be the 141st registry."""
    assert isinstance(matrix["objects"]["states"], dict)
    assert all(isinstance(v, int) for v in matrix["objects"]["states"].values())
    # findings are bounded diagnostics, not a population
    assert len(matrix["findings"]) <= 100


def test_the_matrix_claims_no_authority(matrix) -> None:
    assert matrix["authority"].startswith("NONE")


def test_the_matrix_writes_nothing() -> None:
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
    assert before == after


def test_the_matrix_stays_open(matrix) -> None:
    assert matrix["closed_set"] is False
    assert matrix["upper_limit"] is None


# --- partition correctness ----------------------------------------------------------------


def test_every_governed_object_is_covered(matrix) -> None:
    states = matrix["objects"]["states"]
    assert states[UNREGISTERED] == 0
    assert states[DUPLICATE_REGISTRATION] == 0
    assert states["PARTIALLY_COVERED"] == 0
    assert states[COVERED] == matrix["objects"]["total"]


def test_the_partition_is_exact(matrix) -> None:
    """Corpus + repository governed objects equal the whole universe."""
    governed = {p["plane"]: p["governed"] for p in matrix["planes"]}
    assert sum(governed.values()) == matrix["objects"]["total"]


def test_the_two_planes_are_disjoint() -> None:
    """artifacts.json ∩ id-ledger.by_object must be empty."""
    import os

    root = repo_root()
    with open(os.path.join(root, "00-BOOK", "DATA", "artifacts.json"), encoding="utf-8") as h:
        corpus = {a["path"] for a in json.load(h)["artifacts"]}
    with open(os.path.join(root, "00-BOOK", "DATA", "id-ledger.json"), encoding="utf-8") as h:
        repository = set(json.load(h)["by_object"])
    assert corpus & repository == set()


def test_the_generated_registry_is_contained_in_the_repository_plane() -> None:
    import os

    root = repo_root()
    with open(
        os.path.join(root, "00-BOOK", "DATA", "generated-artifact-registry.json"), encoding="utf-8"
    ) as h:
        generated = {e["canonical_path"] for e in json.load(h)["entries"]}
    with open(os.path.join(root, "00-BOOK", "DATA", "id-ledger.json"), encoding="utf-8") as h:
        repository = set(json.load(h)["by_object"])
    assert generated <= repository, sorted(generated - repository)[:5]


def test_retained_entries_are_reported_separately(matrix) -> None:
    """Append-only retention is not a coverage error, and must not read as one."""
    for plane in matrix["planes"]:
        assert plane["retained_not_governed"] == plane["registered"] - plane["governed"]
        assert plane["retained_not_governed"] >= 0


def test_no_two_planes_claim_one_object_class(declarations) -> None:
    seen: dict[str, str] = {}
    for plane in declarations.planes:
        for klass in plane.object_classes:
            assert klass not in seen, f"{klass} claimed by two planes"
            seen[klass] = plane.name


# --- W5-G1: authority gap handling --------------------------------------------------------


def test_the_disclosed_gaps_record_producer_and_remediation(declarations) -> None:
    """Recorded, not inferred — each gap names where its remediation belongs."""
    assert declarations.gaps, "W5-G1 is not disclosed"
    for gap in declarations.gaps:
        assert gap.producer, gap.gap_id
        assert gap.producer_owner, gap.gap_id
        assert gap.missing, gap.gap_id
        assert gap.remediation, gap.gap_id
        assert gap.referred_to, gap.gap_id


def test_a_disclosed_gap_is_not_reported_as_undeclared(matrix, declarations) -> None:
    disclosed = {g.registry for g in declarations.gaps}
    reported = {
        r["registry"] for r in matrix["registries"]["entries"] if r["status"] == "DISCLOSED_GAP"
    }
    assert reported <= disclosed


def test_no_registry_is_undeclared_today(matrix) -> None:
    undeclared = [
        r["registry"] for r in matrix["registries"]["entries"] if r["status"] == "UNDECLARED"
    ]
    assert undeclared == [], undeclared


def test_an_undisclosed_registry_without_authority_is_refused(matrix) -> None:
    """The ratchet: disclosure is not permission for the NEXT one."""
    forged = copy.deepcopy(matrix)
    forged["registries"]["entries"].append(
        {
            "registry": "00-MASTER/INVENTED/registry.json",
            "authority_mechanism": "",
            "status": "UNDECLARED",
            "plane": "",
        }
    )
    problems = validate(forged)
    assert any("no declared authority and no disclosure" in p for p in problems)


def test_the_producer_is_recorded_but_not_adopted_as_owner(declarations) -> None:
    """Inferring ownership would manufacture the missing declaration."""
    for gap in declarations.gaps:
        assert gap.missing == "AUTHORITY_DECLARATION"
        # the producer owner is recorded as the REFERRAL target, not as the declared owner
        assert gap.referred_to == gap.producer_owner


# --- failure detection --------------------------------------------------------------------


def test_an_unregistered_object_is_detected(matrix) -> None:
    forged = copy.deepcopy(matrix)
    forged["objects"]["states"][UNREGISTERED] = 1
    forged["findings"].append({"path": "x/y.md", "state": UNREGISTERED, "planes": ""})
    assert any(UNREGISTERED in p for p in validate(forged))


def test_a_duplicate_registration_is_detected(matrix) -> None:
    forged = copy.deepcopy(matrix)
    forged["objects"]["states"][DUPLICATE_REGISTRATION] = 2
    forged["findings"].append(
        {"path": "x/y.md", "state": DUPLICATE_REGISTRATION, "planes": "CORPUS,REPOSITORY"}
    )
    assert any(DUPLICATE_REGISTRATION in p for p in validate(forged))


def test_an_empty_plane_is_detected(matrix) -> None:
    forged = copy.deepcopy(matrix)
    forged["planes"][0]["registered"] = 0
    assert any("registers nothing" in p for p in validate(forged))


# --- determinism ---------------------------------------------------------------------------


def test_two_builds_are_byte_identical() -> None:
    assert rendered(build()) == rendered(build())


def test_the_digest_is_stable() -> None:
    assert digest(build()) == digest(build())


def test_verify_reports_determinism_and_passes() -> None:
    report = verify()
    assert report["deterministic"] is True
    assert report["status"] == "PASS", report["problems"]


def test_no_wall_clock_enters_the_matrix(matrix) -> None:
    import re

    trimmed = {k: v for k, v in matrix.items() if k not in ("registries", "findings")}
    assert re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", json.dumps(trimmed)) == []


# --- the declaration refuses an unusable document -------------------------------------------


@pytest.mark.parametrize(
    "section", ["authority_mechanisms", "registration_planes", "coverage_states", "scan"]
)
def test_a_missing_section_is_refused(document, section) -> None:
    document.pop(section)
    with pytest.raises(CoverageError):
        Declarations.of(document)


def test_two_planes_claiming_one_class_is_refused(document) -> None:
    document["registration_planes"][1]["holds_object_classes"].append(
        document["registration_planes"][0]["holds_object_classes"][0]
    )
    with pytest.raises(CoverageError, match="same object class"):
        Declarations.of(document)


def test_a_missing_declaration_file_is_a_fault(tmp_path) -> None:
    with pytest.raises(CoverageError, match="absent"):
        load_declarations(str(tmp_path / "nope.json"))


def test_an_unparseable_declaration_is_a_fault(tmp_path) -> None:
    path = tmp_path / "declarations.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(CoverageError, match="valid JSON"):
        load_declarations(str(path))


# --- no hard-coded reality -------------------------------------------------------------------


def test_registry_paths_and_gap_ids_are_data_not_code(declarations) -> None:
    import ast
    import pathlib

    source = (pathlib.Path(repo_root()) / "engine" / "registry_coverage" / "matrix.py").read_text(
        "utf-8"
    )
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
    forbidden = {g.gap_id for g in declarations.gaps} | {g.registry for g in declarations.gaps}
    for literal in literals:
        for needle in forbidden:
            assert needle not in literal, f"matrix.py hard-codes {needle!r}"
