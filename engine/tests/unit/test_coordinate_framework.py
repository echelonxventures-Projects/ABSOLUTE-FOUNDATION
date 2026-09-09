"""UCCFA-000001 — the coordinate framework alignment gate.

Every law is exercised in BOTH directions. A law that only ever passes is a law nobody has
shown can fail, so each check below is also handed a declaration that violates it and must
refuse: `engine/coordinate_framework/gate.py` is a detector, and a detector with no failing
case is a detector nobody has shown can fail.
"""

from __future__ import annotations

import copy
import json

import pytest

from engine.coordinate_framework import (
    CoordinateAlignmentError,
    CoordinateContract,
    assess,
    declaration_path,
    load_contract,
    load_declaration,
    repo_root,
)

# The private helpers belong to the module that defines them rather than to the package's
# public surface, so they are named from there instead of being re-exported to suit a test.
from engine.coordinate_framework.contract import _part, _primitive_elements, _row
from engine.coordinate_framework.gate import EXIT_CLOSED, EXIT_FAULT, EXIT_OPEN, main, measure


@pytest.fixture(scope="module")
def document() -> dict:
    return load_declaration()


@pytest.fixture(scope="module")
def repo() -> str:
    return repo_root()


def _elsewhere(tmp_path, document: dict) -> str:
    target = tmp_path / "uccfa-declaration.json"
    target.write_text(json.dumps(document), encoding="utf-8")
    return str(target)


def _measure(tmp_path, document: dict) -> dict:
    return measure(_elsewhere(tmp_path, document))


def _refusals(report: dict, law_id: str) -> list[str]:
    return next(law["violations"] for law in report["laws"] if law["law_id"] == law_id)


# --- the declaration as it stands -------------------------------------------------------


def test_the_gate_is_open_over_the_repository_as_it_stands():
    report = measure()
    assert report["holds"], [law for law in report["laws"] if not law["holds"]]
    assert report["coordinates"] == 5


def test_measuring_twice_produces_the_same_report():
    # No clock, no network, no subprocess: one state must yield one report, or the digest
    # below identifies nothing.
    assert measure() == measure()


