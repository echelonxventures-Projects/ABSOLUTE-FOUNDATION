"""UCOS-CERT-004 — the band conductor, held to the claim it makes.

WHY THIS FILE EXISTS AT ALL. ``scripts/cert004_expansion.py`` is 270 statements that sequence four
shipped components through Validation → Certification → Acceptance → Readiness → Freeze and write
the four mission outputs. It had no test, no Makefile target and no verification stage, and it was
measured at 0.0% — a conductor of certification engines about which nothing was certified.

THE DEFECT THE FIRST TEST HERE NAMES. Every ratio in the conductor reads ``100.0 if total == 0``
and ``complete`` reads ``covered >= total``, so a component the coverage document never mentions
scores 100% on all six dimensions and lands in the evidence as READY / FREEZE. An empty Cobertura
report — one ``<packages/>`` element, which is what a mis-scoped pytest-cov run emits — therefore
certified all four units and returned 0. ``unmeasured_targets`` makes that antecedent a FAULT, and
the test below forges it and asserts the literal exit code, because a refusal nothing exercises is
indistinguishable from a refusal that no longer works.

THE COVERAGE REPORT IS SYNTHESISED FROM THE REAL TREE, never from a fixture file. ``.runtime/`` is
untracked, so a test that read the shipped report would pass on the machine that produced it and
fail everywhere else. The builder below names real modules under each target path and marks real
line numbers, so the parse, the AST attribution and the six dimensions all run over the same files
the band governs.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts import cert004_expansion as band

REPO = Path(__file__).resolve().parents[3]


def _real_module(target: band.Target) -> Path:
    """One real, non-empty module under the target's path, so the AST pass has work to do."""
    candidates = sorted(
        path
        for path in (REPO / target.path).rglob("*.py")
        if "__pycache__" not in path.parts and path.stat().st_size > 400
    )
    assert candidates, f"{target.path} ships no module, so the band unit measures nothing"
    return candidates[0]


def _cobertura(tmp_path: Path, *, targets: tuple[band.Target, ...] = band.TARGETS) -> Path:
    """A Cobertura report over real files: odd statement lines hit, even ones missed."""
    parts = [
        '<?xml version="1.0" ?>',
        '<coverage line-rate="0.5" branch-rate="0.5" version="7.6" timestamp="0">',
        f"  <sources><source>{REPO}</source></sources>",
        '  <packages><package name="p"><classes>',
    ]
    for target in targets:
        module = _real_module(target)
        relative = module.relative_to(REPO).as_posix()
        statements = sorted(
            {
                node.lineno
                for node in ast.walk(ast.parse(module.read_text(encoding="utf-8")))
                if isinstance(node, ast.stmt)
            }
        )
        parts.append(f'    <class filename="{relative}" name="{module.stem}"><lines>')
        for index, line in enumerate(statements):
            hits = 1 if index % 2 == 0 else 0
            parts.append(f'      <line number="{line}" hits="{hits}"/>')
        # One partially covered branch, so branches_valid is non-zero and the branch ratio is
        # a real fraction rather than the vacuous 0/0 the empty-report path produced.
        if statements:
            parts.append(
                f'      <line number="{statements[0]}" hits="1" branch="true" '
                'condition-coverage="50% (1/2)"/>'
            )
        parts.append("    </lines></class>")
    parts += ["  </classes></package></packages>", "</coverage>"]
    path = tmp_path / "cert004-coverage.xml"
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return path


# ----------------------------------------------------------------- the refusal, forged


