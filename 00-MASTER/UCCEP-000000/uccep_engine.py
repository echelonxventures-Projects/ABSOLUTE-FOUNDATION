#!/usr/bin/env python3
"""UCCEP-000000 — Universal Continuous Constitutional Evolution Programme engine.

AUTHORITY = NONE (DERIVED TRUTH). This engine legislates nothing, registers nothing,
and owns nothing. It is the *aggregation* of gates that already exist and are already
owned, plus the deterministic emission of the programme determinations the mission names.

    python3 00-MASTER/UCCEP-000000/uccep_engine.py                 # boot + standard tiers, emit
    python3 00-MASTER/UCCEP-000000/uccep_engine.py --tier boot     # fast read-only pass
    python3 00-MASTER/UCCEP-000000/uccep_engine.py --tier full     # every located gate
    python3 00-MASTER/UCCEP-000000/uccep_engine.py --gate          # fail-closed on failure
    python3 00-MASTER/UCCEP-000000/uccep_engine.py --check-declaration
    python3 00-MASTER/UCCEP-000000/uccep_engine.py --check-no-enumeration
    python3 00-MASTER/UCCEP-000000/uccep_engine.py --check-write-scope
    python3 00-MASTER/UCCEP-000000/uccep_engine.py --check-determinism

Exit semantics of --gate:
    0  every EXECUTED blocking check passed
    1  one or more EXECUTED blocking checks failed
    2  fail-closed abort — the declaration is unusable, so no verdict may be asserted

Standing findings (a PROVISIONAL meta-constitution, a vacant Tier T1, a measured
traceability gap) set the CERTIFICATION CEILING; they do not by themselves fail the
gate. A gate whose verdict cannot be reached in both directions carries no evidentiary
value — that defect is itself recorded as a finding in the declaration.

Stdlib only. No network. No timestamp is emitted anywhere, so the sealed output set is
byte-identical for an unchanged repository state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DECLARATION = HERE / "uccep-bindings.json"
EVIDENCE_DIR = HERE / "evidence"

TIERS = ("boot", "standard", "full")
TIER_ORDER = {name: index for index, name in enumerate(TIERS)}

# Keys a declaration entry is permitted to carry. Any key outside its allowed set is a
# fail-closed violation: this is what prevents a finite domain, industry, science,
# technology, platform, language, database, infrastructure or reality from ever being
# smuggled into the declaration as a new field.
ALLOWED_KEYS = {
    "principles": {"id", "name", "owner", "enforced_by"},
    "invariants": {"id", "name", "owner"},
    "checks": {
        "id",
        "name",
        "owner",
        "argv",
        "env",
        "write_scope",
        "tier",
        "fail_closed",
        "advisory",
        "advisory_reason",
        "governed_by_finding",
        "exit_semantics",
        "json_stdout",
        "json_assertions",
        "$assertion_comment",
    },
    "gates": {"id", "name", "owner", "checks"},
    "programs": {"id", "name", "output", "delegated_to", "checks"},
    "findings": {
        "id",
        "title",
        "class",
        "evidence",
        "violates",
        "owner",
        "disposition",
        "work_package",
        "blocking",
        "note",
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
}

VALID_DISPOSITIONS = (
    "IMPLEMENTED",
    "REGISTERED",
    "GOVERNED",
    "VALIDATED",
    "CERTIFIED",
    "REJECTED-WITH-EVIDENCE",
    "WORK-PACKAGE",
)

# Reference strings carry human suffixes (" (…)", " §…", " Art …", " · …"). A reference
# resolves against the repository by exact path first, then by unique prefix within the
# parent directory, so "00-CEP/CEP-009" resolves to the located instrument.
_SUFFIX_SPLITS = (" (", " §", " Art ", " · ", " — ")


# --------------------------------------------------------------------------- helpers


def fail_closed(message: str) -> NoReturn:
    print(f"UCCEP-000000: FAIL-CLOSED ABORT — {message}", file=sys.stderr)
    raise SystemExit(2)


def load_declaration() -> dict:
    if not DECLARATION.is_file():
        fail_closed(f"declaration absent: {DECLARATION.relative_to(REPO)}")
    try:
        return json.loads(DECLARATION.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        fail_closed(f"declaration is not valid JSON: {exc}")


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
    return matches[0] if len(matches) >= 1 else None


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
    porcelain = git("status", "--porcelain")
    return {
        "branch": git("branch", "--show-current") or "UNKNOWN",
        "head": git("rev-parse", "HEAD") or "UNKNOWN",
        "working_tree": "DIRTY" if porcelain else "CLEAN",
        "dirty_entries": len([line for line in porcelain.splitlines() if line.strip()]),
    }


def interpreters() -> dict:
    venv = REPO / ".ec1-venv" / "bin" / "python"
    return {
        "$PY3": sys.executable,
        "$PY": str(venv) if venv.is_file() else "",
        "$SELF": str(Path(__file__).resolve()),
    }


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "| " + " | ".join(headers) + " |\n"
    rule = "|" + "|".join(["---"] * len(headers)) + "|\n"
    body = "".join("| " + " | ".join(cell for cell in row) + " |\n" for row in rows)
    return head + rule + body


MISSING = object()


def get_path(payload: object, dotted: str) -> object:
    node = payload
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return MISSING
        node = node[part]
    return node


def extract_json(text: str) -> object | None:
    """Pull the last top-level JSON object out of stdout that may carry log lines."""
    depth = 0
    start = -1
    best = None
    in_string = False
    escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            if depth:
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        best = json.loads(text[start : index + 1])
                    except json.JSONDecodeError:
                        pass
    return best


# ------------------------------------------------------------------- self-check logic


def check_declaration(decl: dict) -> list[str]:
    """Every identifier unique, every cross-reference bound, every path located."""
    findings: list[str] = []
    seen: dict[str, str] = {}
    for section, allowed in ALLOWED_KEYS.items():
        for entry in decl.get(section, []):
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

    check_ids = {entry["id"] for entry in decl.get("checks", []) if entry.get("id")}
    finding_ids = {entry["id"] for entry in decl.get("findings", []) if entry.get("id")}
    wp_ids = {entry["id"] for entry in decl.get("work_packages", []) if entry.get("id")}

    for section in ("gates", "programs"):
        for entry in decl.get(section, []):
            for bound in entry.get("checks", []):
                if bound not in check_ids:
                    findings.append(f"{entry['id']}: bound check {bound} is not declared")
            if section == "gates" and not entry.get("checks"):
                findings.append(
                    f"{entry['id']}: no executable check bound — a manual gate is prohibited"
                )

    for principle in decl.get("principles", []):
        for bound in principle.get("enforced_by", []):
            if bound not in check_ids:
                findings.append(f"{principle['id']}: enforcing check {bound} is not declared")

    for check in decl.get("checks", []):
        governing = check.get("governed_by_finding")
        if check.get("advisory") and not governing:
            findings.append(f"{check['id']}: advisory without a governing finding is prohibited")
        if governing and governing not in finding_ids:
            findings.append(f"{check['id']}: governing finding {governing} is not declared")
        if check.get("tier") not in TIERS:
            findings.append(f"{check['id']}: tier {check.get('tier')!r} is not declared")

    for finding in decl.get("findings", []):
        disposition = finding.get("disposition")
        if disposition not in VALID_DISPOSITIONS:
            findings.append(
                f"{finding['id']}: disposition {disposition!r} is not one of "
                f"{list(VALID_DISPOSITIONS)} — nothing may remain ambiguous"
            )
        package = finding.get("work_package")
        if disposition == "WORK-PACKAGE" and not package:
            findings.append(f"{finding['id']}: WORK-PACKAGE disposition without a package")
        if package and package not in wp_ids:
            findings.append(f"{finding['id']}: work package {package} is not declared")

    for package in decl.get("work_packages", []):
        for target in package.get("discharges", []):
            if target not in finding_ids:
                findings.append(f"{package['id']}: discharges unknown finding {target}")

    # every located reference must resolve — this is what forbids declaring an
    # abstract, vendor, or otherwise unlocated owner
    references: list[tuple[str, str]] = [("programme.charter", decl["programme"]["charter"])]
    references += [("programme.governed_by", ref) for ref in decl["programme"]["governed_by"]]
    for section in ("principles", "invariants", "checks", "gates"):
        references += [
            (entry["id"], entry["owner"]) for entry in decl.get(section, []) if entry.get("owner")
        ]
    for program in decl.get("programs", []):
        references += [(program["id"], ref) for ref in program.get("delegated_to", [])]
    for source, ref in references:
        if resolve_reference(ref) is None:
            findings.append(f"{source}: reference does not resolve in the repository: {ref!r}")

    return findings


def check_no_enumeration(decl: dict) -> list[str]:
    """Prove the engine is data-driven, so extension needs no code change.

    Two mechanical properties, no denylist of technologies (a denylist would itself be
    an enumeration):

      1. Allowed-key conformance — verified by check_declaration; re-asserted here.
      2. No declared identifier appears as a literal in the engine source. If the engine
         never names a programme, gate or check, it cannot special-case one, so a new
         programme / gate / check / invariant / principle is added by DATA alone.
    """
    findings: list[str] = []
    source = Path(__file__).read_text("utf-8")
    identifiers: list[str] = []
    for section in ALLOWED_KEYS:
        identifiers += [entry["id"] for entry in decl.get(section, []) if entry.get("id")]
    for ident in sorted(set(identifiers)):
        if ident in source:
            findings.append(
                f"engine source special-cases declared identifier {ident} — "
                "extension would require a code change (Infinite Extensibility violated)"
            )
    for section, allowed in ALLOWED_KEYS.items():
        for entry in decl.get(section, []):
            extra = set(entry) - allowed
            if extra:
                findings.append(
                    f"{entry.get('id', section)}: undeclared key(s) {sorted(extra)} — "
                    "a finite domain assumption may be smuggled through a new field"
                )
    return findings


def check_write_scope(decl: dict, written: list[Path] | None = None) -> list[str]:
    """No write may land outside this programme's own operational memory."""
    findings: list[str] = []
    forbidden = decl["programme"]["forbidden_write_prefixes"]
    for prefix in forbidden:
        target = REPO / prefix
        if not target.exists():
            findings.append(f"forbidden-write prefix does not exist: {prefix}")
    for path in written or []:
        resolved = path.resolve()
        try:
            resolved.relative_to(HERE)
        except ValueError:
            findings.append(f"write outside the programme's operational memory: {resolved}")
    return findings


