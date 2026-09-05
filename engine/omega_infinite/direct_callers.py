"""INV-AGN-02 — the direct-caller ratchet for a substitutable facility.

WHY A RATCHET AND NOT A BAN. The repository declares version control git-bound with a
constitutional reason (adr/0039): `git ls-files` IS the eligibility boundary and `git archive`
DEFINES pristine-clone certification. So this does not forbid git — it forbids reaching PAST the
provider for a question the provider answers, which is a different claim and the only one the
evidence supports.

WHAT MADE THIS MEASURABLE. Until the capability dispatch landed, the provider declared five
capabilities and delivered one, so a caller needing a content hash or the working tree had no
choice but to invoke the tool directly. Counting those as bypasses would have been counting the
provider's own gap against its callers. Now every declared capability has a delivery, so a direct
invocation is a choice, and this number is the count of those choices.

THE NUMBER MAY ONLY FALL. A rise means a new module reached past a facility that could have
answered it, which is exactly how nine execution adapters accumulated behind a contract nothing
could fail.
"""

from __future__ import annotations

import ast
import json
import os
import pathlib

#: Modules permitted to invoke the tool directly, each for a stated reason.
DECLARED_DIRECT: dict[str, str] = {
    "engine/omega_infinite/git_provider.py": (
        "IS the provider. Its whole purpose is to be the one place the tool is invoked."
    ),
    "engine/execution_environment/discovery.py": (
        "LOCATES THE REPOSITORY ROOT, which is the step that makes a provider constructible. A "
        "provider is rooted at a path before it can answer anything about that path, so asking "
        "one where its own root is has no answer to give. This is a bootstrap and not a bypass: "
        "there is no abstraction to route through until this call has returned."
    ),
    "engine/omega_infinite/compat.py": (
        "Demonstrates that the provider reproduces the pre-provider population exactly. It must "
        "invoke both sides to compare them, and a comparison that used the provider for both "
        "would prove nothing."
    ),
}

#: Where the scan's roots come from. UCON-000001 already declares the source roots its own
#: closure audit walks, and a second tuple here would be a second answer to one question
#: (UCKP-ART-03) as well as a closed enumeration ISD-L-01 counts. Reading the declared list
#: removes both: the roots are DATA, so admitting a new source tree is an edit to the
#: declaration and never to this module.
#:
#: MEASURED BEFORE ADOPTING IT: the declared list is broader than the tuple it replaced — eight
#: roots against five — and the direct-caller count is 19 under both. Widening the scan changed
#: no verdict, which is what made the replacement safe rather than merely tidier.
UCON_DECLARATION = "00-MASTER/UCON-000001/ucon-declaration.json"


def roots(base: pathlib.Path) -> tuple[str, ...]:
    """The source roots to scan, read from the declaration that already names them."""
    document = json.loads((base / UCON_DECLARATION).read_text(encoding="utf-8"))
    declared = document.get("audit", {}).get("roots")
    if not isinstance(declared, list) or not declared:
        raise RuntimeError(f"{UCON_DECLARATION} declares no audit roots to scan")
    return tuple(str(entry) for entry in declared)


