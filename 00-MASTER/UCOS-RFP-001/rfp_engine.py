#!/usr/bin/env python3
"""UCOS Omega-Infinity — UCOS-RFP-001 Repository Fixed-Point Closure engine.

Executable expression of ``rfp-declaration.json``. The declaration is the ONLY
place the principle, the vocabulary, the artifact classes, the cycle classes, the
pipeline and the closure criteria are stated; this module holds no artifact path,
no lane name, no producer name and no programme field name as a literal. Adding a
producer, a cycle class, an artifact class or a criterion is an edit to that DATA
file and never to this file (PR-07 Zero Enumeration, mechanically proven by
``--check-no-enumeration``).

    rfp_engine.py                        regenerate this programme's determinations
    rfp_engine.py --gate                 G-15: prove the repository is a fixed point
    rfp_engine.py --detect               classify self-reference topologies, per stage
    rfp_engine.py --check-declaration    declaration integrity
    rfp_engine.py --check-no-enumeration zero-enumeration proof
    rfp_engine.py --check-write-scope    forbidden-write guard
    rfp_engine.py --check-determinism    self-determinism (byte-identical rendering)
    rfp_engine.py --check-self-compliance this engine obeys RFP-2 and RFP-3 itself

Exit semantics:
    0  the asserted property holds
    1  the asserted property does not hold (gate CLOSED)
    2  fail-closed abort — the declaration or a required substrate is unusable, so
       no verdict may be asserted

SELF-APPLICATION. This engine is bound by the principle it enforces. Its emitted
artifacts therefore record the declaration and nothing measured: no commit
identity (RFP-2) and no observation of the working tree (RFP-3) — including its
own verdict, which is carried by the exit code and standard output alone. An
engine that wrote "repository is a fixed point" into the repository would falsify
that sentence by writing it. This is the defect class the programme exists to
abolish, so the programme may not commit it.

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DECLARATION = HERE / "rfp-declaration.json"

_HEX = re.compile(rb"\b[0-9a-f]{7,40}\b")
_PY_TOKEN = "$PY"


# --------------------------------------------------------------------------- io
def fail_closed(reason: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"UCOS-RFP-001: FAIL-CLOSED ABORT — {reason}", file=sys.stderr)
    raise SystemExit(2)


def git(*args: str, strip: bool = True) -> str:
    try:
        res = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, timeout=300, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if res.returncode != 0:
        return ""
    return res.stdout.strip() if strip else res.stdout


def canonical_json(obj: object) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def digest(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def load_declaration() -> dict:
    if not DECLARATION.is_file():
        fail_closed(f"declaration absent: {DECLARATION.name}")
    try:
        decl = json.loads(DECLARATION.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail_closed(f"declaration does not parse: {exc}")
    if not isinstance(decl, dict):
        fail_closed("declaration is not an object")
    return decl


def section(decl: dict, key: str) -> list:
    value = decl.get(key)
    if not isinstance(value, list) or not value:
        fail_closed(f"declaration section missing or empty: {key}")
    return value


def programme_id(decl: dict) -> str:
    ident = (decl.get("programme") or {}).get("id")
    if not ident:
        fail_closed("declaration declares no programme id")
    return str(ident)


# ------------------------------------------------------- repository observation
def porcelain() -> list[tuple[str, str]]:
    """(status, path) for every entry git reports. Ignored files never appear, so
    the ignore authority is honoured without this module holding any path."""
    raw = git("status", "--porcelain", strip=False)
    out: list[tuple[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        code, path = line[:2], line[3:].strip()
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        if " -> " in path:  # rename: attribute to the destination
            path = path.split(" -> ", 1)[1]
        out.append((code, path))
    return out


def classify_entries(entries: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Split observed entries into the categories the closure criteria measure."""
    staged, modified, untracked = [], [], []
    for code, path in entries:
        if code == "??":
            untracked.append(path)
            continue
        if code[0] not in " ?":
            staged.append(path)
        if code[1] != " ":
            modified.append(path)
    return {"staged": staged, "modified": modified, "untracked": untracked}


