"""UVI-000001 Part 03 — the Test Object Registry, and the substrates it is projected from.

A DERIVED PROJECTION, not a new registry. Every field below is read from a surface that
already exists and is already gate-measured:

============================  ==========================================================
Substrate                     Owner
============================  ==========================================================
identity, ownership, edges    ``00-MASTER/UCOS-UGA-001/01-EXECUTABLE-OBJECT-REGISTRY.json``
relationship edges            ``00-MASTER/UCOS-UGA-001/04-RELATIONSHIP-GRAPH.json``
capability of an owner        ``intelligence/UCOS-RIE-CAPABILITY-CATALOG.json``
what pytest collects          ``pyproject.toml`` ``[tool.pytest.ini_options] testpaths``
measured cost                 ``00-MASTER/UVI-000001/test-cost-model.json``
============================  ==========================================================

The registry adds exactly two things to what those surfaces already say, and both are
projections rather than facts: **collectibility** (a ``TEST_OBJECT`` that pytest would
never collect is not a selectable unit of verification) and **price** (a measured
duration, used only to balance shards). Deleting this projection changes no verdict; it
changes how long reaching the verdict takes.

Authority: NONE — DERIVED TRUTH.
"""

from __future__ import annotations

import fnmatch
import json
import os
import tomllib
from collections import defaultdict
from dataclasses import dataclass, field

from engine.verification_intelligence.constitution import COST_MODEL, repo_root
from engine.verification_intelligence.model import TestObject, VerificationIntelligenceError

EXECUTABLE_REGISTRY = "00-MASTER/UCOS-UGA-001/01-EXECUTABLE-OBJECT-REGISTRY.json"
RELATIONSHIP_GRAPH = "00-MASTER/UCOS-UGA-001/04-RELATIONSHIP-GRAPH.json"
CAPABILITY_CATALOG = "intelligence/UCOS-RIE-CAPABILITY-CATALOG.json"
PYPROJECT = "pyproject.toml"

#: The price of a test object no measurement covers. Deliberately generous: an
#: unmeasured file that is actually slow would otherwise be packed into an already
#: full shard, and the cost of over-pricing is a slightly uneven plan while the cost of
#: under-pricing is one shard the whole run waits on.
DEFAULT_COST_SECONDS = 4.0


def _read_json(path: str, what: str) -> dict:
    try:
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationIntelligenceError(f"{what} is unreadable: {path}") from exc
    if not isinstance(document, dict):
        raise VerificationIntelligenceError(f"{what} is not an object: {path}")
    return document


@dataclass(slots=True)
class Substrates:
    """Every graph selection derives from, loaded once and indexed for reverse walks."""

    objects: dict[str, dict] = field(default_factory=dict)
    dependents: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    owner_members: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    by_universal_id: dict[str, str] = field(default_factory=dict)
    relationships: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    capability_of_owner: dict[str, str] = field(default_factory=dict)

    def record(self, path: str) -> dict | None:
        return self.objects.get(path)

    def dependents_of(self, seeds: set[str]) -> set[str]:
        """Transitive reverse closure over import edges.

        Breadth-first over the inverted edge set. Seeds are excluded from the result
        unless something reaches them, so a caller can still distinguish "what changed"
        from "what the change reaches".
        """
        seen: set[str] = set()
        frontier = set(seeds)
        while frontier:
            nxt: set[str] = set()
            for path in frontier:
                for dependent in self.dependents.get(path, ()):
                    if dependent not in seen:
                        seen.add(dependent)
                        nxt.add(dependent)
            frontier = nxt
        return seen

    def related_identities(self, universal_ids: set[str]) -> set[str]:
        """One hop over the relationship graph, in both directions."""
        neighbours: set[str] = set()
        for identity in universal_ids:
            neighbours |= self.relationships.get(identity, set())
        return neighbours - universal_ids