#: THE BASELINE IS MEASURED, NOT ASPIRED TO. Setting this to 0 while nineteen modules invoke the
#: tool would be a ceiling nothing could satisfy, and a gate that always fails is as useless as one
#: that never can — the defect this session measured on the execution axis, inverted. The number is
#: what the repository actually holds, and it may only fall.
#:
#: WHY IT IS MEANINGFUL NOW AND WAS NOT BEFORE. Until the capability dispatch landed, a caller
#: needing a content hash, an owner or the working tree had no alternative: the provider declared
#: those capabilities and delivered none of them. Counting such a caller as a bypass would have
#: charged the provider's gap to its callers. Every declared capability now has a delivery, so a
#: direct invocation is a CHOICE, and this counts choices.
#:
#: MOVEMENTS
#:   15 -> 14   (-1)  intelligence/rie/config.py, and it is recorded separately because the
#:                     migration was NOT mechanical. It asked `:(glob)*/__init__.py`, where git's
#:                     pathspec magic stops `*` at a separator; Selector matches with fnmatch,
#:                     where `*` crosses one. The same pattern through the provider returned an
#:                     EXTRA root — `00-BOOK`, from a nested package — which would have widened
#:                     RIE's capability catalogue silently. Measured: 7 roots the old way, 8 the
#:                     naive way, 7 again with depth-1 stated explicitly as `count("/") == 1`.
#:                     The filesystem fallback was RETAINED. It is what makes the function work in
#:                     a non-git checkout, and FilesystemProvider does not declare TRACKED_CONTENT
#:                     — correctly, since a filesystem cannot guarantee it — so resolving by
#:                     capability would find git alone and leave a non-git checkout with nothing.
#:                     Routing the fallback through a provider that cannot answer the question
#:                     would have been the appearance of abstraction, not the thing.
#:
#:   19 -> 15   (-4)  Tranche 1. THREE MIGRATED, ONE DECLARED, and the difference matters.
#:                     engine/certification_integrity/surface.py, engine/uicm/matrix.py and
#:                     platform/repository_intelligence/generated_artifacts.py each asked
#:                     TRACKED_CONTENT with the provider's own flags and each now calls
#:                     `enumerate`. PROVEN IDENTICAL BEFORE THE SWAP: the direct call and the
#:                     provider both return 7,126 paths and the sorted lists compare equal, so
#:                     no verdict any of them reaches can have moved. Failure semantics match
#:                     too — all three refused an empty world by raising, and the provider
#:                     raises rather than returning an empty tuple.
#:                     engine/execution_environment/discovery.py was DECLARED rather than
#:                     migrated: it runs `rev-parse --show-toplevel` to locate the repository
#:                     root, and a provider must be rooted at a path before it can answer
#:                     anything about that path. Asking one where its own root is has no answer
#:                     to give. That is a bootstrap, not a bypass.
#:                     ONE DEFECT CAUGHT IN THE MIGRATION ITSELF: `Artifact.location` renders as
#:                     `git:<path>`, carrying the provider identifier, and the bare path is
#:                     `location.locator`. The first draft used the rendered form and would have
#:                     silently failed every downstream path lookup while reporting a full
#:                     population — an absence indistinguishable from a clean result.
#:
#:   (established) 19  Baseline measured by AST over engine, platform, intelligence,
#:                     infrastructure and service, excluding tests and the two modules declared
#:                     above. Six of the nineteen were invisible to the flag-based scan that
#:                     preceded this one, which matched `ls-files` argument lists and therefore
#:                     missed every caller using another subcommand.
DIRECT_CALLER_CEILING = 14


def _invokes_tool_directly(path: pathlib.Path) -> bool:
    """True when this module names the tool in a call argument list.

    AST rather than text: a module DISCUSSING the tool in a docstring is not invoking it, and the
    distinction is the one UVI-L-06 makes about a selection engine naming a test file. A comment
    cannot execute.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, OSError):  # pragma: no cover - unparseable file
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for arg in list(node.args) + [kw.value for kw in node.keywords]:
            elements = arg.elts if isinstance(arg, ast.List | ast.Tuple) else [arg]
            for element in elements:
                if isinstance(element, ast.Constant) and element.value == "git":
                    return True
    return False


def direct_callers(root: str | None = None) -> tuple[str, ...]:
    """Every module invoking the tool directly, excluding those declared above."""
    base = pathlib.Path(root or os.getcwd())
    found = []
    for top in roots(base):
        for path in (base / top).rglob("*.py"):
            rel = path.relative_to(base).as_posix()
            if {"test", "tests"} & set(path.parts) or path.name.startswith(("test_", "conftest")):
                continue
            if "__pycache__" in rel or rel in DECLARED_DIRECT:
                continue
            if _invokes_tool_directly(path):
                found.append(rel)
    return tuple(sorted(found))


__all__ = ["DECLARED_DIRECT", "DIRECT_CALLER_CEILING", "direct_callers", "roots"]