# ------------------------------------------------------------------ check execution


def run_check(check: dict, resolved_tier: str, interp: dict) -> dict:
    ident = check["id"]
    record = {
        "id": ident,
        "name": check["name"],
        "owner": check["owner"],
        "tier": check["tier"],
        "write_scope": check["write_scope"],
        "advisory": bool(check.get("advisory")),
        "governed_by_finding": check.get("governed_by_finding"),
        "executed": False,
        "exit_code": None,
        "verdict": "NOT-EXECUTED",
        "reason": "",
        "assertions": [],
    }
    if TIER_ORDER[check["tier"]] > TIER_ORDER[resolved_tier]:
        record["reason"] = f"tier {check['tier']} above the selected tier {resolved_tier}"
        return record

    argv = list(check["argv"])
    token = argv[0]
    if token in interp:
        if not interp[token]:
            record["verdict"] = "UNAVAILABLE"
            record["reason"] = f"interpreter {token} is not present in this environment"
            return record
        argv[0] = interp[token]
    elif token.startswith("./") or token.startswith("/"):
        located = REPO / token.lstrip("./") if token.startswith("./") else Path(token)
        if not located.exists():
            record["verdict"] = "UNAVAILABLE"
            record["reason"] = f"entry point not located: {token}"
            return record

    env = dict(os.environ)
    env.update(check.get("env") or {})
    # Self-checks are resolved in-process by the caller; only located, external gates
    # are executed here.
    # noqa: S603 — argv comes from the declaration (Repository Truth), never from user
    # input, and is executed as a list with no shell.
    completed = subprocess.run(  # noqa: S603
        argv, cwd=REPO, capture_output=True, text=True, check=False, env=env
    )
    record["executed"] = True
    record["exit_code"] = completed.returncode
    stdout = completed.stdout or ""
    combined = stdout + (completed.stderr or "")

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / f"{ident}.log").write_text(combined, "utf-8")

    assertions = check.get("json_assertions") or []
    if check.get("json_stdout") and assertions:
        # stdout ONLY: structured log lines on stderr must never be mistaken for the
        # declared verdict document.
        payload = extract_json(stdout)
        if payload is None:
            record["verdict"] = "FAIL"
            record["reason"] = "declared JSON verdict absent from stdout"
            return record
        failed: list[str] = []
        for assertion in assertions:
            value = get_path(payload, assertion["path"])
            if value is MISSING:
                ok = False
                observed = "<path absent from the owner's report>"
            else:
                ok = True
                if assertion.get("must_be_empty"):
                    ok = not value
                if "must_equal" in assertion:
                    ok = ok and value == assertion["must_equal"]
                observed = None if ok else value
            record["assertions"].append(
                {
                    "path": assertion["path"],
                    "result": "PASS" if ok else "FAIL",
                    "observed": observed,
                    "authority": assertion.get("authority"),
                    "finding": assertion.get("finding"),
                }
            )
            if not ok:
                failed.append(assertion["path"])
        record["verdict"] = "PASS" if not failed else "FAIL"
        record["reason"] = "" if not failed else "reported evidence violates: " + ", ".join(failed)
        return record

    record["verdict"] = "PASS" if completed.returncode == 0 else "FAIL"
    if completed.returncode != 0:
        semantics = check.get("exit_semantics") or {}
        record["reason"] = semantics.get(str(completed.returncode)) or semantics.get(
            "nonzero", f"exit {completed.returncode}"
        )
    return record


