"""UISD-000001 Part 02 — the ten laws, each with a computable check.

A law whose compliance nobody computes is manual governance, so every law in
``uisd-declaration.json`` names a check, :data:`LAW_CHECKS` implements it, and
:meth:`engine.infinite_scope.model.InfiniteScopeContract.validate` refuses to construct a
contract whose law names a missing check — or whose check no law claims.

The checks are pure functions of ``(contract, repository_root)``. They read the
declaration, read declared files, and import declared modules in-process. They read no
clock, open no socket, spawn no subprocess and write nothing, so a verdict is reproducible
and a gate built on them cannot dirty the tree.

Three checks are worth reading closely, because they are the ones that make the mission's
claims measurable rather than aspirational:

* :func:`check_scope_expansion_capacity` does **not** assert that no enumeration is
  closed. That would be false — ``engine/uckp/facets.py`` closes 33 facets on purpose so
  that every vocabulary inside them can stay open — and a false law gets disabled. It
  asserts that no enumeration is closed *silently*: each one names the invariant that
  closes it and the path by which a member is admitted.
* :func:`check_relationship_model_expands` proves openness by **performing** an extension
  in memory on every run, then proving the original vocabulary did not move. A comment
  claiming a vocabulary is append-only is not evidence; a non-mutating extension is.
* :func:`check_no_active_permanence_declaration` is a ratchet, not a search. Every located
  occurrence must already be declared with a class and a reason, so a new permanence
  declaration cannot enter the scanned roots unnoticed. Note the check's name: it avoids
  the literal token it detects, because a detector that matches its own source is its own
  first finding, and declaring an exception for it would have blunted the ratchet on the
  one file most likely to be edited.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import tomllib
from collections.abc import Callable
from typing import Any

from engine.infinite_scope.model import (
    FreezeScan,
    InfiniteScopeContract,
    InfiniteScopeError,
)

#: Where the declaration lives, relative to the repository root.
DECLARATION_PATH = "00-MASTER/UISD-000001/uisd-declaration.json"


def repo_root() -> str:
    """Return the repository root, derived from this file's location."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_declaration(path: str | None = None) -> dict[str, Any]:
    """Load the declaration.

    Raises:
        InfiniteScopeError: the declaration is absent or unreadable. Fail closed: a
            declaration that cannot be read is not a declaration that permits everything.
    """
    target = path or os.path.join(repo_root(), DECLARATION_PATH)
    try:
        with open(target, encoding="utf-8") as handle:
            doc = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise InfiniteScopeError("declaration is unreadable", subject=target) from exc
    if not isinstance(doc, dict):
        raise InfiniteScopeError("declaration is not a mapping", subject=target)
    return doc


def load_contract(path: str | None = None) -> InfiniteScopeContract:
    """Rehydrate and validate the contract.

    Raises:
        InfiniteScopeError: the contract is unsound. Every reason is reported at once,
            because a half-diagnosed contract wastes a cycle.
    """
    contract = InfiniteScopeContract.from_declaration(load_declaration(path))
    problems = contract.validate(frozenset(LAW_CHECKS))
    if problems:
        raise InfiniteScopeError("contract is unsound: " + "; ".join(problems))
    return contract


# ----------------------------------------------------------------- shared measurement


def _exists(repo: str, relpath: str) -> bool:
    """Report whether a declared repository-relative path exists."""
    return os.path.exists(os.path.join(repo, relpath))


def _read_text(repo: str, relpath: str) -> str | None:
    """Read a declared file, or return None if it cannot be read."""
    try:
        with open(os.path.join(repo, relpath), encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def _read_json(repo: str, relpath: str) -> Any:
    """Read a declared JSON file, or return None if it cannot be read or parsed."""
    text = _read_text(repo, relpath)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _symbol(module_name: str, symbol_name: str) -> Any:
    """Import a declared symbol, raising ImportError or AttributeError on absence."""
    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)


def candidate_files(repo: str, scan: FreezeScan) -> list[str]:
    """Return the repository-relative files the scan covers, deterministically ordered."""
    found: set[str] = set()
    for root in scan.roots:
        base = os.path.normpath(os.path.join(repo, root))
        if root in scan.root_depth_zero_only:
            try:
                names = os.listdir(base)
            except OSError:
                continue
            for name in names:
                path = os.path.join(base, name)
                if os.path.isfile(path) and os.path.splitext(name)[1] in scan.extensions:
                    found.add(os.path.relpath(path, repo).replace(os.sep, "/"))
            continue
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [
                name
                for name in dirnames
                if name not in scan.excluded_directory_names
                and not (scan.excluded_dot_directories and name.startswith("."))
            ]
            for name in filenames:
                if os.path.splitext(name)[1] in scan.extensions:
                    joined = os.path.join(dirpath, name)
                    found.add(os.path.relpath(joined, repo).replace(os.sep, "/"))
    return sorted(found)


