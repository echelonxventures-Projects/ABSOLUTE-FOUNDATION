"""UKI Deliverable 5 — Knowledge Reuse Engine (EPIC-UKDA-002).

Determines automatically whether an existing capability can be **reused, extended,
or composed** *before* creation is allowed (``UKI-LAW-003``; creation is the last
resort). The determination is deterministic and follows the constitutional order
reuse > extend > compose > create:

    * **reuse**  — identical knowledge already exists (semantic-hash match) → point at it.
    * **extend** — a single existing artifact of the same kind and universe is a
      specialization target → extend it.
    * **compose** — the intent's declared dependencies already exist and are active
      (>= 2 components) → compose from them.
    * **create** — no existing knowledge suffices; creation is justified.

It reuses the UKDA :class:`~engine.knowledge.intelligence.KnowledgeIntelligence` and
content model verbatim (semantic hashing, search) — no second analysis engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.knowledge.integration.contracts import ArtifactIntent, Disposition
from engine.knowledge.intelligence import KnowledgeIntelligence
from engine.knowledge.store import KnowledgeBase

#: Minimum search score for a related object to count as an extension candidate.
_EXTEND_MIN_SCORE = 2
#: Minimum number of resolvable active components required to justify composition.
_COMPOSE_MIN_COMPONENTS = 2


@dataclass(frozen=True, slots=True)
class ReuseCandidate:
    """A single existing artifact considered for reuse/extension/composition."""

    cko_id: str
    relation: str
    score: int

    def to_dict(self) -> dict[str, Any]:
        return {"cko_id": self.cko_id, "relation": self.relation, "score": self.score}


@dataclass(frozen=True, slots=True)
class ReuseAssessment:
    """The deterministic reuse determination for an intent (Deliverable 5)."""

    disposition: Disposition
    targets: tuple[str, ...]
    candidates: tuple[ReuseCandidate, ...]
    reasons: tuple[str, ...]

    @property
    def requires_creation(self) -> bool:
        return self.disposition is Disposition.CREATE

    def to_dict(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition.value,
            "targets": list(self.targets),
            "candidates": [c.to_dict() for c in self.candidates],
            "reasons": list(self.reasons),
            "requires_creation": self.requires_creation,
        }


class ReuseEngine:
    """Determines reuse/extend/compose/create for an intent (Deliverable 5)."""

    __slots__ = ("_base", "_intel")

    def __init__(self, base: KnowledgeBase) -> None:
        self._base = base
        self._intel = KnowledgeIntelligence(base)

    def _semantic_reuse(self, intent: ArtifactIntent) -> tuple[str, ...]:
        target = intent.semantic_hash()
        return tuple(
            sorted(
                obj.cko_id
                for obj in self._base.objects()
                if obj.cko_id != intent.intent_id
                and obj.is_active
                and obj.semantic_hash() == target
            )
        )

    def _extension_candidates(self, intent: ArtifactIntent) -> tuple[ReuseCandidate, ...]:
        query = " ".join((intent.title, intent.statement, *intent.tags))
        candidates: list[ReuseCandidate] = []
        for hit in self._intel.search(query):
            if hit.cko_id == intent.intent_id:
                continue
            obj = self._base.get_object(hit.cko_id)
            if obj is None or not obj.is_active:
                continue
            if obj.kind is intent.kind and obj.universe == intent.universe:
                candidates.append(
                    ReuseCandidate(
                        cko_id=hit.cko_id, relation="same-kind-universe", score=hit.score
                    )
                )
        return tuple(candidates)

    def _composition_components(self, intent: ArtifactIntent) -> tuple[str, ...]:
        components = [
            ref
            for ref in intent.dependencies
            if (obj := self._base.get_object(ref)) is not None and obj.is_active
        ]
        return tuple(sorted(set(components)))

    def assess(self, intent: ArtifactIntent) -> ReuseAssessment:
        """Return the constitutional reuse determination for ``intent`` (deterministic)."""
        # 1. reuse — identical knowledge already exists.
        reuse_targets = self._semantic_reuse(intent)
        if reuse_targets:
            candidates = tuple(
                ReuseCandidate(cko_id=cid, relation="semantic", score=100) for cid in reuse_targets
            )
            return ReuseAssessment(
                disposition=Disposition.REUSE,
                targets=reuse_targets,
                candidates=candidates,
                reasons=("identical knowledge already exists (semantic-hash match)",),
            )

        # 2. extend — a single same-kind/same-universe specialization target.
        extension = self._extension_candidates(intent)
        strong = tuple(c for c in extension if c.score >= _EXTEND_MIN_SCORE)
        if strong:
            top = strong[0]
            return ReuseAssessment(
                disposition=Disposition.EXTEND,
                targets=(top.cko_id,),
                candidates=extension,
                reasons=(
                    f"existing {intent.kind.value} '{top.cko_id}' in universe "
                    f"'{intent.universe}' can be extended",
                ),
            )

        # 3. compose — the declared dependencies already exist and are active.
        components = self._composition_components(intent)
        if len(components) >= _COMPOSE_MIN_COMPONENTS:
            return ReuseAssessment(
                disposition=Disposition.COMPOSE,
                targets=components,
                candidates=tuple(
                    ReuseCandidate(cko_id=cid, relation="component", score=50) for cid in components
                ),
                reasons=(f"{len(components)} existing active components can be composed",),
            )

        # 4. create — no existing knowledge suffices.
        return ReuseAssessment(
            disposition=Disposition.CREATE,
            targets=(),
            candidates=extension,
            reasons=("no reusable, extensible, or composable knowledge found",),
        )


__all__ = ["ReuseCandidate", "ReuseAssessment", "ReuseEngine"]
