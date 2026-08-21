"""UCXI-000001 Parts 12/13 — certification and evidence tests.

The certification verdict must be reachable in *both* directions: the bootstrapped
universal catalog certifies, and a degraded context set does not. Evidence must be
byte-identical across runs for an unchanged context set, and must refuse to write into
the frozen corpus.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.context.certification import (
    CERTIFICATION_DIMENSIONS,
    VERDICT_CERTIFIED,
    VERDICT_NOT_CERTIFIED,
    CertificationDimension,
    ContextCertificate,
    certify,
    require_certified,
)
from engine.context.errors import ContextCertificationError, ContextEvidenceError
from engine.context.evidence import (
    EVIDENCE_VERSION,
    build_evidence,
    evidence_index,
    evidence_json,
    write_evidence,
)
from engine.context.model import ContextRecord, Observer
from engine.context.registry import ContextRegistry
from engine.tests.context.conftest import declaration


def _inject(registry: ContextRegistry, record: ContextRecord) -> None:
    registry._records[record.context_id] = record  # noqa: SLF001 - deliberate corruption


# -------------------------------------------------------------------- certification


def test_universal_catalog_certifies(universal_registry: ContextRegistry) -> None:
    certificate = certify(universal_registry)
    assert certificate.verdict == VERDICT_CERTIFIED
    assert certificate.certified
    assert certificate.failed_dimensions == ()
    assert len(certificate.dimensions) == len(CERTIFICATION_DIMENSIONS) == 8
    assert certificate.certificate_id.startswith("UCOS-CTXCERT-")
    assert certificate.metrics["universal_covered"] == 16
    assert certificate.metrics["laws"] == 12
    assert certificate.metrics["rules"] == 12
    assert certificate.seals["registry"] and certificate.seals["composition"]
    assert certificate.dimension("CXC-01") is not None
    assert certificate.dimension("CXC-99") is None
    assert certificate.summary()["dimensions_passed"] == 8
    assert certificate.to_dict()["certified"] is True


def test_certification_is_deterministic(universal_registry: ContextRegistry) -> None:
    first = certify(universal_registry)
    second = certify(universal_registry)
    assert first.certificate_id == second.certificate_id
    assert first.content_hash == second.content_hash
    assert first.dimension("CXC-08").passed


def test_empty_context_set_does_not_certify(empty_registry: ContextRegistry) -> None:
    certificate = certify(empty_registry)
    assert certificate.verdict == VERDICT_NOT_CERTIFIED
    assert not certificate.certified
    assert "CXC-03" in certificate.failed_dimensions
    assert "CXC-07" in certificate.failed_dimensions
    assert certificate.dimension("CXC-07").measured == "no composition"


def test_partial_context_set_does_not_certify(empty_registry: ContextRegistry) -> None:
    empty_registry.register(declaration())
    certificate = certify(empty_registry)
    assert not certificate.certified
    assert "CXC-03" in certificate.failed_dimensions


def test_corrupted_identity_fails_the_identity_dimension(
    universal_registry: ContextRegistry,
) -> None:
    base = universal_registry.records()[0]
    _inject(
        universal_registry,
        ContextRecord(
            context_id="UCOS-CTX-deadbeefcafe",
            kind=base.kind,
            taxon_id=base.taxon_id,
            namespace=base.namespace,
            natural_key=base.natural_key + "-forged",
            values=base.values,
            authority=base.authority,
            lifecycle=base.lifecycle,
            boundary=base.boundary,
        ),
    )
    certificate = certify(universal_registry)
    assert not certificate.certified
    assert "CXC-05" in certificate.failed_dimensions
    assert "CXC-01" in certificate.failed_dimensions  # the constitution sees it too


def test_certification_accepts_a_supplied_composition_and_observer(
    universal_registry: ContextRegistry, composed: object
) -> None:
    certificate = certify(
        universal_registry,
        composed=composed,  # type: ignore[arg-type]
        observer=Observer(observer_id="o", vantage="test"),
    )
    assert certificate.certified


def test_require_certified_is_fail_closed(
    universal_registry: ContextRegistry, empty_registry: ContextRegistry
) -> None:
    assert require_certified(universal_registry).certified
    with pytest.raises(ContextCertificationError):
        require_certified(empty_registry)


def test_dimension_value_object() -> None:
    dimension = CertificationDimension(
        dimension_id="CXC-01", statement="s", passed=False, detail="d", measured="m"
    )
    assert dimension.to_dict()["passed"] is False
    certificate = ContextCertificate(
        certificate_id="c", verdict=VERDICT_NOT_CERTIFIED, dimensions=(dimension,)
    )
    assert certificate.failed_dimensions == ("CXC-01",)
    assert certificate.content_hash


# ------------------------------------------------------------------------ evidence


def test_evidence_document_is_complete(universal_registry: ContextRegistry) -> None:
    evidence = build_evidence(universal_registry)
    assert evidence["evidence_version"] == EVIDENCE_VERSION
    assert evidence["authority"] == "NONE (DERIVED TRUTH)"
    assert evidence["programme"] == "UCXI-000001"
    assert evidence["operational"] is True
    assert evidence["certification"]["verdict"] == VERDICT_CERTIFIED
    assert len(evidence["constitution"]["laws"]["laws"]) == 12
    assert len(evidence["taxonomy"]["taxa"]) == 17
    assert len(evidence["ontology"]["dimensions"]) == 16
    assert len(evidence["registry"]["contexts"]) == 16
    assert evidence["registry"]["audit_intact"] is True
    assert evidence["resolution"]["all_resolvable"] is True
    assert evidence["composition"]["universally_complete"] is True
    assert evidence["graph"]["valid"] is True
    assert evidence["validation"]["is_valid"] is True
    assert evidence["catalog_sources"]


def test_evidence_exemplars_prove_the_layer_operates(universal_registry: ContextRegistry) -> None:
    exemplars = build_evidence(universal_registry)["exemplars"]
    assert exemplars["resolution"]["resolved"] is not None
    assert exemplars["impact"]["taxon"]
    assert exemplars["runtime"]["activated"] is True
    assert exemplars["runtime"]["released"] is True
    assert exemplars["runtime"]["sample_read"]["value"]
    assert len(exemplars["resolution_order"]) == 16


def test_evidence_defaults_to_the_bootstrapped_catalog() -> None:
    evidence = build_evidence()
    assert evidence["operational"] is True
    assert evidence["registry"]["summary"]["contexts"] == 16


def test_evidence_is_byte_identical_across_runs(universal_registry: ContextRegistry) -> None:
    first = evidence_json(build_evidence(universal_registry))
    second = evidence_json(build_evidence(universal_registry))
    assert first == second
    assert "timestamp" not in first


def test_evidence_reports_a_degraded_set(empty_registry: ContextRegistry) -> None:
    evidence = build_evidence(empty_registry)
    assert evidence["operational"] is False
    assert evidence["composition"]["error"]
    assert evidence["certification"]["verdict"] == VERDICT_NOT_CERTIFIED
    assert evidence["exemplars"]["runtime"]["activated"] is False
    assert evidence["exemplars"]["resolution"]["resolved"] is None


def test_evidence_index_is_compact_and_gate_readable(universal_registry: ContextRegistry) -> None:
    index = evidence_index(build_evidence(universal_registry))
    assert index["schema"] == "ucos-ucxi-context-evidence-index"
    assert index["verdict"] == VERDICT_CERTIFIED
    assert index["seal_sha256"]
    assert index["universal_coverage"] == index["universal_kinds"] == 16
    assert len(index["dimensions"]) == 8
    assert index["operational"] is True


def test_write_evidence_writes_canonically(
    tmp_path: Path, universal_registry: ContextRegistry
) -> None:
    evidence = build_evidence(universal_registry)
    target = write_evidence(evidence, tmp_path / "nested" / "context-evidence.json")
    assert target.exists()
    body = target.read_text(encoding="utf-8")
    assert body.endswith("\n")
    assert body == evidence_json(evidence)


def test_write_evidence_refuses_the_frozen_corpus(universal_registry: ContextRegistry) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    with pytest.raises(ContextEvidenceError):
        write_evidence(
            build_evidence(universal_registry), repo_root / "00-BOOK" / "context-evidence.json"
        )
