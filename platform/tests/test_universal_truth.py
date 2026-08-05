"""Tests — Universal Repository Truth Framework (UCOS-URTF-001)."""

from __future__ import annotations

import json
from pathlib import Path
from platform.foundation.services import ServiceRegistry
from platform.universal_truth import (
    NON_HOME_TRUTH_CLASSES,
    TRUTH_CONTRACTS,
    PathSelector,
    SelectorKind,
    Subject,
    TruthClass,
    TruthClassification,
    TruthPolicy,
    TruthZone,
    bootstrap_repository_truth,
    default_truth_policy,
    locator_segments,
    normalize_locator,
    register_repository_truth,
    truth_contract_names,
    truth_service_descriptor,
)
from platform.universal_truth.cli import main as truth_main
from platform.universal_truth.errors import (
    TruthContractError,
    TruthPolicyError,
    TruthProjectionError,
)
from platform.universal_truth.policy import TruthPartition, catalog_path, load_truth_policy
from platform.universal_truth.projection import (
    ProjectionSpec,
    SubjectProjection,
    project_subjects,
)

import pytest


def _zone(zone_id: str, truth_class: str, value: str, **kwargs: object) -> TruthZone:
    return TruthZone.create(zone_id, truth_class, [{"kind": "root", "value": value}], **kwargs)


# --------------------------------------------------------------------------- locators


def test_normalize_locator_is_separator_agnostic() -> None:
    assert normalize_locator("./a\\b/c.md") == "a/b/c.md"
    assert normalize_locator("/a/./b/") == "a/b"
    assert locator_segments("a/b/c.md") == ("a", "b", "c.md")
    assert locator_segments("") == ()


def test_normalize_locator_rejects_non_string() -> None:
    with pytest.raises(TruthContractError):
        normalize_locator(7)


# --------------------------------------------------------------------------- selectors


@pytest.mark.parametrize(
    ("kind", "value", "locator", "expected"),
    [
        ("root", "engine", "engine/x.py", True),
        ("root", "engine", "platform/x.py", False),
        ("root-file", "*.md", "README.md", True),
        ("root-file", "*.md", "docs/README.md", False),
        ("segment", "__pycache__", "a/__pycache__/b.pyc", True),
        ("segment", "__pycache__", "a/b.pyc", False),
        ("prefix", "a/b", "a/b/c", True),
        ("prefix", "a/b", "a/bc", False),
        ("suffix", ".egg-info", "x.egg-info", True),
        ("glob", "a/*/c.md", "a/b/c.md", True),
        ("exact", "a/b.md", "a/b.md", True),
        ("exact", "a/b.md", "a/b/c.md", False),
    ],
)
def test_selector_matching(kind: str, value: str, locator: str, expected: bool) -> None:
    assert PathSelector.create(kind, value).matches(locator) is expected


def test_selector_identity_and_projection() -> None:
    selector = PathSelector.create(SelectorKind.ROOT, "engine")
    assert selector.selector_id.startswith("UCOS-URTS-")
    assert selector.to_dict()["kind"] == "root"
    assert selector.fingerprint() == PathSelector.create("root", "engine").fingerprint()
    assert selector.matches("") is False


def test_selector_rejects_malformed_declarations() -> None:
    with pytest.raises(TruthContractError):
        PathSelector.create("root", "  ")
    with pytest.raises(TruthContractError):
        PathSelector.create("root", "a/b")
    with pytest.raises(TruthContractError):
        PathSelector.create("nonsense", "a")
    with pytest.raises(TruthContractError):
        PathSelector.create(7, "a")
    with pytest.raises(TruthContractError):
        PathSelector.from_dict({"kind": "root"})
    with pytest.raises(TruthContractError):
        PathSelector.from_dict("root")


def test_truth_class_coercion() -> None:
    assert TruthClass.coerce("canonical") is TruthClass.CANONICAL
    assert TruthClass.coerce(TruthClass.EVIDENCE) is TruthClass.EVIDENCE
    with pytest.raises(TruthContractError):
        TruthClass.coerce("not-a-class")
    with pytest.raises(TruthContractError):
        TruthClass.coerce(3)


# --------------------------------------------------------------------------- zones


def test_zone_declaration_and_matching() -> None:
    zone = _zone(
        "canonical.impl",
        "canonical",
        "engine",
        authority="Implementation Authority",
        canonical_home_eligible=True,
        description="impl",
    )
    assert zone.authoritative is True
    assert zone.matches("engine/x.py") is True
    assert zone.matching_selector("engine/x.py") is not None
    assert zone.matching_selector("platform/x.py") is None
    assert zone.order_key == (-100, "canonical.impl")
    assert zone.to_dict()["canonical_home_eligible"] is True
    assert zone.fingerprint()


