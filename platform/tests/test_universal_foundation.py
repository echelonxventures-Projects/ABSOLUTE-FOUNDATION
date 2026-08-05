"""Tests — Universal Foundation Platform (UCOS-UFP-001)."""

from __future__ import annotations

import json
from pathlib import Path
from platform.foundation.services import ServiceRegistry
from platform.universal_assimilation import KIND_MARKDOWN, SourceInput
from platform.universal_foundation import (
    COMPOSED_CAPABILITIES,
    FoundationDetermination,
    FoundationSpecialization,
    UniversalFoundation,
    bootstrap_universal_foundation,
    catalog_path,
    default_specialization,
    foundation_service_descriptor,
    load_specialization,
    register_universal_foundation,
)
from platform.universal_foundation.cli import main as foundation_main
from platform.universal_foundation.errors import (
    FoundationCompositionError,
    SpecializationError,
)
from platform.universal_measurement import (
    MeasurementContext,
    bootstrap_measurement_policies,
)
from platform.universal_ownership import bootstrap_ownership
from platform.universal_truth import Subject, default_truth_policy

import pytest

# A REGISTERED locator. CEP-002 14.1 requires the canonical owner to be registered in the
# Governance Registry, and the converged determination enforces that through the project's
# declared eligibility ledger — so a synthetic path is no longer a home however constitutional
# its zone looks. This is the artifact that really declares UCOS-COMP-000000 as its own identity.
HOME = "02-MASTER/UCOS-COMP-000000-CONSTITUTIONAL-IMPLEMENTATION-ORCHESTRATION-AUTHORITY.md"
EVIDENCE_ONLY = "00-SOURCE/VISION/UCOS-COMP-000001.docx"


def _project(tmp_path: Path) -> Path:
    """A miniature project: a declared population and a declared specialisation."""
    population = tmp_path / "population.json"
    population.write_text(
        json.dumps(
            {
                "concepts": [
                    {"id": "UCOS-COMP-000000", "files": [HOME], "family": "COMP"},
                    {"id": "UCOS-COMP-000001", "files": [EVIDENCE_ONLY], "family": "COMP"},
                ]
            }
        ),
        "utf-8",
    )
    specialization = tmp_path / "specialization.json"
    specialization.write_text(
        json.dumps(
            {
                "project_id": "miniature",
                "truth_policy": "packaged:",
                "population_document": "population.json",
                "projection": {
                    "collection": "concepts",
                    "identity_field": "id",
                    "locator_fields": ["files"],
                    "attribute_fields": ["family"],
                },
            }
        ),
        "utf-8",
    )
    return specialization


# --------------------------------------------------------------------------- specialisation


def test_packaged_prefix_lets_a_project_reuse_a_shipped_catalogue(tmp_path: Path) -> None:
    specialization = tmp_path / "spec.json"
    specialization.write_text(
        json.dumps(
            {
                "project_id": "reuser",
                "truth_policy": "packaged:ucos-repository-truth.json",
                "ownership_declarations": "packaged:",
            }
        ),
        "utf-8",
    )
    foundation = bootstrap_universal_foundation(specialization, root=tmp_path)
    assert foundation.truth.policy_id == "ucos.repository.truth"
    assert any(
        descriptor.provider_id == "ownership.declared-assignment"
        for descriptor in foundation.ownership.providers.descriptors()
    )


def test_specialization_declaration_round_trip() -> None:
    declared = default_specialization()
    assert declared.project_id == "ucos-consolidation"
    assert declared.projection is not None
    assert declared.specialization_id.startswith("UCOS-UFPZ-")
    assert declared.fingerprint()
    rebuilt = FoundationSpecialization.from_document(declared.to_dict())
    assert rebuilt.fingerprint() == declared.fingerprint()
    assert catalog_path().exists()


def test_specialization_resolution_is_root_relative(tmp_path: Path) -> None:
    declared = FoundationSpecialization.create("p", population_document="a/b.json")
    assert declared.resolve("population_document", root=tmp_path) == tmp_path / "a/b.json"
    assert declared.resolve("truth_policy") is None
    absolute = FoundationSpecialization.create("p", population_document=str(tmp_path / "x.json"))
    assert absolute.resolve("population_document", root="/elsewhere") == tmp_path / "x.json"


def test_specialization_guards(tmp_path: Path) -> None:
    with pytest.raises(SpecializationError):
        FoundationSpecialization.create(" ")
    with pytest.raises(SpecializationError):
        FoundationSpecialization.from_document("nope")
    with pytest.raises(SpecializationError):
        FoundationSpecialization.from_document({})
    with pytest.raises(SpecializationError):
        load_specialization(tmp_path / "missing.json")
    broken = tmp_path / "broken.json"
    broken.write_text("{", "utf-8")
    with pytest.raises(SpecializationError):
        load_specialization(broken)