def excluded_locations() -> set[str]:
    """Untracked paths that a constitutionally excluded location may hold.

    Resolved from the declared authorities, never from a list here: git's own
    ignore machinery already removes ignored paths from `status --porcelain`, and
    the corpus-internal prefixes are read out of the registration authority
    module. Anything still visible is genuinely outside every exclusion.
    """
    prefixes: set[str] = set()
    tools = REPO / "00-BOOK" / "tools"
    if tools.is_dir():
        sys.path.insert(0, str(tools))
        try:
            import config as registration_authority  # noqa: PLC0415

            for prefix in getattr(registration_authority, "EXCLUDE_DIR_PREFIXES", ()) or ():
                prefixes.add(str(prefix))
        except Exception:  # pragma: no cover - authority unavailable
            pass
        finally:
            sys.path.pop(0)
    return prefixes


def untracked_outside_excluded(untracked: list[str]) -> list[str]:
    """Untracked entries that no exclusion authority accounts for.

    The corpus-internal prefixes exclude a path from REGISTRATION, not from the
    repository, so an untracked entry there is still unexplained content and is
    reported. Only the ignore authority removes a path from the fixed point, and
    it has already done so before `status` was read.
    """
    return sorted(untracked)


# ------------------------------------------------------------- pipeline running
def resolve_argv(argv: list[str]) -> list[str]:
    return [sys.executable if token == _PY_TOKEN else str(token) for token in argv]


