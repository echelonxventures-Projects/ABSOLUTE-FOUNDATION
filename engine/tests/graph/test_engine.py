"""Unit tests for engine.graph.engine — the core graph builder."""

from __future__ import annotations

from engine.graph.engine import (
    build_core_graph,
    load_certification,
    load_signals,
    load_twin,
)
from engine.graph.model import KIND_ARTIFACT, KIND_VOLUME
from engine.registry.adapter import RegistryAdapter


def test_build_core_graph_nodes_and_edges(core):
    # 7 artifacts + 4 volumes = 11 nodes
    assert len(core.nodes_of_kind(KIND_ARTIFACT)) == 7
    assert len(core.nodes_of_kind(KIND_VOLUME)) == 4
    assert core.order() == 11
    # every relationship becomes an edge
    assert core.size() > 0
    book = core.node("UCOS-BOOK-000000")
    assert book.kind == KIND_ARTIFACT
    assert book.attributes["category"] == "BOOK"


def test_core_graph_is_version_aware(core):
    node = core.node("UCOS-REG-000001")
    assert node.version == "1.0.0"
    assert node.attributes["status"] == "CERTIFIED"
    # traceability projection retained on artifact nodes
    arch = core.node("UCOS-ARCH-000001")
    assert arch.attributes["traceability"]["requirement"] == ("UCOS-CON-000001",)


def test_core_graph_provenance(core):
    prov = core.provenance
    assert prov.generated_at == "2026-07-16T00:00:00+00:00"
    assert prov.generator_version == "test-1.0"
    assert prov.artifact_count == 7
    assert prov.volume_count == 4


def test_build_is_idempotent(registry):
    a = build_core_graph(registry)
    b = build_core_graph(registry)
    assert a.node_ids() == b.node_ids()
    assert [e.edge_id for e in a.edges()] == [e.edge_id for e in b.edges()]


def test_load_auxiliary_documents(registry):
    signals = load_signals(registry)
    assert len(signals) == 5
    cert = load_certification(registry)
    assert cert["verdict"] == "CERTIFIED"
    twin = load_twin(registry)
    assert "build" in twin["dimensions"]


def test_load_auxiliary_absent_is_empty(minimal_data_dir):
    registry = RegistryAdapter.open(minimal_data_dir)
    assert load_signals(registry) == ()
    assert load_certification(registry) == {}
    assert load_twin(registry) == {}
    # core graph still builds without the optional documents
    core = build_core_graph(registry)
    assert core.order() == 11