# --------------------------------------------------------------------------- composition


def test_bootstrap_composes_the_four_capabilities() -> None:
    foundation = bootstrap_universal_foundation()
    assert foundation.capabilities() == COMPOSED_CAPABILITIES
    assert foundation.truth.count > 0
    assert foundation.ownership.contract.requirement_ids
    assert foundation.assimilation.kinds.count == 14
    assert foundation.policies.registry.count == 9
    assert foundation.specialization.project_id == "ucos-consolidation"
    assert foundation.to_dict()["capabilities"] == list(COMPOSED_CAPABILITIES)
    assert foundation.fingerprint()


def test_bootstrap_accepts_a_declared_specialization_object_or_path(tmp_path: Path) -> None:
    path = _project(tmp_path)
    from_path = bootstrap_universal_foundation(path, root=tmp_path)
    assert from_path.specialization.project_id == "miniature"
    from_object = bootstrap_universal_foundation(load_specialization(path), root=tmp_path)
    assert from_object.specialization.project_id == "miniature"


def test_bootstrap_fails_closed_on_a_missing_declared_policy(tmp_path: Path) -> None:
    specialization = tmp_path / "spec.json"
    specialization.write_text(
        json.dumps({"project_id": "p", "truth_policy": "absent.json"}), "utf-8"
    )
    with pytest.raises(FoundationCompositionError):
        bootstrap_universal_foundation(specialization, root=tmp_path)


def test_bootstrap_honours_declared_registration_requirement(tmp_path: Path) -> None:
    specialization = tmp_path / "spec.json"
    specialization.write_text(
        json.dumps({"project_id": "p", "require_registration": True}), "utf-8"
    )
    foundation = bootstrap_universal_foundation(specialization, root=tmp_path)
    # A declared registration requirement with no ledger to satisfy it refuses every subject
    # rather than being quietly ignored. Zero Silent Repair: dropping a declared obligation
    # because its input is absent is how a requirement stops being enforced without anyone
    # having decided that it should.
    record = foundation.ownership.determine_subject(
        Subject.create("UCOS-COMP-000000", locators=[HOME])
    )
    assert record.declared is False
    assert "SUBJECT-NOT-REGISTERED" in record.reasons


def test_composition_guards() -> None:
    declared = default_specialization()
    truth = default_truth_policy()
    ownership = bootstrap_ownership(policy=truth)
    policies = bootstrap_measurement_policies()
    from platform.universal_assimilation import bootstrap_assimilation

    assimilation = bootstrap_assimilation(policy=truth)
    good = (declared, truth, ownership, assimilation, policies)
    for index in range(5):
        broken = list(good)
        broken[index] = "nope"
        with pytest.raises(FoundationCompositionError):
            UniversalFoundation(*broken)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- determination


def test_determination_over_a_declared_miniature_project(tmp_path: Path) -> None:
    foundation = bootstrap_universal_foundation(_project(tmp_path), root=tmp_path)
    subjects = foundation.project_population(root=tmp_path)
    assert [subject.subject_id for subject in subjects] == [
        "UCOS-COMP-000000",
        "UCOS-COMP-000001",
    ]
    locators = sorted({locator for subject in subjects for locator in subject.locators})
    determination = foundation.determine(
        subjects=subjects,
        locators=locators,
        sources=[SourceInput.from_text(KIND_MARKDOWN, EVIDENCE_ONLY, "# H\nbody")],
        destinations={EVIDENCE_ONLY: HOME},
    )
    assert determination.determination == "NOT-CLOSED"
    assert determination.ownership is not None
    assert determination.ownership.counts() == {
        "total": 2,
        "declared": 1,
        "contested": 0,
        "unresolved": 1,
        "remediable": 1,
    }
    assert determination.assimilation is not None
    assert determination.assimilation.closed is True
    assert determination.partition is not None
    assert determination.partition.total == 2
    assert "ownership.coverage" in determination.blockers()
    assert determination.determination_id.startswith("UCOS-UFPD-")
    assert determination.fingerprint()
    summary = determination.summary()
    assert summary["ownership"]["counts"]["declared"] == 1
    assert summary["truth"]["unclassified"] == 0
    assert summary["assimilation"]["coverage_percentage"] == 100.0
    assert summary["measurement"]["policy_total"] >= 1
    assert determination.to_dict()["determination"] == "NOT-CLOSED"


def test_determination_measures_only_what_it_was_given() -> None:
    foundation = bootstrap_universal_foundation()
    determination = foundation.determine()
    assert determination.partition is None
    assert determination.ownership is None
    assert determination.assimilation is None
    assert determination.blockers() == ()
    assert determination.closed is False
    summary = determination.summary()
    assert summary["truth"] is None
    assert summary["ownership"] is None
    assert summary["assimilation"] is None
    assert FoundationDetermination.create("p").determination == "NOT-CLOSED"
    assert FoundationDetermination.create("p").blockers() == ()


