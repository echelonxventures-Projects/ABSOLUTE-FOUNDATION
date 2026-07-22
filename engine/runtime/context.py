"""TASK-000039 — Runtime Context + Reference Frame Resolution (EPIC-006).

Realises **context resolution** and **reference frame resolution** for the
Universal Runtime Composition Engine (RUNTIME-013 §D14 Orchestration↔Context; §D10
Federation). Every composed universe is **bounded** by exactly one runtime context
(ORL-05/ORL-14), and every cross-context reference is authorised **only** by an
explicit, collision-free **federation reference** (ORL-12; ENG-005 Federation
References). Context isolation is preserved: no dependency may cross a context
boundary implicitly (ORL-13).

Two resolutions are provided, both pure and deterministic:

    * :func:`resolve_contexts` — groups the bound universes into their
      :class:`RuntimeContext` partitions, refusing any unbounded universe (ORL-14).
    * :func:`resolve_reference_frames` — computes, per universe, the
      :class:`ReferenceFrame` of universes it may reference (same-context peers plus
      federated targets) and **fails closed** on any isolation leak: a dependency
      edge that crosses contexts without a matching federation reference is refused
      (ORL-13), a federation whose endpoints share a context is refused (a
      federation is cross-context by definition, ORL-12), a dangling federation
      endpoint is refused, and a duplicate federation is refused (collision-free).

This module consumes a :class:`~engine.runtime.graph.RuntimeGraph` and a
``universe_id -> context_id`` binding; it holds no ``RuntimeUnit`` and sits below
:mod:`engine.runtime.composition`. It resolves scope and references only — it
executes nothing and confers no authority (ORL-15/ORL-22).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from engine.foundation.obs.logging import get_logger
from engine.foundation.obs.telemetry import trace
from engine.runtime.errors import ContextResolutionError, ReferenceFrameError
from engine.runtime.graph import RuntimeGraph

_logger = get_logger("runtime.context")

#: The default bounding context bound when a universe declares none.
DEFAULT_CONTEXT = "runtime"


# --------------------------------------------------------------------------- #
# Value types                                                                  #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """An explicit bounded scope partitioning the composed universes (RUNTIME-012).

    A context confers no authority (ORL-22); it only delimits which universes are
    co-scoped and therefore mutually referenceable without federation.
    """

    context_id: str
    members: tuple[str, ...]

    def contains(self, universe_id: str) -> bool:
        """True iff ``universe_id`` is bounded by this context."""
        return universe_id in self.members

    def to_dict(self) -> dict[str, object]:
        return {"context_id": self.context_id, "members": list(self.members)}


@dataclass(frozen=True, slots=True)
class Federation:
    """An explicit, cross-context ENG-005 Federation Reference (ORL-12).

    ``source`` federates a reference to ``target``, authorising a cross-context
    dependency from ``source`` to ``target`` without merging their contexts.
    """

    source: str
    target: str

    def to_dict(self) -> dict[str, str]:
        return {"source": self.source, "target": self.target}


@dataclass(frozen=True, slots=True)
class ReferenceFrame:
    """The set of universes referenceable from one universe's frame (ORL-13).

    ``visible`` is the union of same-context peers and federated targets; a
    universe may reference exactly these and no others. ``federated`` records the
    cross-context targets reached via explicit federation references.
    """

    universe_id: str
    context_id: str
    visible: tuple[str, ...]
    federated: tuple[str, ...]

    def can_reference(self, other: str) -> bool:
        """True iff this frame may reference universe ``other``."""
        return other in self.visible

    def to_dict(self) -> dict[str, object]:
        return {
            "universe_id": self.universe_id,
            "context_id": self.context_id,
            "visible": list(self.visible),
            "federated": list(self.federated),
        }


# --------------------------------------------------------------------------- #
# Context resolution                                                           #
# --------------------------------------------------------------------------- #


def resolve_contexts(bindings: Mapping[str, str]) -> tuple[RuntimeContext, ...]:
    """Group bound universes into their context partitions (ORL-05/ORL-14).

    Args:
        bindings: a ``universe_id -> context_id`` mapping. Every universe must be
            bound to a non-empty context id.

    Raises:
        ContextResolutionError: if any universe is unbounded (empty/non-string id).
    """
    with trace("runtime.context.resolve", universes=len(bindings)):
        groups: dict[str, list[str]] = {}
        for universe_id in sorted(bindings):
            context_id = bindings[universe_id]
            if not isinstance(context_id, str) or not context_id:
                raise ContextResolutionError(
                    "universe is not bound to a context (unbounded orchestration)",
                    universe_id=universe_id,
                )
            groups.setdefault(context_id, []).append(universe_id)
        contexts = tuple(
            RuntimeContext(context_id=cid, members=tuple(sorted(members)))
            for cid, members in sorted(groups.items())
        )
    _logger.info("runtime.context.resolved", contexts=len(contexts))
    return contexts


# --------------------------------------------------------------------------- #
# Reference frame resolution                                                   #
# --------------------------------------------------------------------------- #


def resolve_reference_frames(
    bindings: Mapping[str, str],
    graph: RuntimeGraph,
    federations: Iterable[Federation] = (),
) -> tuple[ReferenceFrame, ...]:
    """Resolve each universe's reference frame and enforce isolation (ORL-12/13).

    Args:
        bindings: a ``universe_id -> context_id`` mapping covering every graph node.
        graph: the composition dependency graph (source of cross-context edges).
        federations: explicit ENG-005 federation references authorising
            cross-context dependencies.

    Raises:
        ContextResolutionError: if a graph node has no context binding.
        ReferenceFrameError: on a dangling/duplicate/same-context federation, or a
            cross-context dependency with no authorising federation (isolation leak).
    """
    with trace("runtime.context.frames", universes=graph.count()):
        for node in graph.nodes():
            if node not in bindings:
                raise ContextResolutionError(
                    "graph universe has no context binding", universe_id=node
                )

        federated_targets = _validate_federations(bindings, federations)
        by_context = _members_by_context(bindings, graph.nodes())

        frames: list[ReferenceFrame] = []
        for universe_id in graph.nodes():
            context_id = bindings[universe_id]

            # Isolation (ORL-13): every cross-context dependency needs a federation.
            for dependency in graph.dependencies_of(universe_id):
                if bindings[dependency] != context_id and dependency not in (
                    federated_targets.get(universe_id, frozenset())
                ):
                    raise ReferenceFrameError(
                        "cross-context dependency without a federation reference "
                        "(context isolation leak)",
                        universe_id=universe_id,
                        dependency=dependency,
                        context=context_id,
                        dependency_context=bindings[dependency],
                    )

            peers = set(by_context.get(context_id, ())) - {universe_id}
            federated = federated_targets.get(universe_id, frozenset())
            visible = tuple(sorted(peers | set(federated)))
            frames.append(
                ReferenceFrame(
                    universe_id=universe_id,
                    context_id=context_id,
                    visible=visible,
                    federated=tuple(sorted(federated)),
                )
            )
    _logger.info(
        "runtime.context.frames.resolved",
        frames=len(frames),
        federations=sum(len(v) for v in federated_targets.values()),
    )
    return tuple(frames)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _validate_federations(
    bindings: Mapping[str, str], federations: Iterable[Federation]
) -> dict[str, frozenset[str]]:
    """Validate federation references and index them by source (ORL-12).

    Refuses dangling endpoints, same-context (non-federation) links, and duplicate
    (collision) references. Returns ``{source: {target, ...}}``.
    """
    seen: set[tuple[str, str]] = set()
    targets: dict[str, set[str]] = {}
    for federation in federations:
        source, target = federation.source, federation.target
        if source not in bindings:
            raise ReferenceFrameError(
                "federation source is not a member of the composition", source=source
            )
        if target not in bindings:
            raise ReferenceFrameError(
                "federation target is not a member of the composition", target=target
            )
        if source == target:
            raise ReferenceFrameError("a universe cannot federate with itself", universe_id=source)
        if bindings[source] == bindings[target]:
            raise ReferenceFrameError(
                "federation endpoints share a context (federation is cross-context)",
                source=source,
                target=target,
                context=bindings[source],
            )
        pair = (source, target)
        if pair in seen:
            raise ReferenceFrameError(
                "duplicate federation reference (collision)",
                source=source,
                target=target,
            )
        seen.add(pair)
        targets.setdefault(source, set()).add(target)
    return {source: frozenset(t) for source, t in targets.items()}


def _members_by_context(
    bindings: Mapping[str, str], nodes: Iterable[str]
) -> dict[str, tuple[str, ...]]:
    groups: dict[str, list[str]] = {}
    for node in nodes:
        groups.setdefault(bindings[node], []).append(node)
    return {cid: tuple(sorted(members)) for cid, members in groups.items()}


__all__ = [
    "DEFAULT_CONTEXT",
    "RuntimeContext",
    "Federation",
    "ReferenceFrame",
    "resolve_contexts",
    "resolve_reference_frames",
]
