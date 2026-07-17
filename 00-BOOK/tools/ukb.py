#!/usr/bin/env python3
"""
UCOS Ω∞ Universal Master Knowledge Book (UKB) — Generation & Navigation Engine.

This is the authority-neutral automation layer of UCOS-BOOK-000000. It reads the
repository, assigns append-only Universal Artifact IDs and Universal Page Numbers
(persisted in an immutable ledger), builds the Universal Knowledge Graph, and
emits the registries, master index, and control tower. It also provides a search
CLI over the whole knowledge base.

It MODIFIES NO existing artifact. It renames and renumbers nothing. Native program
identifiers (ENG-000, ARCH-DATA-001, CAT-000, RUNTIME-001, …) are read and
preserved verbatim; the Universal IDs are an overlay crosswalk only. This engine
holds no constituent, governance, ratification, or EC-1 authority.

Commands:
    build     Scan the repo, allocate IDs/pages (append-only), emit DATA + registries.
    search    Query the knowledge base (by id/name/keyword/volume/status/program/
              dependency/owner/version).
    trace     Show the parent/dependency/dependents graph for one artifact.
    validate  Validate emitted DATA against the JSON schemas (if jsonschema present),
              plus structural invariants (append-only, no duplicate IDs/pages).
    stats     Print portfolio statistics.

Standard library only (jsonschema optional for `validate`).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BOOK_DIR = os.path.dirname(HERE)                 # …/00-BOOK
REPO = os.path.dirname(BOOK_DIR)                 # repository root
DATA_DIR = os.path.join(BOOK_DIR, "DATA")
REG_DIR = os.path.join(BOOK_DIR, "REGISTRIES")
CT_DIR = os.path.join(BOOK_DIR, "CONTROL-TOWER")
SCHEMA_DIR = os.path.join(BOOK_DIR, "SCHEMAS")

sys.path.insert(0, HERE)
import config as C  # noqa: E402

LEDGER_PATH = os.path.join(DATA_DIR, "id-ledger.json")
ARTIFACTS_PATH = os.path.join(DATA_DIR, "artifacts.json")
VOLUMES_PATH = os.path.join(DATA_DIR, "volumes.json")
RELS_PATH = os.path.join(DATA_DIR, "relationships.json")
CT_JSON_PATH = os.path.join(DATA_DIR, "control-tower.json")
CHANGE_LEDGER_PATH = os.path.join(DATA_DIR, C.CHANGE_LEDGER_FILE)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return default


def _stamp_eq_json(path, obj, stamp_keys=("generated_at",)):
    """True if `path` already holds JSON equal to `obj` once each document's own
    generation stamp is neutralized. Neutralizes the top-level stamp keys AND any
    nested value equal to that same stamp (e.g. control-tower dimension `as_of`
    baselines populated by the same generation clock). Real, content-derived
    timestamps (signal `as_of`, change-event `at`) differ from the generation
    stamp and are preserved, so genuine drift is still detected. Lets writers skip
    no-op rewrites so regeneration is byte-stable when substantive content is
    unchanged — required by the register.sh --guard drift gate (F-1) and the
    UKB-ADV-INV-07 deterministic-reproducibility invariant."""
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as fh:
            old = json.load(fh)
    except Exception:
        return False
    return _neutralize_stamps(old, stamp_keys) == _neutralize_stamps(obj, stamp_keys)


def _neutralize_stamps(doc, stamp_keys):
    stamps = set()
    if isinstance(doc, dict):
        for k in stamp_keys:
            v = doc.get(k)
            if v is not None:
                stamps.add(v)

    def walk(x):
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        if isinstance(x, list):
            return [walk(v) for v in x]
        if isinstance(x, str) and x in stamps:
            return "<STAMP>"
        return x

    return walk(doc)


def _dump_json(path, obj):
    if _stamp_eq_json(path, obj):
        return                                    # idempotent: only the stamp would change
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _relpath(abspath: str) -> str:
    return os.path.relpath(abspath, REPO).replace(os.sep, "/")


def read_metadata(abspath: str) -> dict:
    """Extract an artifact's self-declared UCOS classification metadata from its
    front-matter table (UMB-IMP-001; metadata-driven discovery). Returns a dict
    with any of {program, category, volume, family, domain} it declares. Pure and
    side-effect free; unreadable/binary files yield {}."""
    if not abspath or abspath.endswith(".docx"):
        return {}
    head = _read_head(abspath, 60)
    if not head:
        return {}
    out = {}
    for field, labels in C.METADATA_CLASSIFY_KEYS.items():
        for label in labels:
            # front-matter row:  | LABEL | VALUE |
            m = re.search(r"\|\s*" + re.escape(label) + r"\s*\|\s*([^\n|]+?)\s*\|",
                          head, re.IGNORECASE)
            if m:
                val = m.group(1).strip().strip("*").strip()
                if val and val not in ("—", "-", "N/A", "NONE", "TBD"):
                    out[field] = val
                    break
    return out


# ---------------------------------------------------------------------------
# UMB-IMP-002 — metadata-driven typed relationships + traceability spine.
# These helpers are pure and side-effect free. They recognise the UCOS native-ID
# SHAPE only and resolve against the live registry — no artifact is hard-coded.
# ---------------------------------------------------------------------------
# A UCOS native-ID reference token, e.g. UMB-006, UMB-IMP-001, UKB-ADV-003,
# RUNTIME-001, STATUS-001, REG-AUTO-001. Prefix is one-or-more UPPER segments;
# the final segment is numeric.
_REF_TOKEN = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{1,4}")


def _expand_ref(fragment: str):
    """Expand a single reference fragment into concrete native-ID tokens,
    handling slash-compressed lists (UMB-005/006/007) and ellipsis ranges
    (UKB-ADV-003…007). Returns [] for null tokens. Shape-only; no artifact list."""
    frag = fragment.strip().strip("*").strip()
    # drop a trailing parenthetical qualifier: "UMB-005/006 (read-only targets)"
    frag = re.sub(r"\(.*?\)", "", frag).strip()
    if not frag or frag.upper() in C.RELATIONSHIP_NULL_TOKENS:
        return []
    out = []
    # ellipsis range: PREFIX-000...PREFIX-999 or PREFIX-000…020 (bare end number)
    if ("…" in frag) or ("..." in frag):
        parts = re.split(r"\.\.\.|…", frag, maxsplit=1)
        if len(parts) == 2:
            start_toks = _REF_TOKEN.findall(parts[0])
            if start_toks:
                pa, na = start_toks[-1].rsplit("-", 1)
                end_toks = _REF_TOKEN.findall(parts[1])
                if end_toks and end_toks[0].rsplit("-", 1)[0] == pa:
                    nb = end_toks[0].rsplit("-", 1)[1]
                else:
                    m_end = re.match(r"\s*(\d{1,4})", parts[1])
                    nb = m_end.group(1) if m_end else None
                if nb and na.isdigit() and nb.isdigit() and int(na) <= int(nb):
                    width = len(na)
                    return [f"{pa}-{n:0{width}d}" for n in range(int(na), int(nb) + 1)]
    # slash-compressed numeric list: UMB-005/006/007  → UMB-005, UMB-006, UMB-007
    if "/" in frag:
        m = re.match(r"([A-Z][A-Z0-9-]*)-(\d{1,4})((?:/\d{1,4})+)", frag)
        if m:
            prefix, first, rest = m.group(1), m.group(2), m.group(3)
            width = len(first)
            out.append(f"{prefix}-{first}")
            for n in rest.strip("/").split("/"):
                out.append(f"{prefix}-{int(n):0{width}d}")
            return out
    out.extend(_REF_TOKEN.findall(frag))
    return out


def parse_relationship_refs(cell: str):
    """Parse a relationship-declaring front-matter cell into an ordered, de-duped
    list of native-ID reference tokens (shape-recognised; artifact-agnostic)."""
    if not cell:
        return []
    seen, refs = set(), []
    fragments = re.split("|".join(re.escape(s) for s in C.RELATIONSHIP_REF_SEPARATORS), cell)
    for frag in fragments:
        for tok in _expand_ref(frag):
            if tok not in seen:
                seen.add(tok)
                refs.append(tok)
    return refs


def read_relationship_rows(abspath: str) -> dict:
    """Extract every relationship-declaring front-matter row of an artifact as
    {LABEL_UPPER: cell_value}, plus freeform `RELATES <Type>` rows keyed as
    ('RELATES', Type). Pure; binaries/unreadable files yield {}."""
    if not abspath or abspath.endswith(".docx"):
        return {}
    head = _read_head(abspath, 80)
    if not head:
        return {}
    rows = {}
    # configured labels
    for spec in C.RELATIONSHIP_TYPES:
        for label in spec["labels"]:
            m = re.search(r"\|\s*" + re.escape(label) + r"[^|\n]*\|\s*([^|\n]+?)\s*\|",
                          head, re.IGNORECASE)
            if m and label.upper() not in rows:
                rows[label.upper()] = m.group(1).strip()
    # freeform `RELATES <Type> | value |`
    for m in re.finditer(r"\|\s*" + re.escape(C.RELATIONSHIP_FREEFORM_LABEL) +
                         r"\s+([A-Za-z][A-Za-z0-9-]*)\s*\|\s*([^|\n]+?)\s*\|", head, re.IGNORECASE):
        rows[("RELATES", m.group(1))] = m.group(2).strip()
    return rows


# ---------------------------------------------------------------------------
# UMB-IMP-003 — change / version / lineage / evolution intelligence.
# All pure and side-effect free (except the git subprocess read). They DERIVE
# intelligence from the append-only ledger snapshot history + typed edges + git;
# they create no store as a source of truth (UMB-008 §3; UMB-009 §1; UMB-010 §1).
# ---------------------------------------------------------------------------
def read_version(abspath: str) -> str | None:
    """Extract an artifact's self-declared version VERBATIM (scheme-agnostic;
    UMB-IMP-003 / UMB-009 §6). Returns the raw token (semver 1.4.2, calendar
    2026.07.16, revision REV-C, tag v3, or any future scheme) or None. No version
    FORMAT is assumed or required."""
    if not abspath or abspath.endswith(".docx"):
        return None
    head = _read_head(abspath, 60)
    if not head:
        return None
    for label in C.VERSION_METADATA_KEYS:
        m = re.search(r"\|\s*" + re.escape(label) + r"\s*\|\s*([^\n|]+?)\s*\|",
                      head, re.IGNORECASE)
        if m:
            val = m.group(1).strip().strip("*").strip()
            if val and val not in ("—", "-", "N/A", "NONE", "TBD"):
                return val
    return None


def _git_last_commit(relpath: str):
    """Best-effort LAST git commit touching a path → {commit, date, author,
    subject}. Supplies change CAUSATION (why/when/who; UMB-008 §4). Returns None
    for an untracked/uncommitted file or when git is unavailable — evidence-bound,
    never fabricated. Called only for artifacts that changed this build, so a
    steady-state (no-op) rebuild spawns no git process."""
    try:
        import subprocess
        out = subprocess.run(
            ["git", "log", "-1", "--format=%H%x1f%cI%x1f%an%x1f%s", "--", relpath],
            cwd=REPO, capture_output=True, text=True, timeout=10)
        line = (out.stdout or "").strip()
        if out.returncode != 0 or not line:
            return None
        parts = (line.split("\x1f") + ["", "", "", ""])[:4]
        return {"commit": parts[0][:12], "date": parts[1],
                "author": parts[2], "subject": parts[3]}
    except Exception:
        return None


def record_snapshots(ledger, artifacts, raw_versions):
    """APPEND-ONLY: record the current (content_hash, version, status, path, name)
    of every artifact into the ledger snapshot history IFF it differs from the last
    recorded snapshot of the SAME Universal ID. Preserves every prior content_hash
    and version (UMB-009 §2 — the one append-only gap this mission fills). Idempotent
    by construction: an unchanged rebuild appends nothing. Returns the set of
    Universal IDs that received a NEW snapshot this build."""
    hist = ledger.setdefault("history", {})
    changed = set()
    fields = ("content_hash", "version", "status", "path", "name")
    for a in sorted(artifacts.values(), key=lambda x: x["page_start"]):
        uid = a["universal_id"]
        cur = {"content_hash": a.get("content_hash"),
               "version": raw_versions.get(uid) or a.get("version"),
               "status": a.get("status"), "path": a.get("path"), "name": a.get("name")}
        lst = hist.setdefault(uid, [])
        if lst:
            last = lst[-1]
            if all(last.get(k) == cur[k] for k in fields):
                continue                       # unchanged — append nothing
            at, seq = _now(), last["seq"] + 1
        else:
            # First observation: anchor to the ledger's recorded BIRTH time so the
            # Created event is historically accurate (UMB-010 §2 birth allocation).
            entry = ledger["by_path"].get(a["path"], {})
            at, seq = entry.get("first_seen") or _now(), 1
        lst.append({"seq": seq, "at": at, **cur})
        changed.add(uid)
    return changed


_STATUS_EVENT_KIND = {"SUPERSEDED": "Superseded", "RETIRED": "Retired",
                      "DEPRECATED": "Deprecated"}


def derive_change_events(ledger, git_map, registered_uids=None):
    """Derive change events from consecutive append-only ledger snapshots. Each
    event is bound to a subject Universal ID (a real graph node → graph-participating,
    no dangling endpoint) and carries evidence: snapshot seq, before/after values,
    and — when the file is tracked — the causing git commit. Deterministic: events
    are ordered by (at, subject, seq, kind) and numbered stably, so ids are stable
    across rebuilds. Nothing is stored as a first-class artifact (UMB-008 §2/§3).

    Referential integrity (UMB-017 C-05; GOV-005): the append-only snapshot history
    may retain the UID of a path that is no longer a registered repository artifact
    (e.g. a corrected false registration whose path the version-control eligibility
    boundary now excludes). Such UIDs are NOT emitted as change-event subjects,
    because a change event must bind to a real, currently-registered graph node —
    never a dangling endpoint. The history itself is preserved (append-only)."""
    hist = ledger.get("history", {})
    term = set(C.CHANGE_TERMINAL_STATUSES)
    raw = []
    for uid, snaps in hist.items():
        if registered_uids is not None and uid not in registered_uids:
            continue                           # subject no longer a registered artifact
        for i, s in enumerate(snaps):
            prev = snaps[i - 1] if i > 0 else None
            evs = []
            if prev is None:
                evs.append(("Created", None, s.get("status")))
            else:
                if prev.get("content_hash") != s.get("content_hash"):
                    evs.append(("Modified", prev.get("content_hash"), s.get("content_hash")))
                if prev.get("path") != s.get("path"):
                    evs.append(("Moved", prev.get("path"), s.get("path")))
                if prev.get("name") != s.get("name"):
                    evs.append(("Renamed", prev.get("name"), s.get("name")))
                if prev.get("version") != s.get("version"):
                    evs.append(("Version-Incremented", prev.get("version"), s.get("version")))
                ps, cs = prev.get("status"), s.get("status")
                if ps != cs:
                    if cs in term:
                        evs.append((_STATUS_EVENT_KIND[cs], ps, cs))
                    elif ps in term:
                        evs.append(("Reactivated", ps, cs))
            for kind, before, after in evs:
                raw.append({"subject": uid, "kind": kind, "at": s.get("at"),
                            "snapshot_seq": s.get("seq"), "from": before, "to": after,
                            "commit": git_map.get(uid) if kind in
                            ("Created", "Modified", "Moved", "Renamed") else None})
    raw.sort(key=lambda e: (e["at"] or "", e["subject"], e["snapshot_seq"], e["kind"]))
    return [{"change_id": f"{C.CHANGE_EVENT_ID_PREFIX}-{n:09d}", **e}
            for n, e in enumerate(raw, 1)]


def derive_version_records(ledger, by_uid):
    """Derive per-artifact version history from the append-only snapshot history:
    ordered distinct versions (any scheme), content baselines, depth, current and
    first version (UMB-009 §2/§7). Derived view; no version store."""
    hist = ledger.get("history", {})
    out = {}
    for uid, snaps in hist.items():
        if uid not in by_uid:
            continue                           # skip UIDs no longer registered (GOV-005)
        versions = []
        for s in snaps:
            v = s.get("version")
            if v and (not versions or versions[-1]["version"] != v):
                versions.append({"version": v, "content_hash": s.get("content_hash"),
                                 "at": s.get("at"), "snapshot_seq": s.get("seq")})
        out[uid] = {
            "current_version": snaps[-1]["version"] if snaps else by_uid.get(uid, {}).get("version"),
            "first_version": versions[0]["version"] if versions else None,
            "version_depth": len(versions),
            "content_baseline": snaps[-1]["content_hash"] if snaps else None,
            "history": versions,
        }
    return out


def derive_lineage(edges, by_uid, ledger):
    """Construct bidirectional lineage chains as a PROJECTION of the typed graph
    (UMB-010 §2): ancestor/descendant edge types + ledger birth. Every chain is
    navigable both ways because inverses are materialized. Derived view; no store."""
    anc_types = set(C.LINEAGE_ANCESTOR_EDGE_TYPES)
    desc_types = set(C.LINEAGE_DESCENDANT_EDGE_TYPES)
    ancestors, descendants = defaultdict(set), defaultdict(set)
    for e in edges:
        t, f, to = e["type"], e["from"], e["to"]
        if t in anc_types:
            ancestors[f].add(to); descendants[to].add(f)
        elif t in desc_types:
            descendants[f].add(to); ancestors[to].add(f)

    def walk(seed, adj):
        chain, seen, stack = [], {seed}, sorted(adj.get(seed, []))
        while stack:
            n = stack.pop(0)
            if n in seen:
                continue
            seen.add(n); chain.append(n)
            stack.extend(sorted(adj.get(n, [])))
        return chain

    hist = ledger.get("history", {})
    out = {}
    for uid, a in by_uid.items():
        anc = walk(uid, ancestors)
        desc = walk(uid, descendants)
        snaps = hist.get(uid, [])
        birth = (snaps[0]["at"] if snaps else
                 ledger["by_path"].get(a.get("path", ""), {}).get("first_seen"))
        if anc or desc or snaps:
            out[uid] = {
                "birth": birth,
                "predecessors": sorted(ancestors.get(uid, [])),
                "successors": sorted(descendants.get(uid, [])),
                "ancestor_chain": anc,
                "descendant_chain": desc,
                "origin": anc[-1] if anc else uid,
            }
    return out


def build_change_ledger(events, version_records, lineage):
    """Assemble the DERIVED change/version/lineage/evolution projection persisted to
    DATA/change-ledger.json (regenerated deterministically each transaction; NOT an
    append-only source of truth — the ledger snapshot history + edges + git are)."""
    return {
        "generated_at": _now(),
        "generator_version": C.GENERATOR_VERSION,
        "counts": {
            "change_events": len(events),
            "versioned_artifacts": len(version_records),
            "lineage_nodes": len(lineage),
            "artifacts_with_predecessors": sum(1 for v in lineage.values() if v["predecessors"]),
            "artifacts_with_successors": sum(1 for v in lineage.values() if v["successors"]),
        },
        "change_event_histogram": dict(Counter(e["kind"] for e in events)),
        # Evolution timeline = the append-only, ordered union of every change event
        # — the permanent institutional memory of every state each entity held
        # (UMB-010 §3). Derived, recomputed on demand.
        "evolution_timeline": [
            {"change_id": e["change_id"], "at": e["at"], "subject": e["subject"],
             "kind": e["kind"]} for e in events],
        "change_events": events,
        "version_records": version_records,
        "lineage": lineage,
    }


# Discovered volumes (metadata-declared volumes absent from C.VOLUMES) are held
# here for the duration of a build so classify() and volume emission agree. The
# permanent record lives append-only in the id-ledger (see cmd_build).
_DISCOVERED_VOLUMES: dict = {}


def _volume_for_category(category: str):
    """Return an existing volume id whose category matches, else None. Computed —
    no volume list is hard-coded in the classifier (AUTH-INF-001 infinite expansion)."""
    for vid, _serial, _name, cat, _desc in C.VOLUMES:
        if cat == category:
            return vid
    for vid, meta in _DISCOVERED_VOLUMES.items():
        if meta.get("category") == category:
            return vid
    return None


def _derive_class_from_path(relpath: str):
    """Deterministic path-derived classification (GOV-005 §5.2, CLASS-RC-1
    correction). Replaces the OTHER/MISC dead-end with a REAL, path-derivable
    category so classification is TOTAL: every tracked artifact — present or
    future — resolves to a real (program, category, volume) even when no curated
    CLASSIFY_RULE and no self-declared metadata matched. This is the structural
    guarantee that `unclassified == 0` holds for any future tree with ZERO new
    per-tree config (no artifact name, no manual list).

    Derivation is pure and stable: the identifier namespace is taken from the
    artifact's top-level directory segment (or, for a repo-root file, its
    identifier/name stem), stripped of a leading `NN-` ordinal, upper-cased, and
    reduced to a stable code. The thematic volume is an EXISTING volume whose
    category equals that code when one exists, else the configured derived-catch
    volume — nothing is renumbered."""
    parts = relpath.split("/")
    token = parts[0] if len(parts) > 1 else os.path.splitext(parts[0])[0]
    token = re.sub(r"^\d+[-_.]?", "", token)                 # strip leading "07-" ordinal
    code = re.sub(r"[^A-Za-z0-9]", "", token).upper()[:C.DERIVED_CATEGORY_MAXLEN]
    code = code or C.DERIVED_DEFAULT_CATEGORY
    volume = _volume_for_category(code) or C.DERIVED_DEFAULT_VOLUME
    return code, code, volume


def classify(relpath: str, abspath: str | None = None):
    """Resolve (program, category, volume) for an artifact.

    Order (append-only, non-destructive, TOTAL — GOV-005 §5.2):
      1. Ordered CLASSIFY_RULES — existing families; unchanged, first match wins.
      2. Self-declared metadata — rescues any artifact that would otherwise fall
         to the derived catch-all, so a NEW program/domain/family participates
         with zero config edits (UMB-IMP-001; REG-AUTO-001 L4; UCI-001 CP-6).
      3. Deterministic path-derived catch-all — guarantees a REAL category for
         every remaining tracked artifact (no OTHER/MISC dead-end; no per-tree
         rule ever required to avoid an unclassified result).
    Metadata is consulted ONLY when no rule matches, so it never overrides or
    changes a prior classification (append-only invariant). DEFAULT_CLASS is
    retained only as an unreachable-for-tracked-artifacts final guard.
    """
    for pattern, program, category, volume in C.CLASSIFY_RULES:
        if re.search(pattern, relpath):
            return program, category, volume
    if abspath:
        md = read_metadata(abspath)
        # Accept ONLY well-formed classification CODES from metadata, so a legacy
        # artifact that declares a long descriptive PROGRAM name is NOT reclassified
        # (append-only: existing OTHER artifacts stay unchanged until they declare a
        # clean code or receive a CLASSIFY_RULE). A new family declaring a clean code
        # participates immediately with zero config edits (UMB-IMP-001).
        def _code(v):
            return v if (v and re.fullmatch(r"[A-Z][A-Z0-9]{1,19}", v)) else None
        program = _code(md.get("program"))
        category = _code(md.get("category"))
        if program or category:
            program = program or category
            category = category or program
            vol = md.get("volume")
            volume = vol if (vol and re.fullmatch(r"VOL-\d{3}", vol)) else \
                (_volume_for_category(category) or C.METADATA_DEFAULT_VOLUME)
            return program, category, volume
    # Deterministic, total catch-all — a real path-derived category, never the
    # OTHER/MISC dead-end (GOV-005 §5.2). DEFAULT_CLASS below is now unreachable
    # for any real relpath and kept only as a defensive final guard.
    if relpath:
        return _derive_class_from_path(relpath)
    return C.DEFAULT_CLASS


def _read_head(abspath: str, n_lines: int = 60) -> str:
    try:
        with open(abspath, "r", encoding="utf-8", errors="ignore") as fh:
            return "".join(fh.readline() for _ in range(n_lines))
    except Exception:
        return ""


# Ordered canonical tokens for parsing a declared STATUS front-matter cell.
_STATUS_TOKENS = [
    "NOT STARTED", "NOT_STARTED", "PLANNED", "UNDER_REVIEW", "UNDER REVIEW",
    "IN_PROGRESS", "IN PROGRESS", "BLOCKED", "SUPERSEDED", "RETIRED",
    "PRODUCTION", "DEPLOYED", "CERTIFIED", "TESTED", "IMPLEMENTED",
    "FROZEN", "COMPLETE", "ACTIVE", "FINAL", "APPROVED",
]


def infer_status(abspath: str, relpath: str) -> str:
    if relpath.endswith(".docx"):
        return "FROZEN"          # frozen source corpus
    if relpath.startswith("99-FREEZE/"):
        return "FROZEN"
    head = _read_head(abspath, 40)
    # Prefer the artifact's own declared STATUS front-matter row: | STATUS | ... |
    m = re.search(r"\|\s*STATUS\s*\|([^\n|]*)\|", head, re.IGNORECASE)
    if m:
        cell = m.group(1).upper()
        for tok in _STATUS_TOKENS:
            if tok in cell:
                return tok.replace(" ", "_")
    # Registers / working reconciliation artifacts are FINAL/FROZEN records.
    if relpath.startswith(("01-WORKING/", "00-SOURCE-MANIFEST/")):
        return "FINAL"
    return "ACTIVE"


def infer_native_id(abspath: str, relpath: str) -> str | None:
    """Extract the artifact's own program identifier from its front-matter."""
    head = _read_head(abspath, 40)
    # front-matter: | ARTIFACT ID | ENG-000 |
    m = re.search(r"ARTIFACT ID\s*\|\s*\**([A-Z][A-Z0-9\-]*[0-9])\**", head)
    if m:
        return m.group(1)
    # runtime/eng filenames encode the native id as a prefix, e.g. RUNTIME-001-…
    base = os.path.basename(relpath)
    m = re.match(r"^(RUNTIME-[A-Z]*-?\d+|ENG-[A-Z]*-?\d+)", base)
    if m:
        return m.group(1)
    return None