def test_an_unmeasured_band_unit_is_a_fault_and_never_a_certification(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A readable report that names none of the four components may not certify them."""
    empty = tmp_path / "empty.xml"
    empty.write_text(
        '<?xml version="1.0" ?>\n<coverage><packages></packages></coverage>\n', encoding="utf-8"
    )
    code = band.main(["--coverage-xml", str(empty), "--out", str(tmp_path / "out")])
    assert code == 2, (
        "an empty coverage document certified all four units at 100% of nothing; FAULT is the "
        "only honest answer and it is not the same answer as REFUSED"
    )
    err = capsys.readouterr().err
    assert "no coverage data" in err
    for target in band.TARGETS:
        assert target.unit_id in err, "the refusal must name every unit it could not measure"
    assert not (tmp_path / "out").exists(), "a faulted run may not leave evidence behind"


def test_a_partially_measured_report_is_still_a_fault_for_the_units_it_omits(
    tmp_path: Path,
) -> None:
    """The check is per unit, not "did the report contain anything at all"."""
    partial = _cobertura(tmp_path, targets=band.TARGETS[:2])
    absent = band.unmeasured_targets(band._parse_coverage_xml(partial))
    assert len(absent) == len(band.TARGETS) - 2
    assert band.TARGETS[2].module in " ".join(absent)
    assert band.main(["--coverage-xml", str(partial), "--out", str(tmp_path / "out")]) == 2


def test_every_declared_target_is_a_real_importable_component() -> None:
    """A band unit naming a path or module that does not exist governs nothing."""
    for target in band.TARGETS:
        assert (REPO / target.path).is_dir(), f"{target.unit_id}: {target.path} is absent"
        assert target.module == target.path.replace("/", ".")
        assert target.unit_id.startswith(band.BAND_ID)
    assert len({t.unit_id for t in band.TARGETS}) == len(band.TARGETS)
    assert [t for t in band.TARGETS if not t.in_primary_gate], (
        "the out-of-gate unit is the reason this band exists; if every unit were in the primary "
        "gate the band would be measuring what pyproject already measures"
    )


# ----------------------------------------------------------------- the measurement


def test_the_six_dimensions_are_read_from_the_report_and_the_ast(tmp_path: Path) -> None:
    coverage = band._parse_coverage_xml(_cobertura(tmp_path))
    target = band.TARGETS[0]
    profile = band.measure_component_coverage(target, coverage, REPO)
    covered, total = profile.statements
    assert total > 0 and 0 < covered < total, "the fixture marks half the statements hit"
    assert profile.branches == (1, 2), "one 50% branch was declared, so 1 of 2 is covered"
    assert profile.public_api[1] >= 1
    assert profile.repository == (1, 1)
    assert 0.0 < profile.line_percent < 100.0
    assert profile.branch_percent == 50.0
    assert profile.complete is False
    names = [dimension["name"] for dimension in profile.dimensions()]
    assert set(names) == set(band.REQUIRED_COVERAGE_DIMENSIONS)
    assert all(d["percent"] <= 100.0 for d in profile.dimensions())


def test_a_dimension_with_no_data_is_reported_as_complete_only_vacuously() -> None:
    """``_dim`` is left permissive on purpose; the antecedent is refused instead."""
    assert band._dim("branches", 0, 0) == {
        "name": "branches",
        "covered": 0,
        "total": 0,
        "percent": 100.0,
        "complete": True,
    }
    assert band._dim("statements", 1, 4)["percent"] == 25.0
    assert band._dim("statements", 1, 4)["complete"] is False


def test_function_and_exception_lines_come_from_the_syntax_tree() -> None:
    source = "\n".join(
        [
            "x = 1",
            "def f():",
            "    y = 2",
            "    raise ValueError(y)",
            "try:",
            "    pass",
            "except ValueError:",
            "    z = 3",
        ]
    )
    functions, exceptions = band._executable_lines(source)
    assert functions == frozenset({2, 3, 4}), (
        "the def line counts with the body: it is the statement coverage records when the "
        "function is defined, and excluding it would report a function as uncovered whose "
        "definition ran"
    )
    assert 1 not in functions, "a module-level assignment is not a function line"
    assert exceptions == frozenset({4, 8}), "the raise and the handler body are exception paths"


def test_the_public_api_dimension_measures_resolvability_of_dunder_all() -> None:
    resolvable, declared = band._public_api_coverage("scripts.cert004_expansion")
    assert (resolvable, declared) == (1, 1), "a module with no __all__ is vacuously covered"
    resolvable, declared = band._public_api_coverage("intelligence.rie")
    assert declared >= 1 and resolvable == declared


def test_an_unimportable_module_is_a_coverage_gap_and_not_a_crash(tmp_path: Path) -> None:
    coverage = band._parse_coverage_xml(_cobertura(tmp_path))
    broken = band.Target(
        unit_id="UCOS-CERT-004-U99",
        module="platform.does_not_exist",
        path=band.TARGETS[0].path,
        owner="platform",
        layer_ref="none",
        in_primary_gate=False,
    )
    profile = band.measure_component_coverage(broken, coverage, REPO)
    assert profile.public_api == (0, 1) and profile.repository == (0, 1)
    assert profile.complete is False


# ----------------------------------------------------------------- the band


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    """One band for the whole module: governing four units twice is the expensive part."""
    report = _cobertura(tmp_path_factory.mktemp("band"))
    return band.run_band(REPO, report)


def test_the_band_governs_every_declared_unit(built: dict[str, object]) -> None:
    assert built["band_id"] == band.BAND_ID
    units = built["units"]
    assert set(units) == {target.unit_id for target in band.TARGETS}
    for files in units.values():
        assert files, "a unit with no evidence files was not governed"


def test_the_band_is_content_addressed_and_deterministic(tmp_path: Path) -> None:
    report = _cobertura(tmp_path)
    first = band.run_band(REPO, report)
    second = band.run_band(REPO, report)
    assert first["band_sha256"] == second["band_sha256"]
    assert band.canonical_json(first) == band.canonical_json(second)
    assert len(first["band_sha256"]) == 64


def test_the_four_mission_outputs_are_present_and_summarised(built: dict[str, object]) -> None:
    scope = built["expanded-certification-scope.json"]
    coverage = built["coverage-expansion-report.json"]
    acceptance = built["acceptance-expansion-report.json"]
    readiness = built["repository-readiness-update.json"]
    assert scope["summary"]["units_total"] == len(band.TARGETS)
    assert coverage["added_to_primary_coverage_gate"] == [
        target.module for target in band.TARGETS if target.in_primary_gate
    ]
    assert coverage["out_of_primary_gate_by_design"] == [
        target.module for target in band.TARGETS if not target.in_primary_gate
    ]
    assert acceptance["summary"]["units_total"] == len(band.TARGETS)
    assert readiness["summary"]["units_total"] == len(band.TARGETS)


def test_a_half_covered_component_is_not_accepted(built: dict[str, object]) -> None:
    """The fixture leaves every unit short of 100%, so nothing may report READY."""
    readiness = built["repository-readiness-update.json"]
    assert readiness["summary"]["ready"] == 0, (
        "half the statements are marked missed; a READY verdict here would mean the readiness "
        "gate is not reading the coverage it was handed"
    )
    for component in readiness["components"]:
        assert component["readiness_verdict"] == "NOT-READY"
        assert component["freeze_recommendation"] == "DO-NOT-FREEZE"


# ----------------------------------------------------------------- emission and the CLI


def test_emit_writes_every_unit_bundle_and_the_mission_outputs(
    built: dict[str, object], tmp_path: Path
) -> None:
    out = tmp_path / "evidence"
    band.emit(built, out)
    for name in (
        "expanded-certification-scope.json",
        "coverage-expansion-report.json",
        "acceptance-expansion-report.json",
        "repository-readiness-update.json",
        "band.json",
    ):
        payload = json.loads((out / name).read_text(encoding="utf-8"))
        assert payload, f"{name} was written empty"
    assert "units" not in json.loads((out / "band.json").read_text(encoding="utf-8")), (
        "band.json is the summary; carrying the per-unit bundles too would author the same "
        "evidence twice"
    )
    for unit_id, files in built["units"].items():
        for name in files:
            assert (out / unit_id / name).is_file()


def test_the_cli_reports_the_band_and_leaves_the_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "out"
    code = band.main(
        ["--coverage-xml", str(_cobertura(tmp_path)), "--out", str(out), "--repo-root", str(REPO)]
    )
    assert code == 0
    printed = capsys.readouterr().out
    assert band.BAND_TITLE in printed
    assert "byte_identical=True" in printed
    for target in band.TARGETS:
        assert target.module in printed
    determinism = json.loads((out / "determinism.json").read_text(encoding="utf-8"))
    assert determinism["byte_identical"] is True
    assert determinism["band_sha256_a"] == determinism["band_sha256_b"]


def test_the_json_projection_carries_the_same_verdicts_as_the_render(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report = _cobertura(tmp_path)
    assert band.main(["--coverage-xml", str(report), "--out", str(tmp_path / "j"), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["band_id"] == band.BAND_ID
    assert payload["determinism"]["byte_identical"] is True
    assert payload["readiness"]["units_total"] == len(band.TARGETS)
    assert payload["coverage_added_to_gate"] == [
        target.module for target in band.TARGETS if target.in_primary_gate
    ]


def test_an_absent_report_is_a_usage_error_and_not_a_verdict(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        band.main(["--coverage-xml", str(tmp_path / "nope.xml"), "--out", str(tmp_path)])
    assert raised.value.code == 2, "argparse.error exits 2; the caller must not read it as a pass"