@pytest.mark.parametrize("truth_class", [item.value for item in NON_HOME_TRUTH_CLASSES])
def test_non_owning_classes_can_never_be_declared_a_home(truth_class: str) -> None:
    with pytest.raises(TruthContractError):
        _zone("z", truth_class, "x", canonical_home_eligible=True)


def test_authoritative_zone_requires_an_authority() -> None:
    with pytest.raises(TruthContractError):
        _zone("z", "canonical", "x")


def test_zone_rejects_malformed_declarations() -> None:
    with pytest.raises(TruthContractError):
        TruthZone.create(" ", "derived", [{"kind": "root", "value": "x"}])
    with pytest.raises(TruthContractError):
        TruthZone.create("z", "derived", [])
    with pytest.raises(TruthContractError):
        TruthZone.create("z", "derived", [{"kind": "root", "value": "x"}], precedence="high")
    with pytest.raises(TruthContractError):
        TruthZone.from_dict({"zone_id": "z"})
    with pytest.raises(TruthContractError):
        TruthZone.from_dict({"zone_id": "z", "truth_class": "derived", "selectors": "root"})
    with pytest.raises(TruthContractError):
        TruthZone.from_dict("z")
    with pytest.raises(TruthContractError):
        TruthZone(
            zone_id="z",
            truth_class=TruthClass.DERIVED,
            selectors=("not-a-selector",),  # type: ignore[arg-type]
        )
    with pytest.raises(TruthContractError):
        TruthZone(zone_id="z", truth_class="derived", selectors=())  # type: ignore[arg-type]


def test_zone_deduplicates_selectors() -> None:
    zone = TruthZone.create(
        "z",
        "derived",
        [{"kind": "root", "value": "x"}, {"kind": "root", "value": "x"}],
    )
    assert len(zone.selectors) == 1


# --------------------------------------------------------------------------- policy


def test_policy_resolves_by_declared_precedence_not_insertion_order() -> None:
    low = _zone("low", "derived", "engine", precedence=10)
    high = TruthZone.create(
        "high",
        "canonical",
        [{"kind": "segment", "value": "src"}],
        precedence=900,
        authority="Impl",
        canonical_home_eligible=True,
    )
    forward = TruthPolicy([low, high])
    backward = TruthPolicy([high, low])
    for policy in (forward, backward):
        classification = policy.classify("engine/src/x.py")
        assert classification.zone_id == "high"
        assert classification.canonical_home_eligible is True
    assert forward.zone_ids() == ("high", "low")


def test_policy_reports_honest_absence_for_undeclared_locators() -> None:
    policy = TruthPolicy([_zone("z", "derived", "engine")])
    classification = policy.classify("elsewhere/x.md")
    assert classification.truth_class is TruthClass.UNCLASSIFIED
    assert classification.classified is False
    assert classification.rule == "NO-DECLARED-ZONE"
    assert classification.authoritative is False


def test_policy_registration_is_append_only_and_fail_closed() -> None:
    zone = _zone("z", "derived", "engine")
    policy = TruthPolicy([zone])
    assert policy.register(zone) is zone
    assert policy.count == 1
    with pytest.raises(TruthPolicyError):
        policy.register(_zone("z", "derived", "platform"))
    with pytest.raises(TruthPolicyError):
        policy.register("zone")  # type: ignore[arg-type]
    with pytest.raises(TruthPolicyError):
        policy.zone("missing")
    with pytest.raises(TruthPolicyError):
        policy.classify("   ")


def test_policy_views_and_document_round_trip() -> None:
    policy = default_truth_policy()
    assert policy.policy_id == "ucos.repository.truth"
    assert policy.version == "1.0.0"
    assert policy.count == len(policy.zones())
    assert policy.of_class(TruthClass.EVIDENCE)
    assert policy.home_zones()
    assert policy.register_all(()) == policy.zones()
    rebuilt = TruthPolicy.from_document(policy.to_document())
    assert rebuilt.fingerprint() == policy.fingerprint()
    assert policy.zone("evidence.admitted-sources").truth_class is TruthClass.EVIDENCE


def test_policy_document_validation() -> None:
    with pytest.raises(TruthPolicyError):
        TruthPolicy.from_document("nope")
    with pytest.raises(TruthPolicyError):
        TruthPolicy.from_document({"policy_id": "x"})
    with pytest.raises(TruthPolicyError):
        TruthPolicy.from_document({"policy_id": "x", "zones": []})


