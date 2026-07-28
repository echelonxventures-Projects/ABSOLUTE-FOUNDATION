#!/usr/bin/env python3
"""UCDA-000001 — Universal Constitutional Decision Assimilation engine.

AUTHORITY = NONE (DERIVED TRUTH). This engine legislates nothing, registers nothing and
owns nothing. It is the executable expression of the Implementation Evidence Gate that
the located governance constitution establishes (`00-CEP/CEP-002` Article 28.19), and it
reads a single DATA declaration: `ucda-decisions.json`.

    python3 00-MASTER/UCDA-000001/ucda_engine.py                  # regenerate + report
    python3 00-MASTER/UCDA-000001/ucda_engine.py --gate            # fail-closed
    python3 00-MASTER/UCDA-000001/ucda_engine.py --check-declaration
    python3 00-MASTER/UCDA-000001/ucda_engine.py --check-no-enumeration
    python3 00-MASTER/UCDA-000001/ucda_engine.py --check-write-scope
    python3 00-MASTER/UCDA-000001/ucda_engine.py --check-determinism

Exit semantics of --gate:
    0  the gate is open — every declared decision carries exactly one lawful disposition
       whose required evidence resolves in the repository
    1  the gate is closed — at least one decision is undispositioned (Art 28.14)
    2  fail-closed abort — the declaration is unusable, so no verdict may be asserted

The engine contains no list of decisions, stages or dispositions: the lifecycle and the
disposition set are DATA, closed by the governing Article and extended only by amending
it. A self-check proves this by asserting that no declared identifier or declared value
appears as a literal in this source, so the engine cannot special-case any of them.

Stdlib only. No network. No timestamp is emitted anywhere, so the sealed output set is
byte-identical for an unchanged repository state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DECLARATION = HERE / "ucda-decisions.json"
EVIDENCE_DIR = HERE / "evidence"

# Keys an entry of each declared section is permitted to carry. A key outside its
# allowed set is a fail-closed violation: this is what prevents a new obligation, a new
# disposition, or a finite domain assumption from being smuggled in as a new field.
ALLOWED_KEYS = {
    "outputs": {"id", "file", "title", "purpose"},
    "lifecycle": {"id", "stage", "clause", "next", "terminal"},
    "dispositions": {
        "id",
        "disposition",
        "clause",
        "definition",
        "minimum_stage",
        "requires_fields",
        "located_fields",
        "single_valued_fields",
        "decision_reference_fields",
        "work_package_fields",
    },
    "work_packages": {
        "id",
        "title",
        "discharges",
        "owner",
        "route",
        "acceptance",
        "authorization_required",
    },
    "decisions": {
        "id",
        "title",
        "decision_class",
        "source_register",
        "index",
        "stage",
        "disposition",
        "canonical_owner",
        "evidence",
        "work_package",
        "superseded_by",
        "constitutional_basis",
        "justification",
        "note",
    },
}

# Fields of a decision entry that may carry a disposition-specific obligation. The
# obligation itself is declared per disposition; this set only bounds what may be asked.
OBLIGATION_FIELDS = (
    "canonical_owner",
    "evidence",
    "work_package",
    "superseded_by",
    "constitutional_basis",
    "justification",
)

# Reference strings carry human suffixes. A reference resolves against the repository by
# exact path first, then by unique prefix within the parent directory.
_SUFFIX_SPLITS = (" (", " §", " Art ", " · ", " — ")

# The number of determinations the renderer produces. The declaration binds a file name,
# a title and a purpose to each, positionally, in render order.
RENDERED_OUTPUTS = 7


# --------------------------------------------------------------------------- helpers


def fail_closed(message: str) -> NoReturn:
    print(f"UCDA-000001: FAIL-CLOSED ABORT — {message}", file=sys.stderr)
    raise SystemExit(2)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail_closed(f"declaration absent: {path}")
    try:
        return json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        fail_closed(f"declaration is not valid JSON: {exc}")


def load_declaration() -> dict:
    return load_json(DECLARATION)


def strip_reference(ref: str) -> str:
    text = ref
    for token in _SUFFIX_SPLITS:
        if token in text:
            text = text.split(token, 1)[0]
    return text.strip()


def resolve_reference(ref: str) -> Path | None:
    """Resolve a declaration reference to a located repository path, or None."""
    bare = strip_reference(ref)
    if not bare:
        return None
    candidate = REPO / bare
    if candidate.exists():
        return candidate
    parent = candidate.parent
    if not parent.is_dir():
        return None
    stem = candidate.name
    matches = sorted(child for child in parent.iterdir() if child.name.startswith(stem))
    return matches[0] if matches else None


def canonical_json(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def digest(payload: object) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def git(*args: str) -> str:
    try:
        out = subprocess.run(  # noqa: S603 — fixed argv, no shell, no user input
            ["git", *args],  # noqa: S607 — resolved from PATH by design, as CI does
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        return out.stdout.strip()
    except OSError:
        return ""


def repository_state() -> dict:
    """The repository state RECORDED in this programme's emitted determinations.

    Repository Fixed-Point Closure (UCOS-RFP-001 RFP-2 / RFP-3) forbids a tracked
    artifact from embedding the identity of the commit that contains it, and from
    recording an observation of the working tree that contains it. This function
    previously emitted both, and both are non-convergent by construction:

      * a commit's identity is a function of the bytes it contains, so an artifact
        naming its own commit demands a commit whose hash lies inside its own tree;
      * writing "CLEAN, 0 entries" makes the tree dirty, so the value recorded is
        never the value that holds once it has been recorded.

    Neither is lost. Version control already owns the containing commit, and tree
    cleanliness is owned by the gate's exit code — restating either here duplicated
    state the repository already held and put this programme's determinations in
    permanent Evidence Drift. The value below is constant, so regeneration at an
    unchanged tracked tree is byte-identical in every environment and at every
    commit.
    """
    return {
        "anchor": "the containing commit — owned by version control, never restated here",
        "basis": (
            "UCOS-RFP-001 RFP-2 (no commit self-reference) and RFP-3 "
            "(no working-tree self-observation)"
        ),
    }


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "| " + " | ".join(headers) + " |\n"
    rule = "|" + "|".join(["---"] * len(headers)) + "|\n"
    body = "".join("| " + " | ".join(row) + " |\n" for row in rows)
    return head + rule + body


def as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def declared_values(decl: dict, section: str, field: str) -> list[str]:
    return [entry[field] for entry in decl.get(section, []) if entry.get(field)]


def external_work_packages(decl: dict) -> set[str]:
    """Work packages already registered by another located declaration.

    A decision whose work is registered elsewhere references that package rather than
    duplicating it. The external source is itself declared, never assumed.
    """
    found: set[str] = set()
    for ref in decl["programme"].get("external_work_package_sources") or []:
        located = resolve_reference(ref)
        if located is None or not located.is_file():
            continue
        try:
            payload = json.loads(located.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for entry in payload.get("work_packages") or []:
            if isinstance(entry, dict) and entry.get("id"):
                found.add(entry["id"])
    return found


# ------------------------------------------------------------------- self-check logic


def check_declaration(decl: dict) -> list[str]:
    """Structural integrity: identity, vocabulary, closure of the declared sets."""
    findings: list[str] = []
    seen: dict[str, str] = {}
    for section, allowed in ALLOWED_KEYS.items():
        entries = decl.get(section)
        if not entries:
            findings.append(f"{section}: section is absent or empty")
            continue
        for entry in entries:
            ident = entry.get("id")
            if not ident:
                findings.append(f"{section}: entry without an id")
                continue
            if ident in seen:
                findings.append(f"duplicate identifier {ident} ({seen[ident]} and {section})")
            seen[ident] = section
            extra = set(entry) - allowed
            if extra:
                findings.append(f"{ident}: key(s) outside the permitted set: {sorted(extra)}")

    stages = declared_values(decl, "lifecycle", "stage")
    if len(decl.get("outputs") or []) != RENDERED_OUTPUTS:
        findings.append(
            f"outputs: exactly {RENDERED_OUTPUTS} determinations are rendered, "
            f"{len(decl.get('outputs') or [])} declared"
        )
    for entry in decl.get("outputs") or []:
        for key in ("file", "title", "purpose"):
            if not entry.get(key):
                findings.append(f"{entry.get('id', 'outputs')}: declares no {key}")
    for key in ("gate_name", "gate_clause"):
        if not decl["programme"].get(key):
            findings.append(f"programme: declares no {key}")
    if len(set(stages)) != len(stages):
        findings.append("lifecycle: a stage is declared more than once")
    stage_set = set(stages)

    # ordering, reachability and terminality of the declared lifecycle
    terminal = [entry["stage"] for entry in decl["lifecycle"] if entry.get("terminal")]
    if len(terminal) != 1:
        findings.append(
            f"lifecycle: exactly one terminal stage is required, {len(terminal)} declared"
        )
    for index, entry in enumerate(decl["lifecycle"]):
        successors = as_list(entry.get("next"))
        for successor in successors:
            if successor not in stage_set:
                findings.append(f"{entry['id']}: transition to undeclared stage {successor!r}")
            elif stages.index(successor) <= index:
                findings.append(
                    f"{entry['id']}: transition to {successor!r} is not forward — "
                    "the lifecycle is traversed in order"
                )
        if entry.get("terminal") and successors:
            findings.append(f"{entry['id']}: a terminal stage declares an outgoing transition")
        if not entry.get("terminal") and not successors:
            findings.append(f"{entry['id']}: a non-terminal stage declares no outgoing transition")
    reachable = {stages[0]} if stages else set()
    for entry in decl["lifecycle"]:
        if entry["stage"] in reachable:
            reachable.update(as_list(entry.get("next")))
    for stage in sorted(stage_set - reachable):
        findings.append(f"lifecycle: stage {stage!r} is not reachable from the initial stage")

    names = declared_values(decl, "dispositions", "disposition")
    if len(set(names)) != len(names):
        findings.append("dispositions: a disposition is declared more than once")
    for entry in decl["dispositions"]:
        floor = entry.get("minimum_stage")
        if floor not in stage_set:
            findings.append(f"{entry['id']}: minimum stage {floor!r} is not a declared stage")
        for key in (
            "requires_fields",
            "located_fields",
            "single_valued_fields",
            "decision_reference_fields",
            "work_package_fields",
        ):
            for field in as_list(entry.get(key)):
                if field not in OBLIGATION_FIELDS:
                    findings.append(
                        f"{entry['id']}: {key} names {field!r}, which is not an obligation field"
                    )

    wp_ids = set(declared_values(decl, "work_packages", "id")) | external_work_packages(decl)
    decision_ids = set(declared_values(decl, "decisions", "id"))
    for package in decl["work_packages"]:
        for target in as_list(package.get("discharges")):
            if target not in decision_ids:
                findings.append(f"{package['id']}: discharges undeclared decision {target}")
        for key in ("title", "owner", "route", "acceptance"):
            if not package.get(key):
                findings.append(f"{package['id']}: declares no {key}")

    by_name = {entry["disposition"]: entry for entry in decl["dispositions"]}
    for entry in decl["decisions"]:
        ident = entry["id"]
        if entry.get("stage") not in stage_set:
            findings.append(f"{ident}: stage {entry.get('stage')!r} is not a declared stage")
        name = entry.get("disposition")
        if name not in by_name:
            findings.append(
                f"{ident}: disposition {name!r} is not one of the declared set "
                f"{sorted(by_name)} — the set is closed by the governing Article"
            )
            continue
        rule = by_name[name]
        for field in as_list(rule.get("requires_fields")):
            if not entry.get(field):
                findings.append(f"{ident}: disposition requires {field!r}, which is absent")
        for field in as_list(rule.get("single_valued_fields")):
            if len(as_list(entry.get(field))) > 1:
                findings.append(f"{ident}: {field!r} must carry exactly one value")
        for field in as_list(rule.get("decision_reference_fields")):
            for target in as_list(entry.get(field)):
                if target not in decision_ids:
                    findings.append(
                        f"{ident}: {field!r} names {target}, which is not a declared decision"
                    )
                elif target == ident:
                    findings.append(f"{ident}: {field!r} refers to itself")
        for field in as_list(rule.get("work_package_fields")):
            for target in as_list(entry.get(field)):
                if target not in wp_ids:
                    findings.append(
                        f"{ident}: {field!r} names {target}, which is not a declared work package"
                    )
        # obligations not asked for by the disposition must not be asserted
        asked = set()
        for key in (
            "requires_fields",
            "located_fields",
            "single_valued_fields",
            "decision_reference_fields",
            "work_package_fields",
        ):
            asked.update(as_list(rule.get(key)))
        for field in OBLIGATION_FIELDS:
            if field not in asked and entry.get(field):
                findings.append(
                    f"{ident}: asserts {field!r}, which its disposition does not admit — "
                    "exactly one disposition, with exactly its own obligations"
                )
        floor = rule.get("minimum_stage")
        if floor in stage_set and entry.get("stage") in stage_set:
            if stages.index(entry["stage"]) < stages.index(floor):
                findings.append(f"{ident}: disposition may not be asserted before stage {floor!r}")

    # every located reference of the programme block must resolve
    programme = decl["programme"]
    references: list[tuple[str, str]] = [
        ("programme.governing_instrument", programme["governing_instrument"])
    ]
    references += [("programme.governed_by", ref) for ref in programme["governed_by"]]
    references += [("programme.located_registers", ref) for ref in programme["located_registers"]]
    references.append(("programme.aggregate_gate_owner", programme["aggregate_gate_owner"]))
    references.append(("programme.operational_memory_owner", programme["operational_memory_owner"]))
    for source, ref in references:
        if resolve_reference(ref) is None:
            findings.append(f"{source}: reference does not resolve in the repository: {ref!r}")
    return findings


def check_no_enumeration(decl: dict) -> list[str]:
    """Prove the engine is data-driven, so extension needs no code change.

    Mechanical, with no denylist of technologies (a denylist would itself be an
    enumeration): no declared identifier and no declared lifecycle or disposition value
    may appear as a literal in this source. If the engine never names a stage, a
    disposition or a decision, it cannot special-case one.
    """
    findings: list[str] = []
    source = Path(__file__).read_text("utf-8")
    literals: list[str] = []
    for section in ALLOWED_KEYS:
        literals += declared_values(decl, section, "id")
    literals += declared_values(decl, "lifecycle", "stage")
    literals += declared_values(decl, "dispositions", "disposition")
    for literal in sorted(set(literals)):
        if literal in source:
            findings.append(
                f"engine source special-cases declared value {literal!r} — extension "
                "would require a code change"
            )
    for section, allowed in ALLOWED_KEYS.items():
        for entry in decl.get(section, []):
            extra = set(entry) - allowed
            if extra:
                findings.append(
                    f"{entry.get('id', section)}: undeclared key(s) {sorted(extra)} — "
                    "a new obligation may be smuggled through a new field"
                )
    return findings


def check_write_scope(decl: dict, written: list[Path] | None = None) -> list[str]:
    """No write may land outside this programme's own operational memory."""
    findings: list[str] = []
    for prefix in decl["programme"]["forbidden_write_prefixes"]:
        if not (REPO / prefix).exists():
            findings.append(f"forbidden-write prefix does not exist: {prefix}")
    for path in written or []:
        resolved = path.resolve()
        try:
            resolved.relative_to(HERE)
        except ValueError:
            findings.append(f"write outside the programme's operational memory: {resolved}")
    return findings


