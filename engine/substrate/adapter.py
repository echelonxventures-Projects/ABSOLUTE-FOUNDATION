"""The UCOS adapter — UCOS's own truth, expressed in the substrate's terms.

WHAT AN ADAPTER OWES AND WHAT IT MUST NOT DO. It answers "what exists here" and "who
answers for it" in UCOS's vocabulary, and translates. It does not teach the substrate about
UCOS: no rule, no threshold and no judgement crosses this boundary, only facts.

TWO SOURCES, DELIBERATELY. The filesystem says what EXISTS; `00-BOOK/DATA/artifacts.json`
says what UCOS CLAIMS to govern. Reading only the register would make the adapter agree with
UCOS by construction and find nothing — which is exactly how a register goes stale unnoticed.
The disagreement between the two is the finding.
"""

from __future__ import annotations

import fnmatch
import json
import os
from collections.abc import Iterator

from uakp.adapters.filesystem import FilesystemAdapter
from uakp.core.artifact import Artifact
from uakp.core.authority import Authority

#: Directories that hold no governed truth: caches, virtualenvs and version-control internals.
#: Not a whitelist of what may exist — a list of what is reconstructible from what does.
UNGOVERNED_DIRECTORIES = frozenset(
    {
        "__pycache__",
        "node_modules",
        ".git",
        ".ec1-venv",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".archive",
    }
)

REGISTER = os.path.join("00-BOOK", "DATA", "artifacts.json")
EXCLUSIONS = os.path.join("00-BOOK", "DATA", "exclusion-register.json")
ID_LEDGER = os.path.join("00-BOOK", "DATA", "id-ledger.json")


def artifacts(root: str) -> Iterator[Artifact]:
    """Everything the environment contains, whatever language or format it is in."""
    yield from FilesystemAdapter(root, skip_directories=UNGOVERNED_DIRECTORIES).discover()


def authorities(root: str) -> Iterator[Authority]:
    """What UCOS's own register claims to govern, as one authority.

    One authority rather than many because the register does not attribute its entries to
    distinct owners; claiming otherwise here would be the adapter inventing structure its
    source does not have, which is worse than reporting the structure that exists.
    """
    path = os.path.join(root, REGISTER)
    try:
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        return
    entries = (
        document
        if isinstance(document, list)
        else (document.get("artifacts") or document.get("entries") or [])
    )
    claimed = {
        entry.get("path") or entry.get("canonical_path") or entry.get("identity")
        for entry in entries
        if isinstance(entry, dict)
    }
    claimed.discard(None)
    yield Authority(identity="UCOS-ARTIFACT-REGISTER", governs=frozenset(claimed))

    # EXCLUSION IS GOVERNANCE, NOT ITS ABSENCE, AND OMITTING IT WOULD MAKE THIS GATE LIE.
    # UCOS's exclusion register declares each excluded path with a class and a written
    # reason, so an excluded path is governed BY that register. Reporting those as owned by
    # nobody would drown the real finding in five thousand entries UCOS has already
    # answered for — and a finding nobody can read is not a finding.
    present = frozenset(a.identity for a in artifacts(root))
    yield from _exclusion_authority(root)
    yield from _identity_authority(root, present)


def _identity_authority(root: str, existing: frozenset[str]) -> Iterator[Authority]:
    """UGA's identity ledger — the broadest thing UCOS actually governs.

    `artifacts.json` is the CORPUS register: 1,658 entries, permit-gated, and deliberately
    narrow. The identity ledger is the object map, and an object with a Universal ID is
    governed whether or not the corpus admits it. Reading only the corpus register reported
    5,470 ungoverned artifacts, most of which UGA had in fact minted identities for — a
    finding that was true of the register and false of the repository.
    """
    path = os.path.join(root, ID_LEDGER)
    try:
        with open(path, encoding="utf-8") as handle:
            ledger = json.load(handle)
    except (OSError, ValueError):
        return
    # AN APPEND-ONLY LEDGER RECORDS IDENTITY, IT DOES NOT CLAIM PRESENCE. UCKP-ART-05 makes
    # an identity permanent: when a path is retired the ledger keeps its entry forever, which
    # is what append-only MEANS for a deletion. Mapping every historical entry to a present
    # claim reported thirteen "claims over things that do not exist" — all thirteen genuinely
    # absent, and none of them a defect. `ledger_authority.py` was deliberately moved with its
    # old identity retired, and the ledger recording that is the system working.
    #
    # So the ledger governs what it has minted AND that is still here. The retired remainder
    # is history, and history is not a claim.
    present = set(existing)
    claimed: set[str] = set()
    for section in ("by_path", "by_object"):
        entries = ledger.get(section)
        if isinstance(entries, dict):
            claimed |= set(entries) & present
    if claimed:
        yield Authority(identity="UCOS-IDENTITY-LEDGER", governs=frozenset(claimed))


def _matches(relative: str, rule: str) -> bool:
    """Gitignore-shaped matching, kept deliberately simple and conservative.

    A rule that cannot be interpreted matches NOTHING rather than everything: over-matching
    here would silently absolve paths the register never claimed, which is the direction that
    hides a finding.
    """
    rule = rule.strip().lstrip("/")
    if not rule:
        return False
    # A RULE WHOSE SCOPE IS NOT IN THE DATA MATCHES NOTHING. The register holds an entry
    # whose rule is bare `*`, and whose own rationale says: "The rule is scoped to the cache
    # directory that contains it, never to the repository root, and is admitted only in that
    # scope." That scope lives in PROSE and not in any field, so no consumer can apply it
    # correctly. Applied at root it absolved all 7,351 artifacts and this gate reported zero
    # contradictions — a total false green produced by reading a register faithfully.
    #
    # Refusing it here is the conservative direction, and the only honest one: an
    # unscopeable universal pattern is un-interpretable, and this function's contract is that
    # what it cannot interpret it does not absolve.
    if rule.strip("*/") == "":
        return False
    if rule.endswith("/"):
        prefix = rule.rstrip("/")
        return relative == prefix or relative.startswith(prefix + "/")
    if "*" in rule or "?" in rule:
        return fnmatch.fnmatch(relative, rule) or fnmatch.fnmatch(os.path.basename(relative), rule)
    return relative == rule or os.path.basename(relative) == rule


def _exclusion_authority(root: str) -> Iterator[Authority]:
    path = os.path.join(root, EXCLUSIONS)
    try:
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        return
    rules_declared = [
        entry["rule"]
        for entry in document.get("entries", [])
        if isinstance(entry, dict) and entry.get("rule")
    ]
    if not rules_declared:
        return
    excluded = {
        artifact.identity
        for artifact in artifacts(root)
        if any(_matches(artifact.identity, rule) for rule in rules_declared)
    }
    yield Authority(identity="UCOS-EXCLUSION-REGISTER", governs=frozenset(excluded))


__all__ = [
    "EXCLUSIONS",
    "ID_LEDGER",
    "REGISTER",
    "UNGOVERNED_DIRECTORIES",
    "artifacts",
    "authorities",
]
