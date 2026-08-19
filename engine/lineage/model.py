"""ULP Part 01 — the lineage model.

Lineage answers **"how did this become this?"**, which is a different question from
identity's **"what is this?"**. This module carries the shapes that answer it and nothing
else: no store, no authority, no identifier.

Every family, relation type and direction is DATA in ``engine/lineage/families.json``.
There is no relation name and no family name below. The classification is checked against
``00-BOOK/tools/config.py`` ``RELATIONSHIP_TYPES`` at load time, so this layer cannot
invent a relation, rename one, or drift into a second vocabulary.

**Transformation is deliberately absent from the family set.** ``change_events`` answer
"what happened to this object" — an event stream, not an edge to another object. The
projection carries events beside edges, never as edges, because collapsing the two would
merge two different questions into one answer.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

#: Which endpoint of an edge came first. Declared per relation type in the classification.
ANCESTOR_FROM = "from"
ANCESTOR_TO = "to"


class LineageError(RuntimeError):
    """The classification or a source is unusable. A fault, never a lineage answer."""

    def __init__(self, message: str, *, subject: str | None = None) -> None:
        super().__init__(message if subject is None else f"{message}: {subject}")
        self.subject = subject


def _require(entry: Mapping[str, Any], key: str, context: str) -> Any:
    value = entry.get(key)
    if value in (None, "", [], {}):
        raise LineageError(f"{context}: field {key!r} is absent or empty")
    return value


@dataclass(frozen=True, slots=True)
class RelationRule:
    """One classified relation: which family it belongs to, and which end came first."""

    relation: str
    family: str
    ancestor: str

    @classmethod
    def of(cls, entry: Mapping[str, Any], family: str) -> RelationRule:
        relation = str(_require(entry, "type", f"{family} relation"))
        ancestor = str(_require(entry, "ancestor", relation))
        if ancestor not in (ANCESTOR_FROM, ANCESTOR_TO):
            raise LineageError("ancestor must name an edge endpoint", subject=relation)
        return cls(relation=relation, family=family, ancestor=ancestor)


@dataclass(frozen=True, slots=True)
class Family:
    """One lineage family — a question, and the relations that answer it."""

    name: str
    question: str
    acyclic: bool
    relations: tuple[RelationRule, ...]

    @classmethod
    def of(cls, entry: Mapping[str, Any]) -> Family:
        name = str(_require(entry, "family", "family"))
        return cls(
            name=name,
            question=str(_require(entry, "question", name)),
            acyclic=bool(entry.get("acyclic", False)),
            relations=tuple(RelationRule.of(r, name) for r in _require(entry, "types", name)),
        )


@dataclass(frozen=True, slots=True)
class Classification:
    """The whole family classification, rehydrated and structurally usable."""

    declaration_id: str
    families: tuple[Family, ...]
    non_lineage: frozenset[str]

    @classmethod
    def of(cls, document: Mapping[str, Any]) -> Classification:
        families = tuple(Family.of(f) for f in _require(document, "families", "classification"))
        seen: dict[str, str] = {}
        for family in families:
            for rule in family.relations:
                if rule.relation in seen:
                    raise LineageError(
                        f"{rule.relation} is classified into two families "
                        f"({seen[rule.relation]}, {family.name})"
                    )
                seen[rule.relation] = family.name
        non_lineage = frozenset(str(x) for x in document.get("non_lineage") or ())
        overlap = sorted(non_lineage & set(seen))
        if overlap:
            raise LineageError(f"relations classified as both lineage and non-lineage: {overlap}")
        return cls(
            declaration_id=str(_require(document, "declaration_id", "classification")),
            families=families,
            non_lineage=non_lineage,
        )

    @property
    def rules(self) -> dict[str, RelationRule]:
        """Every lineage relation, keyed by relation name."""
        return {r.relation: r for f in self.families for r in f.relations}

    @property
    def classified(self) -> frozenset[str]:
        """Every relation this classification accounts for, lineage or not."""
        return frozenset(self.rules) | self.non_lineage

    def family_of(self, relation: str) -> str | None:
        rule = self.rules.get(relation)
        return rule.family if rule else None


@dataclass(frozen=True, slots=True)
class LineageEdge:
    """One ancestry edge, carrying the source that declared it.

    ``descendant`` and ``ancestor`` are resolved from the relation's declared direction, so
    a traversal never re-derives which way an edge points.
    """

    descendant: str
    ancestor: str
    relation: str
    family: str
    source: str

    def as_dict(self) -> dict[str, str]:
        return {
            "ancestor": self.ancestor,
            "descendant": self.descendant,
            "family": self.family,
            "relation": self.relation,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class LineageEvent:
    """One transformation event. NOT an edge — see the module docstring."""

    subject: str
    kind: str
    at: str
    sequence: int
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "at": self.at,
            "kind": self.kind,
            "sequence": self.sequence,
            "source": self.source,
            "subject": self.subject,
        }


@dataclass(frozen=True, slots=True)
class LineageProjection:
    """The composed projection. Derived truth: it owns nothing it reports."""

    classification: Classification
    edges: tuple[LineageEdge, ...]
    events: tuple[LineageEvent, ...]
    sources: Mapping[str, int] = field(default_factory=dict)

    def by_family(self) -> dict[str, int]:
        counts: dict[str, int] = {f.name: 0 for f in self.classification.families}
        for edge in self.edges:
            counts[edge.family] = counts.get(edge.family, 0) + 1
        return counts

    def ancestors_of(self, node: str, family: str | None = None) -> tuple[LineageEdge, ...]:
        return tuple(
            e for e in self.edges if e.descendant == node and (family is None or e.family == family)
        )

    def descendants_of(self, node: str, family: str | None = None) -> tuple[LineageEdge, ...]:
        return tuple(
            e for e in self.edges if e.ancestor == node and (family is None or e.family == family)
        )

    def events_for(self, node: str) -> tuple[LineageEvent, ...]:
        return tuple(e for e in self.events if e.subject == node)


__all__ = [
    "ANCESTOR_FROM",
    "ANCESTOR_TO",
    "Classification",
    "Family",
    "LineageEdge",
    "LineageError",
    "LineageEvent",
    "LineageProjection",
    "RelationRule",
]