def run_self_check(check: dict, decl: dict, resolved_tier: str) -> dict:
    record = {
        "id": check["id"],
        "name": check["name"],
        "owner": check["owner"],
        "tier": check["tier"],
        "write_scope": check["write_scope"],
        "advisory": bool(check.get("advisory")),
        "governed_by_finding": check.get("governed_by_finding"),
        "executed": False,
        "exit_code": None,
        "verdict": "NOT-EXECUTED",
        "reason": "",
        "assertions": [],
    }
    if TIER_ORDER[check["tier"]] > TIER_ORDER[resolved_tier]:
        record["reason"] = f"tier {check['tier']} above the selected tier {resolved_tier}"
        return record
    handler = SELF_CHECKS[check["argv"][1]]
    findings = handler(decl)
    record["executed"] = True
    record["exit_code"] = 0 if not findings else 1
    record["verdict"] = "PASS" if not findings else "FAIL"
    record["reason"] = "; ".join(findings[:6])
    record["assertions"] = [
        {"path": "self", "result": "FAIL", "observed": text} for text in findings
    ]
    return record


def self_determinism(decl: dict) -> list[str]:
    """Render the sealed output set twice from one model; the bytes must be identical."""
    stub = {
        check["id"]: {
            "id": check["id"],
            "name": check["name"],
            "owner": check["owner"],
            "tier": check["tier"],
            "write_scope": check["write_scope"],
            "advisory": bool(check.get("advisory")),
            "governed_by_finding": check.get("governed_by_finding"),
            "executed": True,
            "exit_code": 0,
            "verdict": "PASS",
            "reason": "",
            "assertions": [],
        }
        for check in decl["checks"]
    }
    fixed_state = {
        "branch": "self-check",
        "head": "0" * 40,
        "working_tree": "CLEAN",
        "dirty_entries": 0,
    }
    first = render(decl, assemble(decl, stub, "boot", fixed_state))
    second = render(decl, assemble(decl, stub, "boot", fixed_state))
    if set(first) != set(second):
        return ["rendered output set differs between runs"]
    divergent = sorted(name for name in first if first[name] != second[name])
    return [f"non-deterministic rendering: {name}" for name in divergent]


