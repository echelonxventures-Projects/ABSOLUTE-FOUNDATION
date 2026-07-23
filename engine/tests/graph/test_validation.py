"""Unit tests for engine.graph.validation — mission-invariant checks."""

from __future__ import annotations

from engine.graph.model import Edge, KnowledgeGraph, Node
from engine.graph.validation import validate_graph


def test_valid_graph_report(core):
    report = validate_graph(core)
    assert report.is_valid is True
    assert report.duplicate_node_ids == ()
    assert report.malformed_node_ids == ()
    assert report.malformed_edge_ids == ()
    assert report.unversioned_artifacts == ()
    assert report.node_count == core.order()
    assert report.dependency_cycle == ()  # sample substrate is acyclic
    d = report.to_dict()
    assert d["is_valid"] is True


def test_malformed_identifiers_flagged():
    # a node with a non-immutable-looking id, and an artifact missing a version
    graph = KnowledgeGraph(
        nodes=[Node("weird id", "Artifact", version="1.0.0"), Node("A", "Artifact", version="")],
        edges=[Edge("not an edge id", "weird id", "A", "Depends-On")],
    )
    report = validate_graph(graph)
    assert "weird id" in report.malformed_node_ids
    assert "not an edge id" in report.malformed_edge_ids
    assert "A" in report.unversioned_artifacts
    assert report.is_valid is False


def test_dangling_endpoint_is_finding_not_failure():
    # edge points at a node that is not registered -> reported, but still valid
    graph = KnowledgeGraph(nodes=[Node("UCOS-A-000001", "Artifact", version="1.0.0")])
    graph.add_edge(Edge("UEDGE-000000001", "UCOS-A-000001", "UCOS-GHOST-000002", "Depends-On"))
    report = validate_graph(graph)
    assert "UCOS-GHOST-000002" in report.dangling_edge_endpoints
    assert report.is_valid is True  # dangling endpoints are findings


def test_dependency_cycle_is_finding_not_failure():
    graph = KnowledgeGraph(
        nodes=[
            Node("UCOS-A-000001", "Artifact", version="1"),
            Node("UCOS-B-000002", "Artifact", version="1"),
        ],
        edges=[
            Edge("UEDGE-000000001", "UCOS-A-000001", "UCOS-B-000002", "Depends-On"),
            Edge("UEDGE-000000002", "UCOS-B-000002", "UCOS-A-000001", "Depends-On"),
        ],
    )
    report = validate_graph(graph)
    assert report.dependency_cycle  # a cycle was found and reported
    assert report.is_valid is True  # but it does not fail the mission invariants


def test_synthetic_and_registry_identifiers_accepted():
    graph = KnowledgeGraph(
        nodes=[
            Node("CATEGORY::REG", "Category", version=""),
            Node("VOL-000", "Volume", version=""),
            Node("USIG-000000001", "Signal", version=""),
        ],
        edges=[
            Edge(
                "KGE::Of-Category::UCOS-A-000001=>CATEGORY::REG",
                "VOL-000",
                "CATEGORY::REG",
                "X",
            )
        ],
    )
    report = validate_graph(graph, require_acyclic_dependencies=False)
    assert report.malformed_node_ids == ()
    assert report.malformed_edge_ids == ()