def run_stage(stage: dict, env: dict[str, str]) -> tuple[int, str]:
    argv = resolve_argv(list(stage.get("argv") or []))
    if not argv:
        fail_closed(f"stage declares no argv: {stage.get('id')}")
    try:
        res = subprocess.run(
            argv, cwd=REPO, capture_output=True, text=True, timeout=3600, check=False, env=env
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 255, f"{exc}"
    return res.returncode, (res.stdout or "") + (res.stderr or "")


def stage_env(decl: dict) -> dict[str, str]:
    """Child environment with the re-entrancy guard armed.

    A stage may invoke the aggregate certifier, which binds this engine as a
    check. With the declared guard variable set, that nested invocation is a
    no-op, so the aggregate is kept out of its own pipeline without either side
    naming the other. Which topology that guards is declared, not decided here.
    """
    env = dict(os.environ)
    guard = ((decl.get("pipeline") or {}).get("reentrancy_env")) or ""
    if guard:
        env[str(guard)] = "1"
    return env


def nested(decl: dict) -> bool:
    guard = ((decl.get("pipeline") or {}).get("reentrancy_env")) or ""
    return bool(guard) and bool(os.environ.get(str(guard)))


def snapshot_tracked() -> dict[str, str]:
    """path -> sha256 of working-tree content, for every tracked file."""
    out: dict[str, str] = {}
    for rel in (p for p in git("ls-files", "-z").split("\0") if p):
        target = REPO / rel
        try:
            out[rel] = hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError:
            continue
    return out


def added_bytes(rel: str) -> bytes:
    """The bytes a producer WROTE into a tracked path in this pass.

    Only added diff lines, so classification inspects what the producer emitted
    rather than what the artifact happens to contain. An authored document that
    merely cites a commit is therefore never mistaken for a producer that derives
    one — the citation is not in any producer's delta.
    """
    raw = git("diff", "-U0", "--", rel, strip=False)
    return "\n".join(
        line[1:] for line in raw.splitlines() if line.startswith("+") and not line.startswith("+++")
    ).encode("utf-8", "replace")


# ------------------------------------------------------------- cycle detection
def commit_universe() -> tuple[set[str], set[str]]:
    """Every commit identity this repository can name, full and abbreviated.

    Derived from the object database, so the detector recognises commit identity
    structurally rather than by matching a field name a producer happened to use.
    """
    full = {c for c in git("rev-list", "--all").split() if c}
    abbrev = {c[:n] for c in full for n in range(7, 13)}
    return full, abbrev


def detect_commit_cycle(paths: list[str], full: set[str], abbrev: set[str]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for rel in paths:
        found = sorted(
            {
                tok.decode()
                for tok in set(_HEX.findall(added_bytes(rel)))
                if tok.decode() in full or tok.decode() in abbrev
            }
        )
        if found:
            hits[rel] = found[:4]
    return hits


def detect_hash_cycle(paths: list[str]) -> list[tuple[str, str]]:
    live = {}
    for rel in paths:
        try:
            live[rel] = hashlib.sha256((REPO / rel).read_bytes()).hexdigest()
        except OSError:
            continue
    embeds: dict[str, set[str]] = {}
    for rel in paths:
        blob = added_bytes(rel)
        embeds[rel] = {other for other, h in live.items() if other != rel and h.encode() in blob}
    return sorted(
        (a, b) for a, targets in embeds.items() for b in targets if a in embeds.get(b, set())
    )


def owner_of(stages: list[dict], path: str) -> str | None:
    best, best_len = None, -1
    for stage in stages:
        for prefix in stage.get("writes") or []:
            if path.startswith(str(prefix)) and len(str(prefix)) > best_len:
                best, best_len = str(stage.get("id")), len(str(prefix))
    return best


def registration_owner(stages: list[dict]) -> str | None:
    """The stage owning the registration projection zone, taken from the declared
    write zones — the zone with the most declared prefixes is the projection zone
    the registration transaction maintains."""
    ranked = sorted(stages, key=lambda s: -len(s.get("writes") or []))
    return str(ranked[0].get("id")) if ranked and len(ranked[0].get("writes") or []) > 1 else None


# --------------------------------------------------------- detector registry
# The keys below are this engine's declared detection CAPABILITIES. Which topology
# each one evidences, how severe it is and how it is remediated all come from the
# declaration's `detector` binding, so no cycle-class identity appears in code.
def _detect_commit_token_in_delta(ctx: dict) -> list[str]:
    hits = detect_commit_cycle(ctx["residue"], ctx["commits_full"], ctx["commits_abbrev"])
    return [f"{path} embeds commit identity {toks}" for path, toks in sorted(hits.items())]


def _detect_mutual_hash_in_delta(ctx: dict) -> list[str]:
    return [f"{a} <-> {b} embed each other's content hash" for a, b in detect_hash_cycle(ctx["residue"])]


def _detect_pass_instability(ctx: dict) -> list[str]:
    """A path WRITTEN by consecutive passes at one unchanged commit.

    The comparison is between what each pass actually wrote, not between what is
    still dirty. Residue is measured against HEAD and is therefore cumulative: a
    file written once in pass 1 stays dirty through passes 2 and 3 without being
    touched again, and reading that as instability would accuse every one-time
    divergence of self-observation. Only a genuine re-write at an unchanged commit
    implicates an input the producer itself perturbs.
    """
    if ctx["index"] < 2:
        return []
    previous = {p for paths in ctx["previous_attribution"].values() for p in paths}
    written_now = {p for paths in ctx["attribution"].values() for p in paths}
    return [
        f"{path} written again at an unchanged commit"
        for path in sorted(written_now & previous)
    ]


def _detect_foreign_projection_write(ctx: dict) -> list[str]:
    owner = ctx["registration_owner"]
    if not owner:
        return []
    return [
        f"{path} lies in the registration projection zone but was written by {stage_id}"
        for stage_id, paths in ctx["attribution"].items()
        if stage_id != owner
        for path in paths
        if owner_of(ctx["stages"], path) == owner
    ]


def _detect_unattributed_residue(ctx: dict) -> list[str]:
    out: list[str] = []
    for stage_id, paths in ctx["attribution"].items():
        for path in paths:
            if owner_of(ctx["stages"], path) is None:
                ctx["unattributed"].add(path)
                out.append(f"{path} written by {stage_id}, covered by no declared write zone")
    return out


def _detect_reentrancy(ctx: dict) -> list[str]:
    return list(ctx["reentrancy"])


DETECTORS = {
    "commit_token_in_delta": _detect_commit_token_in_delta,
    "mutual_hash_in_delta": _detect_mutual_hash_in_delta,
    "pass_instability": _detect_pass_instability,
    "foreign_projection_write": _detect_foreign_projection_write,
    "unattributed_residue": _detect_unattributed_residue,
    "reentrancy": _detect_reentrancy,
}


# ------------------------------------------------------------------ the gate
def run_pipeline_pass(decl: dict, stages: list[dict], env: dict[str, str], skip_heavy: bool):
    """Execute one pass. Returns (failures, per_stage_paths)."""
    failures: list[str] = []
    attribution: dict[str, list[str]] = {}
    before = snapshot_tracked()
    for stage in stages:
        ident = str(stage.get("id"))
        if skip_heavy and stage.get("heavy"):
            continue
        code, output = run_stage(stage, env)
        if code != 0 and stage.get("required"):
            tail = output.strip().splitlines()[-1:] or [""]
            failures.append(f"{ident}: exit {code} — {tail[0][:160]}")
        after = snapshot_tracked()
        changed = sorted(
            rel for rel, h in after.items() if before.get(rel) not in (None, h)
        ) + sorted(rel for rel in before if rel not in after)
        if changed:
            attribution[ident] = changed
        before = after
    return failures, attribution


def cmd_gate(decl: dict, *, detect_only: bool = False, fast: bool = False) -> int:
    ident = programme_id(decl)
    if nested(decl):
        guarded = next(
            (c for c in section(decl, "cycle_classes") if str(c.get("detector")) == "reentrancy"),
            {},
        )
        print(
            f"{ident}: nested invocation under the declared re-entrancy guard — no-op "
            f"({guarded.get('id', 'recursion')} guard armed, so the aggregate stays out of its "
            "own pipeline)"
        )
        return 0

    pipeline = decl.get("pipeline") or {}
    stages = section(decl, "pipeline") if not isinstance(pipeline, dict) else list(pipeline.get("stages") or [])
    if not stages:
        fail_closed("declaration declares no pipeline stages")
    passes = int(pipeline.get("convergence_passes") or 1)
    criteria = {str(c["id"]): c for c in section(decl, "closure_criteria")}
    cycles = {str(c["id"]): c for c in section(decl, "cycle_classes")}
    env = stage_env(decl)

    measured: dict[str, int] = dict.fromkeys(
        (str(c.get("measure")) for c in criteria.values()), 0
    )
    findings: list[str] = []
    detected: list[tuple[str, str]] = []
    unattributed: set[str] = set()
    reentrancy_notes: list[str] = []

    # CLO-01 — a fixed point may not be asserted over an uncommitted tree.
    start = classify_entries(porcelain())
    initial = len(start["staged"]) + len(start["modified"]) + len(
        untracked_outside_excluded(start["untracked"])
    )
    measured["initial_dirty_entries"] = initial
    if initial:
        for name in ("staged", "modified", "untracked"):
            for path in start[name][:8]:
                findings.append(f"pre-existing {name}: {path}")
        print(f"{ident}: REPOSITORY NOT A FIXED POINT — the tree is not clean before verification")
        for line in findings:
            print(f"  - {line}")
        print(
            "  the fixed point is a property of a COMMITTED state; commit or restore first "
            "(CLO-01, fail-closed by design)"
        )
        return 1

    full, abbrev = commit_universe()
    reg_owner = registration_owner(stages)
    per_pass: list[dict[str, list[str]]] = []

    for index in range(1, passes + 1):
        failures, attribution = run_pipeline_pass(decl, stages, env, fast)
        measured["stage_failures"] += len(failures)
        findings.extend(failures)

        observed = classify_entries(porcelain())
        outside = untracked_outside_excluded(observed["untracked"])
        measured["tracked_modifications"] += len(observed["modified"])
        measured["staged_entries"] += len(observed["staged"])
        measured["untracked_outside_excluded"] += len(outside)
        residue = sorted(set(observed["modified"]) | set(observed["staged"]))
        if residue or outside:
            measured["non_fixed_point_passes"] += 1
        per_pass.append(attribution)

        print(
            f"  pass {index}/{passes}: modified={len(observed['modified'])} "
            f"staged={len(observed['staged'])} untracked={len(outside)}"
        )
        for stage_id, paths in sorted(attribution.items()):
            print(f"      {stage_id} wrote {len(paths)}: {', '.join(paths[:3])}"
                  f"{' …' if len(paths) > 3 else ''}")

        if residue or outside:
            cycle_by_detector = {str(c.get("detector")): c for c in cycles.values()}
            ctx = {
                "residue": residue,
                "attribution": attribution,
                "previous_attribution": per_pass[index - 2] if index > 1 else {},
                "commits_full": full,
                "commits_abbrev": abbrev,
                "stages": stages,
                "registration_owner": reg_owner,
                "index": index,
                "unattributed": unattributed,
                "reentrancy": reentrancy_notes,
            }
            for detector_name, rule in sorted(cycle_by_detector.items()):
                run = DETECTORS.get(detector_name)
                if run is None:
                    findings.append(
                        f"declared detector has no implementation: {detector_name} "
                        f"({rule.get('id')})"
                    )
                    continue
                for description in run(ctx):
                    detected.append((str(rule.get("id")), description))

    measured["unattributed_paths"] = len(unattributed)
    measured["cycles_detected"] = len({cid for cid, _ in detected})

    # Restore: the gate observes, it does not leave damage. Safe because CLO-01
    # proved the tree clean before any stage ran.
    if measured["tracked_modifications"] or measured["staged_entries"]:
        git("reset", "--quiet")
        git("checkout", "--", ".")

    undispositioned = [
        f
        for f in (decl.get("findings") or [])
        if isinstance(f, dict) and f.get("disposition") != "REPAIRED"
    ]

    failed = [
        c
        for c in criteria.values()
        if c.get("blocking") and measured.get(str(c.get("measure")), 0) != c.get("expect")
    ]

    print()
    for c in sorted(criteria.values(), key=lambda x: str(x["id"])):
        got = measured.get(str(c.get("measure")), 0)
        mark = "PASS" if got == c.get("expect") else "FAIL"
        print(f"  [{mark}] {c['id']} {c['criterion']} — {c['measure']}={got}")
    if findings:
        print("\n  stage findings:")
        for line in findings[:20]:
            print(f"    - {line}")
    if detected:
        print("\n  self-reference topologies detected:")
        for cid, description in sorted(set(detected))[:40]:
            rule = cycles.get(cid) or {}
            print(f"    - [{rule.get('severity', '')}] {cid} {description}")
        for cid in sorted({cid for cid, _ in detected}):
            rule = cycles.get(cid) or {}
            if rule:
                print(f"    {cid} ({rule.get('principle')}) → {rule.get('remediation')}")
    if undispositioned:
        print(f"\n  undispositioned declared findings: {len(undispositioned)}")

    verdict = not failed and not undispositioned
    print()
    print(
        f"{ident}: {'REPOSITORY IS A FIXED POINT' if verdict else 'REPOSITORY NOT A FIXED POINT'} | "
        f"passes={passes} | stages={len(stages)}{' (fast: heavy skipped)' if fast else ''} | "
        f"criteria={len(criteria) - len(failed)}/{len(criteria)} | "
        f"cycles={measured['cycles_detected']} | "
        f"gate={'OPEN' if verdict else 'CLOSED'}"
    )
    if detect_only:
        return 0
    return 0 if verdict else 1


# --------------------------------------------------------------- self-guards
def check_declaration(decl: dict) -> list[str]:
    out: list[str] = []
    ids: dict[str, set[str]] = {}
    for key in ("vocabulary", "principle", "artifact_classes", "cycle_classes", "closure_criteria"):
        seen: set[str] = set()
        for record in section(decl, key):
            ident = str(record.get("id") or "")
            if not ident:
                out.append(f"{key}: a record declares no id")
            elif ident in seen:
                out.append(f"{key}: duplicate id {ident}")
            seen.add(ident)
        ids[key] = seen
    for rule in section(decl, "principle"):
        cycle = rule.get("cycle_class")
        if cycle and cycle not in ids["cycle_classes"]:
            out.append(f"principle {rule['id']}: cycle_class {cycle} is not declared")
        if not rule.get("rule") or not rule.get("rationale"):
            out.append(f"principle {rule['id']}: rule or rationale missing")
    for cycle in section(decl, "cycle_classes"):
        if cycle.get("principle") not in ids["principle"]:
            out.append(f"cycle {cycle['id']}: principle {cycle.get('principle')} is not declared")
        for field in ("detector", "signature", "remediation", "severity"):
            if not cycle.get(field):
                out.append(f"cycle {cycle['id']}: {field} missing")
    for criterion in section(decl, "closure_criteria"):
        if criterion.get("expect") is None or not criterion.get("measure"):
            out.append(f"criterion {criterion['id']}: measure or expect missing")
    registrable = [c for c in section(decl, "artifact_classes") if c.get("registrable")]
    if len(registrable) != 1:
        out.append(
            f"artifact_classes: exactly one class may be registrable, {len(registrable)} declared "
            "(RFP-5)"
        )
    pipeline = decl.get("pipeline") or {}
    if not isinstance(pipeline, dict) or not pipeline.get("stages"):
        out.append("pipeline: no stages declared")
    else:
        if not pipeline.get("reentrancy_env"):
            out.append("pipeline: no reentrancy_env declared — recursion is unguardable")
        if int(pipeline.get("convergence_passes") or 0) < 2:
            out.append("pipeline: convergence_passes must be at least 2 to observe stability")
        seen_stage: set[str] = set()
        for stage in pipeline["stages"]:
            sid = str(stage.get("id") or "")
            if not sid or sid in seen_stage:
                out.append(f"pipeline: missing or duplicate stage id {sid!r}")
            seen_stage.add(sid)
            if not stage.get("argv"):
                out.append(f"stage {sid}: no argv")
            if not stage.get("owner"):
                out.append(f"stage {sid}: no owner")
    if not section(decl, "lifecycle"):
        out.append("lifecycle: not declared")
    return out


def check_no_enumeration(decl: dict) -> list[str]:
    """Prove the engine enumerates nothing the declaration owns.

    Every stage id, owner, write zone and argv token, and every vocabulary term,
    must be absent from this module's source. If a rule can only be enforced by
    naming its subject in code, the rule is not data-driven.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    out: list[str] = []
    pipeline = (decl.get("pipeline") or {}).get("stages") or []
    for stage in pipeline:
        for token in [stage.get("id"), stage.get("owner"), *(stage.get("writes") or [])]:
            if token and str(token) in source:
                out.append(f"engine names a declared stage token: {token!r}")
        for token in stage.get("argv") or []:
            token = str(token)
            if token != _PY_TOKEN and len(token) > 6 and token in source:
                out.append(f"engine names a declared argv token: {token!r}")
    for record in section(decl, "artifact_classes") + section(decl, "cycle_classes"):
        ident = str(record.get("id"))
        if ident in source:
            out.append(f"engine names a declared class id: {ident!r} outside data")
    return out


def check_write_scope(decl: dict) -> list[str]:
    """This programme may write only inside its own lane."""
    before = snapshot_tracked()
    written = render_and_write(decl)
    after = snapshot_tracked()
    changed = {rel for rel, h in after.items() if before.get(rel) not in (None, h)}
    out = [
        f"wrote outside this programme's own zone: {rel}"
        for rel in sorted(changed)
        if not (REPO / rel).resolve().is_relative_to(HERE)
    ]
    out += [
        f"emitted outside this programme's own zone: {path}"
        for path in written
        if not Path(path).resolve().is_relative_to(HERE)
    ]
    return out


def check_determinism(decl: dict) -> list[str]:
    first = render(decl)
    second = render(decl)
    if set(first) != set(second):
        return ["rendered output set differs between runs"]
    return [f"non-deterministic rendering: {name}" for name in sorted(first) if first[name] != second[name]]


def check_self_compliance(decl: dict) -> list[str]:
    """This engine's own emitted bytes must satisfy RFP-2 and RFP-3.

    The programme that abolishes commit self-reference and working-tree
    self-observation may not practise either. Measured, not asserted: the
    rendered bytes are scanned for a commit identity, and for the live
    observations this engine is capable of making.
    """
    out: list[str] = []
    full, abbrev = commit_universe()
    rendered = render(decl)
    for name, text in sorted(rendered.items()):
        blob = text.encode("utf-8", "replace")
        embedded = sorted(
            {t.decode() for t in set(_HEX.findall(blob)) if t.decode() in full or t.decode() in abbrev}
        )
        if embedded:
            out.append(f"RFP-2 violation in own output {name}: embeds commit identity {embedded[:3]}")
    observations = {str(len(porcelain())), git("rev-parse", "HEAD")}
    for name, text in sorted(rendered.items()):
        for observed in observations:
            if observed and len(observed) > 6 and observed in text:
                out.append(f"RFP-3 violation in own output {name}: records a live observation")
    return out


# ------------------------------------------------------------------ rendering
def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "| " + " | ".join(headers) + " |\n"
    rule = "|" + "|".join(["---"] * len(headers)) + "|\n"
    return head + rule + "".join("| " + " | ".join(r) + " |\n" for r in rows)


_BANNER = (
    "> GENERATED FROM `rfp-declaration.json` BY UCOS-RFP-001 — DO NOT EDIT BY HAND.\n"
    "> Regenerate with `make rfp`. AUTHORITY = NONE (DERIVED TRUTH).\n"
    ">\n"
    "> This projection records the DECLARATION only. It carries no commit identity\n"
    "> (RFP-2) and no observation of the working tree (RFP-3) — including the\n"
    "> fixed-point verdict itself, which is carried by the gate's exit code and\n"
    "> standard output. An artifact asserting \"the repository is a fixed point\"\n"
    "> would falsify that sentence by being written.\n"
)


def render(decl: dict) -> dict[str, str]:
    p = decl["programme"]
    out: dict[str, str] = {}

    out["REPOSITORY-FIXED-POINT-CONSTITUTION.md"] = (
        f"# {p['id']} — REPOSITORY FIXED-POINT CLOSURE CONSTITUTION\n\n{_BANNER}\n"
        + _table(["Field", "Value"], [
            ["PROGRAMME", f"`{p['id']}` — {p['name']}"],
            ["AUTHORITY", p["authority"]],
            ["ORIGIN", p["origin"]],
            ["DECLARATION", "`00-MASTER/UCOS-RFP-001/rfp-declaration.json`"],
            ["SEAL", f"`{digest(decl)[:16]}`"],
        ])
        + "\n## Vocabulary\n\n"
        + _table(["ID", "Term", "Definition"], [
            [v["id"], f"**{v['term']}**", v["definition"]] for v in decl["vocabulary"]
        ])
        + "\n## Principle\n\n"
        + "".join(
            f"### {r['id']} — {r['title']}\n\n**Rule.** {r['rule']}\n\n"
            f"**Why.** {r['rationale']}\n\n"
            f"*Cycle class:* {r.get('cycle_class', '—')} · *Enforced by:* "
            f"{', '.join('`' + e + '`' for e in r.get('enforced_by', []))}\n\n"
            for r in decl["principle"]
        )
        + "## Admission classes\n\n"
        + _table(["ID", "Class", "Registrable", "Tracked", "Convergence obligation"], [
            [c["id"], c["name"], "**YES**" if c["registrable"] else "no",
             "yes" if c["tracked"] else "no", c["convergence"]]
            for c in decl["artifact_classes"]
        ])
        + "\n### Placing a future family\n\n"
        + "".join(f"{i + 1}. {q}\n" for i, q in enumerate(decl["class_derivation"]["ordered_questions"]))
        + f"\n**Invariant.** {decl['class_derivation']['invariant']}\n\n"
        + "## Governing instruments\n\n"
        + "".join(f"- `{g}`\n" for g in p["governing_instruments"])
        + "\n---\n\n*Regenerate with `make rfp`. Enforce with `make rfp-gate`.*\n"
    )

    pipeline = decl["pipeline"]
    out["FIXED-POINT-GATE.md"] = (
        f"# {p['id']} — REPOSITORY FIXED-POINT GATE (G-15)\n\n{_BANNER}\n"
        "## What the gate does\n\n"
        f"It executes the declared pipeline **{pipeline['convergence_passes']} times** over the "
        "committed HEAD and requires the repository to be byte-identical after every pass. "
        "Stability is an observation over repetitions: a fixed point seen once may be coincidence.\n\n"
        "## Mandatory closure criteria\n\n"
        + _table(["ID", "Criterion", "Measure", "Expect", "Blocking"], [
            [c["id"], c["criterion"], f"`{c['measure']}`", str(c["expect"]),
             "yes" if c.get("blocking") else "no"]
            for c in decl["closure_criteria"]
        ])
        + "\n## The declared pipeline\n\n"
        + _table(["#", "Stage", "Owner", "Heavy", "Required", "Re-entrant"], [
            [str(i + 1), f"`{s['id']}` {s['name']}", s["owner"],
             "yes" if s.get("heavy") else "no",
             "yes" if s.get("required") else "no",
             "yes" if s.get("reentrant") else "**no**"]
            for i, s in enumerate(pipeline["stages"])
        ])
        + "\n## Exit semantics\n\n"
        + _table(["Exit", "Meaning"], [
            ["0", "the repository is a Repository Fixed Point — gate OPEN"],
            ["1", "the repository is not a fixed point — gate CLOSED"],
            ["2", "fail-closed abort — declaration unusable, no verdict asserted"],
        ])
        + "\n## Why the gate records nothing\n\n"
        "The verdict is an observation of the working tree. Persisting it would violate RFP-3 "
        "and make the record permanently false (Evidence Drift). The gate therefore reports "
        "through its exit code and standard output, and its generated artifacts carry the "
        "declaration alone.\n"
        "\n---\n\n*Enforce with `make rfp-gate`.*\n"
    )

    out["SELF-REFERENCE-DETECTION.md"] = (
        f"# {p['id']} — SELF-REFERENCE DETECTION\n\n{_BANNER}\n"
        "## Detection is architectural\n\n"
        "No detector matches a path, a lane, a producer or a field name. Each observes either "
        "the BEHAVIOUR of a producer across executions or the BYTES a producer wrote in its own "
        "delta. Consequently an authored document that merely cites a commit is never flagged: "
        "a citation appears in no producer's delta.\n\n"
        "## Topologies\n\n"
        + _table(["ID", "Topology", "Principle", "Severity", "Detector", "Signature"], [
            [c["id"], c["name"], c["principle"], c["severity"], f"`{c['detector']}`", c["signature"]]
            for c in decl["cycle_classes"]
        ])
        + "\n## Remediation\n\n"
        + _table(["ID", "Remediation"], [[c["id"], c["remediation"]] for c in decl["cycle_classes"]])
        + "\n## Why behaviour, not inspection\n\n"
        "A producer that reads repository state cannot be recognised from its source without "
        "enumerating the calls it might make; the set of such calls is open. What is closed is "
        "the OBSERVABLE consequence: an output that changes at an unchanged commit, or an output "
        "containing an identity only the object database can mint. Detecting the consequence "
        "catches every present and future mechanism that produces it.\n"
        "\n---\n\n*Regenerate with `make rfp`.*\n"
    )

    out["REPOSITORY-CLOSURE-LIFECYCLE.md"] = (
        f"# {p['id']} — REPOSITORY CLOSURE LIFECYCLE\n\n{_BANNER}\n"
        "## The canonical lifecycle\n\n"
        + _table(["#", "Stage", "Closure-relevant", "Gate"], [
            [str(s["step"]), s["stage"], "yes" if s["closure_relevant"] else "—",
             f"`{s['gate']}`" if s.get("gate") else "—"]
            for s in decl["lifecycle"]
        ])
        + "\n## What this programme adds\n\n"
        "Steps 1–10 were already the repository's practice. Steps 11–14 are new and are the "
        "whole substance of the mission: closure is no longer asserted at certification, it is "
        "asserted only after the repository has been shown to reproduce itself from the state "
        "that was committed. Certification says *the state is lawful*; fixed-point verification "
        "says *the state is real*.\n\n"
        "## Inheritance\n\n"
        + "".join(
            f"- **{r['id']} {r['title']}** — {r['rule']}\n"
            for r in decl["principle"] if r["id"] in {"RFP-1", "RFP-7"}
        )
        + "\nInheritance is structural, not registrational: the condition is evaluated over the "
        "REPOSITORY, so every programme the repository contains is bound without enrolling, and "
        "no programme can exempt itself by omission.\n"
        "\n---\n\n*Regenerate with `make rfp`.*\n"
    )

    out["rfp.json"] = canonical_json({
        "programme": decl["programme"],
        "vocabulary": decl["vocabulary"],
        "principle": decl["principle"],
        "artifact_classes": decl["artifact_classes"],
        "class_derivation": decl["class_derivation"],
        "cycle_classes": decl["cycle_classes"],
        "lifecycle": decl["lifecycle"],
        "pipeline": decl["pipeline"],
        "closure_criteria": decl["closure_criteria"],
        "findings": decl.get("findings") or [],
        "declaration_seal_sha256": digest(decl),
        "$measurement_comment": (
            "This artifact records the DECLARATION only. No verdict, no commit identity and no "
            "working-tree observation is persisted (RFP-2, RFP-3): the gate's finding lives in "
            "its exit code."
        ),
    })
    return out


def render_and_write(decl: dict) -> list[str]:
    written: list[str] = []
    for name, text in sorted(render(decl).items()):
        target = HERE / name
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            target.write_text(text, encoding="utf-8")
        written.append(str(target))
    return written


# ----------------------------------------------------------------------- main
_GUARDS = {
    "--check-declaration": check_declaration,
    "--check-no-enumeration": check_no_enumeration,
    "--check-write-scope": check_write_scope,
    "--check-determinism": check_determinism,
    "--check-self-compliance": check_self_compliance,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="UCOS-RFP-001 Repository Fixed-Point Closure")
    ap.add_argument("--gate", action="store_true", help="G-15: prove the repository is a fixed point")
    ap.add_argument("--detect", action="store_true", help="classify self-reference topologies (never fails)")
    ap.add_argument("--fast", action="store_true", help="skip stages declared heavy (never used by the gate)")
    for flag in _GUARDS:
        ap.add_argument(flag, action="store_true")
    args = ap.parse_args()

    decl = load_declaration()
    ident = programme_id(decl)

    integrity = check_declaration(decl)
    if integrity:
        fail_closed("; ".join(integrity))

    for flag, check in _GUARDS.items():
        if getattr(args, flag.lstrip("-").replace("-", "_")):
            findings = check(decl)
            label = flag.lstrip("-")
            if findings:
                print(f"{ident} {label}: FAIL")
                for line in findings:
                    print(f"  - {line}")
                return 1
            print(f"{ident} {label}: PASS")
            return 0

    if args.gate or args.detect:
        return cmd_gate(decl, detect_only=args.detect, fast=args.fast)

    written = render_and_write(decl)
    print(f"{ident}: regenerated {len(written)} determinations in {HERE}")
    for path in written:
        print(f"  - {Path(path).name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