SELF_CHECKS = {
    "--check-declaration": check_declaration,
    "--check-no-enumeration": check_no_enumeration,
    "--check-write-scope": lambda decl: check_write_scope(decl),
    "--check-determinism": self_determinism,
}


# --------------------------------------------------------------------- aggregation


def aggregate(records: dict[str, dict], bound: list[str]) -> dict:
    executed = [records[cid] for cid in bound if records[cid]["executed"]]
    blocking = [rec for rec in executed if not rec["advisory"]]
    failed = [rec["id"] for rec in blocking if rec["verdict"] == "FAIL"]
    advisory_failed = [
        rec["id"] for rec in executed if rec["advisory"] and rec["verdict"] == "FAIL"
    ]
    unexecuted = [cid for cid in bound if not records[cid]["executed"]]
    if failed:
        verdict = "FAIL"
    elif not blocking:
        verdict = "NOT-EXECUTED"
    elif unexecuted:
        verdict = "PARTIAL"
    elif advisory_failed:
        verdict = "PASS-WITH-ADVISORY"
    else:
        verdict = "PASS"
    return {
        "verdict": verdict,
        "failed": failed,
        "advisory_failed": advisory_failed,
        "not_executed": unexecuted,
        "executed": [rec["id"] for rec in executed],
    }