def test_load_truth_policy_failure_modes(tmp_path: Path) -> None:
    with pytest.raises(TruthPolicyError):
        load_truth_policy(tmp_path / "missing.json")
    broken = tmp_path / "broken.json"
    broken.write_text("{", "utf-8")
    with pytest.raises(TruthPolicyError):
        load_truth_policy(broken)


def test_default_policy_classifies_the_declared_repository_zones() -> None:
    policy = default_truth_policy()
    expectations = {
        "00-SOURCE/VISION/x.docx": (TruthClass.EVIDENCE, False),
        "00-MASTER/UAKOS/closure.json": (TruthClass.OPERATIONAL_MEMORY, False),
        "00-MASTER/UCCEP/_evidence/a.md": (TruthClass.DERIVED, False),
        "02-MASTER/UCOS-COMP-000000.md": (TruthClass.DECLARATION, True),
        "platform/universal_truth/policy.py": (TruthClass.CANONICAL, True),
        "knowledge/canonical-knowledge.json": (TruthClass.GENERATED, True),
        "99-FREEZE/SOURCE-FILES.txt": (TruthClass.HISTORICAL, False),
        "platform/x/__pycache__/y.pyc": (TruthClass.TRANSIENT, False),
        "01-READINESS-ASSESSMENT.md": (TruthClass.DERIVED, False),
    }
    for locator, (expected_class, expected_home) in expectations.items():
        classification = policy.classify(locator)
        assert classification.truth_class is expected_class, locator
        assert classification.canonical_home_eligible is expected_home, locator
    assert policy.is_canonical_home("02-MASTER/x.md") is True
    assert policy.is_canonical_home("00-SOURCE/x.docx") is False


def test_partition_projection_and_counts() -> None:
    policy = default_truth_policy()
    partition = policy.classify_all(
        [
            "00-SOURCE/a.docx",
            "00-SOURCE/a.docx",
            "02-MASTER/b.md",
            "nowhere/c.txt",
            "",
        ]
    )
    assert partition.total == 3
    assert partition.count(TruthClass.EVIDENCE) == 1
    assert partition.count("unclassified") == 1
    assert len(partition.of_class(TruthClass.DECLARATION)) == 1
    assert len(partition.canonical_home_eligible()) == 1
    assert [item.locator for item in partition.unclassified()] == ["nowhere/c.txt"]
    payload = partition.to_dict()
    assert payload["total"] == 3
    assert partition.partition_id.startswith("UCOS-URTP-")
    assert partition.fingerprint()
    assert TruthPartition.create(()).total == 0


def test_classification_contract_guards() -> None:
    with pytest.raises(TruthContractError):
        TruthClassification.create("", TruthClass.CANONICAL)
    with pytest.raises(TruthContractError):
        TruthClassification.create("a.md", TruthClass.EVIDENCE, canonical_home_eligible=True)
    classification = TruthClassification.create(
        "a.md", TruthClass.CANONICAL, zone_id="z", canonical_home_eligible=True
    )
    assert classification.classification_id.startswith("UCOS-URTC-")
    assert classification.classified is True
    assert classification.fingerprint()


# --------------------------------------------------------------------------- subjects


def test_subject_normalises_locators_and_attributes() -> None:
    subject = Subject.create(
        " UCOS-COMP-000000 ",
        locators=["./a/b.md", "a/b.md", "", "c/d.md"],
        attributes={"family": "COMP"},
    )
    assert subject.subject_id == "UCOS-COMP-000000"
    assert subject.locators == ("a/b.md", "c/d.md")
    assert subject.attribute("family") == "COMP"
    assert subject.attribute("missing", "none") == "none"
    assert subject.subject_key.startswith("UCOS-URTJ-")
    assert subject.to_dict()["locators"] == ["a/b.md", "c/d.md"]
    assert subject.fingerprint()
    with pytest.raises(TruthContractError):
        Subject.create("  ")


# --------------------------------------------------------------------------- projection


def _document() -> dict[str, object]:
    return {
        "model": {
            "concepts": [
                {"id": "A", "files": ["x/a.md"], "homes": {"k": ["y/a.md"]}, "family": "F"},
                {"id": "A", "files": ["x/a2.md"]},
                {"id": "B", "files": []},
            ]
        }
    }


