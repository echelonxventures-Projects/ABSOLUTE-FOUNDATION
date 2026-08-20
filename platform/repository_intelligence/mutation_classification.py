"""EX-016 — the executable classifier for the mutation governance boundary.

``00-BOOK/DATA/mutation-governance-boundary.json`` declares seven ordered classification
rules and a fail-closed terminal. EX-015 made those rules *declarative*; this module makes
them *decidable*. Until a rule is evaluated it is prose, and prose is what let
``uisd-declaration.json`` be authored, owned, engine-consumed and unclassified while six of
its mutations were certified.

THE RULES ARE DATA, NOT CODE. This module contains no rule text, no class name ordering and
no predicate the register does not declare. It loads ``classification_rules.rules``, and
:func:`validate_rule_coverage` refuses **both** directions — a declared rule with no
implemented predicate cannot be evaluated, and an implemented predicate no rule declares is
dead code wearing the appearance of enforcement. That is the same two-sided construction
``engine.infinite_scope.contract.LAW_CHECKS`` and ``ADMISSION_FORMS`` already use.

UNRESOLVED IS NOT A CLASS. It is the declared terminal, it confers no authority, and it must
never be read as a permissive default — a default would silently grant an authority no owner
claimed, which is exactly how CORPUS_REGISTRATION and GOVERNED_DECLARATION each came to be
missing. Consumers that gate on classification MUST treat it as failure.

DETERMINISM. Every predicate is a pure function of ``(subject, Repository)``. The repository
view is built once, from ``git ls-files`` and the registers, and is then immutable: no clock,
no environment, no filesystem traversal order and no dependence on the order in which
subjects are presented.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from platform.repository_intelligence import generated_artifacts

#: A Python string literal. Used to index what the corpus names, never to parse code.
_LITERAL = re.compile(r"""["']([^"'\n]{1,300})["']""")

BOUNDARY_PATH = "00-BOOK/DATA/mutation-governance-boundary.json"

#: Statuses a classification may carry. UNRESOLVED and ERROR are diagnostic; only
#: CLASSIFIED carries a mutation class.
CLASSIFIED = "CLASSIFIED"
UNRESOLVED = "UNRESOLVED"
ERROR = "ERROR"

#: Subject kinds. Most mutation subjects are paths; CONSTITUTIONAL_TRUTH's are not — its
#: subjects are Population and ConstitutionalMetadata objects reached through the gateway.
#: The register states this in ``$subject_domain``; the classifier honours it rather than
#: assuming every subject is a file.
PATH = "PATH"
OBJECT = "OBJECT"

_EXCLUSION_INSTRUMENTS = frozenset({".gitignore", "00-BOOK/DATA/exclusion-register.json"})
_CORPUS_REGISTERS = frozenset({"00-BOOK/DATA/id-ledger.json", "00-BOOK/DATA/artifacts.json"})
_CONSTITUTIONAL_OBJECT_TYPES = frozenset({"Population", "ConstitutionalMetadata"})
_EXECUTABLE_SUFFIXES = frozenset({".py", ".sh"})
_BUILD_MANIFESTS = frozenset({"pyproject.toml"})
_DECLARATION_KEYS = frozenset(
    {"programme", "manifest", "authority", "laws", "expansion_axes", "determination"}
)


class ClassificationError(RuntimeError):
    """The boundary register could not be read or is unusable. A FAULT, never a verdict."""


@dataclass(frozen=True, slots=True)
class Subject:
    """One mutation subject: a repository path, or a constitutional object."""

    identity: str
    kind: str = PATH
    object_type: str = ""

    @classmethod
    def of_path(cls, path: str) -> Subject:
        return cls(identity=str(path).replace("\\", "/"), kind=PATH)

    @classmethod
    def of_object(cls, identity: str, object_type: str) -> Subject:
        return cls(identity=identity, kind=OBJECT, object_type=object_type)


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    """Exactly one outcome per subject. ``mutation_class`` is empty unless CLASSIFIED."""

    artifact: str
    mutation_class: str
    rule_id: str
    authority: str
    status: str
    reason: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact": self.artifact,
            "mutation_class": self.mutation_class,
            "rule_id": self.rule_id,
            "authority": self.authority,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass
class Repository:
    """An immutable view of one repository state. Built once, reused for every subject."""

    root: Path
    _overrides: dict[str, object] = field(default_factory=dict, repr=False)

    @cached_property
    def tracked(self) -> frozenset[str]:
        if "tracked" in self._overrides:
            return frozenset(self._overrides["tracked"])  # type: ignore[arg-type]
        out = subprocess.run(  # noqa: S603
            ["git", "ls-files"],  # noqa: S607
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        return frozenset(line for line in out.stdout.splitlines() if line)

    @cached_property
    def generated(self) -> frozenset[str]:
        if "generated" in self._overrides:
            return frozenset(self._overrides["generated"])  # type: ignore[arg-type]
        return frozenset(generated_artifacts.canonical_paths(self.root))

    @cached_property
    def producer_homes(self) -> frozenset[str]:
        """The declared producer module homes. A producer is not a declaration."""
        if "producer_homes" in self._overrides:
            return frozenset(self._overrides["producer_homes"])  # type: ignore[arg-type]
        return frozenset(h.home for h in generated_artifacts.producer_homes(self.root) if h.home)

    @cached_property
    def _consumed_literals(self) -> frozenset[str]:
        """Every string literal appearing in tracked Python source, indexed once.

        A set, not a concatenated blob: the predicate is asked once per tracked subject, and
        substring-scanning the whole corpus per subject is quadratic in repository size — a
        classifier the corpus gate cannot afford to run is a classifier that will not be run.
        """
        if "python_corpus" in self._overrides:
            blob = str(self._overrides["python_corpus"])
            return frozenset(_LITERAL.findall(blob))
        literals: set[str] = set()
        for rel in sorted(p for p in self.tracked if p.endswith(".py")):
            try:
                text = (self.root / rel).read_text(encoding="utf-8", errors="replace")
            except OSError:  # pragma: no cover - a file vanishing mid-scan
                continue
            literals.update(_LITERAL.findall(text))
        return frozenset(literals)

    def is_consumed_by_an_engine(self, path: str) -> bool:
        """True iff some tracked Python source names this artifact as a literal.

        Full path or basename: a consumer may assemble the path from segments, which is what
        ``engine/constitution/stages.py`` does for the UCL manifest, so the basename is the
        only literal present. Both forms are decidable and deterministic.
        """
        basename = path.rsplit("/", 1)[-1]
        return path in self._consumed_literals or basename in self._consumed_literals

    def declaration_document(self, path: str) -> dict | None:
        """The artifact parsed as a JSON object, or None when it is not one."""
        if not path.endswith(".json"):
            return None
        try:
            loaded = json.loads((self.root / path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return loaded if isinstance(loaded, dict) else None


def load_boundary(repo: Path) -> dict:
    """Load the boundary register, or fail closed."""
    try:
        doc = json.loads((repo / BOUNDARY_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClassificationError(f"{BOUNDARY_PATH} is absent or unreadable") from exc
    if not isinstance(doc, dict) or "classification_rules" not in doc:
        raise ClassificationError(f"{BOUNDARY_PATH} declares no classification_rules")
    return doc


def authority_for(boundary: dict, mutation_class: str) -> str:
    """The governing authority chain the register names for a class."""
    for entry in boundary.get("mutation_classes", []):
        if entry.get("class") == mutation_class:
            return str(entry.get("governed_by", ""))
    return ""


# --------------------------------------------------------------------- rule predicates
# Each returns True when its rule claims the subject. Signature is uniform so the evaluator
# never branches on rule identity.


def _r01_repository_state(subject: Subject, repo: Repository, boundary: dict) -> bool:
    if subject.kind is not PATH and subject.kind != PATH:
        return False
    path = subject.identity
    if path.startswith(".git/"):
        return True
    if path in _EXCLUSION_INSTRUMENTS or path in repo.tracked:
        return False
    return (repo.root / path).exists()


def _r02_exclusion(subject: Subject, repo: Repository, boundary: dict) -> bool:
    return subject.kind == PATH and subject.identity in _EXCLUSION_INSTRUMENTS


def _r03_corpus_registration(subject: Subject, repo: Repository, boundary: dict) -> bool:
    return subject.kind == PATH and subject.identity in _CORPUS_REGISTERS


def _r04_generated_artifact(subject: Subject, repo: Repository, boundary: dict) -> bool:
    return subject.kind == PATH and subject.identity in repo.generated


def _r05_constitutional_truth(subject: Subject, repo: Repository, boundary: dict) -> bool:
    """An OBJECT predicate. A path subject never satisfies it — the register says so."""
    return subject.kind == OBJECT and subject.object_type in _CONSTITUTIONAL_OBJECT_TYPES


def _r06_governed_declaration(subject: Subject, repo: Repository, boundary: dict) -> bool:
    """All seven declared membership criteria, evaluated. Examples are never consulted."""
    if subject.kind != PATH:
        return False
    path = subject.identity
    document = repo.declaration_document(path)
    checks = governed_declaration_checks(path, document, repo)
    return all(checks.values())


def governed_declaration_checks(
    path: str, document: dict | None, repo: Repository
) -> dict[str, bool]:
    """Each criterion, individually, so a refusal can name which one failed."""
    suffix = "." + path.rsplit(".", 1)[-1] if "." in path else ""
    return {
        "authored": path not in repo.producer_homes and not (document or {}).get("generated_at"),
        "repository-controlled": path in repo.tracked,
        "declaration-bearing": bool(document) and bool(_DECLARATION_KEYS & set(document or {})),
        "programme-owned": _owning_programme(path, document) != "",
        "engine-consumed": repo.is_consumed_by_an_engine(path),
        "non-generated": path not in repo.generated,
        "non-executable": suffix not in _EXECUTABLE_SUFFIXES,
    }


def _owning_programme(path: str, document: dict | None) -> str:
    """Exactly one owning programme, or the empty string. CEP-009 I.3 keeps it single."""
    doc = document or {}
    programme = doc.get("programme")
    if isinstance(programme, dict) and programme.get("id"):
        return str(programme["id"])
    for key in ("artifact_id", "id"):
        if isinstance(doc.get(key), str) and doc[key]:
            return str(doc[key])
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "00-MASTER":
        return parts[1]
    return ""


def _r07_source(subject: Subject, repo: Repository, boundary: dict) -> bool:
    if subject.kind != PATH:
        return False
    path = subject.identity
    suffix = "." + path.rsplit(".", 1)[-1] if "." in path else ""
    return suffix in _EXECUTABLE_SUFFIXES or path.rsplit("/", 1)[-1] in _BUILD_MANIFESTS


#: Rule id to predicate. Two-sided, exactly like LAW_CHECKS: a declared rule with no
#: predicate cannot be evaluated, and a predicate no rule declares is dead code.
RULE_PREDICATES: dict[str, Callable[[Subject, Repository, dict], bool]] = {
    "R-01": _r01_repository_state,
    "R-02": _r02_exclusion,
    "R-03": _r03_corpus_registration,
    "R-04": _r04_generated_artifact,
    "R-05": _r05_constitutional_truth,
    "R-06": _r06_governed_declaration,
    "R-07": _r07_source,
}


def validate_rule_coverage(boundary: dict) -> tuple[str, ...]:
    """Refuse in both directions. Empty means the register and this module agree."""
    declared = [str(r.get("id", "")) for r in boundary["classification_rules"]["rules"]]
    problems: list[str] = []
    for rule_id in declared:
        if rule_id not in RULE_PREDICATES:
            problems.append(f"rule {rule_id!r} is declared but no predicate implements it")
    for orphan in sorted(set(RULE_PREDICATES) - set(declared)):
        problems.append(f"predicate {orphan!r} is implemented but no rule declares it")
    return tuple(problems)


def classify(
    subject: Subject | str, repo: Repository, boundary: dict | None = None
) -> ClassificationResult:
    """Resolve one subject to exactly one outcome, in declared precedence order."""
    if isinstance(subject, str):
        subject = Subject.of_path(subject)
    try:
        doc = boundary if boundary is not None else load_boundary(repo.root)
    except ClassificationError as exc:
        return ClassificationResult(subject.identity, "", "", "", ERROR, str(exc))

    problems = validate_rule_coverage(doc)
    if problems:
        return ClassificationResult(subject.identity, "", "", "", ERROR, "; ".join(problems))

    for rule in doc["classification_rules"]["rules"]:
        rule_id = str(rule.get("id", ""))
        try:
            matched = RULE_PREDICATES[rule_id](subject, repo, doc)
        except Exception as exc:  # noqa: BLE001 - an unevaluable predicate is a FAULT
            return ClassificationResult(
                subject.identity, "", rule_id, "", ERROR, f"{type(exc).__name__}: {exc}"
            )
        if matched:
            mutation_class = str(rule.get("class", ""))
            return ClassificationResult(
                artifact=subject.identity,
                mutation_class=mutation_class,
                rule_id=rule_id,
                authority=authority_for(doc, mutation_class),
                status=CLASSIFIED,
            )

    terminal = doc["classification_rules"].get("terminal", {})
    return ClassificationResult(
        artifact=subject.identity,
        mutation_class="",
        rule_id="",
        authority="",
        status=UNRESOLVED,
        reason=str(terminal.get("effect", "FAILS CLOSED"))
        + " — no mutation classification rule matched",
    )


def classify_all(
    paths: list[str] | tuple[str, ...], repo: Repository
) -> tuple[ClassificationResult, ...]:
    """Classify many subjects deterministically: sorted input, one shared boundary read."""
    doc = load_boundary(repo.root)
    return tuple(classify(Subject.of_path(p), repo, doc) for p in sorted(paths))


def unresolved(results: tuple[ClassificationResult, ...]) -> tuple[str, ...]:
    """The subjects that reached the terminal. Ordered, for a fail-closed consumer."""
    return tuple(r.artifact for r in results if r.status == UNRESOLVED)


__all__ = [
    "BOUNDARY_PATH",
    "CLASSIFIED",
    "ERROR",
    "OBJECT",
    "PATH",
    "RULE_PREDICATES",
    "UNRESOLVED",
    "ClassificationError",
    "ClassificationResult",
    "Repository",
    "Subject",
    "authority_for",
    "classify",
    "classify_all",
    "governed_declaration_checks",
    "load_boundary",
    "unresolved",
    "validate_rule_coverage",
]
