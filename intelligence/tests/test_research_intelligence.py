"""UCOS-URI-001 Research Intelligence validation tests.

Proves the constitutional requirements of the subsystem:
  * deterministic + reproducible: identical state ⇒ byte-identical outputs
  * repository-derived: every count equals the substrate it was read from
  * no duplicate authority: every output declares AUTHORITY = NONE (derived truth)
  * ZERO DUPLICATION: no research record carries canonical prose
  * append-only registry: Knowledge-Once holds and the hash chain recomputes
  * fail-closed: a non-resolving reference is an error, never a substitution

Run: .ec1-venv/bin/python -m pytest intelligence/tests -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from intelligence.kernel.canonical import canonical_json
from intelligence.kernel.config import MemorySink, subsystem_config
from intelligence.kernel.errors import (
    DuplicateRecordError,
    KnowledgeOnceViolation,
    UnresolvedReferenceError,
)
from intelligence.kernel.ids import ArtifactClass, artifact_id, parse_class
from intelligence.kernel.ledger import GENESIS_HASH, LedgerRegistry
from intelligence.research.engine import OUTPUT_DIR, ResearchIntelligenceEngine
from intelligence.research.model import CONFORMANCE_NON_CONFORMANT

REPO = subsystem_config(OUTPUT_DIR).repo_root


def _engine() -> ResearchIntelligenceEngine:
    return ResearchIntelligenceEngine(subsystem_config(OUTPUT_DIR, REPO))


@pytest.fixture(scope="module")
def engine() -> ResearchIntelligenceEngine:
    return _engine()


# -- determinism -------------------------------------------------------------


def test_determinism_identical_state_identical_outputs(engine) -> None:
    result = engine.verify_determinism()
    assert result["deterministic"] is True
    assert result["mismatches"] == []


def test_outputs_byte_identical_across_two_sinks() -> None:
    a, b = MemorySink(), MemorySink()
    _engine().write(a)
    _engine().write(b)
    assert a.store.keys() == b.store.keys()
    for name in a.store:
        assert a.store[name] == b.store[name], f"non-deterministic output: {name}"


def test_corpus_is_reproducible(engine) -> None:
    first = canonical_json(engine.corpus().to_dict())
    second = canonical_json(_engine().corpus().to_dict())
    assert first == second


# -- derivation --------------------------------------------------------------


def test_counts_are_derived_not_hardcoded(engine) -> None:
    corpus = engine.corpus()
    canon = json.loads((REPO / "knowledge/canonical-knowledge.json").read_text(encoding="utf-8"))
    closure = json.loads(
        (REPO / "00-MASTER/UAKOS-CLOSURE-002/closure.json").read_text(encoding="utf-8")
    )
    decisions = json.loads((REPO / "knowledge/decisions.json").read_text(encoding="utf-8"))
    assert len(corpus.claims) == canon["count"] + decisions["count"]
    assert sum(c.concept_count for c in corpus.contributions) == closure["concept_total"]
    assert len(corpus.contributions) == len(closure["families"])


def test_findings_carry_evidence_hashes(engine) -> None:
    for finding in engine.corpus().findings:
        assert finding.basis_content_sha256
        assert finding.basis_content_sha256 != "absent"
        assert finding.basis_locator


def test_substrate_inventory_reports_availability(engine) -> None:
    inventory = {row["key"]: row for row in engine.substrate.inventory()}
    assert inventory["canonical-knowledge"]["available"] is True
    assert engine.substrate.missing_required() == []


# -- authority + sealing -----------------------------------------------------


def test_no_duplicate_authority(engine) -> None:
    for payload in engine.outputs().values():
        assert payload["authority"] == "NONE (derived truth)"
        assert payload["programme"] == "UCOS-URI-001"


def test_all_outputs_are_valid_json_and_sealed(engine) -> None:
    for name, payload in engine.outputs().items():
        assert name.endswith(".json")
        reloaded = json.loads(canonical_json(payload))
        assert reloaded["content_hash"] == payload["content_hash"]


# -- zero duplication -------------------------------------------------------


def test_no_research_record_carries_canonical_prose(engine) -> None:
    resolver = engine.resolver
    corpus = engine.corpus()
    for group in (corpus.claims, corpus.findings, corpus.contributions, corpus.standards,
                  corpus.units, corpus.sources):
        for record in group:
            assert resolver.copied_prose(canonical_json(record.to_dict())) == [], (
                f"canonical prose copied into {type(record).__name__}"
            )


def test_claims_reference_prose_instead_of_storing_it(engine) -> None:
    for claim in engine.corpus().claims:
        payload = claim.to_dict()
        assert claim.claim_ref.startswith(("cko:", "decision:"))
        long_text_fields = {
            k for k, v in payload.items() if isinstance(v, str) and len(v) > 200
        }
        assert long_text_fields == set()
        resolved = engine.resolver.resolve(claim.claim_ref)
        assert resolved.text


# -- registry ---------------------------------------------------------------


def test_registry_integrity(engine) -> None:
    integrity = engine.registry().verify()
    assert integrity["chain_intact"] is True
    assert integrity["knowledge_once_holds"] is True
    assert integrity["intact"] is True
    assert integrity["records"] == engine.registry().count()


def test_registry_covers_every_corpus_record(engine) -> None:
    registry = engine.registry()
    assert registry.count() == len(engine.corpus().record_ids())
    for claim in engine.corpus().claims:
        assert registry.get(claim.claim_id) is not None


def test_registry_ids_are_self_describing(engine) -> None:
    for entry in engine.registry().ledger.all():
        assert parse_class(entry.record_id).value == entry.artifact_class


def test_ledger_rejects_duplicate_identity() -> None:
    ledger = LedgerRegistry("TEST", "test-schema")
    assert ledger.head() == GENESIS_HASH
    ledger.register(ArtifactClass.RESEARCH_CLAIM, "k1", {"a": 1})
    with pytest.raises(DuplicateRecordError):
        ledger.register(ArtifactClass.RESEARCH_CLAIM, "k1", {"a": 2})


def test_ledger_rejects_duplicate_content() -> None:
    ledger = LedgerRegistry("TEST", "test-schema")
    ledger.register(ArtifactClass.RESEARCH_CLAIM, "k1", {"a": 1})
    with pytest.raises(KnowledgeOnceViolation):
        ledger.register(ArtifactClass.RESEARCH_CLAIM, "k2", {"a": 1})


def test_identity_is_deterministic_and_order_independent() -> None:
    first = artifact_id(ArtifactClass.RESEARCH_UNIT, "governance")
    second = artifact_id("RESEARCH_UNIT", "governance")
    assert first == second
    assert first.startswith("UCOS-RSCH-")


# -- resolution / fail-closed ------------------------------------------------


def test_unknown_reference_is_an_error_not_a_substitution(engine) -> None:
    with pytest.raises(UnresolvedReferenceError):
        engine.resolver.resolve("cko:UCKO-DOES-NOT-EXIST#statement")
    with pytest.raises(UnresolvedReferenceError):
        engine.resolver.resolve("nonsense-without-a-space")
    with pytest.raises(UnresolvedReferenceError):
        engine.resolver.resolve("metric:not.declared")


def test_every_corpus_reference_resolves(engine) -> None:
    for ref in engine.corpus().all_refs():
        assert engine.resolver.exists(ref), ref


# -- standards analysis -----------------------------------------------------


def test_standards_analysis_is_fail_closed(engine) -> None:
    model = engine.standards().model()
    assert model["standards_analysed"] == len(engine.corpus().standards)
    assert model["conformance_histogram"][CONFORMANCE_NON_CONFORMANT] == 0
    assert model["external_cross_reference"]["classification"].startswith("CURATED")
    assert model["programme_instruments"]["science_registry_count"] > 0


# -- validation + gate ------------------------------------------------------


def test_validation_certifies_the_corpus(engine) -> None:
    report = engine.validation()
    assert report.verdict == "CERTIFIED", [c.check_id for c in report.blocking_failures()]
    assert len(report.checks) == 13
    assert report.exit_code == 0


def test_gate_opens_and_reports_a_seal(engine) -> None:
    code, line = engine.gate()
    assert code == 0
    assert "gate=OPEN" in line
    assert "seal=" in line


# -- write scope ------------------------------------------------------------


def test_engine_writes_only_inside_its_own_directory() -> None:
    written = _engine().write()
    for path in written:
        parts = Path(path).parts
        assert "intelligence" in parts
        assert OUTPUT_DIR in parts, f"write escaped {OUTPUT_DIR}: {path}"
