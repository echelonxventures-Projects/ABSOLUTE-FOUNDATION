"""UKDA Part 04/09 — Canonical home resolution (declared ownership only).

Resolves, for every constitutional concept, the single **registered repository artifact**
that owns it — and does so *only* where Repository Truth actually declares the
ownership. Where no declaration exists the concept is reported unresolved, with a
reason. Nothing is inferred.

Why this module refuses to infer
--------------------------------
``00-MASTER/UAKOS-CLOSURE-002/closure_engine.py`` measures a *definitional* home by one
rule: a truth-root file whose **basename carries the concept identity**. That rule is
correct and is reused verbatim here. But 304 of the repository's 447 concepts are
sub-identifiers — meta-class criteria, band units, laws, principles — declared inside an
aggregate instrument rather than given a file of their own, so the closure rule yields
nothing and the requirement layer records ownership as ``INFERRED``.

The obvious temptation is to close that gap by pattern-matching: treat the artifact that
tabulates ``AMC-01`` in a definition table, or names it in a heading, or merely cites it,
as its owner. **That was measured and rejected.** Across the 447 concepts such rules
assign a *derived report* as owner wherever one happens to tabulate the identifier —
``DATA-027`` and ``ARCH-EVENT-001`` both resolve to a readiness matrix, ``EC3-B10-U01``
to another unit's completion report, and ``Ω∞-001`` to
``01-WORKING/LAW-REGISTER.md``, which
``02-MASTER/UAKOS-CL003-W1-UNIVERSAL-LAW-CANONICAL-HOMING-DETERMINATION.md`` expressly
excludes as *"operational memory, excluded from Repository Truth"*. No rule over file
content and registration alone separates a definitional owner from a report that
tabulates the same identifier, because that distinction is a governance classification
the repository does not yet carry for these concepts — which is precisely the gap being
measured.

``CEP-002`` Article 14.2 settles it: *"Ownership SHALL be assigned by governed
determination and SHALL NEVER be implied."* A heuristic home *is* implied ownership.
This module therefore reads declarations and refuses to manufacture them; the residue it
reports is work for a Governance Authority determination, not for a regular expression.

What counts as a declaration
----------------------------
Two, both of them statements the repository makes about itself
(:data:`DECLARATION_RULES`):

``D1-DEFINITIONAL-BASENAME``
    The concept's own ``def_homes`` / ``exact_homes`` as measured by the closure engine —
    the artifact's *filename* carries the identity. Reused, not recomputed.

``D2-DECLARED-ARTIFACT-ID``
    The artifact's front-matter identity row (``| ARTIFACT ID | … |``, or the equivalent
    label in :data:`ARTIFACT_ID_LABELS`) states the concept id **exactly**. This is the
    artifact declaring, in its own words, which concept it is. A suffixed value such as
    ``UCOS-COMP-000000-GIG`` declares a *different* identity and therefore does not claim
    the concept — which is exactly how the repository already distinguishes the
    Constitutional Implementation Orchestration Authority from its Global Implementation
    Graph Determination.

Eligibility
-----------
``CEP-002`` Article 14.1 requires the canonical owner to be *"registered in the
Governance Registry"*, so registration is the eligibility test — read from
``00-BOOK/DATA/artifacts.json``, never re-implemented. That projection is produced by
``00-BOOK/tools/register.sh`` applying ``00-BOOK/tools/config.py``, and it already
excludes ``00-MASTER/**``, which ``config.py`` declares Operational Memory under
``UCOS-RECON-C1`` — *"execution state, not corpus"*. The enumerating programme registers
are therefore ineligible by the repository's own configuration, not by any judgement
made here.

Contests
--------
Where more than one eligible artifact declares the same concept the concept is
*contested*. ``CEP-002`` 14.3 requires the contest to be *"logged and the superseded
claim recorded, never silently discarded"*, and 14.4 requires the prior owner preserved
in lineage — so every losing claim is retained in the result. Precedence is read, not
invented: a claimant the repository classifies into the implementation category
(:data:`REALIZATION_CATEGORY`) is a *realization* of the concept rather than its
definition, so a definitional claimant outranks it. A contest that this does not settle
is reported **unresolved**, never broken by a tiebreaker of this module's own devising.

Fail-closed
-----------
Unresolved concepts keep the gate red. That is required by ``CMG-000001`` IX.6 /
``CMG-P-06`` — *"A missing superior authority is recorded, not assumed."*

Standing
--------
Tier T1 is VACANT (``VAC-01`` / ``CMG-OQ-02`` / ``UCCEP-F-004``), so ``CMG-L-12`` caps
any determination built on this evidence at :data:`STANDING_CEILING` — *"Where no such
authority exists, the standing IS PROVISIONAL."* The ceiling is carried in the output so
no consumer can present the result as ratified.

Determinism
-----------
Every input is read as data; nothing is minted from a counter or a clock and no
wall-clock value is recorded (IMP-007 §5). Ordering is total and content-derived, so the
same repository always yields byte-identical output. Standard library only (TP-04/TP-05).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engine.knowledge.errors import KnowledgeSourceError, KnowledgeValidationError

#: Concept truth: the measured closure of every constitutional concept. Read as DATA —
#: this module never re-extracts concepts and never redefines a definitional home.
DEFAULT_CLOSURE_PATH = "00-MASTER/UAKOS-CLOSURE-002/closure.json"

#: The Governance Registry projection that makes an artifact eligible to own a concept
#: (``CEP-002`` 14.1). Membership here *is* the registration test.
DEFAULT_ARTIFACTS_PATH = "00-BOOK/DATA/artifacts.json"

#: Front-matter labels under which an artifact declares its own identity. Several
#: spellings are in use across the corpus; all are the same declaration.
ARTIFACT_ID_LABELS = ("ARTIFACT ID", "ARTIFACT IDENTIFIER", "ARTIFACT-ID")

#: Bytes of an artifact's head searched for the identity row. The declaration is
#: front-matter by convention, so an identifier mentioned deep in a body table cannot be
#: mistaken for a self-declaration.
HEAD_BYTES = 40000

#: Path segments that make a file derived evidence rather than a definitional artifact.
#: Mirrors ``closure_engine.DERIVED_SEG`` so the two measurements agree on what a home
#: can be; presence in one of these is evidence, never ownership.
DERIVED_SEGMENTS = (
    "_evidence/",
    "/outputs/",
    "outputs/",
    "determinism-evidence/",
    "CHECKPOINTS/",
    "/__pycache__/",
    ".egg-info/",
)

#: Only Markdown carries constitutional declarations; JSON projections are derived state.
HOME_SUFFIX = ".md"

#: The classification category the repository assigns to realization artifacts
#: (``config.py::CLASSIFY_RULES`` maps ``^06-IMPLEMENTATION/`` to it). A realization
#: implements a concept; it does not define it.
REALIZATION_CATEGORY = "IMP"

#: Repository-relative prefix of the realization zone, used to recognise a realization
#: claimant without importing the registration configuration into the engine layer.
REALIZATION_ZONE = "06-IMPLEMENTATION/"

#: Declaration rule identifiers, strongest first. Both are declarations the repository
#: makes about itself; there is deliberately no content-similarity rule.
DECLARATION_RULES: tuple[str, ...] = (
    "D1-DEFINITIONAL-BASENAME",
    "D2-DECLARED-ARTIFACT-ID",
)

#: Ownership standings this module reports, mirroring the requirement layer's vocabulary.
STANDING_DECLARED = "DECLARED"
STANDING_UNRESOLVED = "UNRESOLVED"

#: Reason codes for an unresolved concept. Each names a *different* deficit so the
#: residue can be triaged rather than treated as one undifferentiated failure.
REASON_NO_DECLARATION = "NO-REGISTERED-ARTIFACT-DECLARES-OWNERSHIP"
REASON_NO_EVIDENCE = "CONCEPT-HAS-NO-REPOSITORY-EVIDENCE"
REASON_UNSETTLED_CONTEST = "CONTEST-NOT-SETTLED-BY-DECLARED-PRECEDENCE"

#: Ceiling every determination built from this evidence inherits (``CMG-L-12``).
STANDING_CEILING = "PROVISIONAL"

_IDENTITY_ROW = re.compile(
    r"^\|\s*(?:\*\*)?\s*(" + "|".join(re.escape(x) for x in ARTIFACT_ID_LABELS) + r")"
    r"\s*(?:\*\*)?\s*\|\s*(.+?)\s*\|\s*$",
    re.M | re.I,
)


def declared_identity(text: str) -> str:
    """The concept identity an artifact declares about itself, or ``""``.

    Reads the first front-matter identity row. The value is returned verbatim apart from
    stripping Markdown emphasis, so a suffixed identity stays distinct from the bare one.
    """
    match = _IDENTITY_ROW.search(text[:HEAD_BYTES])
    if not match:
        return ""
    return match.group(2).strip().strip("`*_ ")


@dataclass(frozen=True, slots=True)
class ConceptRecord:
    """One constitutional concept, as measured by the closure engine."""

    concept_id: str
    family: str
    evidence_files: tuple[str, ...]
    definitional_homes: tuple[str, ...]
    exact_homes: tuple[str, ...]
    zones: tuple[str, ...]

    @classmethod
    def from_dict(cls, record: Mapping[str, Any]) -> ConceptRecord:
        if not isinstance(record, Mapping):
            raise KnowledgeValidationError("concept record must be an object")
        concept_id = str(record.get("id") or "").strip()
        if not concept_id:
            raise KnowledgeValidationError("concept record has an empty id")
        return cls(
            concept_id=concept_id,
            family=str(record.get("family") or "UNCLASSIFIED"),
            evidence_files=tuple(sorted(str(f) for f in (record.get("files") or ()))),
            definitional_homes=tuple(sorted(str(f) for f in (record.get("def_homes") or ()))),
            exact_homes=tuple(sorted(str(f) for f in (record.get("exact_homes") or ()))),
            zones=tuple(sorted(str(z) for z in (record.get("tops") or ()))),
        )


@dataclass(frozen=True, slots=True)
class RegisteredCorpus:
    """The registered repository artifacts eligible to own a concept (``CEP-002`` 14.1)."""

    universal_id: Mapping[str, str]
    category: Mapping[str, str]

    def is_eligible(self, path: str) -> bool:
        """True iff ``path`` is a registered, non-derived Markdown artifact."""
        return (
            path in self.universal_id
            and path.endswith(HOME_SUFFIX)
            and not any(segment in path for segment in DERIVED_SEGMENTS)
        )

    def is_realization(self, path: str) -> bool:
        """True iff the repository classifies ``path`` as a realization, not a definition."""
        return self.category.get(path) == REALIZATION_CATEGORY or path.startswith(REALIZATION_ZONE)


@dataclass(frozen=True, slots=True)
class ConceptHoming:
    """The resolved canonical home of one concept, with its contest fully recorded."""

    concept_id: str
    family: str
    standing: str
    home: str = ""
    rule: str = ""
    superseded: tuple[str, ...] = ()
    reason: str = ""

    @property
    def contested(self) -> bool:
        """True iff more than one artifact claimed this concept."""
        return bool(self.superseded)

    @property
    def resolved(self) -> bool:
        """True iff exactly one canonical home was determined from a declaration."""
        return self.standing == STANDING_DECLARED

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "concept_id": self.concept_id,
            "family": self.family,
            "standing": self.standing,
        }
        if self.home:
            payload["canonical_home"] = self.home
        if self.rule:
            payload["declaration_rule"] = self.rule
        if self.superseded:
            payload["superseded_claims"] = list(self.superseded)
        if self.reason:
            payload["reason"] = self.reason
        return payload


@dataclass(frozen=True, slots=True)
class HomingDetermination:
    """The declared-ownership evidence for every concept, and the unresolved residue."""

    homings: tuple[ConceptHoming, ...]
    standing_ceiling: str = STANDING_CEILING
    inputs: Mapping[str, str] = field(default_factory=dict)

    @property
    def declared(self) -> tuple[ConceptHoming, ...]:
        """Concepts whose ownership Repository Truth declares."""
        return tuple(h for h in self.homings if h.resolved)

    @property
    def unresolved(self) -> tuple[ConceptHoming, ...]:
        """Concepts Repository Truth does not answer — the fail-closed residue."""
        return tuple(h for h in self.homings if not h.resolved)

    @property
    def contested(self) -> tuple[ConceptHoming, ...]:
        """Concepts more than one artifact claimed (``CEP-002`` 14.3 logging duty)."""
        return tuple(h for h in self.homings if h.contested)

    @property
    def closed(self) -> bool:
        """True iff every concept carries exactly one declared canonical home."""
        return not self.unresolved

    def counts(self) -> dict[str, int]:
        return {
            "concepts": len(self.homings),
            "declared": len(self.declared),
            "unresolved": len(self.unresolved),
            "contested": len(self.contested),
        }

    def by_rule(self) -> dict[str, int]:
        """How many concepts each declaration rule resolved, in rule order."""
        tally = dict.fromkeys(DECLARATION_RULES, 0)
        for homing in self.declared:
            if homing.rule in tally:
                tally[homing.rule] += 1
        return tally

    def unresolved_by_reason(self) -> dict[str, list[str]]:
        """The residue grouped by deficit, so it can be triaged rather than lumped."""
        grouped: dict[str, list[str]] = {}
        for homing in self.unresolved:
            grouped.setdefault(homing.reason, []).append(homing.concept_id)
        return {reason: sorted(ids) for reason, ids in sorted(grouped.items())}

    def to_dict(self) -> dict[str, Any]:
        return {
            "inputs": dict(self.inputs),
            "standing_ceiling": self.standing_ceiling,
            "counts": self.counts(),
            "declared_by_rule": self.by_rule(),
            "unresolved_by_reason": self.unresolved_by_reason(),
            "contests": [h.to_dict() for h in self.contested],
            "homings": [h.to_dict() for h in self.homings],
        }


def _read_json(path: str | Path, *, what: str) -> Mapping[str, Any]:
    resolved = Path(path)
    if not resolved.is_file():
        raise KnowledgeSourceError(f"{what} not found", path=str(resolved))
    try:
        document = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise KnowledgeSourceError(
            f"{what} is not valid JSON", path=str(resolved), detail=str(exc)
        ) from exc
    if not isinstance(document, Mapping):
        raise KnowledgeSourceError(f"{what} root must be an object", path=str(resolved))
    return document


def load_concepts(path: str | Path = DEFAULT_CLOSURE_PATH) -> tuple[ConceptRecord, ...]:
    """Load measured concept truth, in stable concept-id order."""
    document = _read_json(path, what="concept closure")
    records = document.get("concepts")
    if not isinstance(records, list):
        raise KnowledgeSourceError("concept closure is missing its concepts array", path=str(path))
    parsed = [ConceptRecord.from_dict(record) for record in records]
    seen: set[str] = set()
    for record in parsed:
        if record.concept_id in seen:
            raise KnowledgeValidationError(
                "concept measured more than once", concept_id=record.concept_id
            )
        seen.add(record.concept_id)
    return tuple(sorted(parsed, key=lambda r: r.concept_id))


def load_registered_corpus(
    artifacts_path: str | Path = DEFAULT_ARTIFACTS_PATH,
) -> RegisteredCorpus:
    """Load the registered artifacts eligible to own a concept, with their categories."""
    document = _read_json(artifacts_path, what="artifact register")
    artifacts = document.get("artifacts")
    if not isinstance(artifacts, list):
        raise KnowledgeSourceError(
            "artifact register is missing its artifacts array", path=str(artifacts_path)
        )
    universal_id: dict[str, str] = {}
    category: dict[str, str] = {}
    for artifact in artifacts:
        if not isinstance(artifact, Mapping):
            raise KnowledgeValidationError("artifact record must be an object")
        path = str(artifact.get("path") or "").strip()
        uid = str(artifact.get("universal_id") or "").strip()
        if not path or not uid:
            continue
        universal_id[path] = uid
        category[path] = str(artifact.get("category") or "")
    if not universal_id:
        raise KnowledgeSourceError(
            "artifact register declares no registered artifact", path=str(artifacts_path)
        )
    return RegisteredCorpus(universal_id=universal_id, category=category)


def _ok(path: str, corpus: RegisteredCorpus) -> bool:
    """True iff ``path`` may own a concept (``CEP-002`` 14.1 registration test)."""
    return corpus.is_eligible(path)


def _settle(claims: Sequence[str], corpus: RegisteredCorpus) -> tuple[str, tuple[str, ...]] | None:
    """Settle a contest by declared precedence, or ``None`` if it is not settled.

    A definitional claimant outranks a realization claimant (``CEP-002`` 14.3). Losing
    claims are returned so they can be recorded, never discarded (14.3/14.4). A contest
    among peers is deliberately left unsettled rather than broken arbitrarily.
    """
    ordered = sorted(set(claims))
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0], ()
    definitional = [c for c in ordered if not corpus.is_realization(c)]
    if len(definitional) == 1:
        winner = definitional[0]
        return winner, tuple(c for c in ordered if c != winner)
    return None


def _resolve_one(
    concept: ConceptRecord,
    corpus: RegisteredCorpus,
    read_text: Any,
) -> ConceptHoming:
    """Resolve one concept's canonical home from declarations only.

    Rules are consulted strongest first, but a rule that yields an *ambiguous* answer does
    not end the search: a weaker rule that yields a decisive declaration settles what the
    stronger one could not. That is the ``UCOS-COMP-000000`` shape — four artifacts carry
    the identity in their basename, and exactly one declares that identity as its own —
    and it is resolution by declared evidence, which is what ``CEP-002`` 14.3 requires.
    Only if no rule settles is the concept reported unresolved, carrying every claim seen.
    """

    def homing(**kwargs: Any) -> ConceptHoming:
        return ConceptHoming(concept_id=concept.concept_id, family=concept.family, **kwargs)

    # D1 — the closure engine's own measurement: the artifact's basename carries the
    # identity. An exact basename match is a stronger declaration than a prefix match.
    # D2 — the artifact declares this concept as its own identity, in its own words.
    def declares_identity() -> list[str]:
        return sorted(
            {
                path
                for path in concept.evidence_files
                if corpus.is_eligible(path)
                and declared_identity(read_text(path)) == concept.concept_id
            }
        )

    ladder: tuple[tuple[str, Any], ...] = (
        ("D1-DEFINITIONAL-BASENAME", lambda: [c for c in concept.exact_homes if _ok(c, corpus)]),
        (
            "D1-DEFINITIONAL-BASENAME",
            lambda: [c for c in concept.definitional_homes if _ok(c, corpus)],
        ),
        ("D2-DECLARED-ARTIFACT-ID", declares_identity),
    )

    unsettled: set[str] = set()
    for rule_name, gather in ladder:
        claims = gather()
        if not claims:
            continue
        settled = _settle(claims, corpus)
        if settled:
            home, superseded = settled
            return homing(
                standing=STANDING_DECLARED,
                home=home,
                rule=rule_name,
                superseded=superseded,
            )
        unsettled.update(claims)

    if unsettled:
        return homing(
            standing=STANDING_UNRESOLVED,
            reason=REASON_UNSETTLED_CONTEST,
            superseded=tuple(sorted(unsettled)),
        )

    return homing(
        standing=STANDING_UNRESOLVED,
        reason=REASON_NO_EVIDENCE if not concept.evidence_files else REASON_NO_DECLARATION,
    )


def derive_homing(
    concepts: Sequence[ConceptRecord],
    corpus: RegisteredCorpus,
    *,
    repo_root: str | Path = ".",
    inputs: Mapping[str, str] | None = None,
) -> HomingDetermination:
    """Resolve every concept's canonical home from declared ownership only.

    Reads each candidate artifact at most once. Nothing is written, and no concept is
    assigned a home the repository does not declare.
    """
    root = Path(repo_root)
    cache: dict[str, str] = {}

    def read_text(rel: str) -> str:
        if rel not in cache:
            try:
                cache[rel] = (root / rel).read_text(encoding="utf-8", errors="replace")
            except OSError:
                cache[rel] = ""
        return cache[rel]

    homings = tuple(
        _resolve_one(concept, corpus, read_text)
        for concept in sorted(concepts, key=lambda c: c.concept_id)
    )
    return HomingDetermination(homings=homings, inputs=dict(inputs or {}))


def homing_index(determination: HomingDetermination) -> dict[str, str]:
    """Concept id → declared canonical home, for every resolved concept."""
    return {h.concept_id: h.home for h in determination.declared}


def families(homings: Iterable[ConceptHoming]) -> dict[str, int]:
    """Concept counts by family for an arbitrary subset, in descending count order."""
    tally: dict[str, int] = {}
    for homing in homings:
        tally[homing.family] = tally.get(homing.family, 0) + 1
    return dict(sorted(tally.items(), key=lambda kv: (-kv[1], kv[0])))


__all__ = [
    "ARTIFACT_ID_LABELS",
    "DECLARATION_RULES",
    "DEFAULT_ARTIFACTS_PATH",
    "DEFAULT_CLOSURE_PATH",
    "DERIVED_SEGMENTS",
    "REALIZATION_CATEGORY",
    "REASON_NO_DECLARATION",
    "REASON_NO_EVIDENCE",
    "REASON_UNSETTLED_CONTEST",
    "STANDING_CEILING",
    "STANDING_DECLARED",
    "STANDING_UNRESOLVED",
    "ConceptHoming",
    "ConceptRecord",
    "HomingDetermination",
    "RegisteredCorpus",
    "declared_identity",
    "derive_homing",
    "families",
    "homing_index",
    "load_concepts",
    "load_registered_corpus",
]