def test_a_changed_declaration_changes_the_reported_identity(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["version"] = "9.9"
    assert measure()["declaration_digest"] != _measure(tmp_path, altered)["declaration_digest"]


def test_every_declared_law_is_measured_and_every_check_is_declared(document, repo):
    contract = CoordinateContract.of(document)
    assessed = {law_id for law_id, _, _ in assess(contract, repo)}
    assert assessed == {str(law["id"]) for law in document["laws"]}


# --- each law refuses what it exists to refuse -------------------------------------------


def test_l01_refuses_a_coordinate_the_register_does_not_carry(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["coordinate_binding"][0]["element"] = "HYPERSPACE"
    assert _refusals(_measure(tmp_path, altered), "UCCFA-L-01")


def test_l02_refuses_a_standing_the_ratification_record_does_not_grant(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["ratified_standing"][0]["evidence_phrase"] = "ratified as a root primitive"
    assert _refusals(_measure(tmp_path, altered), "UCCFA-L-02")


def test_l03_refuses_an_element_bound_as_both_primitive_and_coordinate(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["coordinate_binding"][0]["element"] = "TRANSFORMATION"
    assert _refusals(_measure(tmp_path, altered), "UCCFA-L-03")


def test_l04_refuses_an_equation_term_bound_by_nothing(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["coordinate_binding"] = altered["coordinate_binding"][:-1]
    assert _refusals(_measure(tmp_path, altered), "UCCFA-L-04")


def test_l05_refuses_a_superseded_element_resolving_into_an_unbound_coordinate(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["superseded_root_element"]["resolves_into"] = ["ONT-06", "ONT-99"]
    assert _refusals(_measure(tmp_path, altered), "UCCFA-L-05")


def test_l05_refuses_a_superseded_element_the_register_does_not_carry(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["superseded_root_element"]["id"] = "ONT-99"
    assert _refusals(_measure(tmp_path, altered), "UCCFA-L-05")


def test_l06_refuses_a_bound_element_the_omega_law_does_not_name(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["omega_law_binding"]["dimensions"] = [
        name for name in altered["omega_law_binding"]["dimensions"] if name != "SCALE"
    ]
    assert _refusals(_measure(tmp_path, altered), "UCCFA-L-06")


def test_l06_refuses_when_the_law_carries_no_row(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["omega_law_binding"]["law_id"] = "Ω∞-999"
    assert _refusals(_measure(tmp_path, altered), "UCCFA-L-06")


# --- faults are not verdicts --------------------------------------------------------------


def test_an_absent_declaration_is_a_fault(tmp_path, capsys):
    assert main(["--declaration", str(tmp_path / "nowhere.json")]) == EXIT_FAULT
    assert "FAULT" in capsys.readouterr().err


def test_a_declaration_that_is_not_json_is_a_fault(tmp_path, capsys):
    target = tmp_path / "uccfa-declaration.json"
    target.write_text("{not json", encoding="utf-8")
    assert main(["--declaration", str(target)]) == EXIT_FAULT
    assert "not valid JSON" in capsys.readouterr().err


def test_a_declaration_missing_a_required_section_is_a_fault(tmp_path, document, capsys):
    altered = copy.deepcopy(document)
    del altered["coordinate_binding"]
    assert main(["--declaration", _elsewhere(tmp_path, altered)]) == EXIT_FAULT
    assert "coordinate_binding" in capsys.readouterr().err


def test_a_declared_law_that_names_no_check_is_a_fault(document, repo):
    altered = copy.deepcopy(document)
    altered["laws"] = [*altered["laws"], {"id": "UCCFA-L-99", "title": "invented"}]
    with pytest.raises(CoordinateAlignmentError, match="names no check"):
        assess(CoordinateContract.of(altered), repo)


def test_a_declared_law_naming_a_check_that_does_not_exist_is_a_fault(document, repo):
    # Distinct from the case above and worth distinguishing: a law that forgot to name its
    # check and a law naming one nobody wrote are different mistakes, and a single message
    # for both would send the reader to the wrong file.
    altered = copy.deepcopy(document)
    altered["laws"] = [
        *altered["laws"],
        {"id": "UCCFA-L-99", "title": "invented", "check": "a_check_nobody_wrote"},
    ]
    with pytest.raises(CoordinateAlignmentError, match="no check implements"):
        assess(CoordinateContract.of(altered), repo)


def test_a_check_no_declared_law_names_is_a_fault(document, repo):
    altered = copy.deepcopy(document)
    altered["laws"] = altered["laws"][:-1]
    with pytest.raises(CoordinateAlignmentError, match="no declared law names"):
        assess(CoordinateContract.of(altered), repo)


# --- the CLI --------------------------------------------------------------------------------


def test_the_cli_reports_open(capsys):
    assert main([]) == EXIT_OPEN
    assert "VERDICT: OPEN" in capsys.readouterr().out


def test_the_cli_can_emit_json(capsys):
    assert main(["--json"]) == EXIT_OPEN
    assert json.loads(capsys.readouterr().out)["artifact_id"] == "UCCFA-000001"


def test_the_cli_closes_on_a_refused_law(tmp_path, document, capsys):
    altered = copy.deepcopy(document)
    altered["coordinate_binding"][0]["element"] = "HYPERSPACE"
    assert main(["--declaration", _elsewhere(tmp_path, altered)]) == EXIT_CLOSED
    assert "VERDICT: CLOSED" in capsys.readouterr().out


def test_the_declaration_path_is_the_binding():
    assert declaration_path().endswith("00-MASTER/UCCFA-000001/uccfa-declaration.json")
    assert load_contract().artifact_id == "UCCFA-000001"


def test_a_declaration_that_is_not_an_object_is_a_fault(tmp_path):
    target = tmp_path / "uccfa-declaration.json"
    target.write_text("[]", encoding="utf-8")
    with pytest.raises(CoordinateAlignmentError, match="not an object"):
        load_declaration(str(target))


@pytest.mark.parametrize("field", ["artifact_id", "name", "version", "authority", "principle"])
def test_a_declaration_missing_a_stated_field_is_a_fault(document, field):
    altered = copy.deepcopy(document)
    del altered[field]
    with pytest.raises(CoordinateAlignmentError, match=field):
        CoordinateContract.of(altered)


@pytest.mark.parametrize(
    "section", ["ontology_source", "superseded_root_element", "omega_law_binding"]
)
def test_a_declaration_missing_a_stated_object_is_a_fault(document, section):
    altered = copy.deepcopy(document)
    altered[section] = {}
    with pytest.raises(CoordinateAlignmentError, match=section):
        CoordinateContract.of(altered)


def test_an_unreadable_declared_surface_is_a_fault(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["ontology_source"]["canonical_owner"] = "01-WORKING/NO-SUCH-REGISTER.md"
    with pytest.raises(CoordinateAlignmentError, match="unreadable"):
        measure(_elsewhere(tmp_path, altered))


# --- the helpers, exercised where a whole-declaration case cannot reach them ---------------


def test_a_section_that_runs_to_the_end_of_the_document_is_read_whole():
    # PART B is not the last section of the real register, so the loop always breaks there.
    # A document whose section IS last exercises the other exit.
    document = "## PART A — ROOT\n| ONT-01 | BEING |\n## PART B — COORD\n| ONT-06 | SPACE |"
    body = _part(document, "PART B")
    assert body.strip() == "| ONT-06 | SPACE |"


def test_a_row_the_register_does_not_carry_is_the_empty_string():
    assert _row("| ONT-06 | SPACE |", "ONT-99") == ""


def test_an_unreadable_ucpa_declaration_is_a_fault(tmp_path):
    # Reached directly: every law that consults UCPA is preceded by one that reads the
    # register, so a repository without UCPA fails earlier for a different reason.
    with pytest.raises(CoordinateAlignmentError, match="UCPA-000001 declaration is unreadable"):
        _primitive_elements(str(tmp_path))


def test_l02_refuses_a_ratification_id_the_record_does_not_carry(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["ontology_source"]["ratified_by"] = "SUP-99"
    assert "carries no row" in _refusals(_measure(tmp_path, altered), "UCCFA-L-02")[0]


def test_l05_refuses_when_part_a_does_not_record_the_supersession(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["superseded_root_element"]["superseded_by"] = "SUP-99"
    assert any("does not record" in f for f in _refusals(_measure(tmp_path, altered), "UCCFA-L-05"))


def test_l05_refuses_an_evidence_phrase_part_a_does_not_carry(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["superseded_root_element"]["evidence_phrase"] = "ratified as a root primitive"
    assert any("does not carry" in f for f in _refusals(_measure(tmp_path, altered), "UCCFA-L-05"))


def test_l05_refuses_a_superseded_element_ucpa_still_binds(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["superseded_root_element"]["element"] = "TRANSFORMATION"
    refusals = _refusals(_measure(tmp_path, altered), "UCCFA-L-05")
    assert any("bound as a primitive" in f for f in refusals)


def test_l05_refuses_a_superseded_element_this_declaration_binds(tmp_path, document):
    altered = copy.deepcopy(document)
    altered["superseded_root_element"]["element"] = "SPACE"
    refusals = _refusals(_measure(tmp_path, altered), "UCCFA-L-05")
    assert any("bound as a coordinate" in f for f in refusals)


def test_l06_refuses_a_dimension_the_law_does_not_name(tmp_path, document):
    altered = copy.deepcopy(document)
    dimensions = altered["omega_law_binding"]["dimensions"]
    altered["omega_law_binding"]["dimensions"] = [*dimensions, "FLAVOUR"]
    assert any("not named by" in f for f in _refusals(_measure(tmp_path, altered), "UCCFA-L-06"))