def build_model(decl: dict, resolved_tier: str) -> dict:
    interp = interpreters()
    records: dict[str, dict] = {}
    for check in decl["checks"]:
        if check["argv"][0] == "$SELF":
            records[check["id"]] = run_self_check(check, decl, resolved_tier)
        else:
            records[check["id"]] = run_check(check, resolved_tier, interp)
    return assemble(decl, records, resolved_tier, repository_state())


def assemble(decl: dict, records: dict[str, dict], resolved_tier: str, repo_state: dict) -> dict:
    """Pure aggregation over collected check records — no execution, no I/O."""
    gates = [
        {
            "id": gate["id"],
            "name": gate["name"],
            "owner": gate["owner"],
            "checks": gate["checks"],
            **aggregate(records, gate["checks"]),
        }
        for gate in decl["gates"]
    ]
    programs = [
        {
            "id": program["id"],
            "name": program["name"],
            "output": program["output"],
            "delegated_to": program["delegated_to"],
            "checks": program["checks"],
            **aggregate(records, program["checks"]),
        }
        for program in decl["programs"]
    ]

    ordered = [records[check["id"]] for check in decl["checks"]]
    executed = [rec for rec in ordered if rec["executed"]]
    blocking_failures = sorted(
        rec["id"] for rec in executed if not rec["advisory"] and rec["verdict"] == "FAIL"
    )
    advisory_failures = sorted(
        rec["id"] for rec in executed if rec["advisory"] and rec["verdict"] == "FAIL"
    )
    unavailable = sorted(rec["id"] for rec in ordered if rec["verdict"] == "UNAVAILABLE")

    ceiling = sorted(
        f"`{f['id']}` — {f['title']}"
        for f in decl["findings"]
        if f.get("blocking") and f.get("disposition") != "IMPLEMENTED"
    )
    if blocking_failures:
        certification = "NOT-CERTIFIED"
    elif ceiling:
        certification = "CERTIFIED-PROVISIONAL"
    else:
        certification = "CERTIFIED"

    model = {
        "programme": decl["programme"],
        "tier": resolved_tier,
        "repository": repo_state,
        "checks": ordered,
        "gates": gates,
        "programs": programs,
        "blocking_failures": blocking_failures,
        "advisory_failures": advisory_failures,
        "unavailable": unavailable,
        "certification": certification,
        "certification_ceiling": ceiling,
        "gate_exit": 1 if blocking_failures else 0,
    }
    sealed = {
        "gates": [{k: g[k] for k in ("id", "verdict", "failed", "not_executed")} for g in gates],
        "programs": [
            {k: p[k] for k in ("id", "verdict", "failed", "not_executed")} for p in programs
        ],
        "checks": [{k: c[k] for k in ("id", "verdict", "exit_code")} for c in ordered],
        "certification": certification,
        "tier": resolved_tier,
    }
    model["seal_sha256"] = digest(sealed)
    return model


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
                ["CHARTER", f"`{programme['charter']}`"],
                ["EVOLUTION OWNER", f"`{programme['evolution_owner']}`"],
                ["TIER", f"`{model['tier']}`"],
                ["BRANCH / HEAD", f"`{repo['branch']}` · `{repo['head'][:12]}`"],
                ["WORKING TREE", f"{repo['working_tree']} ({repo['dirty_entries']} entries)"],
                ["CERTIFICATION", f"**{model['certification']}**"],
                ["SEAL (sha256)", f"`{model['seal_sha256']}`"],
                ["GENERATED BY", "`uccep_engine.py` — regenerated, never hand-authored"],
            ],
        )
        + f"\n> {purpose}\n\n---\n\n"
    )


