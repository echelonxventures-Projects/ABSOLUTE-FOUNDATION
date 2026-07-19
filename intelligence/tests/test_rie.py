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
