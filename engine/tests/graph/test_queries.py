"""Unit tests for engine.graph.queries — traversal algorithms."""

from __future__ import annotations

import pytest

from engine.graph import queries
from engine.graph.model import Edge, KnowledgeGraph, Node


def _chain_graph():
    # A -> B -> C -> D (Depends-On), plus a side Consumes A -> D
    nodes = [Node(x, "Artifact") for x in ("A", "B", "C", "D")]
    edges = [
        Edge("E1", "A", "B", "Depends-On"),
        Edge("E2", "B", "C", "Depends-On"),
        Edge("E3", "C", "D", "Depends-On"),
        Edge("E4", "A", "D", "Consumes"),
    ]
    return KnowledgeGraph(nodes, edges)


def test_breadth_first_and_closures():
    g = _chain_graph()
    assert queries.breadth_first(g, "A", types=["Depends-On"]) == ("B", "C", "D")
    assert queries.descendants(g, "A", types=["Depends-On"]) == ("B", "C", "D")
    assert queries.ancestors(g, "D", types=["Depends-On"]) == ("C", "B", "A")
    # unfiltered includes the Consumes edge target too
    assert set(queries.descendants(g, "A")) == {"B", "C", "D"}


def test_shortest_path_variants():
    g = _chain_graph()
    assert queries.shortest_path(g, "A", "A") == ("A",)
    assert queries.shortest_path(g, "A", "D", types=["Depends-On"]) == ("A", "B", "C", "D")
    # with Consumes allowed, the direct A->D shortcut wins
    assert queries.shortest_path(g, "A", "D") == ("A", "D")
    assert queries.shortest_path(g, "D", "A") == ()  # unreachable forward
    assert queries.has_path(g, "A", "D") is True
    assert queries.has_path(g, "D", "A") is False


def test_topological_order_and_acyclic():
    g = _chain_graph()
    order = queries.topological_order(g, types=["Depends-On"])
    assert order.index("A") < order.index("B") < order.index("C") < order.index("D")
    assert queries.is_acyclic(g, types=["Depends-On"]) is True


def test_cycle_detection():
    nodes = [Node(x, "Artifact") for x in ("X", "Y", "Z")]
    edges = [
        Edge("E1", "X", "Y", "Depends-On"),
        Edge("E2", "Y", "Z", "Depends-On"),
        Edge("E3", "Z", "X", "Depends-On"),
    ]
    g = KnowledgeGraph(nodes, edges)
    assert queries.is_acyclic(g, types=["Depends-On"]) is False
    with pytest.raises(ValueError):
        queries.topological_order(g, types=["Depends-On"])
    cycle = queries.find_cycle(g, types=["Depends-On"])
    assert cycle and cycle[0] == cycle[-1]  # closed cycle path
    # acyclic graph -> empty cycle
    assert queries.find_cycle(_chain_graph(), types=["Depends-On"]) == ()


def test_connected_component():
    nodes = [Node(x, "Artifact") for x in ("A", "B", "C", "ISO")]
    edges = [Edge("E1", "A", "B", "Depends-On"), Edge("E2", "B", "C", "Consumes")]
    g = KnowledgeGraph(nodes, edges)
    assert queries.connected_component(g, "A") == ("A", "B", "C")
    assert queries.connected_component(g, "ISO") == ("ISO",)


def test_self_loop_cycle():
    g = KnowledgeGraph(nodes=[Node("A", "Artifact")], edges=[Edge("E", "A", "A", "Depends-On")])
    assert queries.find_cycle(g, types=["Depends-On"]) == ("A", "A")
