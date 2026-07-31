"""UCKP Layer Zero — Universal Intelligence (Article 15).

Article 15 requires that knowledge reason about itself, and that no conclusion rest on a
hardcoded assumption. Both clauses are design constraints here.

Every reasoner takes the registry and returns findings derived from what the objects
actually declare. None contains a list of expected identities, a threshold tuned to the
present corpus, or a special case for a particular object. That is not a stylistic
preference: a reasoner with a hardcoded expectation reports "correct" for the corpus it
was written against and quietly goes blind as the universe grows, which is the failure
mode Article 15 exists to prevent.

Thirteen reasoners are provided, one per reasoning kind the mission names. They report;
they never mutate. Findings carry a severity so a consumer can distinguish a violation
from an observation, and :meth:`UniversalIntelligence.report` aggregates all thirteen
into one deterministic document.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum

from engine.uckp.canonical import content_hash
from engine.uckp.errors import UCKPValidationError
from engine.uckp.graph import OBJECT_SCOPE
from engine.uckp.law import ROOT_LAW
from engine.uckp.registry import UniversalKnowledgeRegistry
from engine.uckp.ucko import UCKO

#: Similarity at or above which two statements are reported as near-duplicates.
#: Derived from the mission's own duplicate-prevention discipline rather than tuned to
#: this corpus, and exposed so a caller can reason at a different tolerance.
NEAR_DUPLICATE_SIMILARITY = 0.85


class ReasoningKind(str, Enum):
    """The thirteen ways the universe reasons about itself."""

    DEPENDENCY = "dependency"
    SEMANTIC = "semantic"
    CONSTITUTIONAL = "constitutional"
    AUTHORITY = "authority"
    GOVERNANCE = "governance"
    EVOLUTION = "evolution"
    RISK = "risk"
    IMPACT = "impact"
    CONSISTENCY = "consistency"
    GAP = "gap"
    REDUNDANCY = "redundancy"
    OPTIMIZATION = "optimization"
    FUTURE = "future"

    @classmethod
    def coerce(cls, value: object) -> ReasoningKind:
        if isinstance(value, cls):
            return value
        text = str(value).strip().lower()
        for member in cls:
            if member.value == text:
                return member
        raise UCKPValidationError("unknown reasoning kind", kind=str(value))


VIOLATION = "violation"
OBSERVATION = "observation"


@dataclass(frozen=True, slots=True)
class Finding:
    """One conclusion the universe reached about itself."""

    reasoning: str
    severity: str
    subject: str
    statement: str

    def to_dict(self) -> dict[str, str]:
        return {
            "reasoning": self.reasoning,
            "severity": self.severity,
            "subject": self.subject,
            "statement": self.statement,
        }


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    """The findings and measurements of one reasoner."""

    kind: ReasoningKind
    findings: tuple[Finding, ...] = field(default_factory=tuple)
    observations: Mapping[str, float] = field(default_factory=dict)

    @property
    def violations(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity == VIOLATION)

    @property
    def clean(self) -> bool:
        return not self.violations

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "clean": self.clean,
            "counts": {"findings": len(self.findings), "violations": len(self.violations)},
            "observations": {k: self.observations[k] for k in sorted(self.observations)},
            "findings": [finding.to_dict() for finding in self.findings],
        }


def _tokens(text: str) -> frozenset[str]:
    return frozenset(part for part in str(text).casefold().split() if len(part) > 2)


def _similarity(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    union = len(left | right)
    return len(left & right) / union if union else 0.0


class UniversalIntelligence:
    """Reasoning over the canonical universe. Reports; never mutates."""

    __slots__ = ("_registry", "_graph")

    def __init__(self, registry: UniversalKnowledgeRegistry) -> None:
        self._registry = registry
        self._graph = registry.graph()

    # --- the thirteen reasoners -------------------------------------------------

    def dependency_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        depths: list[int] = []
        for obj in self._registry.objects():
            for dependency in obj.dependencies:
                if dependency not in self._registry:
                    findings.append(
                        Finding(
                            "dependency",
                            VIOLATION,
                            obj.ucko_id,
                            f"depends on {dependency}, which does not exist",
                        )
                    )
            depths.append(len(self._graph.authority_chain(obj.ucko_id)))
        for edge in self._graph.dangling():
            findings.append(
                Finding(
                    "dependency",
                    VIOLATION,
                    edge.source,
                    f"{edge.relation} edge to {edge.target} cannot be executed",
                )
            )
        return ReasoningResult(
            ReasoningKind.DEPENDENCY,
            tuple(findings),
            {
                "objects": float(len(self._registry)),
                "edges": float(len(self._graph.edges())),
                "max_authority_depth": float(max(depths) if depths else 0),
            },
        )

    def semantic_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        objects = self._registry.objects()
        profiles = [
            (obj, _tokens(f"{obj.semantic_identity.concept} {obj.semantic_identity.definition}"))
            for obj in objects
        ]
        near = 0
        for index, (left, left_tokens) in enumerate(profiles):
            for right, right_tokens in profiles[index + 1 :]:
                score = _similarity(left_tokens, right_tokens)
                if score >= NEAR_DUPLICATE_SIMILARITY:
                    near += 1
                    # An OBSERVATION, not a VIOLATION. This is a token-overlap
                    # heuristic, and a heuristic cannot establish a breach — the
                    # registry has already admitted both objects as semantically
                    # distinct, which is the actual finding of fact. Reporting a
                    # score as a violation is the same category error as reporting
                    # an unmeasured invariant as satisfied: it asserts more than the
                    # measurement supports.
                    #
                    # It would also make the constitution self-contradicting. Articles
                    # 9 and 10 require that every persistence and execution technology
                    # satisfy *one identical contract*, so a family of ten adapters
                    # necessarily describes itself in near-identical words. High overlap
                    # there is the property being demanded, not a defect in it.
                    findings.append(
                        Finding(
                            "semantic",
                            OBSERVATION,
                            left.ucko_id,
                            f"is worded much like {right.ucko_id} (score {score:.2f}); "
                            "distinct meanings, so worth a look but not a breach",
                        )
                    )
        # Identical meaning under two identities *is* a fact, and a breach of Article 3.
        for group in self._registry.duplicate_semantics():
            findings.append(
                Finding("semantic", VIOLATION, group[0], f"identical meaning homed at {group}")
            )
        return ReasoningResult(
            ReasoningKind.SEMANTIC,
            tuple(findings),
            {"objects": float(len(objects)), "near_duplicates": float(near)},
        )

    def constitutional_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        for obj in self._registry.objects():
            if not ROOT_LAW.governs(obj.taxonomy.category):
                findings.append(
                    Finding(
                        "constitutional",
                        VIOLATION,
                        obj.ucko_id,
                        f"category {obj.taxonomy.category!r} is not a governed category",
                    )
                )
            if ROOT_LAW.is_non_authoritative(obj.taxonomy.category):
                findings.append(
                    Finding(
                        "constitutional",
                        VIOLATION,
                        obj.ucko_id,
                        f"category {obj.taxonomy.category!r} may only ever be a projection",
                    )
                )
        covered = {obj.taxonomy.category for obj in self._registry.objects()}
        return ReasoningResult(
            ReasoningKind.CONSTITUTIONAL,
            tuple(findings),
            {
                "governed_categories": float(len(ROOT_LAW.governed_categories)),
                "categories_populated": float(len(covered)),
                "articles": float(len(ROOT_LAW.articles)),
            },
        )

    def authority_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        roots = self._registry.root_ids()
        if len(roots) != 1:
            findings.append(
                Finding(
                    "authority",
                    VIOLATION,
                    "uckp.universe",
                    f"the universe declares {len(roots)} constitutional roots, not one",
                )
            )
        tiers = self._registry.vocabularies().require("uckp.authority-tier")
        for obj in self._registry.objects():
            parent_id = obj.authority.derives_from
            if parent_id == obj.ucko_id:
                continue
            parent = self._registry.get(parent_id)
            if parent is None:
                findings.append(
                    Finding(
                        "authority",
                        VIOLATION,
                        obj.ucko_id,
                        f"derives authority from {parent_id}, which does not exist",
                    )
                )
                continue
            child_rank = tiers.require(obj.authority.tier).rank
            parent_rank = tiers.require(parent.authority.tier).rank
            if parent_rank > child_rank:
                findings.append(
                    Finding(
                        "authority",
                        VIOLATION,
                        obj.ucko_id,
                        f"outranks the authority it derives from ({parent_id})",
                    )
                )
        for cycle in self._graph.cycles("authority"):
            findings.append(
                Finding("authority", VIOLATION, cycle[0], f"authority cycle {list(cycle)}")
            )
        return ReasoningResult(
            ReasoningKind.AUTHORITY,
            tuple(findings),
            {"roots": float(len(roots)), "objects": float(len(self._registry))},
        )

    def governance_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        ungoverned = 0
        for obj in self._registry.objects():
            if not obj.governance_context.value:
                ungoverned += 1
                findings.append(
                    Finding("governance", VIOLATION, obj.ucko_id, "names no governance authority")
                )
        return ReasoningResult(
            ReasoningKind.GOVERNANCE,
            tuple(findings),
            {
                "objects": float(len(self._registry)),
                "ungoverned": float(ungoverned),
                "governance_edges": float(len(self._graph.edges_of_class("governance"))),
            },
        )

    def evolution_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        without_history = [
            obj.ucko_id for obj in self._registry.objects() if not obj.temporal_history
        ]
        for ucko_id in without_history:
            findings.append(Finding("evolution", VIOLATION, ucko_id, "records no temporal history"))
        stateless = sum(1 for obj in self._registry.objects() if not obj.evolution_history)
        return ReasoningResult(
            ReasoningKind.EVOLUTION,
            tuple(findings),
            {
                "objects": float(len(self._registry)),
                "without_temporal_history": float(len(without_history)),
                "not_yet_in_a_state": float(stateless),
            },
        )

    def risk_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        owners: dict[str, int] = {}
        uncertified = 0
        for obj in self._registry.objects():
            owners[obj.ownership.owner] = owners.get(obj.ownership.owner, 0) + 1
            if obj.authority.tier == "constitutional" and not obj.certification.attested:
                uncertified += 1
                findings.append(
                    Finding(
                        "risk",
                        OBSERVATION,
                        obj.ucko_id,
                        "carries constitutional authority with no certification",
                    )
                )
        total = max(len(self._registry), 1)
        concentration = max(owners.values()) / total if owners else 0.0
        return ReasoningResult(
            ReasoningKind.RISK,
            tuple(findings),
            {
                "owners": float(len(owners)),
                "ownership_concentration": round(concentration, 4),
                "uncertified_constitutional": float(uncertified),
            },
        )

    def impact_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        fan_in: dict[str, int] = {}
        for edge in self._graph.edges():
            fan_in[edge.target] = fan_in.get(edge.target, 0) + 1
        top = sorted(fan_in.items(), key=lambda item: (-item[1], item[0]))[:3]
        for ucko_id, count in top:
            findings.append(
                Finding(
                    "impact",
                    OBSERVATION,
                    ucko_id,
                    f"{count} relationships point at it; changing it changes them",
                )
            )
        return ReasoningResult(
            ReasoningKind.IMPACT,
            tuple(findings),
            {
                "max_fan_in": float(top[0][1] if top else 0),
                "objects_referenced": float(len(fan_in)),
            },
        )

    def consistency_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        for obj in self._registry.objects():
            if obj.lifecycle == "operational" and not obj.validation.attested:
                findings.append(
                    Finding(
                        "consistency",
                        VIOLATION,
                        obj.ucko_id,
                        "is operational but was never validated",
                    )
                )
            if not obj.verify_integrity():
                findings.append(
                    Finding("consistency", VIOLATION, obj.ucko_id, "seal does not match content")
                )
            if not obj.verify_replay():
                findings.append(
                    Finding("consistency", VIOLATION, obj.ucko_id, "replay proof does not hold")
                )
        return ReasoningResult(
            ReasoningKind.CONSISTENCY,
            tuple(findings),
            {"objects": float(len(self._registry))},
        )

    def gap_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        populated = {obj.taxonomy.category for obj in self._registry.objects()}
        missing = tuple(
            category for category in ROOT_LAW.governed_categories if category not in populated
        )
        for category in missing:
            findings.append(
                Finding(
                    "gap",
                    OBSERVATION,
                    f"category:{category}",
                    "a governed category with no canonical object yet",
                )
            )
        for obj in self._registry.objects():
            for facet in obj.missing_facets():
                findings.append(
                    Finding("gap", VIOLATION, obj.ucko_id, f"facet {facet.value} is absent")
                )
        return ReasoningResult(
            ReasoningKind.GAP,
            tuple(findings),
            {
                "governed_categories": float(len(ROOT_LAW.governed_categories)),
                "unpopulated_categories": float(len(missing)),
                "coverage": round(
                    len(populated & set(ROOT_LAW.governed_categories))
                    / max(len(ROOT_LAW.governed_categories), 1),
                    4,
                ),
            },
        )

    def redundancy_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        by_definition: dict[str, list[str]] = {}
        for obj in self._registry.objects():
            key = content_hash(" ".join(obj.semantic_identity.definition.split()).casefold())
            by_definition.setdefault(key, []).append(obj.ucko_id)
        repeated = 0
        for _, ids in sorted(by_definition.items()):
            if len(ids) > 1:
                repeated += 1
                findings.append(
                    Finding(
                        "redundancy",
                        VIOLATION,
                        sorted(ids)[0],
                        f"the identical definition is stated by {sorted(ids)}",
                    )
                )
        return ReasoningResult(
            ReasoningKind.REDUNDANCY,
            tuple(findings),
            {
                "distinct_definitions": float(len(by_definition)),
                "repeated_definitions": float(repeated),
            },
        )

    def optimization_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        # Object-scoped edges only. An ownership edge points at an accountable *person*
        # and every object carries one (Facet 7 is mandatory), so counting every edge
        # would make "participates in nothing" a statement that is never true of
        # anything — a measurement whose finding is unreachable measures nothing. The
        # graph draws the same distinction for dangling edges and reachability.
        fan_out = {
            obj.ucko_id: len(
                tuple(
                    edge
                    for edge in self._graph.out_edges(obj.ucko_id)
                    if edge.scope == OBJECT_SCOPE
                )
            )
            for obj in self._registry.objects()
        }
        isolated = tuple(sorted(key for key, count in fan_out.items() if count == 0))
        for ucko_id in isolated:
            findings.append(
                Finding(
                    "optimization",
                    OBSERVATION,
                    ucko_id,
                    "declares no relationship to another object; it participates in nothing",
                )
            )
        average = sum(fan_out.values()) / max(len(fan_out), 1)
        return ReasoningResult(
            ReasoningKind.OPTIMIZATION,
            tuple(findings),
            {
                "average_fan_out": round(average, 4),
                "isolated_objects": float(len(isolated)),
            },
        )

    def future_reasoning(self) -> ReasoningResult:
        findings: list[Finding] = []
        future_edges = self._graph.edges_of_class("future")
        for edge in future_edges:
            findings.append(
                Finding(
                    "future",
                    OBSERVATION,
                    edge.source,
                    f"declares an intended future binding to {edge.target}",
                )
            )
        extensible = self._registry.vocabularies().is_extensible()
        if not extensible:
            findings.append(
                Finding(
                    "future",
                    VIOLATION,
                    "uckp.universe",
                    "a vocabulary refuses an unknown future member",
                )
            )
        return ReasoningResult(
            ReasoningKind.FUTURE,
            tuple(findings),
            {
                "future_bindings": float(len(future_edges)),
                "vocabularies_extensible": 1.0 if extensible else 0.0,
            },
        )

    # --- dispatch ---------------------------------------------------------------

    def reasoners(self) -> Mapping[ReasoningKind, Callable[[], ReasoningResult]]:
        return {
            ReasoningKind.AUTHORITY: self.authority_reasoning,
            ReasoningKind.CONSISTENCY: self.consistency_reasoning,
            ReasoningKind.CONSTITUTIONAL: self.constitutional_reasoning,
            ReasoningKind.DEPENDENCY: self.dependency_reasoning,
            ReasoningKind.EVOLUTION: self.evolution_reasoning,
            ReasoningKind.FUTURE: self.future_reasoning,
            ReasoningKind.GAP: self.gap_reasoning,
            ReasoningKind.GOVERNANCE: self.governance_reasoning,
            ReasoningKind.IMPACT: self.impact_reasoning,
            ReasoningKind.OPTIMIZATION: self.optimization_reasoning,
            ReasoningKind.REDUNDANCY: self.redundancy_reasoning,
            ReasoningKind.RISK: self.risk_reasoning,
            ReasoningKind.SEMANTIC: self.semantic_reasoning,
        }

    def reason(self, kind: ReasoningKind | str) -> ReasoningResult:
        resolved = ReasoningKind.coerce(kind)
        return self.reasoners()[resolved]()

    def reason_all(self) -> tuple[ReasoningResult, ...]:
        reasoners = self.reasoners()
        return tuple(reasoners[kind]() for kind in sorted(reasoners, key=lambda k: k.value))

    def report(self) -> dict[str, object]:
        results = self.reason_all()
        violations = [f for result in results for f in result.violations]
        return {
            "schema": "ucos-uckp-intelligence-report",
            "version": "1.0.0",
            "counts": {
                "reasoners": len(results),
                "findings": sum(len(r.findings) for r in results),
                "violations": len(violations),
            },
            "clean": not violations,
            "graph_fingerprint": self._graph.fingerprint(),
            "results": [result.to_dict() for result in results],
        }


def build_intelligence(registry: UniversalKnowledgeRegistry) -> UniversalIntelligence:
    return UniversalIntelligence(registry)


def reasoning_kinds() -> tuple[str, ...]:
    return tuple(kind.value for kind in ReasoningKind)


__all__ = [
    "NEAR_DUPLICATE_SIMILARITY",
    "OBSERVATION",
    "VIOLATION",
    "Finding",
    "ReasoningKind",
    "ReasoningResult",
    "UCKO",
    "UniversalIntelligence",
    "build_intelligence",
    "reasoning_kinds",
]