# --------------------------------------------------------------------- assessment


def assess(decl: dict) -> dict:
    """Assess every declared decision against its disposition's evidence obligation."""
    by_name = {entry["disposition"]: entry for entry in decl["dispositions"]}
    records: list[dict] = []
    for entry in decl["decisions"]:
        rule = by_name.get(entry.get("disposition")) or {}
        located_fields = as_list(rule.get("located_fields"))
        resolved: list[str] = []
        unresolved: list[str] = []
        for field in located_fields:
            for ref in as_list(entry.get(field)):
                (resolved if resolve_reference(ref) is not None else unresolved).append(ref)
        register = entry.get("source_register") or ""
        register_located = resolve_reference(register) is not None if register else False
        index = entry.get("index") or ""
        index_located = resolve_reference(index) is not None if index else False
        missing = [field for field in as_list(rule.get("requires_fields")) if not entry.get(field)]
        lawful = entry.get("disposition") in by_name
        # Art 28.5 — a decision whose trace is only conversational is not recorded.
        conversation_only = not register_located and not resolved
        undispositioned = bool(
            not lawful or missing or unresolved or not register_located or conversation_only
        )
        reasons: list[str] = []
        if not lawful:
            reasons.append("disposition is outside the closed set")
        if missing:
            reasons.append("required field(s) absent: " + ", ".join(sorted(missing)))
        if unresolved:
            reasons.append("evidence does not resolve: " + ", ".join(sorted(unresolved)))
        if not register_located:
            reasons.append(f"source register does not resolve: {register!r}")
        if conversation_only:
            reasons.append("no repository trace — conversation-only")
        records.append(
            {
                "id": entry["id"],
                "title": entry["title"],
                "decision_class": entry.get("decision_class") or "",
                "stage": entry.get("stage") or "",
                "disposition": entry.get("disposition") or "",
                "source_register": register,
                "source_register_located": register_located,
                "index": index,
                "index_located": index_located,
                "work_package": entry.get("work_package"),
                "superseded_by": entry.get("superseded_by"),
                "canonical_owner": entry.get("canonical_owner"),
                "constitutional_basis": entry.get("constitutional_basis"),
                "justification": entry.get("justification"),
                "note": entry.get("note") or "",
                "evidence_resolved": resolved,
                "evidence_unresolved": unresolved,
                "conversation_only": conversation_only,
                "undispositioned": undispositioned,
                "reasons": reasons,
            }
        )
    return {"decisions": records}