def test_projection_merges_records_and_flattens_locators() -> None:
    spec = ProjectionSpec.create(
        "model.concepts",
        "id",
        locator_fields=("files", "homes"),
        attribute_fields=("family",),
    )
    subjects = SubjectProjection(spec).project(_document())
    assert [subject.subject_id for subject in subjects] == ["A", "B"]
    assert subjects[0].locators == ("x/a.md", "x/a2.md", "y/a.md")
    assert subjects[0].attribute("family") == "F"
    assert subjects[1].locators == ()
    assert spec.spec_id.startswith("UCOS-URTX-")
    assert spec.fingerprint()
    assert SubjectProjection(spec).spec is spec


def test_projection_accepts_mapping_collections_and_declared_specs() -> None:
    document = {"concepts": {"b": {"id": "B"}, "a": {"id": "A", "files": ["a.md"]}}}
    subjects = project_subjects(
        document, {"collection": "concepts", "identity_field": "id", "locator_fields": ["files"]}
    )
    assert [subject.subject_id for subject in subjects] == ["A", "B"]


def test_projection_failure_modes(tmp_path: Path) -> None:
    spec = ProjectionSpec.create("concepts", "id")
    with pytest.raises(TruthProjectionError):
        SubjectProjection(spec).project({"other": []})
    with pytest.raises(TruthProjectionError):
        SubjectProjection(spec).project({"concepts": "nope"})
    with pytest.raises(TruthProjectionError):
        SubjectProjection(spec).project({"concepts": ["nope"]})
    with pytest.raises(TruthProjectionError):
        SubjectProjection(spec).project({"concepts": [{"nope": 1}]})
    with pytest.raises(TruthProjectionError):
        SubjectProjection(spec).project("nope")
    with pytest.raises(TruthProjectionError):
        SubjectProjection("nope")  # type: ignore[arg-type]
    with pytest.raises(TruthProjectionError):
        ProjectionSpec.create("", "id")
    with pytest.raises(TruthProjectionError):
        ProjectionSpec.create("c", " ")
    with pytest.raises(TruthProjectionError):
        ProjectionSpec.from_dict({"collection": "c"})
    with pytest.raises(TruthProjectionError):
        ProjectionSpec.from_dict("c")
    with pytest.raises(TruthProjectionError):
        SubjectProjection(spec).project_file(tmp_path / "missing.json")
    broken = tmp_path / "broken.json"
    broken.write_text("{", "utf-8")
    with pytest.raises(TruthProjectionError):
        SubjectProjection(spec).project_file(broken)


def test_projection_reads_a_declared_document(tmp_path: Path) -> None:
    path = tmp_path / "model.json"
    path.write_text(json.dumps({"concepts": [{"id": "A", "files": ["a.md"]}]}), "utf-8")
    spec = ProjectionSpec.create("concepts", "id", locator_fields=("files",))
    subjects = SubjectProjection(spec).project_file(path)
    assert subjects[0].locators == ("a.md",)


# --------------------------------------------------------------------------- wiring


def test_contract_surface_is_published() -> None:
    assert truth_contract_names()
    assert len(TRUTH_CONTRACTS) == len(truth_contract_names())
    assert all(ref.version == "1.0.0" for ref in TRUTH_CONTRACTS)


def test_bootstrap_and_service_registration() -> None:
    assert bootstrap_repository_truth().count == default_truth_policy().count
    assert bootstrap_repository_truth(catalog_path()).count == default_truth_policy().count
    registry = ServiceRegistry()
    descriptor = register_repository_truth(registry)
    assert descriptor.name == truth_service_descriptor().name
    resolved = registry.resolve("universal.truth")
    assert isinstance(resolved, TruthPolicy)


# --------------------------------------------------------------------------- cli


def test_cli_policy_and_classify(capsys: pytest.CaptureFixture[str]) -> None:
    assert truth_main(["policy", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["policy_id"] == "ucos.repository.truth"
    assert truth_main(["classify", "00-SOURCE/a.docx", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["classifications"][0]["truth_class"] == "evidence"


def test_cli_partition_gate_and_faults(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    listing = tmp_path / "locators.txt"
    listing.write_text("02-MASTER/a.md\nnowhere/b.md\n", "utf-8")
    assert truth_main(["partition", "--locators-file", str(listing), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["unclassified"] == ["nowhere/b.md"]
    assert truth_main(["partition", "--locators-file", str(listing), "--require-classified"]) == 1
    assert truth_main(["classify", "02-MASTER/a.md", "--require-classified"]) == 0
    assert truth_main(["classify"]) == 0
    assert truth_main(["policy", "--policy", str(tmp_path / "missing.json")]) == 2