def test_facade_delegates_to_each_capability() -> None:
    foundation = bootstrap_universal_foundation()
    assert foundation.classify([HOME]).total == 1
    # Ownership resolves from what the artifact DECLARES about itself, read from the head of a
    # locator Truth already declared. The framework's own definitional-basename rule is
    # deliberately not in play for this project: 'what is a definitional home' is measured by
    # the closure engine and adopted as a declared locator role, so a second rule over the same
    # question would be exactly the competing measurement UFC-16 forbids.
    determination = foundation.determine_ownership(
        [Subject.create("UCOS-COMP-000000", locators=[HOME])]
    )
    assert determination.closed
    assert determination.records[0].owner == HOME
    report = foundation.assimilate(
        [SourceInput.from_text(KIND_MARKDOWN, EVIDENCE_ONLY, "# H\nbody")],
        destinations={EVIDENCE_ONLY: HOME},
    )
    assert report.closed is True
    suite = foundation.measure(MeasurementContext.create(assimilation=report))
    assert suite.outcome("assimilation.coverage").satisfied is True


def test_population_projection_is_declared_not_discovered(tmp_path: Path) -> None:
    specialization = tmp_path / "spec.json"
    specialization.write_text(json.dumps({"project_id": "p"}), "utf-8")
    foundation = bootstrap_universal_foundation(specialization, root=tmp_path)
    assert foundation.project_population(root=tmp_path) == ()
    assert foundation.registered_subjects(root=tmp_path) == ()


def test_registration_ledger_forms_and_faults(tmp_path: Path) -> None:
    for body, expected in (
        (json.dumps(["B", "A"]), ("A", "B")),
        (json.dumps({"B": {}, "A": {}}), ("A", "B")),
    ):
        ledger = tmp_path / "ledger.json"
        ledger.write_text(body, "utf-8")
        specialization = tmp_path / "spec.json"
        specialization.write_text(
            json.dumps({"project_id": "p", "registered_subjects": "ledger.json"}), "utf-8"
        )
        foundation = bootstrap_universal_foundation(specialization, root=tmp_path)
        assert foundation.registered_subjects(root=tmp_path) == expected

    ledger = tmp_path / "ledger.json"
    ledger.write_text("7", "utf-8")
    specialization = tmp_path / "spec.json"
    specialization.write_text(
        json.dumps({"project_id": "p", "registered_subjects": "ledger.json"}), "utf-8"
    )
    foundation = bootstrap_universal_foundation(specialization, root=tmp_path)
    with pytest.raises(FoundationCompositionError):
        foundation.registered_subjects(root=tmp_path)
    ledger.write_text("{", "utf-8")
    with pytest.raises(FoundationCompositionError):
        foundation.registered_subjects(root=tmp_path)


# --------------------------------------------------------------------------- wiring


def test_every_capability_is_a_resolvable_service() -> None:
    registry = ServiceRegistry()
    descriptors = register_universal_foundation(registry)
    assert [descriptor.name for descriptor in descriptors] == [
        "universal.truth",
        "universal.ownership",
        "universal.assimilation",
        "universal.measurement.policy",
        "universal.foundation.constitution",
        "universal.foundation",
    ]
    # The composed platform depends on its own law: a Foundation that could be composed without
    # the Constitution being resolvable would be a Foundation nothing governs.
    assert foundation_service_descriptor().dependencies == (
        "universal.truth",
        "universal.ownership",
        "universal.assimilation",
        "universal.measurement.policy",
        "universal.foundation.constitution",
    )
    assert isinstance(registry.resolve("universal.foundation"), UniversalFoundation)
    assert "universal.foundation" in registry.startup_order()


# --------------------------------------------------------------------------- cli


def test_cli_capabilities_and_composition(capsys: pytest.CaptureFixture[str]) -> None:
    assert foundation_main(["capabilities", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["capabilities"] == list(COMPOSED_CAPABILITIES)
    assert len(payload["measurement_policies"]) == 9
    assert foundation_main(["composition", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["specialization"]["project_id"] == "ucos-consolidation"


def test_cli_determine_executes_from_declared_truth(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _project(tmp_path)
    assert (
        foundation_main(
            ["determine", "--specialization", str(path), "--root", str(tmp_path), "--json"]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["determination"] == "NOT-CLOSED"
    assert payload["ownership"]["counts"]["total"] == 2
    assert (
        foundation_main(
            [
                "determine",
                "--specialization",
                str(path),
                "--root",
                str(tmp_path),
                "--detail",
                "--gate",
                "--json",
            ]
        )
        == 1
    )
    detail = json.loads(capsys.readouterr().out)
    assert detail["ownership"]["records"]
    assert foundation_main(["capabilities", "--specialization", str(tmp_path / "no.json")]) == 2