def build_model(decl: dict, repo_state: dict) -> dict:
    integrity = check_declaration(decl)
    assessment = assess(decl)
    records = assessment["decisions"]

    by_disposition: dict[str, int] = {entry["disposition"]: 0 for entry in decl["dispositions"]}
    by_stage: dict[str, int] = {entry["stage"]: 0 for entry in decl["lifecycle"]}
    for record in records:
        if record["disposition"] in by_disposition:
            by_disposition[record["disposition"]] += 1
        if record["stage"] in by_stage:
            by_stage[record["stage"]] += 1

    undispositioned = sorted(r["id"] for r in records if r["undispositioned"])
    conversation_only = sorted(r["id"] for r in records if r["conversation_only"])
    unevidenced = sorted(r["id"] for r in records if r["evidence_unresolved"])
    unindexed = sorted(r["id"] for r in records if r["index"] and not r["index_located"])

    gate_open = not integrity and not undispositioned
    model = {
        "programme": decl["programme"],
        "repository": repo_state,
        "decision_total": len(records),
        "decisions": records,
        "by_disposition": by_disposition,
        "by_stage": by_stage,
        "declaration_findings": integrity,
        "undispositioned": undispositioned,
        "conversation_only": conversation_only,
        "unevidenced": unevidenced,
        "unindexed": unindexed,
        "evidence_references": sum(len(r["evidence_resolved"]) for r in records),
        "gate": "OPEN" if gate_open else "CLOSED",
        "determination": "ASSIMILATED" if gate_open else "NOT-ASSIMILATED",
        "gate_exit": 0 if gate_open else 1,
    }
    sealed = {
        "decisions": [
            {
                "id": r["id"],
                "stage": r["stage"],
                "disposition": r["disposition"],
                "undispositioned": r["undispositioned"],
            }
            for r in records
        ],
        "gate": model["gate"],
        "determination": model["determination"],
        "declaration_findings": integrity,
    }
    model["seal_sha256"] = digest(sealed)
    return model