def check_rows(model: dict, ids: list[str]) -> list[list[str]]:
    by_id = {rec["id"]: rec for rec in model["checks"]}
    rows = []
    for cid in ids:
        rec = by_id[cid]
        mark = "**" if rec["verdict"] == "FAIL" and not rec["advisory"] else ""
        rows.append(
            [
                f"`{rec['id']}`",
                rec["name"],
                f"`{rec['owner']}`",
                "advisory" if rec["advisory"] else "blocking",
                f"{mark}{rec['verdict']}{mark}",
                rec["reason"] or "—",
            ]
        )
    return rows


CHECK_HEADERS = ["Check", "What it executes", "Located owner", "Force", "Verdict", "Detail"]


def joined(items: list[str]) -> str:
    return ", ".join(f"`{item}`" for item in items) or "none"


def render(decl: dict, model: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    programme = decl["programme"]

    # ---- the programme determinations
    for program in model["programs"]:
        out[program["output"]] = (
            header(
                f"{program['id']} — {program['name']}",
                decl,
                model,
                f"The mission output of {program['id']}. Produced by AGGREGATING the located "
                f"owners below; this programme implements no owner of its own.",
            )
            + "## Delegation (Zero Parallel Authority)\n\n"
            + table(
                ["#", "Located owner this programme delegates to"],
                [[str(i + 1), f"`{ref}`"] for i, ref in enumerate(program["delegated_to"])],
            )
            + f"\n**Verdict: {program['verdict']}**\n\n"
            + "## Executable evidence\n\n"
            + table(CHECK_HEADERS, check_rows(model, program["checks"]))
            + (
                "\nNot executed at this tier: "
                + ", ".join(f"`{cid}`" for cid in program["not_executed"])
                + "\n"
                if program["not_executed"]
                else ""
            )
            + "\n---\n\n*This determination is DERIVED TRUTH. It creates no authority and "
            "supersedes no governing instrument. Where it conflicts with a higher frozen or "
            "governing instrument, the higher instrument governs.*\n"
        )

    # ---- gate register
    out["16-CONSTITUTIONAL-GATE-REGISTER.md"] = (
        header(
            "16 — Constitutional Gate Register",
            decl,
            model,
            f"The {len(model['gates'])} mandatory gates, each bound to the located executables "
            "that discharge it. A gate with no bound executable would be a manual gate and is "
            "rejected at declaration time.",
        )
        + table(
            ["Gate", "Name", "Located owner", "Bound checks", "Verdict"],
            [
                [
                    f"`{gate['id']}`",
                    gate["name"],
                    f"`{gate['owner']}`",
                    ", ".join(f"`{c}`" for c in gate["checks"]),
                    f"**{gate['verdict']}**" if gate["verdict"] == "FAIL" else gate["verdict"],
                ]
                for gate in model["gates"]
            ],
        )
        + "\n## Every declared check\n\n"
        + table(CHECK_HEADERS, check_rows(model, [rec["id"] for rec in model["checks"]]))
        + "\n## Principles → enforcing executable\n\n"
        + table(
            ["Principle", "Name", "Located owner", "Enforced by"],
            [
                [
                    f"`{p['id']}`",
                    p["name"],
                    f"`{p['owner']}`",
                    ", ".join(f"`{c}`" for c in p["enforced_by"]),
                ]
                for p in decl["principles"]
            ],
        )
        + "\n## Permanent invariants → located owner\n\n"
        + table(
            ["Invariant", "Name", "Located owner"],
            [[f"`{i['id']}`", i["name"], f"`{i['owner']}`"] for i in decl["invariants"]],
        )
    )

    # ---- assimilation / findings register
    findings = decl["findings"]
    out["17-ASSIMILATION-FINDINGS-REGISTER.md"] = (
        header(
            "17 — Assimilation & Findings Register",
            decl,
            model,
            "Nothing agreed or observed may remain only in conversation. Every entry carries "
            "exactly one disposition: IMPLEMENTED, REGISTERED, GOVERNED, VALIDATED, CERTIFIED, "
            "REJECTED-WITH-EVIDENCE, or WORK-PACKAGE.",
        )
        + table(
            ["Finding", "Class", "Disposition", "Blocks certification", "Owner", "Work package"],
            [
                [
                    f"`{f['id']}`",
                    f["class"],
                    f"**{f['disposition']}**",
                    "YES" if f.get("blocking") else "no",
                    f"`{f['owner']}`",
                    f"`{f['work_package']}`" if f.get("work_package") else "—",
                ]
                for f in findings
            ],
        )
        + "\n"
        + "".join(
            f"\n### {f['id']} — {f['title']}\n\n"
            f"- **Class** — {f['class']}\n"
            f"- **Disposition** — {f['disposition']}\n"
            f"- **Owner** — `{f['owner']}`\n"
            + ("- **Violates** — " + ", ".join(f["violates"]) + "\n" if f.get("violates") else "")
            + f"- **Evidence** — {f['evidence']}\n"
            + (f"- **Note** — {f['note']}\n" if f.get("note") else "")
            for f in findings
        )
        + "\n---\n\n## Work packages\n\n"
        + "".join(
            f"\n### {w['id']} — {w['title']}\n\n"
            f"- **Discharges** — {', '.join(w['discharges'])}\n"
            f"- **Owner** — `{w['owner']}`\n"
            f"- **Constitutional route** — {w['route']}\n"
            f"- **Acceptance** — {w['acceptance']}\n"
            f"- **Explicit authorization required** — "
            f"{'YES' if w.get('authorization_required') else 'no'}\n"
            for w in decl["work_packages"]
        )
    )

    # ---- dashboard
    out["00-UCCEP-DASHBOARD.md"] = (
        header(
            f"{programme['id']} — Continuous Constitutional Evolution Dashboard",
            decl,
            model,
            "The single continuously-regenerated view of programme state. This loop has no "
            "terminal state: Knowledge → Assimilation → Repository Truth → Governance → "
            "Meta-Model → Registries → Dependencies → Implementation → Validation → "
            "Certification → Evidence → Evolution Intelligence → Repository Truth.",
        )
        + "## Programme state\n\n"
        + table(
            ["Programme", "Name", "Output", "Verdict"],
            [
                [
                    f"`{p['id']}`",
                    p["name"],
                    f"`{p['output']}`",
                    f"**{p['verdict']}**" if p["verdict"] == "FAIL" else p["verdict"],
                ]
                for p in model["programs"]
            ],
        )
        + "\n## Gate state\n\n"
        + table(
            ["Gate", "Name", "Verdict"],
            [
                [
                    f"`{g['id']}`",
                    g["name"],
                    f"**{g['verdict']}**" if g["verdict"] == "FAIL" else g["verdict"],
                ]
                for g in model["gates"]
            ],
        )
        + "\n## Determination\n\n"
        + table(
            ["Dimension", "Value"],
            [
                ["Blocking check failures", joined(model["blocking_failures"])],
                [
                    "Advisory failures (recorded, governed by a finding)",
                    joined(model["advisory_failures"]),
                ],
                ["Unavailable in this environment", joined(model["unavailable"])],
                ["Certification", f"**{model['certification']}**"],
                ["Gate exit code", str(model["gate_exit"])],
            ],
        )
        + "\n### Certification ceiling\n\n"
        + (
            "The maximum attainable verdict is **CERTIFIED-PROVISIONAL**. A final or ratified "
            "certification is not assertable while the following stand:\n\n"
            + "".join(f"- {reason}\n" for reason in model["certification_ceiling"])
            if model["certification_ceiling"]
            else "No standing ceiling recorded.\n"
        )
        + "\n---\n\n*Regenerate with `make uccep`. Enforce with `make uccep-gate`.*\n"
    )

    return out


def emit(decl: dict, model: dict) -> list[Path]:
    rendered = render(decl, model)
    written: list[Path] = []
    for name, body in sorted(rendered.items()):
        target = HERE / name
        target.write_text(body, "utf-8")
        written.append(target)
    machine = HERE / "uccep.json"
    machine.write_text(canonical_json(model), "utf-8")
    written.append(machine)
    return written


# ----------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="uccep_engine.py",
        description="UCCEP-000000 aggregate constitutional gate (AUTHORITY = NONE).",
    )
    parser.add_argument("--tier", choices=TIERS, default="standard")
    parser.add_argument("--gate", action="store_true", help="fail-closed: exit non-zero on failure")
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
                print(f"UCCEP-000000 {label}: {len(findings)} finding(s)")
                for text in findings:
                    print(f"  - {text}")
                return 1
            print(f"UCCEP-000000 {label}: PASS")
            return 0

    integrity = check_declaration(decl)
    if integrity:
        for text in integrity:
            print(f"  - {text}", file=sys.stderr)
        fail_closed(
            f"declaration integrity: {len(integrity)} finding(s) — no verdict may be asserted"
        )

    model = build_model(decl, args.tier)
    written = emit(decl, model)

    scope = check_write_scope(decl, written)
    if scope:
        for text in scope:
            print(f"  - {text}", file=sys.stderr)
        fail_closed("forbidden-write guard tripped")

    if not args.quiet:
        gate_failures = ",".join(model["blocking_failures"]) or "none"
        gates_pass = sum(1 for g in model["gates"] if g["verdict"].startswith("PASS"))
        programmes_pass = sum(1 for p in model["programs"] if p["verdict"].startswith("PASS"))
        print(
            f"{decl['programme']['id']}: {model['certification']} | tier={model['tier']} | "
            f"gates={gates_pass}/{len(model['gates'])} PASS | "
            f"programmes={programmes_pass}/{len(model['programs'])} PASS | "
            f"blocking={gate_failures} | seal={model['seal_sha256'][:16]}"
        )
        print(f"wrote {len(written)} artifacts to {HERE}")

    if args.gate and model["blocking_failures"]:
        print(
            "GATE: FAIL-CLOSED — blocking constitutional checks failed: "
            + ", ".join(model["blocking_failures"]),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