def scan_occurrences(repo: str, scan: FreezeScan) -> dict[str, int]:
    """Count permanence-vocabulary occurrences per file across the declared roots."""
    pattern = re.compile(scan.status_pattern) if scan.status_pattern else None
    counts: dict[str, int] = {}
    for relpath in candidate_files(repo, scan):
        text = _read_text(repo, relpath)
        if text is None:
            continue
        lowered = text.lower()
        total = sum(lowered.count(phrase) for phrase in scan.phrases)
        if pattern is not None:
            total += len(pattern.findall(text))
        if total:
            counts[relpath] = total
    return counts


# --------------------------------------------------------------------------- the checks
# Each returns the violations it found. An empty tuple means the law holds.


def check_scope_expansion_capacity(contract: InfiniteScopeContract, repo: str) -> tuple[str, ...]:
    """ISD-L-01 — no enumeration is closed silently."""
    problems: list[str] = []
    if not contract.closed_enumerations:
        return (
            "no closed enumeration is disclosed; an empty disclosure list would make this "
            "law vacuous rather than satisfied",
        )
    for disclosure in contract.closed_enumerations:
        if not disclosure.closing_invariant.strip():
            problems.append(f"{disclosure.disclosure_id}: discloses no closing invariant")
        if not disclosure.admission.strip():
            problems.append(f"{disclosure.disclosure_id}: discloses no admission path")
        if not _exists(repo, disclosure.declared_at):
            problems.append(
                f"{disclosure.disclosure_id}: declared_at {disclosure.declared_at} does not exist"
            )
        if not disclosure.intentional and not disclosure.gap:
            problems.append(
                f"{disclosure.disclosure_id}: closure is not intentional and names no gap, "
                "so it is an undisclosed finite assumption"
            )
    return tuple(problems)


def check_direction_expansion_capacity(
    contract: InfiniteScopeContract, repo: str
) -> tuple[str, ...]:
    """ISD-L-02 — the relationship type space is pattern-bound, not enumeration-bound."""
    problems: list[str] = []
    config = contract.direction_expansion
    schema_path = str(config.get("edge_schema", ""))
    schema = _read_json(repo, schema_path)
    if not isinstance(schema, dict):
        return (f"edge schema {schema_path} is absent or unparseable",)
    node: Any = schema
    for step in config.get("type_property_path", []):
        if not isinstance(node, dict) or step not in node:
            return (f"edge schema {schema_path} has no property path {step!r}",)
        node = node[step]
    if not isinstance(node, dict):
        return (f"edge schema {schema_path}: the type property is not a mapping",)
    for key in config.get("forbidden_property_keys", []):
        if key in node:
            problems.append(
                f"edge schema constrains relationship type with {key!r}, which closes the "
                "direction space"
            )
    for key in config.get("required_property_keys", []):
        if key not in node:
            problems.append(f"edge schema relationship type declares no {key!r}")
    admission = config.get("freeform_admission")
    if not isinstance(admission, dict):
        return (*problems, "no freeform admission path is declared")
    declared_at = str(admission.get("declared_at", ""))
    symbol = str(admission.get("symbol", ""))
    expected = str(admission.get("expected", ""))
    text = _read_text(repo, declared_at)
    if text is None:
        problems.append(f"freeform admission source {declared_at} is unreadable")
    elif not re.search(rf"{re.escape(symbol)}\s*=\s*[\"']{re.escape(expected)}[\"']", text):
        problems.append(
            f"{declared_at} does not bind {symbol} to {expected!r}, so a new relationship "
            "type would require a configuration edit"
        )
    return tuple(problems)