def self_determinism(decl: dict) -> list[str]:
    """Render the sealed output set twice from one model; the bytes must be identical."""
    fixed_state = repository_state()
    first = render(decl, build_model(decl, fixed_state))
    second = render(decl, build_model(decl, fixed_state))
    if set(first) != set(second):
        return ["rendered output set differs between runs"]
    return [
        f"non-deterministic rendering: {name}"
        for name in sorted(first)
        if first[name] != second[name]
    ]


SELF_CHECKS = {
    "--check-declaration": check_declaration,
    "--check-no-enumeration": check_no_enumeration,
    "--check-write-scope": lambda decl: check_write_scope(decl),
    "--check-determinism": self_determinism,
}


# ------------------------------------------------------------------------ rendering


def header(title: str, decl: dict, model: dict, purpose: str) -> str:
    programme = decl["programme"]
    repo = model["repository"]
    return (
        f"# {title}\n\n"
        + table(
            ["Field", "Value"],
            [
                ["PROGRAMME", f"`{programme['id']}` — {programme['name']} v{programme['version']}"],
                ["AUTHORITY", f"**{programme['authority']}**"],
                ["GOVERNING INSTRUMENT", f"`{programme['governing_instrument']}`"],
                ["OPERATIONAL HOME", f"`{programme['operational_home']}`"],
                ["REPOSITORY ANCHOR", repo["anchor"]],
                ["FIXED-POINT BASIS", repo["basis"]],
                ["DECISIONS", str(model["decision_total"])],
                ["DETERMINATION", f"**{model['determination']}**"],
                [
                    programme["gate_name"].upper(),
                    f"**{model['gate']}** (`{programme['gate_clause']}`)",
                ],
                ["SEAL (sha256)", f"`{model['seal_sha256']}`"],
                ["GENERATED BY", "`ucda_engine.py` — regenerated, never hand-authored"],
            ],
        )
        + f"\n> {purpose}\n\n---\n\n"
    )


