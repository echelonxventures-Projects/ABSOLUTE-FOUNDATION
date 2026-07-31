"""UCKP Layer Zero — open vocabularies (Articles 15 and 17).

Article 15 forbids hardcoded assumptions and Article 17 requires that an unknown
future member be admitted by *registration*, never by amendment. A vocabulary
frozen into a Python ``Enum`` fails both: the set of admissible knowledge kinds,
authority tiers, lifecycle stages, relationship classes, persistence technologies
and execution technologies becomes a code edit, and a code edit in Layer Zero is a
constitutional amendment. So Layer Zero holds its vocabularies as *data with an
append-only registry*.

Two properties make this safe rather than merely flexible:

    * **Append-only.** :meth:`Vocabulary.extended_with` returns a new vocabulary; it
      never mutates. Redefining an existing term raises, because a term whose
      meaning can change retroactively invalidates every digest computed under the
      old meaning.
    * **Closed at the point of use.** :meth:`Vocabulary.require` refuses an
      unregistered term, so the openness is "register then use", not "anything goes".

The seeded vocabularies below are the canonical home of these term sets. The
``Enum`` vocabularies in :mod:`engine.knowledge.model` (``KnowledgeKind``,
``KnowledgeAuthority``, ``Lifecycle``, ``RelationType``) are a *checked projection*
of them: :func:`engine.uckp.assimilation.verify_vocabulary_alignment` fails closed
if the two ever diverge, so there is one authority and one verified view rather
than two competing declarations.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from engine.uckp.canonical import content_hash
from engine.uckp.errors import LawViolation
from engine.uckp.facets import Facet
from engine.uckp.law import ROOT_LAW

#: Identifiers of the vocabularies Layer Zero seeds.
KNOWLEDGE_KIND = "uckp.knowledge-kind"
AUTHORITY_TIER = "uckp.authority-tier"
LIFECYCLE_STAGE = "uckp.lifecycle-stage"
RELATION_TYPE = "uckp.relation-type"
RELATIONSHIP_CLASS = "uckp.relationship-class"
FACET_VOCABULARY = "uckp.facet"
GOVERNED_CATEGORY = "uckp.governed-category"
NON_AUTHORITATIVE_CATEGORY = "uckp.non-authoritative-category"


@dataclass(frozen=True, slots=True)
class Term:
    """One admissible member of a vocabulary."""

    term_id: str
    definition: str
    rank: int = 0
    successors: tuple[str, ...] = ()
    symmetric: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "term_id": self.term_id,
            "definition": self.definition,
            "rank": self.rank,
            "successors": list(self.successors),
            "symmetric": self.symmetric,
        }


@dataclass(frozen=True, slots=True)
class Vocabulary:
    """An append-only, self-describing set of admissible terms."""

    vocabulary_id: str
    purpose: str
    terms: tuple[Term, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for term in self.terms:
            if term.term_id in seen:
                raise LawViolation(
                    "vocabulary term declared twice",
                    vocabulary_id=self.vocabulary_id,
                    term_id=term.term_id,
                )
            seen.add(term.term_id)

    def term_ids(self) -> tuple[str, ...]:
        return tuple(sorted(term.term_id for term in self.terms))

    def has(self, term_id: str) -> bool:
        return any(term.term_id == str(term_id) for term in self.terms)

    def get(self, term_id: str) -> Term | None:
        for term in self.terms:
            if term.term_id == str(term_id):
                return term
        return None

    def require(self, term_id: str) -> Term:
        """Return the term, or fail closed. Openness is register-then-use."""
        term = self.get(term_id)
        if term is None:
            raise LawViolation(
                "term is not registered in this vocabulary",
                vocabulary_id=self.vocabulary_id,
                term_id=str(term_id),
            )
        return term

    def extended_with(self, term: Term) -> Vocabulary:
        """Return a new vocabulary containing ``term`` (append-only)."""
        existing = self.get(term.term_id)
        if existing is not None:
            if existing == term:
                return self
            raise LawViolation(
                "a registered term may not be redefined",
                vocabulary_id=self.vocabulary_id,
                term_id=term.term_id,
            )
        ordered = tuple(sorted((*self.terms, term), key=lambda item: item.term_id))
        return Vocabulary(self.vocabulary_id, self.purpose, ordered)

    def can_transition(self, source: str, target: str) -> bool:
        """True iff ``target`` is a declared successor of ``source``."""
        return str(target) in self.require(source).successors

    def to_dict(self) -> dict[str, object]:
        return {
            "vocabulary_id": self.vocabulary_id,
            "purpose": self.purpose,
            "terms": [term.to_dict() for term in sorted(self.terms, key=lambda t: t.term_id)],
        }

    def digest(self) -> str:
        return content_hash(self.to_dict())


class VocabularyRegistry:
    """The registry of every vocabulary in the Constitutional Knowledge Universe."""

    __slots__ = ("_vocabularies",)

    def __init__(self, vocabularies: Iterable[Vocabulary] = ()) -> None:
        self._vocabularies: dict[str, Vocabulary] = {}
        for vocabulary in vocabularies:
            self.register(vocabulary)

    def register(self, vocabulary: Vocabulary) -> Vocabulary:
        if vocabulary.vocabulary_id in self._vocabularies:
            raise LawViolation(
                "vocabulary already registered",
                vocabulary_id=vocabulary.vocabulary_id,
            )
        self._vocabularies[vocabulary.vocabulary_id] = vocabulary
        return vocabulary

    def extend(self, vocabulary_id: str, term: Term) -> Vocabulary:
        """Admit a previously unknown term. This is the *only* extension mechanism."""
        vocabulary = self.require(vocabulary_id)
        extended = vocabulary.extended_with(term)
        self._vocabularies[vocabulary_id] = extended
        return extended

    def get(self, vocabulary_id: str) -> Vocabulary | None:
        return self._vocabularies.get(str(vocabulary_id))

    def require(self, vocabulary_id: str) -> Vocabulary:
        vocabulary = self.get(vocabulary_id)
        if vocabulary is None:
            raise LawViolation("no such vocabulary", vocabulary_id=str(vocabulary_id))
        return vocabulary

    def require_term(self, vocabulary_id: str, term_id: str) -> Term:
        return self.require(vocabulary_id).require(term_id)

    def vocabulary_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._vocabularies))

    def is_extensible(self) -> bool:
        """True iff every vocabulary admits an unregistered future member.

        Article 17 is proved, not asserted: a probe term is admitted into a copy of
        each vocabulary. If any vocabulary refused, the universe would be closed to
        the future and :data:`engine.uckp.law.UCKP_INVARIANTS` INV-14 must fail.
        """
        probe = Term("uckp.future-probe", "an as-yet-unknown future member")
        for vocabulary in self._vocabularies.values():
            extended = vocabulary.extended_with(probe)
            if not extended.has(probe.term_id):
                return False
        return True

    def to_document(self) -> dict[str, object]:
        return {
            "schema": "ucos-uckp-vocabularies",
            "version": "1.0.0",
            "count": len(self._vocabularies),
            "vocabularies": [self._vocabularies[key].to_dict() for key in self.vocabulary_ids()],
        }

    def digest(self) -> str:
        return content_hash(self.to_document())


def _terms(pairs: Mapping[str, str]) -> tuple[Term, ...]:
    return tuple(Term(key, pairs[key]) for key in sorted(pairs))


KNOWLEDGE_KIND_VOCABULARY = Vocabulary(
    KNOWLEDGE_KIND,
    "what a canonical object is",
    _terms(
        {
            "anti-pattern": "a construction known to be harmful",
            "best-practice": "a recommended construction",
            "constraint": "a condition that must always hold",
            "convention": "an agreed form with no force of law",
            "decision": "a chosen architecture with rationale and rejected options",
            "evidence": "an observation supporting a claim",
            "example": "an instance illustrating a rule",
            "exception": "a bounded, justified departure from a rule",
            "fact": "an observed, verifiable statement",
            "guideline": "non-binding guidance",
            "law": "a supreme, non-derogable rule",
            "pattern": "a reusable construction",
            "policy": "an enforceable rule of use",
            "principle": "a foundational commitment from which rules derive",
            "rationale": "the reasoning that justifies a decision",
            "reference": "a pointer to knowledge held elsewhere",
            "rule": "a binding, checkable requirement",
            "standard": "a normative specification",
        }
    ),
)

AUTHORITY_TIER_VOCABULARY = Vocabulary(
    AUTHORITY_TIER,
    "the force a statement carries; rank 0 outranks all",
    (
        Term("constitutional", "supreme; nothing may contradict it", rank=0),
        Term("architectural", "binding on all implementations", rank=1),
        Term("engineering", "binding on an implementation", rank=2),
        Term("advisory", "informative only", rank=3),
    ),
)

LIFECYCLE_STAGE_VOCABULARY = Vocabulary(
    LIFECYCLE_STAGE,
    "the stage of existence of an object, with its lawful successors",
    (
        Term("draft", "authored, not yet reviewed", successors=("review", "archived")),
        Term("review", "under review", successors=("approved", "draft", "archived")),
        Term(
            "approved", "accepted, not yet ratified", successors=("ratified", "review", "archived")
        ),
        Term(
            "ratified",
            "in constitutional force",
            successors=("implemented", "deprecated", "superseded"),
        ),
        Term(
            "implemented",
            "realised in an execution environment",
            successors=("operational", "deprecated", "superseded"),
        ),
        Term(
            "operational",
            "in service",
            successors=("deprecated", "superseded"),
        ),
        Term("deprecated", "discouraged, still resolvable", successors=("superseded", "archived")),
        Term("superseded", "replaced by a successor object", successors=("archived",)),
        Term("archived", "withdrawn from service, still replayable", successors=("historical",)),
        Term("historical", "terminal; retained for replay only"),
    ),
)

RELATION_TYPE_VOCABULARY = Vocabulary(
    RELATION_TYPE,
    "how one object is bound to another",
    (
        Term("conflicts-with", "mutually unsatisfiable with", symmetric=True),
        Term("consumes", "reads or depends on the output of"),
        Term("certifies", "attests to the completeness of"),
        Term("depends-on", "cannot exist without"),
        Term("derived-from", "computed from"),
        Term("equivalent-to", "the same knowledge as", symmetric=True),
        Term("extends", "adds to without contradicting"),
        Term("generated-from", "projected from"),
        Term("governs", "holds decision authority over"),
        Term("implements", "realises"),
        Term("inherits", "takes the properties of"),
        Term("owns", "is accountable for"),
        Term("produces", "creates"),
        Term("references", "points at"),
        Term("related-to", "associated with", symmetric=True),
        Term("supersedes", "replaces"),
        Term("validates", "checks the shape of"),
    ),
)

RELATIONSHIP_CLASS_VOCABULARY = Vocabulary(
    RELATIONSHIP_CLASS,
    "the constitutional register a relationship belongs to",
    _terms(
        {
            "authority": "from whom the right to exist is derived",
            "constitutional": "binding under the root law",
            "evolution": "how the object changed between states",
            "future": "an intended, not-yet-realised binding",
            "governance": "who decides about the object",
            "historical": "a binding that held in a prior state",
            "knowledge": "what the object knows or is known by",
            "ownership": "who is accountable",
            "runtime": "which execution environment acts on it",
            "semantic": "what it means in relation to another meaning",
            "traceability": "upstream intent and downstream effect",
            "validation": "what checks it and what it checks",
        }
    ),
)

FACET_VOCABULARY_INSTANCE = Vocabulary(
    FACET_VOCABULARY,
    "the questions every object must be able to answer",
    tuple(Term(facet.value, facet.question) for facet in Facet),
)

GOVERNED_CATEGORY_VOCABULARY = Vocabulary(
    GOVERNED_CATEGORY,
    "categories of entity that must exist as a canonical object (Article 2)",
    tuple(
        Term(category, "shall exist exactly once as a UCKO")
        for category in ROOT_LAW.governed_categories
    ),
)

NON_AUTHORITATIVE_CATEGORY_VOCABULARY = Vocabulary(
    NON_AUTHORITATIVE_CATEGORY,
    "categories that may only ever be a view of a canonical object (Article 4)",
    tuple(
        Term(category, "holds no independent architectural authority")
        for category in ROOT_LAW.non_authoritative_categories
    ),
)


def build_vocabulary_registry() -> VocabularyRegistry:
    """Return a fresh registry seeded with the Layer Zero vocabularies."""
    return VocabularyRegistry(
        (
            KNOWLEDGE_KIND_VOCABULARY,
            AUTHORITY_TIER_VOCABULARY,
            LIFECYCLE_STAGE_VOCABULARY,
            RELATION_TYPE_VOCABULARY,
            RELATIONSHIP_CLASS_VOCABULARY,
            FACET_VOCABULARY_INSTANCE,
            GOVERNED_CATEGORY_VOCABULARY,
            NON_AUTHORITATIVE_CATEGORY_VOCABULARY,
        )
    )


#: The process-wide default vocabularies. Callers that need to admit a term
#: without affecting the whole universe build their own registry instead.
DEFAULT_VOCABULARIES = build_vocabulary_registry()


__all__ = [
    "AUTHORITY_TIER",
    "AUTHORITY_TIER_VOCABULARY",
    "DEFAULT_VOCABULARIES",
    "FACET_VOCABULARY",
    "FACET_VOCABULARY_INSTANCE",
    "GOVERNED_CATEGORY",
    "GOVERNED_CATEGORY_VOCABULARY",
    "KNOWLEDGE_KIND",
    "KNOWLEDGE_KIND_VOCABULARY",
    "LIFECYCLE_STAGE",
    "LIFECYCLE_STAGE_VOCABULARY",
    "NON_AUTHORITATIVE_CATEGORY",
    "NON_AUTHORITATIVE_CATEGORY_VOCABULARY",
    "RELATIONSHIP_CLASS",
    "RELATIONSHIP_CLASS_VOCABULARY",
    "RELATION_TYPE",
    "RELATION_TYPE_VOCABULARY",
    "Term",
    "Vocabulary",
    "VocabularyRegistry",
    "build_vocabulary_registry",
]
