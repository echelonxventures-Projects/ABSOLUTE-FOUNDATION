"""Unit tests for engine.graph.evidence — operational evidence artifacts."""

from __future__ import annotations

import json

import pytest

from engine.graph.evidence import (
    EVIDENCE_VERSION,
    EvidenceWriteError,
    build_evidence,
    write_evidence,
)


def test_build_evidence_is_operational(kg):
    evidence = build_evidence(kg)
    assert evidence["evidence_version"] == EVIDENCE_VERSION
    assert evidence["operational"] is True
    assert len(evidence["projections"]) == 10
    assert evidence["validation"]["is_valid"] is True
    assert evidence["certification_verdict"] == "CERTIFIED"
    # the worked exemplar demonstrates a real traversal
    ex = evidence["exemplars"]
    assert ex["subject"]
    assert ex["blast_radius"] >= 1


def test_write_evidence_to_tmp(kg, tmp_path):
    evidence = build_evidence(kg)
    out = tmp_path / "nested" / "evidence.json"
    written = write_evidence(evidence, out)
    assert written.is_file()
    reloaded = json.loads(written.read_text())
    assert reloaded["operational"] is True


def test_write_evidence_refuses_frozen_corpus(kg):
    evidence = build_evidence(kg)
    repo_root = (
        __import__("pathlib")
        .Path(__import__("engine.graph.evidence", fromlist=["__file__"]).__file__)
        .resolve()
        .parents[2]
    )
    frozen_target = repo_root / "00-BOOK" / "DATA" / "should-not-write.json"
    with pytest.raises(EvidenceWriteError):
        write_evidence(evidence, frozen_target)
    assert not frozen_target.exists()
