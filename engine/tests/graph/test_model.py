"""Unit tests for engine.graph.model — nodes, edges, and the core graph."""

from __future__ import annotations

import pytest

from engine.graph.errors import (
    DuplicateEdgeError,
    DuplicateNodeError,
    ImmutableIdentifierError,
    NodeNotFoundError,
)
from engine.graph.model import (
    KIND_ARTIFACT,
    Edge,
    GraphProvenance,
    KnowledgeGraph,
    Node,
)


def test_node_defaults_and_immutability():
    node = Node("UCOS-REG-000001", KIND_ARTIFACT, version="1.0.0")
    assert node.label == "UCOS-REG-000001"  # label defaults to id
    assert node.version == "1.0.0"
    # frozen: cannot reassign the immutable identifier
    with pytest.raises(AttributeError):
        node.node_id = "other"  # type: ignore[misc]
    # attributes are a read-only mapping
    node2 = Node("A", "Artifact", attributes={"x": 1})
    with pytest.raises(TypeError):
        node2.attributes["y"] = 2  # type: ignore[index]


@pytest.mark.parametrize("bad_id", ["", None, 123])
def test_node_rejects_bad_identifier(bad_id):
    with pytest.raises(ImmutableIdentifierError):
        Node(bad_id, "Artifact")  # type: ignore[arg-type]


def test_node_rejects_empty_kind():
    with pytest.raises(ImmutableIdentifierError):
        Node("A", "")


def test_node_to_dict_and_identity():
    node = Node("A", "Artifact", label="Alpha", version="1.0.0", attributes={"k": "v"})
    assert node.to_dict() == {
        "id": "A",
        "kind": "Artifact",
        "label": "Alpha",
        "version": "1.0.0",
        "attributes": {"k": "v"},
    }
    assert node.identity()[0] == "A"


def test_edge_validation_and_to_dict():
    edge = Edge("UEDGE-000000001", "A", "B", "Depends-On", note="n")
    assert edge.to_dict()["from"] == "A"
    assert edge.to_dict()["to"] == "B"
    assert edge.identity() == ("UEDGE-000000001", "A", "B", "Depends-On")
    with pytest.raises(ImmutableIdentifierError):
        Edge("", "A", "B", "T")
    with pytest.raises(ImmutableIdentifierError):
        Edge("E", "A", "B", "")
    with pytest.raises(ImmutableIdentifierError):
        Edge("E", "", "B", "T")


def test_add_node_idempotent_and_conflict():
    graph = KnowledgeGraph()
    node = Node("A", "Artifact", version="1.0.0")
    graph.add_node(node)
    graph.add_node(Node("A", "Artifact", version="1.0.0"))  # identical: idempotent
    assert graph.order() == 1
    with pytest.raises(DuplicateNodeError):
        graph.add_node(Node("A", "Volume", version="1.0.0"))  # conflicting


def test_add_edge_idempotent_and_conflict():
    graph = KnowledgeGraph(nodes=[Node("A", "Artifact"), Node("B", "Artifact")])
    graph.add_edge(Edge("E1", "A", "B", "Depends-On"))
    graph.add_edge(Edge("E1", "A", "B", "Depends-On"))  # idempotent
    assert graph.size() == 1
    with pytest.raises(DuplicateEdgeError):
        graph.add_edge(Edge("E1", "A", "B", "Consumes"))  # conflicting


def test_lookups_and_not_found():
    graph = KnowledgeGraph(nodes=[Node("A", "Artifact", version="1.0.0")])
    assert graph.has_node("A")
    assert graph.find("A") is not None
    assert graph.find("Z") is None
    assert graph.version_of("A") == "1.0.0"
    with pytest.raises(NodeNotFoundError):
        graph.node("Z")


def test_adjacency_queries():
    nodes = [Node(x, "Artifact") for x in ("A", "B", "C")]
    edges = [
        Edge("E1", "A", "B", "Depends-On"),
        Edge("E2", "A", "C", "Consumes"),
        Edge("E3", "C", "A", "Depends-On"),
    ]
    graph = KnowledgeGraph(nodes, edges)
    assert graph.successors("A") == ("B", "C")
    assert graph.successors("A", type="Depends-On") == ("B",)
    assert graph.predecessors("A") == ("C",)
    assert graph.neighbors("A") == ("B", "C")
    assert graph.out_degree("A") == 2
    assert graph.in_degree("A") == 1
    assert graph.degree("A") == 3
    assert graph.edges_from("A", type="Consumes")[0].edge_id == "E2"
    assert graph.edges_to("A", type="Depends-On")[0].edge_id == "E3"
    assert graph.edges_of_type("Consumes")[0].edge_id == "E2"
    assert set(graph.edge_types()) == {"Depends-On", "Consumes"}
    assert graph.kinds() == ("Artifact",)


def test_orphan_and_kind_views():
    graph = KnowledgeGraph(
        nodes=[Node("A", "Artifact"), Node("B", "Volume"), Node("ORPH", "Artifact")],
        edges=[Edge("E1", "A", "B", "In-Volume")],
    )
    assert graph.is_orphan("ORPH") is True
    assert graph.is_orphan("A") is False
    assert [n.node_id for n in graph.nodes_of_kind("Artifact")] == ["A", "ORPH"]


def test_provenance_default_and_custom():
    prov = GraphProvenance(generated_at="t", generator_version="v", artifact_count=3)
    graph = KnowledgeGraph(provenance=prov)
    assert graph.provenance.artifact_count == 3
    assert graph.provenance.to_dict()["generated_at"] == "t"
    assert KnowledgeGraph().provenance.generated_at == ""


def test_subgraph_edge_type_filter_prunes_isolated():
    nodes = [Node(x, "Artifact") for x in ("A", "B", "C")]
    edges = [Edge("E1", "A", "B", "Depends-On"), Edge("E2", "A", "C", "Consumes")]
    graph = KnowledgeGraph(nodes, edges)
    sub = graph.subgraph(edge_types={"Depends-On"})
    assert sub.node_ids() == ("A", "B")  # C pruned (only had a Consumes edge)
    assert sub.size() == 1


def test_subgraph_keep_isolated_and_extras():
    graph = KnowledgeGraph(nodes=[Node("A", "Artifact"), Node("B", "Artifact")])
    extra_node = Node("SYN", "Signal")
    extra_edge = Edge("SE", "SYN", "A", "Evidences")
    sub = graph.subgraph(
        node_ids={"A"},
        edge_types=set(),
        extra_nodes=[extra_node],
        extra_edges=[extra_edge],
        keep_isolated=True,
    )
    assert sub.has_node("SYN")
    assert sub.has_node("A")
    assert sub.size() == 1


def test_subgraph_node_filter_restricts_edges():
    nodes = [Node(x, "Artifact") for x in ("A", "B", "C")]
    edges = [Edge("E1", "A", "B", "Depends-On"), Edge("E2", "B", "C", "Depends-On")]
    graph = KnowledgeGraph(nodes, edges)
    sub = graph.subgraph(node_ids={"A", "B"})
    assert sub.size() == 1  # only the A->B edge (B->C excluded, C not in filter)
    assert set(sub.node_ids()) == {"A", "B"}