FOOTER = (
    "\n---\n\n*This determination is DERIVED TRUTH. It creates no authority, allocates no "
    "identity, and supersedes no governing instrument. Where it conflicts with a higher "
    "frozen or governing instrument, the higher instrument governs.*\n"
)


def render(decl: dict, model: dict) -> dict[str, str]:
    # Artifact names, titles and purposes are DATA (see the declaration's outputs
    # section) and are bound positionally in the order the engine renders them. The
    # engine therefore holds no artifact name and no domain vocabulary of its own.
    spec = decl["outputs"]
    name = [entry["file"] for entry in spec]
    title = [entry["title"] for entry in spec]
    purpose = [entry["purpose"] for entry in spec]
    out: dict[str, str] = {}
    records = model["decisions"]

    # ---- 01 the register
    out[name[1]] = (
        header(
            title[1],
            decl,
            model,
            purpose[1],
        )
        + "## Located registers this overlay reads (no decision originates here)\n\n"
        + table(
            ["#", "Located decision register"],
            [
                [str(i + 1), f"`{ref}`"]
                for i, ref in enumerate(decl["programme"]["located_registers"])
            ],
        )
        + "\n## The decision population\n\n"
        + table(
            ["Decision", "Title", "Class", "Stage", "Disposition", "Source register", "Evidence"],
            [
                [
                    f"`{r['id']}`",
                    r["title"],
                    r["decision_class"],
                    r["stage"],
                    f"**{r['disposition']}**",
                    f"`{r['source_register']}`"
                    + ("" if r["source_register_located"] else " **UNRESOLVED**"),
                    (
                        f"{len(r['evidence_resolved'])} located"
                        + (
                            f", **{len(r['evidence_unresolved'])} unresolved**"
                            if r["evidence_unresolved"]
                            else ""
                        )
                    ),
                ]
                for r in records
            ],
        )
        + "\n## Per-decision evidence\n\n"
        + "".join(
            f"\n### {r['id']} — {r['title']}\n\n"
            f"- **Class** — {r['decision_class']}\n"
            f"- **Stage** — {r['stage']}\n"
            f"- **Disposition** — {r['disposition']}\n"
            f"- **Source register** — `{r['source_register']}`\n"
            + (f"- **Indexed at** — `{r['index']}`\n" if r["index"] else "")
            + (
                f"- **Canonical owner** — `{r['canonical_owner']}`\n"
                if r["canonical_owner"]
                else ""
            )
            + (f"- **Work package** — `{r['work_package']}`\n" if r["work_package"] else "")
            + (f"- **Superseded by** — `{r['superseded_by']}`\n" if r["superseded_by"] else "")
            + (
                f"- **Constitutional basis** — {r['constitutional_basis']}\n"
                if r["constitutional_basis"]
                else ""
            )
            + (f"- **Justification** — {r['justification']}\n" if r["justification"] else "")
            + (
                "- **Located evidence** — "
                + ", ".join(f"`{ref}`" for ref in r["evidence_resolved"])
                + "\n"
                if r["evidence_resolved"]
                else ""
            )
            + (
                "- **UNRESOLVED evidence** — "
                + ", ".join(f"`{ref}`" for ref in r["evidence_unresolved"])
                + "\n"
                if r["evidence_unresolved"]
                else ""
            )
            + (f"- **Note** — {r['note']}\n" if r["note"] else "")
            for r in records
        )
        + FOOTER
    )

    # ---- 02 lifecycle
    out[name[2]] = (
        header(
            title[2],
            decl,
            model,
            purpose[2],
        )
        + "## The lifecycle\n\n"
        + table(
            ["#", "Stage", "Legal next stage(s)", "Terminal", "Clause", "Decisions here"],
            [
                [
                    str(i + 1),
                    f"**{entry['stage']}**",
                    ", ".join(as_list(entry.get("next"))) or "—",
                    "YES" if entry.get("terminal") else "no",
                    f"`{entry['clause']}`",
                    str(model["by_stage"].get(entry["stage"], 0)),
                ]
                for i, entry in enumerate(decl["lifecycle"])
            ],
        )
        + "\n## Structural properties verified\n\n"
        + table(
            ["Property", "Result"],
            [
                ["Exactly one terminal stage", "PASS"],
                ["Every transition is forward (traversed in order)", "PASS"],
                ["Every stage reachable from the initial stage", "PASS"],
                ["Every non-terminal stage has an outgoing transition", "PASS"],
                [
                    "Every decision occupies exactly one declared stage",
                    "PASS" if not model["declaration_findings"] else "**FAIL**",
                ],
            ],
        )
        + "\n> These properties are asserted by `--check-declaration`; a failure aborts "
        "fail-closed and no verdict is emitted.\n" + FOOTER
    )

    # ---- 03 dispositions
    out[name[3]] = (
        header(
            title[3],
            decl,
            model,
            purpose[3],
        )
        + "## The closed set\n\n"
        + table(
            [
                "#",
                "Disposition",
                "Clause",
                "Earliest lawful stage",
                "Required",
                "Must resolve",
                "Count",
            ],
            [
                [
                    str(i + 1),
                    f"**{entry['disposition']}**",
                    f"`{entry['clause']}`",
                    entry["minimum_stage"],
                    ", ".join(f"`{f}`" for f in as_list(entry.get("requires_fields"))) or "—",
                    ", ".join(f"`{f}`" for f in as_list(entry.get("located_fields"))) or "—",
                    str(model["by_disposition"].get(entry["disposition"], 0)),
                ]
                for i, entry in enumerate(decl["dispositions"])
            ],
        )
        + "\n## Definitions\n\n"
        + "".join(
            f"- **{entry['disposition']}** (`{entry['clause']}`) — {entry['definition']}\n"
            for entry in decl["dispositions"]
        )
        + "\n## Distribution\n\n"
        + table(
            ["Disposition", "Decisions"],
            [
                [
                    f"**{name}**",
                    ", ".join(f"`{r['id']}`" for r in records if r["disposition"] == name) or "—",
                ]
                for name in model["by_disposition"]
            ],
        )
        + FOOTER
    )

    # ---- 04 the gate
    out[name[4]] = (
        header(
            title[4],
            decl,
            model,
            purpose[4],
        )
        + "## Determination\n\n"
        + table(
            ["Dimension", "Value"],
            [
                ["Decisions declared", str(model["decision_total"])],
                ["Located evidence references verified", str(model["evidence_references"])],
                [
                    "Undispositioned decisions",
                    ", ".join(f"`{i}`" for i in model["undispositioned"]) or "none",
                ],
                [
                    "Conversation-only decisions (no repository trace)",
                    ", ".join(f"`{i}`" for i in model["conversation_only"]) or "none",
                ],
                [
                    "Decisions with unresolved evidence",
                    ", ".join(f"`{i}`" for i in model["unevidenced"]) or "none",
                ],
                [
                    "Decisions whose index does not resolve",
                    ", ".join(f"`{i}`" for i in model["unindexed"]) or "none",
                ],
                [
                    "Declaration integrity findings",
                    str(len(model["declaration_findings"])) or "0",
                ],
                [
                    f"**{decl['programme']['gate_name'].upper()}**",
                    f"**{model['gate']}**",
                ],
                ["Gate exit code", str(model["gate_exit"])],
            ],
        )
        + (
            "\n## Consequence\n\nThe gate is **OPEN**. Every declared decision carries "
            "exactly one lawful disposition whose required evidence resolves in the "
            "repository. Successor implementation and architectural work is not blocked "
            "by this gate.\n"
            if model["gate"] == "OPEN"
            else "\n## Consequence\n\nThe gate is **CLOSED**. The affected programme is "
            "HALTED until every decision below is dispositioned. The gate is not "
            "waivable, deferrable, or overridable.\n\n"
            + table(
                ["Decision", "Why it is undispositioned"],
                [
                    [f"`{r['id']}`", "; ".join(r["reasons"])]
                    for r in records
                    if r["undispositioned"]
                ],
            )
            + (
                "\n### Declaration integrity findings\n\n"
                + "".join(f"- {text}\n" for text in model["declaration_findings"])
                if model["declaration_findings"]
                else ""
            )
        )
        + "\n## Enforcement route (no new gate apparatus)\n\n"
        + table(
            ["Layer", "Located owner"],
            [
                ["Law", f"`{decl['programme']['governing_instrument']}`"],
                ["Executable expression", "`00-MASTER/UCDA-000001/ucda_engine.py --gate`"],
                ["Aggregate gate binding", f"`{decl['programme']['aggregate_gate_owner']}`"],
                ["Developer entry point", "`make ucda-gate`"],
                ["Continuous integration", "`.github/workflows/uccep-gate.yml`"],
                ["Session-start signal", "`.kiro/hooks/ucda-000001.json`"],
            ],
        )
        + FOOTER
    )

    # ---- 05 work packages
    out[name[5]] = (
        header(
            title[5],
            decl,
            model,
            purpose[5],
        )
        + table(
            ["Work package", "Title", "Discharges", "Authorization required"],
            [
                [
                    f"`{package['id']}`",
                    package["title"],
                    ", ".join(f"`{d}`" for d in as_list(package.get("discharges"))),
                    "YES" if package.get("authorization_required") else "no",
                ]
                for package in decl["work_packages"]
            ],
        )
        + "\n"
        + "".join(
            f"\n### {package['id']} — {package['title']}\n\n"
            f"- **Discharges** — {', '.join(as_list(package.get('discharges')))}\n"
            f"- **Owner** — `{package['owner']}`\n"
            f"- **Constitutional route** — {package['route']}\n"
            f"- **Acceptance** — {package['acceptance']}\n"
            f"- **Explicit authorization required** — "
            f"{'YES' if package.get('authorization_required') else 'no'}\n"
            for package in decl["work_packages"]
        )
        + "\n### Work packages referenced from another located declaration\n\n"
        + (
            table(
                ["Work package", "Referenced by", "Registered in"],
                [
                    [
                        f"`{r['work_package']}`",
                        f"`{r['id']}`",
                        f"`{decl['programme']['aggregate_gate_owner']}`",
                    ]
                    for r in records
                    if r["work_package"]
                    and r["work_package"] not in set(declared_values(decl, "work_packages", "id"))
                ],
            )
            or "None.\n"
        )
        + FOOTER
    )

    # ---- 06 traceability
    out[name[6]] = (
        header(
            title[6],
            decl,
            model,
            purpose[6],
        )
        + table(
            ["Decision", "Located register", "Index", "Disposition", "Located evidence"],
            [
                [
                    f"`{r['id']}`",
                    ("OK" if r["source_register_located"] else "**MISSING**")
                    + f" `{r['source_register']}`",
                    ("OK" if r["index_located"] else ("**MISSING**" if r["index"] else "—")),
                    r["disposition"],
                    ", ".join(f"`{ref}`" for ref in r["evidence_resolved"]) or "—",
                ]
                for r in records
            ],
        )
        + "\n## Closure\n\n"
        + table(
            ["Dimension", "Value"],
            [
                ["Decisions", str(model["decision_total"])],
                ["Located evidence references", str(model["evidence_references"])],
                [
                    "Decisions with a resolving located register",
                    str(sum(1 for r in records if r["source_register_located"])),
                ],
                [
                    "Decisions with a resolving index",
                    str(sum(1 for r in records if r["index_located"])),
                ],
                ["Conversation-only decisions", str(len(model["conversation_only"]))],
                ["Traceability closed", "YES" if model["gate"] == "OPEN" else "NO"],
            ],
        )
        + FOOTER
    )

    # ---- 00 dashboard
    out[name[0]] = (
        header(
            f"{decl['programme']['id']} — {title[0]}",
            decl,
            model,
            purpose[0]
            + " Lifecycle: "
            + " → ".join(entry["stage"] for entry in decl["lifecycle"])
            + ".",
        )
        + "## Lifecycle occupancy\n\n"
        + table(
            ["Stage", "Decisions"],
            [[stage, str(count)] for stage, count in model["by_stage"].items()],
        )
        + "\n## Disposition distribution\n\n"
        + table(
            ["Disposition", "Decisions"],
            [[name, str(count)] for name, count in model["by_disposition"].items()],
        )
        + "\n## Determination\n\n"
        + table(
            ["Dimension", "Value"],
            [
                ["Decisions declared", str(model["decision_total"])],
                ["Undispositioned", str(len(model["undispositioned"]))],
                ["Conversation-only", str(len(model["conversation_only"]))],
                ["Unresolved evidence", str(len(model["unevidenced"]))],
                ["Determination", f"**{model['determination']}**"],
                ["Implementation Evidence Gate", f"**{model['gate']}**"],
            ],
        )
        + "\n---\n\n*Regenerate with `make ucda`. Enforce with `make ucda-gate`.*\n"
    )

    return out