def check_principle_inherits_itself(contract: InfiniteScopeContract, repo: str) -> tuple[str, ...]:
    """ISD-L-03 — the principle is subject to its own laws and holds a birth record."""
    problems: list[str] = []
    subjects = contract.self_application.get("subject_of_own_laws")
    if not isinstance(subjects, list) or contract.artifact_id not in subjects:
        problems.append(
            f"{contract.artifact_id} does not name itself in self_application."
            "subject_of_own_laws, so the principle exempts itself"
        )
    if contract.self_application.get("declares_independent_lifecycle") is not False:
        problems.append("the principle does not declare independent_lifecycle false")
    if contract.lifecycle_inheritance.get("independent_lifecycle_defined") is not False:
        problems.append(
            "lifecycle_inheritance does not declare independent_lifecycle_defined false"
        )
    if not str(contract.lifecycle_inheritance.get("lifecycle_owner", "")).strip():
        problems.append("lifecycle_inheritance names no lifecycle owner")
    authority_over = contract.self_application.get("declares_authority_over")
    if authority_over:
        problems.append(
            f"the principle claims authority over {authority_over!r}; it is a pervasive "
            "property, not an authority layer"
        )
    identity = str(contract.self_application.get("birth_identity", ""))
    ledger_path = str(contract.self_application.get("birth_ledger", ""))
    ledger = _read_json(repo, ledger_path)
    if not isinstance(ledger, dict):
        problems.append(f"birth ledger {ledger_path} is absent or unparseable")
    elif identity not in ledger.get("births", {}):
        problems.append(f"{identity} holds no birth record, so the principle exists anonymously")
    return tuple(problems)


def check_lifecycle_applies_to_itself(
    contract: InfiniteScopeContract, repo: str
) -> tuple[str, ...]:
    """ISD-L-04 — the lifecycle stage graph is open and its projection has not drifted."""
    problems: list[str] = []
    config = contract.lifecycle_openness
    manifest_path = str(config.get("manifest", ""))
    manifest = _read_json(repo, manifest_path)
    if not isinstance(manifest, dict):
        return (f"lifecycle manifest {manifest_path} is absent or unparseable",)
    declared = manifest.get("manifest")
    if not isinstance(declared, dict):
        return (f"lifecycle manifest {manifest_path} holds no manifest block",)
    for flag, expected in dict(config.get("required_manifest_flags", {})).items():
        if declared.get(flag) != expected:
            problems.append(
                f"lifecycle manifest declares {flag}={declared.get(flag)!r}, not {expected!r}"
            )
    for field in config.get("required_manifest_fields", []):
        if not str(declared.get(field, "")).strip():
            problems.append(f"lifecycle manifest declares no {field!r}")
    module_name = str(config.get("alignment_module", ""))
    function_name = str(config.get("alignment_function", ""))
    try:
        align = _symbol(module_name, function_name)
    except (ImportError, AttributeError) as exc:
        return (*problems, f"alignment {module_name}.{function_name} is unavailable: {exc}")
    divergences = tuple(align(manifest))
    for divergence in divergences:
        problems.append(f"lifecycle projection diverges from its manifest: {divergence}")
    return tuple(problems)


def check_evolution_applies_to_itself(
    contract: InfiniteScopeContract, repo: str
) -> tuple[str, ...]:
    """ISD-L-05 — the evolution cycle has no terminal stage and returns to its first."""
    problems: list[str] = []
    config = contract.evolution_openness
    module_name = str(config.get("module", ""))
    try:
        cycle = tuple(_symbol(module_name, str(config.get("cycle_symbol", ""))))
        is_terminal = _symbol(module_name, str(config.get("terminal_predicate", "")))
        next_stage = _symbol(module_name, str(config.get("successor_function", "")))
    except (ImportError, AttributeError) as exc:
        return (f"evolution module {module_name} is unusable: {exc}",)
    minimum = int(config.get("minimum_stages", 2))
    if len(cycle) < minimum:
        problems.append(f"the evolution cycle declares {len(cycle)} stages, fewer than {minimum}")
    if not cycle:
        return tuple(problems)
    for stage in cycle:
        if is_terminal(stage):
            problems.append(f"evolution stage {stage!r} is terminal, so evolution can end")
        if next_stage(stage) not in cycle:
            problems.append(f"evolution stage {stage!r} has a successor outside the cycle")
    if next_stage(cycle[-1]) != cycle[0]:
        problems.append(
            "the last evolution stage does not return to the first, so the cycle does not wrap"
        )
    return tuple(problems)


