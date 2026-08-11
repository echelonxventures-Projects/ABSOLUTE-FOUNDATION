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
from pathlib import Path

from intelligence.rie.canonical import canonical_json
from intelligence.rie.config import MemorySink, RepoConfig
from intelligence.rie.engine import RepositoryIntelligenceEngine

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


def test_engine_writes_only_under_intelligence_dir() -> None:
    written = _engine().write()
    for path in written:
        assert "intelligence" in Path(path).parts, f"write escaped intelligence/: {path}"


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
# Fix: coverage_measurement is excluded from state_fingerprint(); coverage data
# remains accessible via coverage_enrichment() for health and progress outputs only.
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
    assert set(fp.keys()) == {"evidence_files"}, (
        f"state_fingerprint() must contain only 'evidence_files', got: {set(fp.keys())}"
    )
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


def test_coverage_enrichment_is_observational_not_identity() -> None:
    """coverage_enrichment() is accessible for health/progress but excluded from canonical identity.

    Proves the separation mandated by UCOS-P0-FCL-002-FIX-001: coverage data is
    readable as observational evidence without affecting the canonical artifact identity
    that the RIB → AEE → P0-FCL-002 certification chain depends on.
    """
    from intelligence.rie.evidence import EvidenceReader

    reader = EvidenceReader(RepoConfig.create(REPO))
    enrichment = reader.coverage_enrichment()

    # enrichment carries the correct constitutional classification
    assert enrichment["classification"] == "TEST_EXECUTION_STATE / QUALITY_MEASUREMENT"
    assert enrichment["identity_role"].startswith("EXCLUDED"), (
        f"identity_role must declare EXCLUDED, got: {enrichment['identity_role']!r}"
    )
    assert "fingerprint" in enrichment, "enrichment must expose a coverage fingerprint"
    assert "source" in enrichment, "enrichment must expose the source path"

    # coverage_measurement must still not appear in state_fingerprint
    fp = reader.state_fingerprint()
    assert "coverage_measurement" not in fp, (
        "coverage_measurement appeared in state_fingerprint() even after "
        "coverage_enrichment() was called — enrichment must not pollute identity"
    )