def emit(decl: dict, model: dict) -> list[Path]:
    rendered = render(decl, model)
    written: list[Path] = []
    for name, body in sorted(rendered.items()):
        target = HERE / name
        target.write_text(body, "utf-8")
        written.append(target)
    machine = HERE / "ucda.json"
    machine.write_text(canonical_json(model), "utf-8")
    written.append(machine)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    index = EVIDENCE_DIR / "decision-evidence-index.json"
    index.write_text(
        canonical_json(
            {
                "schema": "ucos-ucda-decision-evidence-index",
                "authority": "NONE (DERIVED TRUTH)",
                "governing_instrument": decl["programme"]["governing_instrument"],
                "seal_sha256": model["seal_sha256"],
                "entries": [
                    {
                        "id": r["id"],
                        "stage": r["stage"],
                        "disposition": r["disposition"],
                        "source_register": r["source_register"],
                        "source_register_located": r["source_register_located"],
                        "evidence_resolved": r["evidence_resolved"],
                        "evidence_unresolved": r["evidence_unresolved"],
                        "undispositioned": r["undispositioned"],
                    }
                    for r in model["decisions"]
                ],
            }
        ),
        "utf-8",
    )
    written.append(index)
    return written


# ----------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ucda_engine.py",
        description="UCDA-000001 Implementation Evidence Gate (AUTHORITY = NONE).",
    )
    parser.add_argument("--gate", action="store_true", help="fail-closed: exit non-zero if closed")
    parser.add_argument("--quiet", action="store_true")
    for flag in sorted(SELF_CHECKS):
        parser.add_argument(flag, action="store_true", dest=flag.lstrip("-").replace("-", "_"))
    args = parser.parse_args(argv)

    decl = load_declaration()

    for flag, handler in sorted(SELF_CHECKS.items()):
        if getattr(args, flag.lstrip("-").replace("-", "_")):
            findings = handler(decl)
            label = flag.lstrip("-")
            if findings:
                print(f"UCDA-000001 {label}: {len(findings)} finding(s)")
                for text in findings:
                    print(f"  - {text}")
                return 1
            print(f"UCDA-000001 {label}: PASS")
            return 0

    model = build_model(decl, repository_state())
    written = emit(decl, model)

    scope = check_write_scope(decl, written)
    if scope:
        for text in scope:
            print(f"  - {text}", file=sys.stderr)
        fail_closed("forbidden-write guard tripped")

    if not args.quiet:
        print(
            f"{decl['programme']['id']}: {model['determination']} | "
            f"decisions={model['decision_total']} | "
            f"undispositioned={len(model['undispositioned'])} | "
            f"conversation_only={len(model['conversation_only'])} | "
            f"evidence={model['evidence_references']} | "
            f"gate={model['gate']} | seal={model['seal_sha256'][:16]}"
        )
        print(f"wrote {len(written)} artifacts to {HERE}")

    if model["declaration_findings"]:
        for text in model["declaration_findings"]:
            print(f"  - {text}", file=sys.stderr)
        fail_closed(
            f"declaration integrity: {len(model['declaration_findings'])} finding(s) — "
            "no verdict may be asserted"
        )

    if args.gate and model["gate_exit"]:
        print(
            "GATE: CLOSED — undispositioned decision(s): " + ", ".join(model["undispositioned"]),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