def check_relationship_model_expands(contract: InfiniteScopeContract, repo: str) -> tuple[str, ...]:
    """ISD-L-06 — a relationship vocabulary admits a term without amendment or mutation."""
    problems: list[str] = []
    config = contract.relationship_expansion
    module_name = str(config.get("module", ""))
    probe_id = str(config.get("probe_term_id", ""))
    method_name = str(config.get("extension_method", ""))
    try:
        term_type = _symbol(module_name, str(config.get("term_symbol", "")))
    except (ImportError, AttributeError) as exc:
        return (f"relationship vocabulary module {module_name} is unusable: {exc}",)
    vocabularies = config.get("vocabularies")
    if not isinstance(vocabularies, list) or not vocabularies:
        return ("no relationship vocabulary is declared, so expansion is unmeasured",)
    for entry in vocabularies:
        symbol_name = str(entry.get("symbol", ""))
        try:
            vocabulary = _symbol(module_name, symbol_name)
            extend = getattr(vocabulary, method_name)
        except (ImportError, AttributeError) as exc:
            problems.append(f"{symbol_name}: unusable: {exc}")
            continue
        before = len(vocabulary.terms)
        baseline = entry.get("population_at_baseline")
        if isinstance(baseline, int) and before < baseline:
            problems.append(
                f"{symbol_name}: holds {before} terms, fewer than the {baseline} disclosed; "
                "an append-only vocabulary cannot shrink"
            )
        probe = term_type(
            term_id=probe_id,
            definition="in-memory probe that the vocabulary admits a term by registration",
        )
        extended = extend(probe)
        if extended is vocabulary:
            problems.append(f"{symbol_name}: extension returned the original vocabulary")
        if not extended.has(probe_id):
            problems.append(f"{symbol_name}: refused a well-formed new term, so the tier is closed")
        if vocabulary.has(probe_id):
            problems.append(f"{symbol_name}: extension mutated the original vocabulary")
        if len(extended.terms) != before + 1:
            problems.append(
                f"{symbol_name}: extension produced {len(extended.terms)} terms, not {before + 1}"
            )
    return tuple(problems)


def check_no_active_permanence_declaration(
    contract: InfiniteScopeContract, repo: str
) -> tuple[str, ...]:
    """ISD-L-07 — every permanence occurrence is a disclosed, classified, non-active site."""
    problems: list[str] = []
    scan = contract.freeze_scan
    declared = {site.path: site for site in scan.preserved_sites}
    if len(declared) != len(scan.preserved_sites):
        problems.append("freeze_scan declares the same path as a preserved site more than once")
    found = scan_occurrences(repo, scan)
    for path in sorted(found):
        if path not in declared:
            problems.append(
                f"{path}: carries {found[path]} permanence occurrence(s) and is not a declared "
                "preserved site; a new permanence declaration entered the scanned roots"
            )
    for site in scan.preserved_sites:
        if site.site_class == "A":
            problems.append(
                f"{site.site_id} ({site.path}): classified A — an active lifecycle declaration "
                "forbidding future change is not a category a site may be preserved in"
            )
        if site.site_class not in scan.classes:
            problems.append(f"{site.site_id}: class {site.site_class!r} is not declared")
        if site.site_class in scan.count_enforced_classes:
            actual = found.get(site.path, 0)
            if actual != site.occurrences:
                problems.append(
                    f"{site.site_id} ({site.path}): class {site.site_class} is count-enforced and "
                    f"carries {actual} occurrence(s), not the {site.occurrences} disclosed"
                )
    return tuple(problems)


def check_baseline_temporal_qualification(
    contract: InfiniteScopeContract, repo: str
) -> tuple[str, ...]:
    """ISD-L-08 — every baseline surface parses its coordinate or discloses that it cannot."""
    problems: list[str] = []
    if not contract.baseline_surfaces:
        return ("no baseline surface is declared, so temporal qualification is unmeasured",)
    try:
        parse = _symbol(contract.baseline_resolver_module, contract.baseline_resolver_function)
    except (ImportError, AttributeError) as exc:
        return (
            f"temporal resolver {contract.baseline_resolver_module}."
            f"{contract.baseline_resolver_function} is unavailable: {exc}",
        )
    for surface in contract.baseline_surfaces:
        if not _exists(repo, surface.surface):
            problems.append(f"{surface.surface_id}: surface {surface.surface} does not exist")
            continue
        if not surface.qualified:
            if not surface.deferred_to:
                problems.append(
                    f"{surface.surface_id}: declares no temporal coordinate and names no owner "
                    "it is deferred to, so the non-conformance is undisclosed"
                )
            if not surface.gap:
                problems.append(
                    f"{surface.surface_id}: declares no temporal coordinate and records no gap"
                )
            continue
        if not surface.sample:
            problems.append(f"{surface.surface_id}: declared qualified but carries no sample")
            continue
        try:
            parse(surface.sample, authority=contract.artifact_id)
        except Exception as exc:  # noqa: BLE001 - any refusal is the finding
            problems.append(
                f"{surface.surface_id}: declared qualified but sample {surface.sample!r} does "
                f"not parse under the temporal contract: {exc}"
            )
            continue
        text = _read_text(repo, surface.surface)
        if text is not None and surface.sample not in text:
            problems.append(
                f"{surface.surface_id}: sample {surface.sample!r} is absent from "
                f"{surface.surface}, so the disclosure describes no recorded coordinate"
            )
    return tuple(problems)