def load_substrates(root: str | None = None) -> Substrates:
    """Load identity, ownership, dependency, capability and relationship in one pass.

    Raises:
        VerificationIntelligenceError: any declared substrate is absent or unusable.
            Fail closed: a selector missing one of its graphs would narrow silently,
            which is the one outcome this design refuses.
    """
    base = root or repo_root()
    substrates = Substrates()

    registry = _read_json(os.path.join(base, EXECUTABLE_REGISTRY), "the executable object registry")
    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        raise VerificationIntelligenceError("the executable object registry holds no entries")
    for entry in entries:
        if not isinstance(entry, dict) or "path" not in entry:
            continue
        path = str(entry["path"])
        substrates.objects[path] = entry
        owner = str(entry.get("owner") or "")
        if owner:
            substrates.owner_members[owner].add(path)
        identity = str(entry.get("universal_id") or "")
        if identity:
            substrates.by_universal_id[identity] = path
        for dependency in entry.get("dependencies") or ():
            substrates.dependents[str(dependency)].add(path)
    if not substrates.dependents:
        raise VerificationIntelligenceError(
            "the registry carries no dependency edges, so impact cannot be computed; run "
            "`python 00-MASTER/UCOS-UGA-001/uga_engine.py run` to regenerate it"
        )

    graph = _read_json(os.path.join(base, RELATIONSHIP_GRAPH), "the relationship graph")
    edges = graph.get("relationships")
    if not isinstance(edges, list) or not edges:
        raise VerificationIntelligenceError("the relationship graph holds no relationships")
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source, target = str(edge.get("from") or ""), str(edge.get("to") or "")
        if not source or not target:
            continue
        substrates.relationships[source].add(target)
        substrates.relationships[target].add(source)

    catalog = _read_json(os.path.join(base, CAPABILITY_CATALOG), "the capability catalogue")
    capabilities = catalog.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise VerificationIntelligenceError("the capability catalogue holds no capabilities")
    for capability in capabilities:
        if not isinstance(capability, dict):
            continue
        location = str(capability.get("canonical_location") or "")
        name = str(capability.get("canonical_name") or location)
        if location:
            substrates.capability_of_owner[location] = name

    return substrates


def collection_roots(root: str | None = None) -> tuple[str, ...]:
    """The paths pytest collects from, read from the pytest configuration itself.

    Restating them here would create a second answer to "what is the test suite", and
    the two would drift the first time a path was added to one of them.
    """
    base = root or repo_root()
    try:
        with open(os.path.join(base, PYPROJECT), "rb") as handle:
            document = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise VerificationIntelligenceError("pyproject.toml is unreadable") from exc
    paths = document.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("testpaths")
    if not isinstance(paths, list) or not paths:
        raise VerificationIntelligenceError(
            "pytest declares no testpaths, so the collectible set is unknown"
        )
    return tuple(str(path) for path in paths)


def is_collectible(path: str, roots: tuple[str, ...]) -> bool:
    """True when pytest would collect ``path`` under the declared roots.

    ``python_files`` is left at the pytest default because the configuration does not
    override it; the moment it does, this reads it instead of assuming.
    """
    if not path.endswith(".py"):
        return False
    if not any(path == root or path.startswith(root.rstrip("/") + "/") for root in roots):
        return False
    return fnmatch.fnmatch(os.path.basename(path), "test_*.py")


def load_cost_model(root: str | None = None) -> tuple[dict[str, float], dict[str, dict], float]:
    """Measured durations, split tables and the split threshold.

    A missing or unparseable model is not an error. Every test object is then priced at
    the default and nothing is split, which produces a slower plan and never a wrong one.
    """
    target = os.path.join(root or repo_root(), COST_MODEL)
    if not os.path.isfile(target):
        return {}, {}, 0.0
    try:
        with open(target, encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}, {}, 0.0
    raw_costs = document.get("costs")
    costs = (
        {str(path): float(value) for path, value in raw_costs.items() if _is_number(value)}
        if isinstance(raw_costs, dict)
        else {}
    )
    raw_split = document.get("split")
    split = (
        {str(path): entry for path, entry in raw_split.items() if isinstance(entry, dict)}
        if isinstance(raw_split, dict)
        else {}
    )
    threshold = document.get("split_threshold_seconds")
    return costs, split, float(threshold) if _is_number(threshold) else 0.0


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