def title_from(abspath: str, relpath: str) -> str:
    if relpath.endswith((".md", ".txt")):
        try:
            with open(abspath, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    s = line.strip()
                    if s.startswith("#"):
                        return s.lstrip("#").strip()
                    if s.startswith("| ARTIFACT ") or s.startswith("|ARTIFACT"):
                        parts = [p.strip() for p in s.strip("|").split("|")]
                        if len(parts) >= 2 and parts[0].upper().startswith("ARTIFACT"):
                            return parts[1].strip("*")
        except Exception:
            pass
    # fall back to a humanised file name
    base = os.path.basename(relpath)
    base = re.sub(r"^UCOS-Ω∞-", "", base)
    base = re.sub(r"\.(md|txt|docx|json)$", "", base)
    return base.replace("-", " ").title()


def page_count_for(abspath: str, relpath: str) -> int:
    try:
        if relpath.endswith(".docx"):
            size = os.path.getsize(abspath)
            return max(1, math.ceil(size / C.BYTES_PER_PAGE))
        with open(abspath, "r", encoding="utf-8", errors="ignore") as fh:
            lines = sum(1 for _ in fh)
        return max(1, math.ceil(lines / C.LINES_PER_PAGE))
    except Exception:
        return 1


def sha256(abspath: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(abspath, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def _repo_artifact_paths():
    """Return the REPOSITORY ARTIFACT BOUNDARY as declared by version control, or
    None if git is unavailable (GOV-005 §5.1, ELIG-RC-1 correction).

    The eligibility universe is derived from what the repository itself considers
    to be part of the repository — never from raw environmental filesystem
    contents. Concretely this is the union of git-tracked files and new
    (not-yet-committed) files, with `.gitignore` (+ the standard exclude sources)
    as the single authoritative non-artifact boundary:

      * tracked files                     → repository artifacts (in scope);
      * new, un-ignored files             → repository artifacts being authored
                                            (in scope, so the enforcement gate
                                            sees a document the instant it exists);
      * ignored files (`.gitignore`)      → environment / build / cache /
                                            generated outputs → automatically
                                            excluded with ZERO hand-maintained
                                            path list (venvs, *.egg-info,
                                            .pytest_cache, .ruff_cache, coverage,
                                            build/, dist/, __pycache__, and any
                                            FUTURE ignored directory).

    `git ls-files --cached --others --exclude-standard` is exactly this set. No
    environment path is named here; the ignore authority is consulted instead of
    contradicted (the previous os.walk denylist ignored `.gitignore` — the root
    trigger of unbounded eligibility drift)."""
    try:
        import subprocess
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=REPO, capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            return None
        return [p for p in out.stdout.split("\0") if p]
    except Exception:
        return None


def _iter_files_walk():
    """Filesystem-walk enumeration — used ONLY as a degraded fallback when git is
    unavailable (e.g. an exported tree with no VCS). Retains the historical
    denylist so the engine still functions off-VCS; inside a git work tree the
    version-control boundary in _repo_artifact_paths() is authoritative."""
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames.sort()
        for fn in sorted(filenames):
            abspath = os.path.join(dirpath, fn)
            rel = _relpath(abspath)
            if rel.startswith(tuple(C.EXCLUDE_DIR_PREFIXES)):
                continue
            if not rel.endswith(C.INCLUDE_EXTENSIONS):
                continue
            yield abspath, rel


def _iter_files():
    """Enumerate eligible repository artifacts (deterministic, sorted order).

    Eligibility = (repository artifact boundary from version control)
                  ∩ INCLUDE_EXTENSIONS
                  ∖ intentional corpus-internal excludes.

    The corpus-internal EXCLUDE_DIR_PREFIXES are retained ON TOP of the VCS
    boundary because they name the generator's OWN machinery and its GENERATED
    outputs (tools/, DATA/, REGISTRIES/, CONTROL-TOWER/, VOLUMES/, PORTAL/) —
    tracked files that must never be registered as artifacts (the registry must
    not list itself). Everything else that version control considers part of the
    repository, and carries a registerable extension, is eligible."""
    paths = _repo_artifact_paths()
    if paths is None:
        yield from _iter_files_walk()
        return
    excl = tuple(C.EXCLUDE_DIR_PREFIXES)
    for rel in sorted(paths):
        if rel.startswith(excl):
            continue
        if not rel.endswith(C.INCLUDE_EXTENSIONS):
            continue
        abspath = os.path.join(REPO, rel)
        if not os.path.isfile(abspath):
            continue          # index entry with no working-tree file (e.g. staged delete)
        yield abspath, rel


# ---------------------------------------------------------------------------
# ledger — append-only Universal ID + page allocation
# ---------------------------------------------------------------------------
def load_ledger():
    # `by_execution` (EXEC-REG-001) is an append-only map of execution KEY ->
    # {execution_id, first_seen} sharing the ONE identity authority (category_seq).
    # Additive to the ledger; a legacy ledger lacking it gets it on next load.
    return _load_json(LEDGER_PATH, {"version": 1, "by_path": {}, "page_cursor": 0,
                                    "category_seq": {}, "discovered_volumes": {},
                                    "volume_seq": 0, "by_execution": {}})


def allocate(ledger, relpath, category, page_count):
    """Return (universal_id, page_start, page_count), allocating append-only."""
    entry = ledger["by_path"].get(relpath)
    if entry:
        return entry["universal_id"], entry["page_start"], entry["page_count"]
    # allocate a new immutable identifier for this category
    if relpath == C.BOOK_ROOT_PATH:
        uid = C.BOOK_ROOT_ID
        ledger["category_seq"].setdefault("BOOK", 0)
    else:
        seq = ledger["category_seq"].get(category, 0) + 1
        ledger["category_seq"][category] = seq
        uid = f"UCOS-{category}-{seq:06d}"
    page_start = ledger["page_cursor"] + 1
    ledger["page_cursor"] = page_start + page_count - 1
    ledger["by_path"][relpath] = {
        "universal_id": uid,
        "category": category,
        "page_start": page_start,
        "page_count": page_count,
        "first_seen": _now(),
    }
    return uid, page_start, page_count


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def upn(n: int) -> str:
    return f"UPN-{n:09d}"


def cmd_build(args):
    ledger = load_ledger()
    # Seed the in-process discovered-volume map from the append-only ledger so
    # metadata-declared volumes keep stable serials across builds (UMB-IMP-001).
    ledger.setdefault("discovered_volumes", {})
    ledger.setdefault("volume_seq", 0)
    _DISCOVERED_VOLUMES.clear()
    _DISCOVERED_VOLUMES.update(ledger["discovered_volumes"])
    files = list(_iter_files())

    # Ensure the BOOK root is allocated first (UPN-000000001 onwards) if present.
    files.sort(key=lambda t: (t[1] != C.BOOK_ROOT_PATH, t[1]))

    _known_vol_ids = {v[0] for v in C.VOLUMES}
    _max_serial = max((v[1] for v in C.VOLUMES), default=0)

    artifacts = {}
    raw_versions = {}                 # uid -> self-declared version token (any scheme)
    for abspath, rel in files:
        program, category, volume = classify(rel, abspath)
        # Infinite expansion: a metadata-declared volume that is not one of the
        # permanent C.VOLUMES is auto-registered append-only into the ledger and
        # emitted, so unlimited future volumes work without editing config.
        if volume not in _known_vol_ids and volume not in _DISCOVERED_VOLUMES:
            ledger["volume_seq"] = ledger.get("volume_seq", 0) + 1
            serial = _max_serial + ledger["volume_seq"]
            md = read_metadata(abspath)
            _DISCOVERED_VOLUMES[volume] = {
                "serial": serial,
                "name": (md.get("family") or program or volume).upper(),
                "category": category,
                "description": f"Auto-discovered volume (metadata-driven, "
                               f"UMB-IMP-001) first declared by {rel}.",
                "first_seen": _now(),
            }
            ledger["discovered_volumes"] = _DISCOVERED_VOLUMES
        pc = page_count_for(abspath, rel)
        uid, pstart, pc = allocate(ledger, rel, category, pc)
        # UMB-IMP-003: capture the self-declared version VERBATIM (scheme-agnostic).
        # The schema-constrained artifact `version` field is populated only when the
        # declared token is a valid semver; the raw token is preserved in the ledger
        # snapshot history so the version engine supports every scheme (UMB-009 §6).
        _dv = read_version(abspath)
        raw_versions[uid] = _dv or "1.0.0"
        _semver = _dv if (_dv and re.match(C.VERSION_SEMVER_SHAPE, _dv)) else "1.0.0"
        art = {
            "universal_id": uid,
            "native_id": infer_native_id(abspath, rel),
            "name": title_from(abspath, rel),
            "description": "",
            "category": category,
            "volume": volume,
            "page_start": pstart,
            "page_end": pstart + pc - 1,
            "status": infer_status(abspath, rel),
            "version": _semver,
            "parent": None,
            "dependencies": [],
            "program": program,
            "owner": "UCOS-PROGRAM-CUSTODIAN",
            "tags": [program, category, volume],
            "path": rel,
            "return_link": C.BOOK_ROOT_PATH,
            "content_hash": sha256(abspath),
            "traceability": {k: [] for k in (
                "requirement", "architecture", "design", "implementation",
                "source_code", "unit_test", "integration_test", "functional_test",
                "security_test", "certification", "deployment", "production",
                "operations")},
        }
        artifacts[rel] = art

    # index helpers
    by_uid = {a["universal_id"]: a for a in artifacts.values()}
    paths = list(artifacts.keys())

    def find_uid(substr):
        for p in paths:
            if substr in os.path.basename(p):
                return artifacts[p]["universal_id"]
        return None

    # ----- build relationships (knowledge graph) --------------------------
    edges = []
    edge_seq = [0]
    _seen_edges = set()

    def add_edge(src, dst, etype, note="", inverse_of=None):
        if not src or not dst or src == dst:
            return None
        key = (src, dst, etype)
        if key in _seen_edges:            # dedup: metadata never duplicates a
            return None                   # structurally-emitted edge (UMB-IMP-002)
        _seen_edges.add(key)
        edge_seq[0] += 1
        eid = f"UEDGE-{edge_seq[0]:09d}"
        edges.append({"edge_id": eid, "from": src, "to": dst, "type": etype,
                      "inverse_of": inverse_of, "note": note})
        return eid

    chain_first_uid = {}
    chain_last_uid = {}
    parented = set()  # uids that received a parent via a chain

    for key, members in C.CHAINS.items():
        prev_uid = None
        for i, sub in enumerate(members):
            uid = find_uid(sub)
            if not uid:
                continue
            if i == 0 or chain_first_uid.get(key) is None:
                chain_first_uid.setdefault(key, uid)
            chain_last_uid[key] = uid
            if prev_uid:
                # child depends on predecessor; predecessor is parent
                add_edge(uid, prev_uid, "Depends-On", note="structural:chain")
                add_edge(uid, prev_uid, "Parent", note="structural:chain")
                add_edge(prev_uid, uid, "Child", note="structural:chain")
                by_uid[uid]["parent"] = prev_uid
                by_uid[uid]["dependencies"] = sorted(set(by_uid[uid]["dependencies"] + [prev_uid]))
                parented.add(uid)
            prev_uid = uid

    # cross-program: each program's first member depends on upstream terminal
    for prog_key, upstream_key in C.CROSS_PROGRAM:
        first = chain_first_uid.get(prog_key)
        if not first:
            continue
        if upstream_key and chain_last_uid.get(upstream_key):
            up = chain_last_uid[upstream_key]
            add_edge(first, up, "Depends-On", note="structural:cross-program")
            by_uid[first]["dependencies"] = sorted(set(by_uid[first]["dependencies"] + [up]))
            if by_uid[first]["parent"] is None:
                by_uid[first]["parent"] = up
                add_edge(first, up, "Parent", note="structural:cross-program")
                add_edge(up, first, "Child", note="structural:cross-program")
                parented.add(first)

    # program-root parenting for non-chained members of a program
    root_uid_by_program = {}
    for prog, sub in C.PROGRAM_ROOTS.items():
        root_uid_by_program[prog] = find_uid(sub)

    book_uid = by_uid.get(C.BOOK_ROOT_ID, {}).get("universal_id", C.BOOK_ROOT_ID)
    for rel, art in artifacts.items():
        uid = art["universal_id"]
        if uid == C.BOOK_ROOT_ID:
            continue
        if uid in parented or art["parent"] is not None:
            continue
        root = root_uid_by_program.get(art["program"])
        if root and root != uid:
            art["parent"] = root
            add_edge(uid, root, "Parent", note="structural:program-root")
            add_edge(root, uid, "Child", note="structural:program-root")
        else:
            art["parent"] = C.BOOK_ROOT_ID
            add_edge(uid, C.BOOK_ROOT_ID, "Parent", note="structural:book-root")
            add_edge(C.BOOK_ROOT_ID, uid, "Child", note="structural:book-root")

    # every program root's parent is the BOOK root (via Child edge from book)
    for prog, root in root_uid_by_program.items():
        if root and by_uid.get(root, {}).get("parent") is None:
            by_uid[root]["parent"] = C.BOOK_ROOT_ID
            add_edge(root, C.BOOK_ROOT_ID, "Parent", note="structural:book-root")
            add_edge(C.BOOK_ROOT_ID, root, "Child", note="structural:book-root")

    # ----- UMB-IMP-002: metadata-driven TYPED edges + traceability spine ----
    # Turn the structural graph into a typed SEMANTIC graph and populate the
    # `traceability` spine, entirely from artifact self-declared metadata. Zero
    # hard coding: only relationship TYPES/labels are configured (config.py
    # RELATIONSHIP_TYPES); the participating artifacts are discovered. Both edge
    # endpoints must resolve to registered Universal IDs (referential integrity,
    # UMB-017 C-05); an unresolved reference (e.g. an authority held outside the
    # registry) is recorded as an evidence-bound EXTERNAL MARKER in the spine
    # field only — never as a dangling edge (UMB-007 §5).
    native_index = {a["native_id"]: a["universal_id"]
                    for a in artifacts.values() if a.get("native_id")}
    uid_set = set(by_uid.keys())

    def _resolve_ref(tok):
        if tok in uid_set:                       # a Universal ID cited directly
            return tok
        return native_index.get(tok)             # else resolve the native ID

    def _trace_add(art, lane, value):
        if lane and value and value not in art["traceability"][lane]:
            art["traceability"][lane].append(value)

    label_to_spec = {}
    for spec in C.RELATIONSHIP_TYPES:
        for label in spec["labels"]:
            label_to_spec[label.upper()] = spec

    typed_edge_count = 0
    external_marker_count = 0
    for rel, art in artifacts.items():
        uid = art["universal_id"]
        rows = read_relationship_rows(os.path.join(REPO, rel))
        for key, cell in rows.items():
            if isinstance(key, tuple):           # freeform `RELATES <Type>`
                ftype = key[1][:1].upper() + key[1][1:]
                spec = {"type": ftype, "inverse": f"{ftype}-Inverse",
                        "subject_lane": None, "object_lane": None}
            else:
                spec = label_to_spec.get(key)
                if not spec:
                    continue
            for tok in parse_relationship_refs(cell):
                target = _resolve_ref(tok)
                if target and target != uid:
                    label = key[1] if isinstance(key, tuple) else key
                    fwd = add_edge(uid, target, spec["type"],
                                   note=f"metadata:{label}")
                    if fwd:
                        typed_edge_count += 1
                    add_edge(target, uid, spec["inverse"],
                             note=f"inverse-of {spec['type']} (metadata:{label})",
                             inverse_of=fwd)
                    _trace_add(art, spec.get("subject_lane"), target)
                    if spec.get("object_lane"):
                        _trace_add(by_uid[target], spec["object_lane"], uid)
                elif not target:
                    # unresolved reference → evidence-bound external spine marker
                    lane = spec.get("subject_lane")
                    if lane and tok not in art["traceability"][lane]:
                        _trace_add(art, lane, tok)
                        external_marker_count += 1

    # ----- UMB-IMP-003: change / version / lineage / evolution intelligence -
    # Append-only snapshot history preserves every prior content_hash/version
    # (UMB-009 §2 — the one append-only gap this mission fills). Change events,
    # version records, lineage chains, and the evolution timeline are then DERIVED
    # from that history + the typed edges (lineage projection) + git causation —
    # created as regenerated views, never as an authoritative store (UMB-008 §3;
    # UMB-010 §1). Idempotent: a no-op rebuild appends no snapshot and spawns no
    # git process.
    changed_uids = record_snapshots(ledger, artifacts, raw_versions)
    git_map = {}
    for uid in sorted(changed_uids):
        commit = _git_last_commit(by_uid[uid]["path"])
        if commit:
            git_map[uid] = commit
    change_events = derive_change_events(ledger, git_map, set(by_uid))
    version_records = derive_version_records(ledger, by_uid)
    lineage = derive_lineage(edges, by_uid, ledger)
    change_ledger = build_change_ledger(change_events, version_records, lineage)

    # ----- volumes --------------------------------------------------------
    vol_counts = Counter(a["volume"] for a in artifacts.values())
    vol_pages = defaultdict(list)
    for a in artifacts.values():
        vol_pages[a["volume"]].append((a["page_start"], a["page_end"]))
    volumes = []
    for vid, serial, name, cat, desc in C.VOLUMES:
        ranges = vol_pages.get(vid, [])
        p_start = min((r[0] for r in ranges), default=None)
        p_end = max((r[1] for r in ranges), default=None)
        volumes.append({
            "volume_id": vid, "serial": serial, "name": name, "description": desc,
            "category": cat, "status": "ACTIVE" if ranges else "PLANNED",
            "artifact_count": vol_counts.get(vid, 0),
            "page_range_start": p_start, "page_range_end": p_end,
            "index_path": f"00-BOOK/REGISTRIES/VOLUME-REGISTRY.md#{vid.lower()}",
        })
    # Append auto-discovered volumes (metadata-driven; append-only) after the
    # permanent set, ordered by their stable serials (UMB-IMP-001; AUTH-INF-001).
    for vid, meta in sorted(_DISCOVERED_VOLUMES.items(), key=lambda kv: kv[1]["serial"]):
        ranges = vol_pages.get(vid, [])
        p_start = min((r[0] for r in ranges), default=None)
        p_end = max((r[1] for r in ranges), default=None)
        volumes.append({
            "volume_id": vid, "serial": meta["serial"], "name": meta["name"],
            "description": meta["description"], "category": meta["category"],
            "status": "ACTIVE" if ranges else "PLANNED",
            "artifact_count": vol_counts.get(vid, 0),
            "page_range_start": p_start, "page_range_end": p_end,
            "index_path": f"00-BOOK/REGISTRIES/VOLUME-REGISTRY.md#{vid.lower()}",
            "discovered": True,
        })

    # ----- persist DATA ---------------------------------------------------
    art_list = sorted(artifacts.values(), key=lambda a: a["page_start"])
    _dump_json(LEDGER_PATH, ledger)
    _dump_json(ARTIFACTS_PATH, {"generated_at": _now(),
                                "generator_version": C.GENERATOR_VERSION,
                                "count": len(art_list), "artifacts": art_list})
    _dump_json(VOLUMES_PATH, {"generated_at": _now(), "count": len(volumes),
                              "volumes": volumes})
    _dump_json(RELS_PATH, {"generated_at": _now(), "count": len(edges),
                           "relationships": edges})
    _dump_json(CHANGE_LEDGER_PATH, change_ledger)

    ct = build_control_tower(art_list, volumes, edges, ledger)
    _dump_json(CT_JSON_PATH, ct)

    # ----- emit markdown --------------------------------------------------
    write_artifact_registry(art_list, volumes)
    write_volume_registry(volumes, art_list)
    write_page_registry(art_list, ledger)
    write_knowledge_graph(edges, by_uid)
    write_control_tower_md(ct)
    write_change_registry(change_ledger, by_uid)

    print(f"UKB build complete: {len(art_list)} artifacts, {len(volumes)} volumes, "
          f"{len(edges)} edges, {ledger['page_cursor']} pages allocated.")
    _spine_pop = sum(1 for a in art_list
                     if any(a["traceability"][k] for k in a["traceability"]))
    _etypes = Counter(e["type"] for e in edges)
    print(f"  UMB-IMP-002: {typed_edge_count} typed semantic edges derived; "
          f"{external_marker_count} external spine markers; "
          f"{_spine_pop}/{len(art_list)} artifacts carry a populated traceability spine.")
    print(f"  edge types ({len(_etypes)}): " +
          ", ".join(f"{t}:{n}" for t, n in sorted(_etypes.items(), key=lambda kv: -kv[1])))
    _cc = change_ledger["counts"]
    _ceh = change_ledger["change_event_histogram"]
    print(f"  UMB-IMP-003: {_cc['change_events']} change events "
          f"({', '.join(f'{k}:{v}' for k, v in sorted(_ceh.items(), key=lambda kv: -kv[1]))}); "
          f"{_cc['versioned_artifacts']} version records; "
          f"{_cc['lineage_nodes']} lineage nodes "
          f"({_cc['artifacts_with_predecessors']} with predecessors, "
          f"{_cc['artifacts_with_successors']} with successors).")
    print(f"  DATA:       {_relpath(DATA_DIR)}/")
    print(f"  REGISTRIES: {_relpath(REG_DIR)}/")
    print(f"  CONTROL:    {_relpath(CT_DIR)}/")


# ---------------------------------------------------------------------------
# control tower
# ---------------------------------------------------------------------------
DIMENSION_STATUS = {
    "architecture": "APPROVED",
    "implementation": "IMPLEMENTED",
    "build": "IMPLEMENTED",
    "unit_testing": "NOT_STARTED",
    "integration_testing": "NOT_STARTED",
    "functional_testing": "NOT_STARTED",
    "performance_testing": "NOT_STARTED",
    "security": "APPROVED",
    "certification": "CERTIFIED",
    "deployment": "NOT_STARTED",
    "production": "NOT_STARTED",
    "operational": "NOT_STARTED",
    "release": "NOT_STARTED",
    # EXEC-REG-001 (RUNTIME-006) DOMAIN-C execution dimension baseline. Append-only;
    # rolled up automatically by the execution-register connector when executions
    # exist. NEVER a DOMAIN-B/roadmap projection (STATUS-001 §2).
    "execution": "NOT_STARTED",
    "portfolio": "IN_PROGRESS",
}


def _canonical(status):
    return C.CANONICAL_ALIAS.get(status, status)


def build_control_tower(art_list, volumes, edges, ledger):
    hist = Counter(a["status"] for a in art_list)
    prog_hist = defaultdict(Counter)
    for a in art_list:
        prog_hist[a["program"]][a["status"]] += 1
    # One generation clock for this control-tower projection: the top-level stamp
    # and every manual-baseline dimension `as_of` (which is generation metadata,
    # not real event time) share it, so the idempotent writer can neutralize them
    # as a single stamp and a no-op rebuild stays byte-stable (F-1 drift gate).
    ts = _now()

    def rollup(counter):
        # lowest-progress state that still has members wins (blocking view)
        order = ["BLOCKED", "NOT_STARTED", "PLANNED", "IN_PROGRESS", "UNDER_REVIEW",
                 "APPROVED", "ACTIVE", "IMPLEMENTED", "COMPLETE", "TESTED",
                 "CERTIFIED", "DEPLOYED", "PRODUCTION", "FROZEN", "FINAL"]
        present = [s for s in order if counter.get(s)]
        return present[0] if present else "NOT_STARTED"

    programs = []
    for prog in sorted(prog_hist):
        c = prog_hist[prog]
        programs.append({
            "program": prog,
            "artifact_count": sum(c.values()),
            "status_histogram": dict(c),
            "rollup_status": rollup(c),
        })

    # Preserve any prior (possibly signal-enriched) dimension state so the
    # foundation build does not regress dimensions that `ukbx twin` already
    # populated from the signal ledger; only dimensions absent from the prior
    # projection get a fresh MANUAL baseline. This keeps a no-op rebuild
    # byte-stable under the idempotent writer (F-1 drift gate) instead of
    # clobbering enriched `as_of`/status and forcing a churny rewrite.
    prior = _load_json(CT_JSON_PATH, {})
    prior_dims = prior.get("dimensions", {}) if isinstance(prior, dict) else {}
    dimensions = {}
    for k, v in DIMENSION_STATUS.items():
        pd = prior_dims.get(k)
        if pd and pd.get("signal_source") not in (None, "MANUAL"):
            dimensions[k] = pd                    # preserve signal-enriched state (real as_of)
        else:
            dimensions[k] = {"status": v, "signal_source": "MANUAL", "as_of": ts,
                             "note": "Manual baseline; automated signals (GitHub Actions/Jira/SonarQube/OWASP/Trivy/Prometheus/Grafana/OTel/K8s/Cloud) roll up here when connected."}

    return {
        "generated_at": ts,
        "generator_version": C.GENERATOR_VERSION,
        "portfolio": {
            "total_artifacts": len(art_list),
            "total_pages": ledger["page_cursor"],
            "total_volumes": len(volumes),
            "total_edges": len(edges),
            "portfolio_status": "IN_PROGRESS — analysis/architecture/generation complete; runtime testing/deployment pending EC-1",
            "status_histogram": dict(hist),
        },
        "programs": programs,
        "dimensions": dimensions,
    }


# ---------------------------------------------------------------------------
# markdown emitters
# ---------------------------------------------------------------------------
_AUTOGEN = ("<!-- AUTO-GENERATED by 00-BOOK/tools/ukb.py — do not edit by hand. "
            "Regenerate with: python3 00-BOOK/tools/ukb.py build -->")


def _link(rel):
    # link relative to 00-BOOK/REGISTRIES/
    return "../../" + rel


def write_artifact_registry(art_list, volumes):
    lines = [f"# UCOS Ω∞ — UNIVERSAL ARTIFACT REGISTRY", "", _AUTOGEN, "",
             "The authoritative crosswalk from every reachable UCOS Ω∞ artifact to its "
             "**Universal Artifact ID**, volume, page range, native program identifier, "
             "status, parent, dependencies, and direct/return links. Universal IDs and "
             "page numbers are append-only and never reused or renumbered; native "
             "identifiers are preserved verbatim.", "",
             f"**Total artifacts:** {len(art_list)}", "",
             "| # | Universal ID | Name | Native ID | Vol | Pages | Status | Parent | Deps | Link |",
             "|---|--------------|------|-----------|-----|-------|--------|--------|------|------|"]
    for i, a in enumerate(art_list, 1):
        deps = str(len(a["dependencies"]))
        pages = f"{upn(a['page_start'])}–{upn(a['page_end'])}"
        native = a["native_id"] or "—"
        name = a["name"].replace("|", "/")
        if len(name) > 60:
            name = name[:57] + "…"
        lines.append(f"| {i} | `{a['universal_id']}` | {name} | {native} | "
                     f"{a['volume'].split('-')[1]} | {pages} | {a['status']} | "
                     f"`{a['parent'] or '—'}` | {deps} | [↗]({_link(a['path'])}) |")
    lines += ["", "*Return: [UCOS-BOOK-000000 Master Index](" + _link(C.BOOK_ROOT_PATH) + ")*", ""]
    _write(os.path.join(REG_DIR, "UNIVERSAL-ARTIFACT-REGISTRY.md"), lines)


def write_volume_registry(volumes, art_list):
    by_vol = defaultdict(list)
    for a in art_list:
        by_vol[a["volume"]].append(a)
    # UMB-REMED-002 (F-5 documentation drift): the volume count is DERIVED from
    # the emitted volume set, never a hard-coded literal, so this authoritative
    # generator string can never again drift from the append-only volume total
    # (was the stale literal "21"; the system emits 23 after VOL-021/VOL-022).
    lines = ["# UCOS Ω∞ — VOLUME REGISTRY", "", _AUTOGEN, "",
             f"The {len(volumes)} root volumes of the Universal Master Knowledge Book. Volumes are "
             "permanent and append-only; unlimited future volumes may be appended.", "",
             "| Volume | Serial | Name | Category | Status | Artifacts | Page Range |",
             "|--------|--------|------|----------|--------|-----------|------------|"]
    for v in volumes:
        pr = (f"{upn(v['page_range_start'])}–{upn(v['page_range_end'])}"
              if v["page_range_start"] else "—")
        lines.append(f"| `{v['volume_id']}` | {v['serial']} | {v['name']} | "
                     f"{v['category']} | {v['status']} | {v['artifact_count']} | {pr} |")
    lines.append("")
    for v in volumes:
        arts = by_vol.get(v["volume_id"], [])
        lines += [f"", f"### {v['volume_id']} — {v['name']} <a id=\"{v['volume_id'].lower()}\"></a>",
                  "", f"*{v['description']}*  \\\n**Category:** {v['category']} · "
                  f"**Status:** {v['status']} · **Artifacts:** {len(arts)}", ""]
        if arts:
            lines += ["| Universal ID | Name | Native | Status |",
                      "|--------------|------|--------|--------|"]
            for a in sorted(arts, key=lambda x: x["page_start"]):
                nm = a["name"].replace("|", "/")
                if len(nm) > 64:
                    nm = nm[:61] + "…"
                lines.append(f"| `{a['universal_id']}` | {nm} | {a['native_id'] or '—'} | {a['status']} |")
    lines += ["", "*Return: [UCOS-BOOK-000000 Master Index](" + _link(C.BOOK_ROOT_PATH) + ")*", ""]
    _write(os.path.join(REG_DIR, "VOLUME-REGISTRY.md"), lines)


def write_page_registry(art_list, ledger):
    lines = ["# UCOS Ω∞ — UNIVERSAL PAGE REGISTRY", "", _AUTOGEN, "",
             "Universal Page Numbers (UPN) are globally unique, immutable, and "
             "append-only. A page number is never reused and never renumbered. Each "
             "artifact owns a contiguous, permanently-fixed UPN range assigned at first "
             "registration; new artifacts append after the current page cursor.", "",
             f"**Pages allocated:** {ledger['page_cursor']}  ·  **Page cursor (next free):** "
             f"{upn(ledger['page_cursor'] + 1)}", "",
             "| UPN Start | UPN End | Count | Universal ID | Volume | Artifact |",
             "|-----------|---------|-------|--------------|--------|----------|"]
    for a in art_list:
        cnt = a["page_end"] - a["page_start"] + 1
        nm = a["name"].replace("|", "/")
        if len(nm) > 48:
            nm = nm[:45] + "…"
        lines.append(f"| {upn(a['page_start'])} | {upn(a['page_end'])} | {cnt} | "
                     f"`{a['universal_id']}` | {a['volume'].split('-')[1]} | {nm} |")
    lines += ["", "*Return: [UCOS-BOOK-000000 Master Index](" + _link(C.BOOK_ROOT_PATH) + ")*", ""]
    _write(os.path.join(REG_DIR, "UNIVERSAL-PAGE-REGISTRY.md"), lines)


def write_knowledge_graph(edges, by_uid):
    tc = Counter(e["type"] for e in edges)
    lines = ["# UCOS Ω∞ — UNIVERSAL KNOWLEDGE GRAPH REGISTRY", "", _AUTOGEN, "",
             "Every relationship in the UKB is a first-class, navigable, directional "
             "edge. Parent/Child and Supersedes/Superseded-By are materialized as "
             "inverse pairs so navigation is bidirectional.", "",
             f"**Total edges:** {len(edges)}", "",
             "| Edge type | Count |", "|-----------|-------|"]
    for t, n in sorted(tc.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {t} | {n} |")
    lines += ["", "## Edge list", "",
              "| Edge ID | From | Type | To | Derivation |",
              "|---------|------|------|----|------------|"]
    for e in edges:
        lines.append(f"| `{e['edge_id']}` | `{e['from']}` | {e['type']} | `{e['to']}` | {e.get('note') or '—'} |")
    lines += ["", "*Return: [UCOS-BOOK-000000 Master Index](" + _link(C.BOOK_ROOT_PATH) + ")*", ""]
    _write(os.path.join(REG_DIR, "KNOWLEDGE-GRAPH-REGISTRY.md"), lines)


def write_control_tower_md(ct):
    p = ct["portfolio"]
    lines = ["# UCOS Ω∞ — PROGRAM CONTROL TOWER", "", _AUTOGEN, "",
             f"**Generated:** {ct['generated_at']}  ·  **Generator:** v{ct['generator_version']}", "",
             "Enterprise roll-up of program and portfolio status across every tracked "
             "dimension. Status is derived deterministically from the Universal Artifact "
             "Registry; automated signals (GitHub Actions, Jira, SonarQube, OWASP, Trivy, "
             "Prometheus, Grafana, OpenTelemetry, Kubernetes, cloud providers) roll up "
             "into these dimensions when connected.", "",
             "## Portfolio", "",
             "| Metric | Value |", "|--------|-------|",
             f"| Total artifacts | {p['total_artifacts']} |",
             f"| Total pages | {p['total_pages']} |",
             f"| Total volumes | {p['total_volumes']} |",
             f"| Total relationships | {p['total_edges']} |",
             f"| Portfolio status | {p['portfolio_status']} |", "",
             "### Status histogram", "", "| Status | Count |", "|--------|-------|"]
    for s, n in sorted(p["status_histogram"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {s} | {n} |")
    lines += ["", "## Programs", "",
              "| Program | Artifacts | Roll-up status | Histogram |",
              "|---------|-----------|----------------|-----------|"]
    for pr in ct["programs"]:
        hist = ", ".join(f"{k}:{v}" for k, v in sorted(pr["status_histogram"].items()))
        lines.append(f"| {pr['program']} | {pr['artifact_count']} | {pr['rollup_status']} | {hist} |")
    lines += ["", "## Control Tower dimensions", "",
              "| Dimension | Status | Signal source |",
              "|-----------|--------|---------------|"]
    for dim, d in ct["dimensions"].items():
        lines.append(f"| {dim.replace('_', ' ').title()} | {d['status']} | {d['signal_source']} |")
    lines += ["", "*Return: [UCOS-BOOK-000000 Master Index](../../" + C.BOOK_ROOT_PATH + ")*", ""]
    _write(os.path.join(CT_DIR, "PROGRAM-CONTROL-TOWER.md"), lines)


def write_change_registry(cl, by_uid):
    """Emit the CHANGE-VERSION-LINEAGE registry markdown — the human-navigable view
    of the derived change/version/lineage/evolution intelligence (UMB-IMP-003)."""
    c = cl["counts"]
    lines = ["# UCOS Ω∞ — CHANGE · VERSION · LINEAGE REGISTRY", "", _AUTOGEN, "",
             f"**Generated:** {cl['generated_at']}  ·  **Generator:** v{cl['generator_version']}", "",
             "Derived Change / Version / Lineage / Evolution intelligence over the "
             "append-only ledger snapshot history, the typed knowledge graph, and git "
             "causation. Every record is a projection recomputed each transaction; no "
             "change/version/lineage store is an authoritative source (UMB-008/009/010).", "",
             "## Portfolio", "", "| Metric | Value |", "|--------|-------|",
             f"| Change events | {c['change_events']} |",
             f"| Versioned artifacts | {c['versioned_artifacts']} |",
             f"| Lineage nodes | {c['lineage_nodes']} |",
             f"| Artifacts with predecessors | {c['artifacts_with_predecessors']} |",
             f"| Artifacts with successors | {c['artifacts_with_successors']} |", "",
             "### Change-event histogram", "", "| Change kind | Count |", "|-------------|-------|"]
    for k, n in sorted(cl["change_event_histogram"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {n} |")

    # Lineage chains with a non-trivial ancestry or successor set.
    chains = [(uid, v) for uid, v in cl["lineage"].items()
              if v["predecessors"] or v["successors"]]
    lines += ["", "## Lineage chains (non-trivial)", "",
              f"*{len(chains)} artifact(s) participate in a supersession/evolution/"
              f"derivation chain.*", "",
              "| Artifact | Origin | Predecessors | Successors |",
              "|----------|--------|--------------|------------|"]
    for uid, v in sorted(chains):
        preds = ", ".join(f"`{p}`" for p in v["predecessors"]) or "—"
        succs = ", ".join(f"`{s}`" for s in v["successors"]) or "—"
        lines.append(f"| `{uid}` | `{v['origin']}` | {preds} | {succs} |")

    # Most-recent change events (evolution timeline tail).
    tl = cl["evolution_timeline"][-40:]
    lines += ["", "## Evolution timeline (most recent 40)", "",
              "| Change ID | When | Subject | Kind |",
              "|-----------|------|---------|------|"]
    for e in reversed(tl):
        lines.append(f"| `{e['change_id']}` | {e['at']} | `{e['subject']}` | {e['kind']} |")
    lines += ["", "*Return: [UCOS-BOOK-000000 Master Index](" + _link(C.BOOK_ROOT_PATH) + ")*", ""]
    _write(os.path.join(REG_DIR, "CHANGE-VERSION-LINEAGE-REGISTRY.md"), lines)


def _stamp_eq_text(path, text, markers=("**Generated:**", "*Generated ")):
    """True if `path` already holds text equal to `text` ignoring only lines that
    begin with a volatile generation-stamp marker. Enables byte-stable no-op
    regeneration of the auto-generated registries and portal (F-1 drift gate)."""
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as fh:
            old = fh.read()
    except Exception:
        return False
    strip = lambda s: "\n".join(
        ln for ln in s.splitlines()
        if not any(ln.lstrip().startswith(m) for m in markers))
    return strip(old) == strip(text)


def _write(path, lines):
    text = "\n".join(lines)
    if _stamp_eq_text(path, text):
        return                                    # idempotent: only the stamp would change
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ---------------------------------------------------------------------------
# search / trace / stats / validate
# ---------------------------------------------------------------------------
def _load_artifacts():
    data = _load_json(ARTIFACTS_PATH, None)
    if not data:
        sys.exit("No artifacts.json — run `ukb.py build` first.")
    return data["artifacts"]


def cmd_search(args):
    arts = _load_artifacts()
    q = (args.query or "").lower()

    def match(a):
        if args.id and args.id.lower() not in a["universal_id"].lower():
            return False
        if args.volume and args.volume.upper() not in a["volume"]:
            return False
        if args.status and args.status.upper() != a["status"]:
            return False
        if args.program and args.program.upper() != a["program"].upper():
            return False
        if args.owner and args.owner.lower() not in a["owner"].lower():
            return False
        if args.dependency and args.dependency not in a["dependencies"]:
            return False
        if q:
            hay = " ".join([a["universal_id"], a["name"], a.get("native_id") or "",
                            a["program"], a["volume"], " ".join(a["tags"]),
                            a["path"]]).lower()
            if q not in hay:
                return False
        return True

    hits = [a for a in arts if match(a)]
    if not hits:
        print("No matches.")
        return
    for a in hits[: args.limit]:
        print(f"{a['universal_id']}  [{a['volume']}/{a['status']}]  {a['name']}")
        print(f"    native={a['native_id'] or '—'}  program={a['program']}  "
              f"pages={upn(a['page_start'])}-{upn(a['page_end'])}")
        print(f"    → {a['path']}")
    if len(hits) > args.limit:
        print(f"... {len(hits) - args.limit} more (use --limit).")
    print(f"\n{len(hits)} match(es).")


def cmd_trace(args):
    arts = _load_artifacts()
    by_uid = {a["universal_id"]: a for a in arts}
    rels = _load_json(RELS_PATH, {"relationships": []})["relationships"]
    target = args.id
    if target not in by_uid:
        # allow native-id or substring
        cand = [a for a in arts if a["universal_id"] == target
                or (a["native_id"] or "") == target or target.lower() in a["name"].lower()]
        if not cand:
            sys.exit(f"Not found: {target}")
        target = cand[0]["universal_id"]
    a = by_uid[target]
    print(f"{a['universal_id']}  {a['name']}")
    print(f"  volume={a['volume']} status={a['status']} native={a['native_id'] or '—'}")
    print(f"  parent: {a['parent'] or '—'}")
    print(f"  depends-on: {', '.join(a['dependencies']) or '—'}")
    dependents = [x["universal_id"] for x in arts if target in x["dependencies"]]
    children = [x["universal_id"] for x in arts if x["parent"] == target]
    print(f"  children: {', '.join(children) or '—'}")
    print(f"  dependents: {', '.join(dependents) or '—'}")

    # UMB-IMP-002: typed semantic graph — grouped, bidirectional navigation.
    out_by_type, in_by_type = defaultdict(list), defaultdict(list)
    for e in rels:
        if e["from"] == target:
            out_by_type[e["type"]].append(e["to"])
        if e["to"] == target:
            in_by_type[e["type"]].append(e["from"])
    if out_by_type:
        print("  typed edges (outbound):")
        for t in sorted(out_by_type):
            print(f"    -{t}-> {', '.join(sorted(set(out_by_type[t])))}")
    if in_by_type:
        print("  typed edges (inbound / impact surface):")
        for t in sorted(in_by_type):
            print(f"    <-{t}- {', '.join(sorted(set(in_by_type[t])))}")

    # UMB-IMP-002: the traceability spine (only populated lanes shown).
    spine = a.get("traceability", {})
    populated = {k: v for k, v in spine.items() if v}
    if populated:
        print("  traceability spine:")
        for lane in ("requirement", "architecture", "design", "implementation",
                     "source_code", "unit_test", "integration_test",
                     "functional_test", "security_test", "certification",
                     "deployment", "production", "operations"):
            if spine.get(lane):
                print(f"    {lane:16s}: {', '.join(spine[lane])}")


def cmd_evolve(args):
    """UMB-IMP-003 navigation: from any artifact to its Change history, Version
    history, Lineage (backward + forward), Evolution path, and change Impact —
    all derived, evidence-bound (change-ledger.json + typed edges)."""
    arts = _load_artifacts()
    by_uid = {a["universal_id"]: a for a in arts}
    cl = _load_json(CHANGE_LEDGER_PATH, None)
    if not cl:
        sys.exit("No change-ledger.json — run `ukb.py build` first.")
    rels = _load_json(RELS_PATH, {"relationships": []})["relationships"]
    target = args.id
    if target not in by_uid:
        cand = [a for a in arts if a["universal_id"] == target
                or (a["native_id"] or "") == target or target.lower() in a["name"].lower()]
        if not cand:
            sys.exit(f"Not found: {target}")
        target = cand[0]["universal_id"]
    a = by_uid[target]
    print(f"{a['universal_id']}  {a['name']}")
    print(f"  volume={a['volume']} status={a['status']} native={a['native_id'] or '—'}")

    # Version history
    vr = cl["version_records"].get(target, {})
    print(f"  version: current={vr.get('current_version') or '—'} "
          f"first={vr.get('first_version') or '—'} depth={vr.get('version_depth', 0)}")
    for h in vr.get("history", []):
        print(f"    v{h['version']:12s} @ {h['at']}  hash={str(h['content_hash'])[:12]}")

    # Change history
    evs = [e for e in cl["change_events"] if e["subject"] == target]
    print(f"  change history: {len(evs)} event(s)")
    for e in evs:
        why = ""
        if e.get("commit"):
            why = f"  ⇐ {e['commit']['commit']} \"{e['commit']['subject']}\" ({e['commit']['author']})"
        print(f"    [{e['change_id']}] {e['kind']:20s} @ {e['at']}{why}")

    # Lineage (bidirectional) + evolution path
    ln = cl["lineage"].get(target, {})
    print(f"  lineage: origin={ln.get('origin') or target} birth={ln.get('birth') or '—'}")
    print(f"    predecessors: {', '.join(ln.get('predecessors', [])) or '—'}")
    print(f"    successors:   {', '.join(ln.get('successors', [])) or '—'}")
    if ln.get("ancestor_chain"):
        print(f"    ancestry (backward):  {' → '.join(ln['ancestor_chain'])}")
    if ln.get("descendant_chain"):
        print(f"    evolution (forward):  {' → '.join(ln['descendant_chain'])}")

    # Change impact: inbound typed edges are the artifacts affected by a change here.
    impact = defaultdict(list)
    for e in rels:
        if e["to"] == target and e["type"] in (
                "Required-By", "Consumed-By", "Referenced-By", "Implemented-By",
                "Certified-By", "Tested-By", "Deployed-By"):
            impact[e["type"]].append(e["from"])
    if impact:
        print("  change impact (who is affected if this changes):")
        for t in sorted(impact):
            print(f"    {t}: {', '.join(sorted(set(impact[t])))}")


def cmd_stats(args):
    arts = _load_artifacts()
    vols = _load_json(VOLUMES_PATH, {"volumes": []})["volumes"]
    rels = _load_json(RELS_PATH, {"count": 0})
    print(f"Artifacts: {len(arts)}")
    print(f"Volumes:   {len([v for v in vols if v['artifact_count']])} active / {len(vols)} total")
    print(f"Edges:     {rels['count']}")
    print("By program:")
    for prog, n in Counter(a["program"] for a in arts).most_common():
        print(f"  {prog:16s} {n}")
    print("By status:")
    for s, n in Counter(a["status"] for a in arts).most_common():
        print(f"  {s:16s} {n}")


def cmd_validate(args):
    arts = _load_artifacts()
    problems = []

    # structural invariants
    uids = [a["universal_id"] for a in arts]
    if len(uids) != len(set(uids)):
        problems.append("Duplicate Universal IDs detected.")
    # page ranges non-overlapping & contiguous-append
    spans = sorted((a["page_start"], a["page_end"], a["universal_id"]) for a in arts)
    last_end = 0
    for s, e, uid in spans:
        if s <= last_end:
            problems.append(f"Page overlap at {uid}: start {s} <= prev end {last_end}.")
        if e < s:
            problems.append(f"Inverted page range at {uid}.")
        last_end = max(last_end, e)
    # parent/dep referential integrity
    known = set(uids)
    for a in arts:
        if a["parent"] and a["parent"] not in known:
            problems.append(f"{a['universal_id']} parent {a['parent']} unknown.")
        for d in a["dependencies"]:
            if d not in known:
                problems.append(f"{a['universal_id']} dep {d} unknown.")

    # schema validation (optional)
    try:
        import jsonschema  # type: ignore
        schema = _load_json(os.path.join(SCHEMA_DIR, "artifact.schema.json"), None)
        for a in arts:
            try:
                jsonschema.validate(a, schema)
            except jsonschema.ValidationError as ex:  # type: ignore
                problems.append(f"{a['universal_id']} schema: {ex.message}")
        print("jsonschema validation: ran.")
    except ImportError:
        print("jsonschema not installed — ran structural checks only "
              "(pip install jsonschema for full schema validation).")

    # EXEC-REG-001: the execution register's structural integrity is part of the
    # atomic transaction's validation (register.sh §7 Phase 5). Vacuous ([],0) when
    # the register is empty/absent, so this never fails a corpus without executions.
    exec_problems, exec_count = validate_executions()
    problems += exec_problems

    if problems:
        print(f"\nVALIDATION FAILED — {len(problems)} problem(s):")
        for p in problems[:50]:
            print("  -", p)
        sys.exit(1)
    print(f"\nVALIDATION PASSED — {len(arts)} artifacts, append-only page ledger intact, "
          f"referential integrity OK; {exec_count} execution(s) — forward-only "
          f"append-only lifecycle intact.")


def _enforcement_audit(record):
    """Append an enforcement-gate outcome to the append-only audit log, de-duping
    consecutive runs with identical content so idempotent re-runs never grow the
    file (keeps register.sh --guard drift-free). Operational log, not a registry."""
    path = os.path.join(DATA_DIR, C.ENFORCEMENT_AUDIT_FILE)
    doc = _load_json(path, {"version": 1, "runs": []})
    fp_keys = ("mode", "result", "eligible", "registered", "unregistered",
               "unclassified", "invalid", "violations")
    fingerprint = {k: record.get(k) for k in fp_keys}
    # Dedup against the most recent run of the SAME mode so idempotent re-runs
    # (pre/post alternate every transaction) never grow the log — otherwise the
    # log itself would be perpetual registration drift.
    prior_same_mode = [r for r in doc["runs"] if r.get("mode") == record.get("mode")]
    last = prior_same_mode[-1] if prior_same_mode else None
    if last and {k: last.get(k) for k in fp_keys} == fingerprint:
        return last["seq"]                       # unchanged — no-op append
    record["seq"] = (doc["runs"][-1]["seq"] + 1) if doc["runs"] else 1
    doc["runs"].append(record)
    _dump_json(path, doc)
    return record["seq"]


def cmd_enforce(args):
    """UMB-IMP-001 enforcement gate. Guarantees no unregistered, unclassified, or
    invalid artifact silently enters the corpus (REG-AUTO-001 §16; STATUS-001 §5).

    The gate applies a SINGLE FIXED POLICY (GOV-005 §5.4): eligibility, validity,
    classification, and registration are all enforced, so the result is a pure,
    deterministic function of repository state. Modes:
      --pre   (pre-registration): validate every ELIGIBLE file that is not yet
              registered — it must be valid and classifiable BEFORE the transaction
              registers it. Fails closed on an invalid or unclassified new artifact.
      (post, default): after the transaction — asserts registration completeness
              (count parity), validity, and classification for every eligible file.
    """
    default_program = C.DEFAULT_CLASS[0]
    eligible = list(_iter_files())                       # (abspath, rel)
    data = _load_json(ARTIFACTS_PATH, None)
    registered = {a["path"] for a in data["artifacts"]} if data else set()

    invalid, unclassified, unregistered = [], [], []
    for abspath, rel in eligible:
        # validity gate
        try:
            size = os.path.getsize(abspath)
            ok_read = size >= C.MIN_ARTIFACT_BYTES
        except OSError:
            ok_read = False
        if not ok_read or not title_from(abspath, rel):
            invalid.append(rel)
        # classification gate — OTHER is the only true "unclassified" marker;
        # a real rule may legitimately resolve to VOL-000 (MASTER INDEX).
        program, category, _vol = classify(rel, abspath)
        if program == default_program or category == C.DEFAULT_CLASS[1]:
            unclassified.append(rel)
        # registration gate
        if rel not in registered:
            unregistered.append(rel)

    pre = getattr(args, "pre", False)

    # SINGLE FIXED GATE POLICY (GOV-005 §5.4, AUD-RC-1 correction). Classification
    # is ALWAYS enforced — never conditional on an invocation flag — so the audit
    # result is a PURE FUNCTION of repository state: identical repository contents
    # always produce identical output. This is safe and deterministic because the
    # total path-derived classifier (§5.2) drives `unclassified` to 0 structurally.
    # The former `--strict` flag no longer changes the outcome (it is retained as
    # an accepted no-op for backward compatibility; see argparse) — so running the
    # gate with or without it yields byte-identical results. Combined with the
    # version-control eligibility boundary (§5.1), the audit is also repeatable
    # across environments (a present/absent venv, a fresh test run, or generated
    # evidence can no longer perturb `eligible`).
    if pre:
        # PRE: only NEWLY-created (unregistered) files are gated; already-registered
        # legacy artifacts are out of scope for the authoring gate. A new artifact
        # must be valid AND classifiable before the transaction registers it.
        pending = set(unregistered)
        hard = ([r for r in invalid if r in pending]
                + [r for r in unclassified if r in pending])
        gate_label = "PRE-REGISTRATION"
    else:
        # POST: every eligible file must be registered (parity), valid, and classified.
        hard = list(unregistered) + list(invalid) + list(unclassified)
        gate_label = "POST-REGISTRATION"

    violations = sorted(set(hard))
    result = "PASS" if not violations else "FAIL"
    record = {
        "generated_at": _now(),
        "generator_version": C.GENERATOR_VERSION,
        "mode": "pre" if pre else "post",
        "gates": list(C.ENFORCEMENT_GATES),
        "eligible": len(eligible),
        "registered": len(registered),
        "unregistered": sorted(unregistered),
        "unclassified": sorted(unclassified),
        "invalid": sorted(invalid),
        "violations": violations,
        "result": result,
    }
    seq = _enforcement_audit(record)

    print(f"UMB-IMP-001 Enforcement Gate [{gate_label}]  (audit run #{seq})")
    print("-" * 60)
    print(f"  eligible on-disk artifacts : {len(eligible)}")
    print(f"  registered (in registers)  : {len(registered)}")
    print(f"  unregistered eligible      : {len(unregistered)}")
    print(f"  unclassified (OTHER/MISC)  : {len(unclassified)} (GATED)")
    print(f"  invalid (unreadable/empty) : {len(invalid)}")
    for r in unregistered[:10]:
        print(f"    UNREGISTERED  {r}")
    for r in unclassified[:10]:
        print(f"    unclassified  {r}  (declare metadata or a CLASSIFY_RULE)")
    print("-" * 60)
    if violations:
        print(f"ENFORCEMENT FAILED — {len(violations)} blocking violation(s); "
              f"artifacts remain UNREGISTERED / INVALID; completion claims INVALID.")
        for v in violations[:20]:
            print("  -", v)
        sys.exit(1)
    print(f"ENFORCEMENT PASSED — no unregistered or invalid artifact "
          f"can silently enter the corpus.")


# ---------------------------------------------------------------------------
# EXEC-REG-001 — UCOS AUTONOMOUS EXECUTION REGISTER (RUNTIME EXTENSION)
#
# Realizes RUNTIME-006 (Universal Execution Architecture) as a record-only,
# append-only, evidence-derived, NON-CONSTITUTIVE runtime register of execution
# INSTANCES. Execution identities are minted from the SAME append-only Universal
# Identity ledger authority as every other Universal Entity (allocate_execution
# reuses ledger["category_seq"]); there is no second identity scheme (EXL-02).
# The lifecycle engine enforces the forward-only RUNTIME-006 D7 lifecycle
# (EXL-07/10). The register is NOT a runtime engine (EXL-23; authorized reading:
# deterministic repository machinery is permitted) — it selects no technology and
# executes nothing; it RECORDS the typed, identified, bounded, lineage-linked
# behavioral progression of foundation constructs. Registration state is kept
# synchronized by the same atomic transaction as every other register
# (register.sh: ukb validate Phase 5, ukbx sync Phase 2, ukbx certify Phase 8).
# ---------------------------------------------------------------------------
EXECUTIONS_PATH = os.path.join(DATA_DIR, C.EXECUTION_STORE_FILE)

_SECRET_HINTS = ("password=", "secret=", "api_key=", "apikey=", "token=ghp_",
                 "-----begin", "aws_secret_access_key")


def _secret_free_text(text) -> bool:
    """RR-07 guard: reject obvious secret material from execution content."""
    low = str(text).lower()
    return not any(h in low for h in _SECRET_HINTS)


def _exec_cycle(graph):
    """Return a node on a cycle in the execution-dependency graph, else None
    (EXL-17 requires acyclic, downward-only, closed dependencies)."""
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}

    def dfs(u):
        color[u] = GREY
        for v in graph.get(u, []):
            if color.get(v, WHITE) == GREY:
                return True
            if color.get(v, WHITE) == WHITE and dfs(v):
                return True
        color[u] = BLACK
        return False

    for n in list(graph):
        if color[n] == WHITE and dfs(n):
            return n
    return None


def allocate_execution(ledger, exec_key):
    """Mint (or return) an append-only Universal execution identity for exec_key.
    Reuses the ONE identity authority (the id-ledger category_seq counter) and the
    UCOS-<CATEGORY>-NNNNNN convention; keyed by a stable execution key so
    re-declaration is idempotent. Executions are NOT paginated (Universal Pages
    index the book's documents, not runtime instances). Append-only: an allocated
    execution id is never reused, renumbered, or reordered (P4; EXL-02)."""
    ledger.setdefault("by_execution", {})
    entry = ledger["by_execution"].get(exec_key)
    if entry:
        return entry["execution_id"]
    cat = C.EXECUTION_CATEGORY
    seq = ledger["category_seq"].get(cat, 0) + 1
    ledger["category_seq"][cat] = seq
    eid = f"UCOS-{cat}-{seq:06d}"
    ledger["by_execution"][exec_key] = {"execution_id": eid, "first_seen": _now()}
    return eid


def _exec_load():
    return _load_json(EXECUTIONS_PATH, {
        "generated_at": None,
        "generator_version": C.GENERATOR_VERSION,
        "standard": "RUNTIME-006 Universal Execution Architecture "
                    "(record-only; append-only; non-constitutive)",
        "count": 0, "executions": {}})


def _exec_save(doc):
    doc["count"] = len(doc.get("executions", {}))
    doc["generated_at"] = _now()
    _dump_json(EXECUTIONS_PATH, doc)


def _exec_subject_index():
    """(uid_set, native->uid) over the registered artifact registry so an
    execution subject may be given as either a Universal ID or a native ID and is
    resolved to the ONE registered identity — never fabricated (EXL-02)."""
    arts = _load_artifacts()
    uids = {a["universal_id"] for a in arts}
    native = {a["native_id"]: a["universal_id"] for a in arts if a.get("native_id")}
    return uids, native


def validate_executions():
    """Structural integrity of the execution register (RUNTIME-006 conformance).
    Returns (problems, count). An absent/empty register is vacuously valid ([],0)."""
    if not os.path.exists(EXECUTIONS_PATH):
        return [], 0
    doc = _exec_load()
    execs = doc.get("executions", {})
    ledger = load_ledger()
    minted = {v["execution_id"] for v in ledger.get("by_execution", {}).values()}
    try:
        uids, _native = _exec_subject_index()
    except SystemExit:
        uids = set()
    problems = []
    dep_graph = {}
    for eid, r in execs.items():
        if r.get("execution_id") != eid:
            problems.append(f"{eid}: record execution_id mismatch ({r.get('execution_id')})")
        if eid not in minted:
            problems.append(f"{eid}: not minted from the id-ledger identity authority (EXL-02)")
        if r.get("lifecycle_state") not in C.EXECUTION_LIFECYCLE:
            problems.append(f"{eid}: illegal lifecycle_state {r.get('lifecycle_state')}")
        if r.get("type") not in C.EXECUTION_TYPES:
            problems.append(f"{eid}: illegal type {r.get('type')}")
        if r.get("category") not in C.EXECUTION_CATEGORIES:
            problems.append(f"{eid}: illegal category {r.get('category')}")
        trs = r.get("transitions", [])
        if [t.get("seq") for t in trs] != list(range(1, len(trs) + 1)):
            problems.append(f"{eid}: transition seq not monotonic append-only")
        if trs:
            if trs[0].get("from") is not None or trs[0].get("to") != C.EXECUTION_INITIAL_STATE:
                problems.append(f"{eid}: first transition must be →{C.EXECUTION_INITIAL_STATE}")
            for a, b in zip(trs, trs[1:]):
                if b.get("from") != a.get("to"):
                    problems.append(f"{eid}: transition #{b.get('seq')} from-state discontinuity")
                if b.get("to") not in C.EXECUTION_TRANSITIONS.get(a.get("to"), ()):
                    problems.append(f"{eid}: illegal transition {a.get('to')} → {b.get('to')} "
                                    f"(forward-only; EXL-07/10)")
            if trs[-1].get("to") != r.get("lifecycle_state"):
                problems.append(f"{eid}: lifecycle_state disagrees with last transition")
        subj = r.get("subject_universal_id")
        if subj and uids and subj not in uids:
            problems.append(f"{eid}: subject {subj} does not resolve to a registered artifact")
        deps = r.get("dependencies", [])
        for d in deps:
            if d not in execs:
                problems.append(f"{eid}: dependency {d} does not resolve to a registered execution")
        dep_graph[eid] = [d for d in deps if d in execs]
        blob = json.dumps({"n": r.get("name"), "c": r.get("context"),
                           "b": r.get("boundary"), "t": [t.get("note") for t in trs]})
        if not _secret_free_text(blob):
            problems.append(f"{eid}: secret-bearing content rejected (RR-07)")
    cyc = _exec_cycle(dep_graph)
    if cyc:
        problems.append(f"execution dependency cycle via {cyc} (EXL-17 requires acyclic)")
    return problems, len(execs)


def _exec_declare(args):
    if not args.key or not args.name:
        sys.exit("exec declare requires --key and --name")
    etype = args.type or C.EXECUTION_DEFAULT_TYPE
    ecat = args.category or C.EXECUTION_DEFAULT_CATEGORY
    if etype not in C.EXECUTION_TYPES:
        sys.exit(f"invalid --type {etype}; one of {C.EXECUTION_TYPES}")
    if ecat not in C.EXECUTION_CATEGORIES:
        sys.exit(f"invalid --category {ecat}; one of {C.EXECUTION_CATEGORIES}")
    subject = None
    if args.subject:
        uids, native = _exec_subject_index()
        subject = args.subject if args.subject in uids else native.get(args.subject)
        if not subject:
            sys.exit(f"subject does not resolve to a registered artifact: {args.subject} "
                     "(no fabrication; declare against a real Universal/native ID; EXL-02)")
    for blob in (args.name, args.context, args.start, args.terminal, args.note):
        if blob and not _secret_free_text(blob):
            sys.exit("declaration content appears to contain a secret; rejected (RR-07)")
    deps = sorted(set(args.depends or []))
    ledger = load_ledger()
    doc = _exec_load()
    for d in deps:
        if d not in doc["executions"]:
            sys.exit(f"execution dependency does not resolve: {d} "
                     "(declare dependencies first; EXL-17 closed/acyclic)")
    eid = allocate_execution(ledger, args.key)
    if eid in doc["executions"]:
        _dump_json(LEDGER_PATH, ledger)          # idempotent re-declare — no-op
        print(f"execution already declared: {eid} (idempotent no-op)")
        return
    now = _now()
    doc["executions"][eid] = {
        "execution_id": eid, "execution_key": args.key, "name": args.name,
        "type": etype, "category": ecat,
        "subject_universal_id": subject,
        "context": args.context or None,
        "boundary": {"start_condition": args.start or None,
                     "terminal_condition": args.terminal or None},
        "dependencies": deps,
        "lifecycle_state": C.EXECUTION_INITIAL_STATE,
        "transitions": [{"seq": 1, "from": None, "to": C.EXECUTION_INITIAL_STATE,
                         "at": now, "note": args.note or "declared"}],
        "first_seen": now, "last_transition_at": now, "last_transition_seq": 1,
    }
    _dump_json(LEDGER_PATH, ledger)
    _exec_save(doc)
    print(f"declared {eid}  [{etype}/{ecat}] subject={subject or '—'} state=declared")


def _exec_transition(args, target):
    if not args.id:
        sys.exit("exec transition requires --id")
    if target not in C.EXECUTION_LIFECYCLE:
        sys.exit(f"invalid target state: {target}")
    if args.note and not _secret_free_text(args.note):
        sys.exit("transition note appears to contain a secret; rejected (RR-07)")
    doc = _exec_load()
    rec = doc["executions"].get(args.id)
    if not rec:
        sys.exit(f"unknown execution: {args.id}")
    cur = rec["lifecycle_state"]
    if cur == target:
        print(f"{args.id} already in state {target} (idempotent no-op)")
        return
    if target not in C.EXECUTION_TRANSITIONS.get(cur, ()):
        allowed = C.EXECUTION_TRANSITIONS.get(cur, ())
        sys.exit(f"illegal transition {cur} → {target} (forward-only; "
                 f"legal: {allowed or 'none — terminal'}; RUNTIME-006 EXL-07/10)")
    seq = rec["last_transition_seq"] + 1
    now = _now()
    rec["transitions"].append({"seq": seq, "from": cur, "to": target,
                               "at": now, "note": args.note or target})
    rec["lifecycle_state"] = target
    rec["last_transition_at"] = now
    rec["last_transition_seq"] = seq
    _exec_save(doc)
    print(f"{args.id}  {cur} → {target}  (transition #{seq})")


def cmd_exec(args):
    """EXEC-REG-001 execution register CLI (RUNTIME-006)."""
    op = args.op
    if op == "declare":
        return _exec_declare(args)
    if op == "list":
        doc = _exec_load()
        rows = list(doc["executions"].values())
        if getattr(args, "state", None):
            rows = [r for r in rows if r["lifecycle_state"] == args.state]
        if getattr(args, "subject", None):
            rows = [r for r in rows if r.get("subject_universal_id") == args.subject]
        for r in sorted(rows, key=lambda r: r["execution_id"]):
            print(f"{r['execution_id']}  {r['lifecycle_state']:10s} "
                  f"[{r['type']}/{r['category']}] subject={r.get('subject_universal_id') or '—'}  {r['name']}")
        print(f"\n{len(rows)} execution(s).")
        return
    if op == "show":
        doc = _exec_load()
        rec = doc["executions"].get(args.id)
        if not rec:
            sys.exit(f"unknown execution: {args.id}")
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return
    if op == "validate":
        problems, count = validate_executions()
        if problems:
            print(f"EXECUTION REGISTER VALIDATION FAILED — {len(problems)} problem(s):")
            for p in problems[:50]:
                print("  -", p)
            sys.exit(1)
        print(f"EXECUTION REGISTER VALIDATION PASSED — {count} execution(s); minted from "
              f"the id-ledger authority; forward-only append-only lifecycle; acyclic "
              f"dependencies; subjects resolve; secret-free.")
        return
    verb_to_state = {"transition": getattr(args, "to", None), "activate": "active",
                     "suspend": "suspended", "resume": "active",
                     "complete": "completed", "terminate": "terminated"}
    target = verb_to_state.get(op)
    if not target:
        sys.exit(f"unknown exec op: {op}")
    return _exec_transition(args, target)


def main():
    ap = argparse.ArgumentParser(prog="ukb", description="UCOS Ω∞ Universal Master Knowledge Book engine.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("build", help="Scan repo, allocate IDs/pages, emit registries + control tower.")

    sp = sub.add_parser("search", help="Search the knowledge base.")
    sp.add_argument("query", nargs="?", default="")
    sp.add_argument("--id"); sp.add_argument("--volume"); sp.add_argument("--status")
    sp.add_argument("--program"); sp.add_argument("--owner"); sp.add_argument("--dependency")
    sp.add_argument("--limit", type=int, default=25)

    tp = sub.add_parser("trace", help="Show graph neighbourhood of an artifact.")
    tp.add_argument("id")

    evp = sub.add_parser("evolve", help="UMB-IMP-003 change/version/lineage/evolution navigation for an artifact.")
    evp.add_argument("id")

    sub.add_parser("stats", help="Portfolio statistics.")
    sub.add_parser("validate", help="Validate DATA (structural + schema).")

    ep = sub.add_parser("enforce", help="UMB-IMP-001 registration/classification/validity enforcement gate.")
    ep.add_argument("--pre", action="store_true",
                    help="Pre-registration gate: gate only newly-created (unregistered) artifacts.")
    ep.add_argument("--strict", action="store_true",
                    help="DEPRECATED no-op (GOV-005 §5.4): classification is now always "
                         "enforced under the single fixed gate policy. Accepted for "
                         "backward compatibility; it no longer changes the audit result.")

    xp = sub.add_parser("exec", help="EXEC-REG-001 execution register (RUNTIME-006): declare / "
                        "transition / activate / suspend / resume / complete / terminate / "
                        "list / show / validate execution instances.")
    xp.add_argument("op", choices=["declare", "transition", "activate", "suspend", "resume",
                                   "complete", "terminate", "list", "show", "validate"])
    xp.add_argument("--id", help="Execution Universal ID (UCOS-EXEC-NNNNNN).")
    xp.add_argument("--key", help="Stable execution key (idempotent declaration key).")
    xp.add_argument("--name", help="Human-readable execution name.")
    xp.add_argument("--type", help=f"Execution type: {', '.join(C.EXECUTION_TYPES)}.")
    xp.add_argument("--category", help=f"Execution category: {', '.join(C.EXECUTION_CATEGORIES)}.")
    xp.add_argument("--subject", help="Subject artifact (Universal or native ID) the execution progresses.")
    xp.add_argument("--context", help="Bounded execution context (scope).")
    xp.add_argument("--start", help="Explicit start condition (boundary).")
    xp.add_argument("--terminal", help="Explicit terminal condition (boundary).")
    xp.add_argument("--to", help="Target lifecycle state for `transition`.")
    xp.add_argument("--note", help="Transition/declaration note (recorded, secret-free).")
    xp.add_argument("--depends", nargs="*", help="Execution dependencies (existing UCOS-EXEC-* ids).")
    xp.add_argument("--state", help="Filter `list` by lifecycle state.")

    args = ap.parse_args()
    {"build": cmd_build, "search": cmd_search, "trace": cmd_trace,
     "evolve": cmd_evolve, "stats": cmd_stats, "validate": cmd_validate,
     "enforce": cmd_enforce, "exec": cmd_exec}[args.cmd](args)


if __name__ == "__main__":
    main()