def check_technology_is_evolutionary_state(
    contract: InfiniteScopeContract, repo: str
) -> tuple[str, ...]:
    """ISD-L-09 — no runtime pin, no version ceiling, and every toolchain pin disclosed."""
    problems: list[str] = []
    config = contract.technology
    manifest_path = str(config.get("manifest", ""))
    text = _read_text(repo, manifest_path)
    if text is None:
        return (f"technology manifest {manifest_path} is unreadable",)
    try:
        manifest = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        return (f"technology manifest {manifest_path} is unparseable: {exc}",)
    project = manifest.get("project", {})
    runtime = project.get("dependencies", [])
    if config.get("runtime_dependencies_must_be_empty") and runtime:
        problems.append(
            f"{manifest_path} declares {len(runtime)} runtime dependency(ies): {runtime!r}; "
            "a pinned runtime encodes a technology as constitutional truth"
        )
    requires_key = str(config.get("requires_python_key", "requires-python"))
    requirement = str(project.get(requires_key, ""))
    if not requirement:
        problems.append(f"{manifest_path} declares no {requires_key}")
    for operator in config.get("forbidden_version_operators", []):
        if operator in requirement:
            problems.append(
                f"{requires_key} is {requirement!r}, which carries {operator!r}: a ceiling or an "
                "exact pin makes the language version a constitutional truth, not a state"
            )
    disclosed = {pin.requirement for pin in contract.declared_pins}
    actual = {
        str(requirement_text)
        for group in project.get("optional-dependencies", {}).values()
        for requirement_text in group
        if "==" in str(requirement_text)
    }
    for undisclosed in sorted(actual - disclosed):
        problems.append(f"{undisclosed}: pinned in {manifest_path} and not disclosed with a reason")
    for stale in sorted(disclosed - actual):
        problems.append(f"{stale}: disclosed as a pin but no longer pinned in {manifest_path}")
    return tuple(problems)


def check_capability_seed_openness(contract: InfiniteScopeContract, repo: str) -> tuple[str, ...]:
    """ISD-L-10 — the capability model is a seed, and every enumeration names its admission."""
    problems: list[str] = []
    if contract.capability_final:
        problems.append(
            "the capability model declares itself final, which closes the capability universe"
        )
    if not contract.capability_enumerations:
        return (*problems, "no capability enumeration is declared, so openness is unmeasured")
    for enumeration in contract.capability_enumerations:
        if not enumeration.admission.strip():
            problems.append(f"{enumeration.enumeration_id}: names no admission path")
        if not _exists(repo, enumeration.declared_at):
            problems.append(
                f"{enumeration.enumeration_id}: declared_at {enumeration.declared_at} "
                "does not exist"
            )
    if not any(enumeration.open_set for enumeration in contract.capability_enumerations):
        problems.append("no declared capability enumeration is open, so the seed model cannot grow")
    return tuple(problems)


#: Law check name to implementation. Every declared law's ``check`` must appear here, and
#: every entry here must be claimed by a law, or the contract refuses to construct.
LAW_CHECKS: dict[str, Callable[[InfiniteScopeContract, str], tuple[str, ...]]] = {
    "scope_expansion_capacity": check_scope_expansion_capacity,
    "direction_expansion_capacity": check_direction_expansion_capacity,
    "principle_inherits_itself": check_principle_inherits_itself,
    "lifecycle_applies_to_itself": check_lifecycle_applies_to_itself,
    "evolution_applies_to_itself": check_evolution_applies_to_itself,
    "relationship_model_expands": check_relationship_model_expands,
    "no_active_permanence_declaration": check_no_active_permanence_declaration,
    "baseline_temporal_qualification": check_baseline_temporal_qualification,
    "technology_is_evolutionary_state": check_technology_is_evolutionary_state,
    "capability_seed_openness": check_capability_seed_openness,
}


def assess(
    contract: InfiniteScopeContract, repo: str
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Measure every law, returning ``(law_id, title, violations)`` in declaration order."""
    return tuple(
        (law.law_id, law.title, LAW_CHECKS[law.check](contract, repo)) for law in contract.laws
    )