@dataclass(slots=True)
class TestObjectRegistry:
    """Every collectible test object, priced and attributed.

    ``by_owner`` is what makes ownership-driven selection possible: a test that
    exercises a module through a subprocess has no import edge to it, but it is owned
    by the same owner, and the owner is recorded truth.
    """

    objects: dict[str, TestObject] = field(default_factory=dict)
    by_owner: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    by_capability: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    roots: tuple[str, ...] = ()
    priced: int = 0
    node_costs: dict[str, float] = field(default_factory=dict)
    splittable: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def paths(self) -> tuple[str, ...]:
        """Every collectible test path, sorted — the whole suite, as a selection."""
        return tuple(sorted(self.objects))

    def cost_of(self, unit: str) -> float:
        """The measured price of one schedulable unit — a test file or a test node."""
        if unit in self.node_costs:
            return self.node_costs[unit]
        entry = self.objects.get(unit)
        return entry.cost_seconds if entry else DEFAULT_COST_SECONDS

    def units_for(self, test_paths: tuple[str, ...]) -> tuple[str, ...]:
        """The schedulable units covering ``test_paths``.

        A test object whose measured cost exceeds the declared threshold is placed as its
        individual nodes; every other object is placed whole. Splitting happens only when
        the recorded content hash still matches the registry's, so the node ids are known
        to be current — a changed file falls back to whole-file placement, which is always
        correct and merely slower. Every node of a split file is present exactly once, so
        the union of the units is exactly ``test_paths``.
        """
        units: list[str] = []
        for path in sorted(set(test_paths)):
            nodes = self.splittable.get(path)
            units.extend(nodes if nodes else (path,))
        return tuple(units)

    def total_cost(self, paths: tuple[str, ...] | None = None) -> float:
        return sum(self.cost_of(path) for path in (paths if paths is not None else self.paths))


def build_test_registry(
    substrates: Substrates | None = None, root: str | None = None
) -> TestObjectRegistry:
    """Project the Test Object Registry from the substrates and the pytest configuration."""
    base = root or repo_root()
    substrates = substrates or load_substrates(base)
    roots = collection_roots(base)
    costs, split, threshold = load_cost_model(base)

    registry = TestObjectRegistry(roots=roots)
    for path, entry in substrates.objects.items():
        if entry.get("object_class") != "TEST_OBJECT" or not is_collectible(path, roots):
            continue
        owner = str(entry.get("owner") or "")
        measured = costs.get(path)
        test_object = TestObject(
            path=path,
            universal_id=str(entry.get("universal_id") or ""),
            owner=owner,
            capability=substrates.capability_of_owner.get(owner, ""),
            content_hash=entry.get("content_hash"),
            cost_seconds=float(measured) if measured is not None else DEFAULT_COST_SECONDS,
        )
        registry.objects[path] = test_object
        registry.by_owner[owner].add(path)
        if test_object.capability:
            registry.by_capability[test_object.capability].add(path)
        if measured is not None:
            registry.priced += 1
        entry_split = split.get(path)
        if (
            entry_split is not None
            and threshold > 0
            and (measured or 0.0) > threshold
            and entry_split.get("content_hash") == test_object.content_hash
        ):
            nodes = entry_split.get("nodes")
            if isinstance(nodes, dict) and nodes:
                registry.splittable[path] = tuple(sorted(str(node) for node in nodes))
                for node, seconds in nodes.items():
                    if _is_number(seconds):
                        registry.node_costs[str(node)] = float(seconds)

    if not registry.objects:
        raise VerificationIntelligenceError(
            "the Test Object Registry projected no collectible test object; the executable "
            "registry and the pytest configuration disagree about what the suite is"
        )
    return registry
