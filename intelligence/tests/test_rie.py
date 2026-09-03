"""RIE validation tests.

Proves the constitutional requirements:
  * deterministic + reproducible: identical state ⇒ identical outputs
  * repository-derived: reported facts equal the evidence sources (not hardcoded)
  * no duplicate authority: every output declares AUTHORITY = NONE (derived truth)
  * composition: the engine reads existing evidence, produces only additive JSON

Run: .ec1-venv/bin/python -m pytest intelligence/tests -q
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from intelligence.rie.__main__ import main as cli_main
from intelligence.rie.canonical import canonical_json, sha256_text
from intelligence.rie.config import MemorySink, RepoConfig
from intelligence.rie.engine import RepositoryIntelligenceEngine, build_model
from intelligence.rie.evidence import EvidenceReader

REPO = RepoConfig.create().repo_root


def _engine() -> RepositoryIntelligenceEngine:
    return RepositoryIntelligenceEngine(RepoConfig.create(REPO))


def test_determinism_identical_state_identical_outputs() -> None:
    eng = _engine()
    result = eng.verify_determinism()
    assert result["deterministic"] is True
    assert result["mismatches"] == []


def test_outputs_byte_identical_across_two_sinks() -> None:
    a, b = MemorySink(), MemorySink()
    _engine().write(a)
    _engine().write(b)
    assert a.store.keys() == b.store.keys()
    for name in a.store:
        assert a.store[name] == b.store[name], f"non-deterministic output: {name}"


def test_repository_derived_not_hardcoded() -> None:
    """Reported corpus/coverage equal the evidence files (proves derivation)."""
    eng = _engine()
    model = eng.model()
    ct = json.loads((REPO / "00-BOOK/DATA/control-tower.json").read_text(encoding="utf-8"))
    assert model["health"]["corpus"]["artifacts"] == ct["portfolio"]["total_artifacts"]
    assert model["health"]["corpus"]["edges"] == ct["portfolio"]["total_edges"]
    cert = json.loads((REPO / "00-BOOK/DATA/certification.json").read_text(encoding="utf-8"))
    assert model["health"]["certification"]["digital_twin_verdict"] == cert["verdict"]


def test_no_duplicate_authority() -> None:
    for payload in _engine().outputs().values():
        assert payload["authority"] == "NONE (derived truth)"


def test_all_outputs_are_valid_json_and_sealed() -> None:
    for name, payload in _engine().outputs().items():
        assert name.endswith(".json")
        text = canonical_json(payload)
        reloaded = json.loads(text)
        assert reloaded["content_hash"] == payload["content_hash"]


def test_rib_is_a_generated_output() -> None:
    outputs = _engine().outputs()
    assert "UCOS-IMP-BASELINE-001.rib.json" in outputs
    assert outputs["UCOS-IMP-BASELINE-001.rib.json"]["artifact_id"] == "UCOS-IMP-BASELINE-001"


def test_engine_writes_only_under_intelligence_dir(tmp_path: Path) -> None:
    """Writes are contained under the configured intelligence directory.

    Proven in two halves, neither of which touches Repository Truth:

      (a) the DEFAULT output directory is under ``intelligence/`` — asserted without
          writing anything, because the location of a directory is a property of the
          configuration, not of a file that must exist;
      (b) an ACTUAL write is contained by the directory it was configured with — proven
          against a temporary output root, with the real reader and the real model, so
          the write path is exercised rather than mocked.

    Both halves were previously one line that called ``write()`` against the live
    repository. It proved the property and, on every certification run, rewrote four
    tracked artifacts — UCOS-RIE-MODEL, UCOS-RIE-HEALTH, UCOS-RIE-CAPABILITY-CATALOG and
    UCOS-IMP-BASELINE-001.rib — so ``./verify.sh --full`` could not certify the tree it
    had measured. A certification that edits what it certifies is not an observation.
    """
    assert "intelligence" in RepoConfig.create(REPO).output_dir.parts

    sandbox = tmp_path / "intelligence"
    engine = RepositoryIntelligenceEngine(replace(RepoConfig.create(REPO), output_dir=sandbox))
    written = engine.write()
    assert written, "the engine wrote nothing, so containment is vacuous"
    for path in written:
        assert "intelligence" in Path(path).parts, f"write escaped intelligence/: {path}"
        assert Path(path).parent == sandbox, f"write escaped its configured directory: {path}"


# ---------------------------------------------------------------------------
# UCOS-P0-FCL-002-FIX-001 — coverage isolation regression tests
#
# coverage.xml is TEST_EXECUTION_STATE / QUALITY_MEASUREMENT: an environmental
# output of the test runner that is absent from every pristine clone (the bootstrap
# never runs the test suite). Including it in the canonical identity fingerprint
# caused every clone regeneration to produce a different input_hash and therefore a
# different catalog SHA256, making Phase-9 pristine-clone certification
# irreproducible across all four variance dimensions:
#   registry_variance / ordering_variance / certification_variance / dictionary_variance
#
# Fix: coverage_measurement is excluded from state_fingerprint(). That closed the
# fingerprint route only; UCOS-CL-005 below closes the remaining route through
# analysis.py and asserts the invariant over the serialized canonical model.
# ---------------------------------------------------------------------------


def test_canonical_identity_independent_of_coverage() -> None:
    """UCOS-P0-FCL-002-FIX-001: coverage.xml must not influence canonical artifact identity.

    Three invariants proven:
      (a) structural  — coverage_measurement absent from state_fingerprint() keys
      (b) input domain — state_fingerprint() contains exactly the 5 canonical DATA files
      (c) behavioral  — input_hash is stable across re-derivations (no coverage leakage)
    """
    from intelligence.rie.evidence import EvidenceReader

    config = RepoConfig.create(REPO)
    reader = EvidenceReader(config)
    fp = reader.state_fingerprint()

    # (a) coverage_measurement must not be a top-level key in the fingerprint
    assert "coverage_measurement" not in fp, (
        "coverage_measurement must not appear in state_fingerprint() — "
        "it is TEST_EXECUTION_STATE and must not influence canonical artifact identity"
    )

    # (b) the only key is evidence_files, mapping exactly the 5 canonical DATA files
    assert set(fp.keys()) == {
        "evidence_files"
    }, f"state_fingerprint() must contain only 'evidence_files', got: {set(fp.keys())}"
    expected_files = {
        "00-BOOK/DATA/control-tower.json",
        "00-BOOK/DATA/artifacts.json",
        "00-BOOK/DATA/certification.json",
        "00-BOOK/DATA/twin.json",
        "00-BOOK/DATA/volumes.json",
    }
    assert set(fp["evidence_files"].keys()) == expected_files, (
        f"evidence_files keys mismatch.\n"
        f"  expected: {sorted(expected_files)}\n"
        f"  got:      {sorted(fp['evidence_files'].keys())}"
    )

    # (c) input_hash is stable across re-derivations — no wall-clock or env leakage
    h1 = reader.generation_state()["input_hash"]
    reader._cache.pop("generation_state", None)  # force re-derivation
    h2 = reader.generation_state()["input_hash"]
    assert h1 == h2, (
        f"input_hash is not stable across calls: {h1!r} != {h2!r}\n"
        "A non-deterministic input (coverage, wall-clock, environment) has leaked "
        "back into canonical identity."
    )


# ---------------------------------------------------------------------------
# UCOS-CL-005 — canonical identity is invariant under environmental state.
#
# The two tests above assert the SHAPE of state_fingerprint(). That is necessary
# but not sufficient, and it is not what the architecture promises. Neither of
# them fails while coverage still reaches canonical output bytes by another
# route, which is exactly what happened: be46a300 removed coverage from the
# fingerprint while analysis.py went on writing coverage_line_pct into
# health.code, so the model digest still moved with coverage.xml and Phase-9
# variance survived the fix that was supposed to remove it.
#
# The test below is the invariant itself, asserted at the boundary where it is
# claimed to hold: the serialized canonical model. It compares a build that can
# see coverage.xml against a build that cannot, which is precisely the
# difference between this working tree and a pristine clone.
# ---------------------------------------------------------------------------


def _model_without_coverage() -> dict:
    """The canonical model as a pristine clone derives it — no coverage.xml on disk."""
    base = RepoConfig.create(REPO)
    absent = replace(base, coverage_xml=REPO / "__absent__" / "coverage.xml")
    assert not absent.coverage_xml.exists(), "fixture must point at a non-existent path"
    return build_model(EvidenceReader(absent))


def test_canonical_model_bytes_invariant_under_coverage_presence() -> None:
    """UCOS-CL-005: coverage.xml must not change one byte of canonical output.

    coverage.xml is TEST_EXECUTION_STATE: gitignored, environmental, and absent from
    every pristine clone because the bootstrap never runs the suite. If it reaches the
    canonical model, the same commit yields different artifact bytes in the clone than
    in a working tree where tests have run — which is irreproducibility, measured by
    Phase-9 as registry / ordering / certification / dictionary variance.

    Asserted over the serialized bytes rather than over any single field, so the whole
    class is covered rather than the one field that happened to leak.
    """
    with_coverage = build_model(EvidenceReader(RepoConfig.create(REPO)))
    without_coverage = _model_without_coverage()

    a, b = canonical_json(with_coverage), canonical_json(without_coverage)
    if a != b:
        diff = [
            k
            for k in set(with_coverage) | set(without_coverage)
            if with_coverage.get(k) != without_coverage.get(k)
        ]
        raise AssertionError(
            "canonical model bytes changed with coverage.xml presence — an environmental "
            f"input has reached canonical identity. Divergent top-level sections: {sorted(diff)}"
        )


def test_canonical_identity_hashes_invariant_under_coverage_presence() -> None:
    """The derived identities must be invariant for the same reason as the bytes.

    input_hash was already fixed at be46a300; content identity was not. Both are
    asserted here so a future change cannot repair one and regress the other.
    """
    with_coverage = build_model(EvidenceReader(RepoConfig.create(REPO)))
    without_coverage = _model_without_coverage()

    assert (
        with_coverage["generation"]["input_hash"] == without_coverage["generation"]["input_hash"]
    ), "input_hash moved with coverage.xml presence"

    assert sha256_text(canonical_json(with_coverage)) == sha256_text(
        canonical_json(without_coverage)
    ), "canonical content hash moved with coverage.xml presence"


def test_no_canonical_output_carries_a_coverage_field() -> None:
    """Structural backstop: no coverage-derived key may appear anywhere in the model.

    The byte test above catches a leak only when the two builds actually differ. A
    coverage field that happens to hold the same value in both builds — an absent
    coverage.xml on a machine that never ran tests, say — would slip past it. This
    closes that gap by forbidding the key outright, at any depth.
    """
    model = build_model(EvidenceReader(RepoConfig.create(REPO)))
    forbidden = (
        "coverage_line_pct",
        "coverage_branch_pct",
        "coverage_measurement",
        "lines_covered",
        "lines_valid",
        "coverage_full",
    )
    found: list[str] = []

    def walk(node: object, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in forbidden:
                    found.append(f"{path}.{key}")
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")

    walk(model, "model")
    assert not found, (
        "canonical model carries coverage-derived fields, which makes its identity a "
        f"function of test-execution state: {found}"
    )


# --------------------------------------------------------------------------- the CLI
#
# ``python -m intelligence.rie`` was 62 units at 0.0%, and the cost of that was not academic:
# ``answer`` — one of the five subcommands its own docstring documents — raised
# ``KeyError: 'coverage_line_pct'`` on every invocation. UCOS-CL-005 correctly removed that key
# from the canonical model (see the four tests above); the projection that read it was never
# updated, and nothing executed the projection, so a broken documented command shipped.
#
# Each test below therefore calls ``main`` with the argv an operator would type, and the first
# one asserts the whole answer document is serialisable rather than only that the call returned 0.


def _run(capsys, *argv: str) -> tuple[int, str]:  # noqa: ANN001 - pytest fixture type
    code = cli_main(list(argv))
    return code, capsys.readouterr().out


def test_the_answer_subcommand_answers_instead_of_raising(capsys) -> None:  # noqa: ANN001
    """The regression witness for ``KeyError: 'coverage_line_pct'``."""
    code, out = _run(capsys, "answer")
    assert code == 0
    answers = json.loads(out)
    assert set(answers) == {
        "what_exists",
        "what_is_implemented",
        "what_remains",
        "what_is_blocked",
        "what_is_executable",
        "critical_path",
        "current_repository_state",
        "is_aeos_ready",
    }
    assert "coverage" not in canonical_json(answers), (
        "the answer document must not quote a coverage figure: coverage.xml is "
        "TEST_EXECUTION_STATE, so an answer carrying it would differ in a pristine clone"
    )
    assert answers["what_is_implemented"].startswith("engine EC-1 + platform EC-2")


def test_the_snapshot_subcommand_emits_the_sealed_snapshot(capsys) -> None:  # noqa: ANN001
    code, out = _run(capsys, "snapshot")
    assert code == 0
    snapshot = json.loads(out)
    assert snapshot["authority"] == "NONE (derived truth)"
    assert snapshot["content_hash"] == _engine().outputs()["UCOS-RIE-SNAPSHOT.json"]["content_hash"]


def test_the_verify_subcommand_returns_the_determinism_verdict(capsys) -> None:  # noqa: ANN001
    code, out = _run(capsys, "verify")
    result = json.loads(out)
    assert (code == 0) is (result["deterministic"] is True), (
        "the exit code must be the report's own verdict; deciding it separately would let the "
        "shell and the document disagree about one run"
    )
    assert code == 0


def test_the_build_subcommand_writes_into_the_repo_it_is_given(
    tmp_path: Path,
    capsys,  # noqa: ANN001
) -> None:
    """``--repo`` is honoured, so the build is provable without touching Repository Truth.

    ``build`` against the live tree would rewrite four tracked artifacts mid-certification —
    the defect ``test_engine_writes_only_under_intelligence_dir`` above exists to prevent — so
    the subcommand is exercised against a copy of the evidence the engine reads.
    """
    for relative in (
        "00-BOOK/DATA/control-tower.json",
        "00-BOOK/DATA/artifacts.json",
        "00-BOOK/DATA/certification.json",
        "00-BOOK/DATA/twin.json",
        "00-BOOK/DATA/volumes.json",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO / relative).read_bytes())

    code, out = _run(capsys, "--repo", str(tmp_path), "build")
    assert code == 0
    assert "RIE: regenerated" in out
    assert out.count("  - ") >= 1, "a build that names no artifact reports nothing"
    written = sorted(p.name for p in (tmp_path / "intelligence").rglob("*.json"))
    assert written, "the build reported outputs it did not write"
    assert not list((REPO / "intelligence").glob("__absent__")), "sanity: no stray write path"


def test_the_portal_subcommand_generates_pages_where_it_is_told(
    tmp_path: Path,
    capsys,  # noqa: ANN001
) -> None:
    out_dir = tmp_path / "portal"
    code, out = _run(capsys, "portal", "--out", str(out_dir))
    assert code == 0
    assert "RIE portal: generated" in out
    pages = sorted(p.name for p in out_dir.iterdir())
    assert pages, "the portal reported pages it did not write"
    for page in pages:
        assert f"  - {page}" in out, f"{page} was written but not reported"


def test_an_explicit_repo_root_is_resolved_rather_than_assumed(capsys) -> None:  # noqa: ANN001
    """``--repo .`` must reach the same snapshot as the auto-resolved default."""
    code, explicit = _run(capsys, "--repo", str(REPO), "snapshot")
    assert code == 0
    code, implicit = _run(capsys, "snapshot")
    assert code == 0
    assert json.loads(explicit)["content_hash"] == json.loads(implicit)["content_hash"]


def test_a_subcommand_is_required() -> None:
    with pytest.raises(SystemExit) as raised:
        cli_main([])
    assert raised.value.code == 2, "argparse.error exits 2; a caller must not read it as a pass"
