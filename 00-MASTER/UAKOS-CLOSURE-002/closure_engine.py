#!/usr/bin/env python3
"""UAKOS-CLOSURE-002 — deterministic repository closure engine.

Implements the Vision-to-Repository closure program as an auditable, re-runnable,
standard-library-only tool (honors UCKO-PRIN-0003 vendor-neutral core and
UCKO-PRIN-0005 determinism). It never mutates the frozen corpus and never issues
a closure certificate that the evidence does not support (fail-closed, TRACK-001).

Pipeline (mission phases 1-10):
    discover sources -> extract canonical concept anchors -> match Repository Truth
    -> assign one disposition -> analyze duplicates/orphans/traceability
    -> emit 14 artifacts + closure.json -> fail-closed determination.

Usage:
    python3 00-MASTER/UAKOS-CLOSURE-002/closure_engine.py            # generate reports
    python3 00-MASTER/UAKOS-CLOSURE-002/closure_engine.py --gate     # exit 1 if NOT-CLOSED
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

# --------------------------------------------------------------------------- paths
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent  # <repo>/00-MASTER/UAKOS-CLOSURE-002 -> <repo>
CORPUS = REPO.parent / "UCOS"  # external corpus sibling (conversation/upload material)

# Canonical-truth roots: a concept ID found here is "homed" (has a canonical home).
TRUTH_ROOTS = (
    "02-MASTER", "00-CEP", "00-MASTER", "00-BOOK", "03-CATALOGS", "04-REFERENCE",
    "06-IMPLEMENTATION", "07-ENGINEERING", "08-RUNTIME", "09-PLATFORM",
    "10-DATA", "11-SERVICE", "12-APPLICATION", "13-INFRASTRUCTURE", "14-SECURITY",
    "99-FREEZE", "adr", "knowledge",
)
# Engineering (code) roots: presence here is IMPLEMENTED evidence.
CODE_ROOTS = ("engine", "platform", "data", "service", "application", "infrastructure", "intelligence")
# Upload/source roots: presence ONLY here (or in corpus) = upload/conversation-only gap.
SOURCE_ROOTS = ("00-SOURCE",)
# Spec/constitution roots: presence here is SPECIFIED evidence.
SPEC_ROOTS = ("02-MASTER", "00-CEP", "10-DATA", "11-SERVICE", "12-APPLICATION",
              "13-INFRASTRUCTURE", "14-SECURITY", "08-RUNTIME", "09-PLATFORM", "06-IMPLEMENTATION")
PLAN_MARK = re.compile(r"\b(ROADMAP|MASTER PLAN|MASTER-PLAN|MEP-\d|CHARTER|PLANNED|FUTURE)\b", re.I)
DEFER_MARK = re.compile(r"\b(DEFERRED|BLOCKED|PENDING AUTHORIZATION|DEFER)\b", re.I)
REJECT_MARK = re.compile(r"\b(REJECTED|rejected_options|REJECT)\b")

TEXT_EXT = {".md", ".txt", ".py", ".json", ".toml", ".sh", ".yml", ".yaml", ".cfg"}

# --------------------------------------------------------------------------- concept anchor families
# Each family is (name, compiled-regex). Curated to the repo's real ID namespace.
FAMILIES: list[tuple[str, re.Pattern[str]]] = [
    ("UCKO", re.compile(r"\bUCKO-[A-Z]+-\d{3,4}\b")),
    ("UKDA-DEC", re.compile(r"\bUKDA-DEC-\d{3,4}\b")),
    ("ARCH", re.compile(r"\bARCH-[A-Z0-9]+-\d{3}\b")),
    ("MEP", re.compile(r"\bMEP-\d{2}\b")),
    ("MCP", re.compile(r"\bMCP-\d{3}\b")),
    ("MCS", re.compile(r"\bMCS-\d{3}\b")),
    ("CEP", re.compile(r"\bCEP-\d{3}\b")),
    ("DATA", re.compile(r"\bDATA-\d{3}\b")),
    ("SERVICE", re.compile(r"\bSERVICE-\d{3}\b")),
    ("APPLICATION", re.compile(r"\bAPPLICATION-\d{3}\b")),
    ("INFRASTRUCTURE", re.compile(r"\bINFRASTRUCTURE-\d{3}\b")),
    ("PLATFORM", re.compile(r"\bPLATFORM-\d{3}\b")),
    ("RUNTIME", re.compile(r"\bRUNTIME-\d{3}\b")),
    ("UCOS-COMP", re.compile(r"\bUCOS-COMP-\d{6}\b")),
    ("UCOS-GOV", re.compile(r"\bUCOS-GOV-\d{3}\b")),
    ("UCOS-EXEC", re.compile(r"\bUCOS-EXEC-\d{3}\b")),
    ("UCOS-RAT", re.compile(r"\bUCOS-RAT-\d{3}\b")),
    ("UCOS-RECON", re.compile(r"\bUCOS-RECON-[A-Z0-9]+\b")),
    ("EPIC", re.compile(r"\bEPIC-[A-Z]+-\d{3}\b")),
    ("GOV", re.compile(r"\bGOV-\d{3}\b")),
    ("METACLASS", re.compile(r"\b(?:AMC|AMR|DMC|DMR|SMC|SMR|ICMP|ICNW|ISTO|ICAP)-\d{2}\b")),
    ("BAND-UNIT", re.compile(r"\bEC3-B\d{2}-[A-Z]?\d{2}\b")),
    ("EC3-GATE", re.compile(r"\bEC-3-AP-\d\b")),
    ("FOUNDATION", re.compile(r"\b(?:EL-1|RL-F2|PL-F2|DF-2|SF-2|AF-3)\b")),
    ("LAW", re.compile(r"Ω∞-\d{3}\b")),
    ("PHASE", re.compile(r"\bPhase-\d{3}\b")),
]
CERT_RE = re.compile(r"\bUCOS-CERT-[A-Za-z0-9-]{6,}\b")  # evidence token, not a concept
_SENTINEL = re.compile(r"-U?9{2,3}$")  # wildcard/example ids (…-99, …-999, …-U99) are not real concepts


def _run(cmd: list[str]) -> str:
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False).stdout


def _read_text(path: Path, limit: int = 4_000_000) -> str:
    try:
        if path.suffix.lower() == ".docx":
            with zipfile.ZipFile(path) as z:
                if "word/document.xml" not in z.namelist():
                    return ""
                raw = z.read("word/document.xml").decode("utf-8", "ignore")
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw))[:limit]
        if path.suffix.lower() in TEXT_EXT or path.suffix.lower() == ".docx":
            return path.read_text("utf-8", "ignore")[:limit]
    except (OSError, zipfile.BadZipFile):
        return ""
    return ""


def _top(rel: str) -> str:
    return rel.split("/", 1)[0]


# --------------------------------------------------------------------------- phase 1: source discovery
def _tracked_paths() -> list[str]:
    """Every tracked path, NUL-delimited so non-ASCII names survive verbatim.

    `git ls-files` without `-z` renders any path containing a non-ASCII byte in
    double-quoted, octal-escaped form (`"…/UCOS-\\316\\251\\342\\210\\236-…"`). That
    literal string does not resolve on disk, so every such artifact was silently read as
    empty and dropped from concept extraction — 116 tracked `Ω∞` artifacts, including
    canonical `02-MASTER/` architecture constitutions that DECLARE concept identities.
    Their concepts therefore measured as having no canonical home, which is a measurement
    defect, not repository truth. `-z` is the same fix `00-BOOK/tools/ukb.py::_git_ls`
    already applies, so closure now sees exactly the eligibility boundary registration
    sees (the divergence recorded as OBS-1 in
    `00-MASTER/UCCEP-000007/17-EVIDENCE-APPENDIX.md` §E-02).
    """
    return [f for f in _run(["git", "ls-files", "-z"]).split("\0") if f]


def discover_sources() -> dict:
    tracked = _tracked_paths()
    docx = sorted(f for f in tracked if f.lower().endswith(".docx"))
    md = sorted(f for f in tracked if f.lower().endswith(".md"))
    root_uploads = sorted(f for f in tracked if "/" not in f and f.lower().endswith((".md", ".docx")))
    corpus_files: list[str] = []
    if CORPUS.is_dir() and os.environ.get("CLOSURE_SKIP_CORPUS") != "1":
        for p in sorted(CORPUS.rglob("*")):
            if p.is_file() and p.suffix.lower() in (TEXT_EXT | {".docx"}):
                corpus_files.append(str(p.relative_to(CORPUS)))
    by_top: dict[str, int] = defaultdict(int)
    for f in tracked:
        by_top[_top(f)] += 1
    return {
        "tracked_total": len(tracked),
        "tracked_by_top": dict(sorted(by_top.items(), key=lambda kv: (-kv[1], kv[0]))),
        "markdown": md,
        "docx_uploads": docx,
        "root_uploads": root_uploads,
        "corpus_dir": str(CORPUS),
        "corpus_present": CORPUS.is_dir(),
        "corpus_files": corpus_files,
        "_tracked": tracked,
    }


# --------------------------------------------------------------------------- phase 2/3/4: extract + match
def _new_rec(cid: str, fam: str) -> dict:
    return {
        "id": cid, "family": fam, "zones": set(), "tops": set(),
        "homed": False, "in_filename": False, "in_code": False, "in_book": False,
        "in_spec": False, "in_constitution": False, "in_plan": False,
        "deferred": False, "rejected": False, "certified": False,
        "files": set(), "def_homes": set(), "exact_homes": set(),
        "source_only_files": set(), "corpus_files": set(),
    }


# derived / non-definitional path segments: presence here is evidence, never a canonical home
DERIVED_SEG = ("_evidence/", "/outputs/", "outputs/", "determinism-evidence/",
               "CHECKPOINTS/", "/__pycache__/", ".egg-info/")


def _is_def_home(rel: str, cid: str) -> bool:
    """A definitional home: a truth-root file whose basename is (or starts with) the id,
    excluding derived/evidence/checkpoint artifacts."""
    if any(seg in rel for seg in DERIVED_SEG):
        return False
    if _top(rel) not in TRUTH_ROOTS:
        return False
    stem = rel.rsplit("/", 1)[-1].upper()
    cu = cid.upper()
    return stem == cu or stem.startswith(cu + "-") or stem.startswith(cu + ".") or stem.startswith(cu + "_")


def _scan(paths: list[tuple[str, Path]], concepts: dict, cert_index: dict, zone: str) -> None:
    """Populate concept occurrences with line-local disposition markers. zone in {repo, source, corpus}."""
    for rel, abspath in paths:
        text = _read_text(abspath)
        if not text:
            continue
        top = _top(rel)
        name_upper = rel.upper()
        # line-local pass: attribute disposition markers only to ids on the same line
        for line in text.splitlines() if "\n" in text else [text]:
            ids_here: list[tuple[str, str]] = []
            for fam, rx in FAMILIES:
                for cid in rx.findall(line):
                    if _SENTINEL.search(cid):  # wildcard/example ids (…-99, …-999) are not concepts
                        continue
                    ids_here.append((cid, fam))
            if not ids_here:
                continue
            reject = bool(REJECT_MARK.search(line))
            defer = bool(DEFER_MARK.search(line))
            plan = bool(PLAN_MARK.search(line))
            certs_here = CERT_RE.findall(line)
            for cid, fam in ids_here:
                rec = concepts.get(cid) or concepts.setdefault(cid, _new_rec(cid, fam))
                rec["zones"].add(zone)
                rec["tops"].add(top)
                rec["files"].add(rel)
                if reject:
                    rec["rejected"] = True
                if defer:
                    rec["deferred"] = True
                if plan:
                    rec["in_plan"] = True
                if certs_here:
                    rec["certified"] = True
                    cert_index.setdefault(cid, set()).update(certs_here)
                if zone == "repo":
                    in_derived = any(s in rel for s in DERIVED_SEG)
                    if top in TRUTH_ROOTS:
                        rec["homed"] = True
                    if top in CODE_ROOTS and not in_derived:
                        rec["in_code"] = True
                        rec["homed"] = True  # implementation is a valid canonical home
                    if top in SPEC_ROOTS:
                        rec["in_spec"] = True
                    if top in ("02-MASTER", "00-CEP"):
                        rec["in_constitution"] = True
                    if top in ("00-BOOK", "00-MASTER", "03-CATALOGS", "04-REFERENCE"):
                        rec["in_book"] = True
                    if cid in name_upper:
                        rec["homed"] = True
                    if _is_def_home(rel, cid):
                        rec["homed"] = True
                        rec["in_filename"] = True
                        rec["def_homes"].add(rel)
                        stem = rel.rsplit("/", 1)[-1].rsplit(".", 1)[0].upper()
                        if stem == cid.upper():
                            rec["exact_homes"].add(rel)
                elif zone == "source":
                    rec["source_only_files"].add(rel)
                elif zone == "corpus":
                    rec["corpus_files"].add(rel)


def build_concepts(sources: dict) -> tuple[dict, dict]:
    cert_index: dict[str, set] = {}
    concepts: dict[str, dict] = {}

    repo_paths, source_paths, corpus_paths = [], [], []
    for rel in sources["_tracked"]:
        p = REPO / rel
        if p.suffix.lower() not in (TEXT_EXT | {".docx"}):
            continue
        (source_paths if _top(rel) in SOURCE_ROOTS else repo_paths).append((rel, p))
    # The UKDA canonical store is authoritative Repository Truth even though it is git-ignored
    # (generated). Scan it explicitly so seeded UCKO-*/UKDA-DEC-* count as homed.
    for extra in ("knowledge/canonical-knowledge.json", "knowledge/decisions.json"):
        p = REPO / extra
        if p.is_file() and (extra, p) not in repo_paths:
            repo_paths.append((extra, p))
    if (REPO / "knowledge" / "handbooks").is_dir():
        for hb in sorted((REPO / "knowledge" / "handbooks").rglob("*.md")):
            repo_paths.append((str(hb.relative_to(REPO)), hb))
    if sources["corpus_present"]:
        for rel in sources["corpus_files"]:
            corpus_paths.append((rel, CORPUS / rel))

    # First pass over repo to build cert_index, then classify.
    _scan(repo_paths, concepts, cert_index, "repo")
    _scan(source_paths, concepts, cert_index, "source")
    _scan(corpus_paths, concepts, cert_index, "corpus")

    # resolve certification from co-located cert evidence
    for cid, rec in concepts.items():
        if cert_index.get(cid):
            rec["certified"] = True
    return concepts, cert_index


# --------------------------------------------------------------------------- phase 5/6: disposition + traceability
def assign(concepts: dict) -> None:
    for rec in concepts.values():
        homed = rec["homed"]
        # disposition precedence: strongest evidence wins; UNCLASSIFIED only when not homed
        if not homed:
            disp = "UNCLASSIFIED"
        elif rec["in_code"] or rec["certified"]:
            disp = "IMPLEMENTED"
        elif rec["rejected"]:
            disp = "REJECTED"
        elif rec["deferred"]:
            disp = "DEFERRED"
        elif rec["in_constitution"] or rec["in_spec"] or rec["in_filename"] or rec["in_book"]:
            disp = "SPECIFIED"
        elif rec["in_plan"]:
            disp = "PLANNED"
        else:
            disp = "SPECIFIED"
        rec["disposition"] = disp
        # gap location subsets (a not-homed concept is the gap; these say where it currently lives)
        rec["upload_only"] = (not homed) and bool(rec["source_only_files"]) and "repo" not in rec["zones"]
        rec["conversation_only"] = (
            (not homed) and bool(rec["corpus_files"])
            and not rec["source_only_files"] and "repo" not in rec["zones"]
        )
        rec["in_repo_unhomed"] = (not homed) and "repo" in rec["zones"]
        # traceability tiers
        rec["trace"] = {
            "source": bool(rec["source_only_files"]) or bool(rec["corpus_files"]),
            "constitution": rec["in_constitution"],
            "specification": rec["in_spec"] or rec["in_filename"] or rec["in_book"],
            "implementation": rec["in_code"],
            "certification": rec["certified"],
        }
        rec["orphan"] = homed and not (
            rec["trace"]["constitution"] or rec["trace"]["specification"] or rec["trace"]["implementation"]
        )


# --------------------------------------------------------------------------- serialization helpers
def _clean(rec: dict) -> dict:
    out = {k: (sorted(v) if isinstance(v, set) else v) for k, v in rec.items()}
    return out


def build_model(sources: dict, concepts: dict) -> dict:
    recs = [_clean(r) for r in concepts.values()]
    recs.sort(key=lambda r: r["id"])
    disp_counts: dict[str, int] = defaultdict(int)
    fam_counts: dict[str, int] = defaultdict(int)
    for r in recs:
        disp_counts[r["disposition"]] += 1
        fam_counts[r["family"]] += 1
    upload_only = [r for r in recs if r["upload_only"]]
    conversation_only = [r for r in recs if r["conversation_only"]]
    in_repo_unhomed = [r for r in recs if r["in_repo_unhomed"]]
    unclassified = [r for r in recs if r["disposition"] == "UNCLASSIFIED"]
    orphans = [r for r in recs if r["orphan"]]
    # duplicate canonical homes: same id is the EXACT basename of >1 definitional file
    # (series-prefixed distinct artifacts like UCOS-COMP-000000-* are NOT duplicates)
    dup_home = [r for r in recs if len(r["exact_homes"]) > 1]
    # UKDA content-hash duplicates (Repository Truth store)
    hash_dups = _ukda_hash_dups()

    # distinct concept-level gap set (no double counting): every not-homed concept + every orphan
    gap_ids = {r["id"] for r in unclassified} | {r["id"] for r in orphans}
    gaps = {
        "not_homed_concepts": len(unclassified),
        "upload_only": len(upload_only),
        "conversation_only": len(conversation_only),
        "in_repo_unhomed": len(in_repo_unhomed),
        "orphan_concepts": len(orphans),
        "duplicate_canonical_homes": len(dup_home),
        "ukda_content_hash_duplicates": len(hash_dups),
    }
    # blocking invariants (determination): distinct not-homed/orphan concepts + structural duplicates
    blocking = len(gap_ids) + len(dup_home) + len(hash_dups)
    closed = blocking == 0
    return {
        "program": "UAKOS-CLOSURE-002",
        "baseline_commit": _run(["git", "rev-parse", "--short", "HEAD"]).strip(),
        "branch": _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip(),
        "determination": "CLOSED" if closed else "NOT-CLOSED",
        "gap_total": blocking,
        "gaps": gaps,
        "concept_total": len(recs),
        "dispositions": dict(sorted(disp_counts.items())),
        "families": dict(sorted(fam_counts.items())),
        "sources": {
            "tracked_total": sources["tracked_total"],
            "markdown": len(sources["markdown"]),
            "docx_uploads": len(sources["docx_uploads"]),
            "corpus_present": sources["corpus_present"],
            "corpus_files": len(sources["corpus_files"]),
            "tracked_by_top": sources["tracked_by_top"],
        },
        "detail": {
            "upload_only": upload_only,
            "conversation_only": conversation_only,
            "in_repo_unhomed": in_repo_unhomed,
            "unclassified": unclassified,
            "orphans": orphans,
            "duplicate_homes": dup_home,
            "ukda_hash_duplicates": hash_dups,
        },
        "concepts": recs,
    }


def _ukda_hash_dups() -> list[dict]:
    store = REPO / "knowledge" / "canonical-knowledge.json"
    if not store.is_file():
        return []
    data = json.loads(store.read_text("utf-8"))
    seen: dict[str, list[str]] = defaultdict(list)
    for obj in data.get("objects", []):
        h = obj.get("content_sha256")
        if h:
            seen[h].append(obj.get("cko_id", "?"))
    return [{"content_sha256": h, "ids": ids} for h, ids in sorted(seen.items()) if len(ids) > 1]


# --------------------------------------------------------------------------- phase 9/10: emit artifacts
def _fence(rows: list[list[str]], header: list[str]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def _hdr(title: str, m: dict, answers: str) -> str:
    return (
        f"# {title}\n\n"
        f"> PROGRAM UAKOS-CLOSURE-002 · baseline `{m['baseline_commit']}` (branch `{m['branch']}`) · "
        f"AUTHORITY = NONE (DERIVED TRUTH) · generated by `closure_engine.py`\n>\n"
        f"> {answers}\n\n"
    )


def emit(m: dict) -> list[Path]:
    written: list[Path] = []

    def w(name: str, body: str) -> None:
        p = HERE / name
        p.write_text(body.rstrip() + "\n", "utf-8")
        written.append(p)

    s = m["sources"]
    # 01 Source Inventory
    rows = [[k, v] for k, v in s["tracked_by_top"].items()]
    w("01-SOURCE-INVENTORY.md",
      _hdr("01 — Source Inventory", m, "Every discovered knowledge source.") +
      f"- Tracked files: **{s['tracked_total']}** · Markdown: **{s['markdown']}** · "
      f"docx uploads: **{s['docx_uploads']}** · external corpus present: **{s['corpus_present']}** "
      f"(**{s['corpus_files']}** files)\n\n## Tracked files by top-level source\n\n" +
      _fence(rows, ["Source root", "Files"]))

    # 02 Conversation Inventory (external corpus = conversation/upload material)
    conv = m["detail"]["conversation_only"]
    w("02-CONVERSATION-INVENTORY.md",
      _hdr("02 — Conversation Inventory", m, "External corpus / conversation material scanned for concepts.") +
      f"External corpus dir scanned: **{s['corpus_present']}** — **{s['corpus_files']}** files.\n\n"
      f"Concepts appearing **only** in the corpus (conversation-only, not yet in Repository Truth): "
      f"**{len(conv)}**.\n\n" +
      (_fence([[r["id"], r["family"], len(r["corpus_files"])] for r in conv[:200]],
              ["Concept", "Family", "Corpus files"]) if conv else "_None — no conversation-only concepts detected._"))

    # 03 Uploaded Document Inventory
    docx_rows = [[f] for f in _sources_docx(m)]
    w("03-UPLOADED-DOCUMENT-INVENTORY.md",
      _hdr("03 — Uploaded Document Inventory", m, "Every uploaded architectural document (docx) in the repository.") +
      "Uploaded `.docx` sources are tracked and hash-pinned in `00-SOURCE-MANIFEST/SOURCE-HASHES.txt`.\n\n" +
      _fence(docx_rows, ["Uploaded document"]))

    # 04 Constitutional Concept Inventory
    fam_rows = [[k, v] for k, v in m["families"].items()]
    w("04-CONSTITUTIONAL-CONCEPT-INVENTORY.md",
      _hdr("04 — Constitutional Concept Inventory", m, "Every discovered canonical concept anchor, by family.") +
      f"Total distinct concept anchors: **{m['concept_total']}**.\n\n## By family\n\n" +
      _fence(fam_rows, ["Family", "Concepts"]) +
      "\n\n## Full concept ledger\n\n" +
      _fence([[r["id"], r["family"], r["disposition"], "yes" if r["homed"] else "**NO**"]
              for r in m["concepts"]], ["Concept", "Family", "Disposition", "Homed"]))

    # 05 Vision-to-Repository Matrix
    w("05-VISION-TO-REPOSITORY-MATRIX.md",
      _hdr("05 — Vision-to-Repository Traceability Matrix", m,
           "Vision -> Constitution -> Specification -> Implementation -> Certification per concept.") +
      _fence([[r["id"],
               "✓" if r["trace"]["source"] else "·",
               "✓" if r["trace"]["constitution"] else "·",
               "✓" if r["trace"]["specification"] else "·",
               "✓" if r["trace"]["implementation"] else "·",
               "✓" if r["trace"]["certification"] else "·"]
              for r in m["concepts"]],
             ["Concept", "Source", "Constitution", "Spec", "Impl", "Cert"]))

    # 06 Repository Coverage Matrix
    dr = [[k, v] for k, v in m["dispositions"].items()]
    w("06-REPOSITORY-COVERAGE-MATRIX.md",
      _hdr("06 — Repository Coverage Matrix", m, "Disposition coverage across all concepts.") +
      _fence(dr, ["Disposition", "Concepts"]) +
      f"\n\nHomed (canonical home present): **{sum(1 for r in m['concepts'] if r['homed'])}** / "
      f"**{m['concept_total']}**.")

    # 07 Duplicate Knowledge Report
    dh = m["detail"]["duplicate_homes"]
    hd = m["detail"]["ukda_hash_duplicates"]
    w("07-DUPLICATE-KNOWLEDGE-REPORT.md",
      _hdr("07 — Duplicate Knowledge Report", m, "Concepts with more than one canonical home; UKDA content-hash duplicates.") +
      f"Concepts declared in >1 filename-home: **{len(dh)}**.\n\n" +
      (_fence([[r["id"], "; ".join(sorted(r["exact_homes"]))[:180]] for r in dh],
              ["Concept", "Duplicate homes"]) if dh else "_None._") +
      f"\n\nUKDA content-hash duplicates (Repository Truth store): **{len(hd)}**.\n\n" +
      (_fence([[d["content_sha256"][:16], ", ".join(d["ids"])] for d in hd], ["content_sha256", "cko_ids"])
       if hd else "_None — no two canonical objects share a content hash (UCKO-RULE-0001 holds)._"))

    # 08 Missing Knowledge Report
    uo = m["detail"]["upload_only"]
    co = m["detail"]["conversation_only"]
    uc = m["detail"]["unclassified"]
    iru = m["detail"]["in_repo_unhomed"]
    w("08-MISSING-KNOWLEDGE-REPORT.md",
      _hdr("08 — Missing Knowledge Report", m, "Concepts not present in Repository Truth (gaps).") +
      f"- Not-homed concepts (no canonical home = no disposition): **{len(uc)}**\n"
      f"  - of which upload-only (`00-SOURCE`/uploads only): **{len(uo)}**\n"
      f"  - of which conversation-only (external corpus only): **{len(co)}**\n"
      f"  - of which in-repo but unhomed (mentioned, never defined): **{len(iru)}**\n\n"
      "## Upload-only\n\n" +
      (_fence([[r["id"], r["family"], "; ".join(sorted(r["source_only_files"]))[:160]] for r in uo[:300]],
              ["Concept", "Family", "Source files"]) if uo else "_None._") +
      "\n\n## In-repo but unhomed (closure violations — must reach zero)\n\n" +
      (_fence([[r["id"], r["family"], ", ".join(sorted(r["tops"]))[:120]] for r in iru[:300]],
              ["Concept", "Family", "Seen in"]) if iru else "_None._"))

    # 09 Repository Enrichment Plan
    w("09-REPOSITORY-ENRICHMENT-PLAN.md",
      _hdr("09 — Repository Enrichment Plan", m, "How every gap becomes Repository Truth.") +
      _enrichment_plan(m))

    # 10 Constitutional Gap Register
    w("10-CONSTITUTIONAL-GAP-REGISTER.md",
      _hdr("10 — Constitutional Gap Register", m, "One row per open gap; the closure backlog.") +
      _gap_register(m))

    # 11 Closure Evidence
    w("11-CLOSURE-EVIDENCE.md",
      _hdr("11 — Closure Evidence", m, "The evidence basis of the determination.") +
      f"- Baseline commit: `{m['baseline_commit']}` (branch `{m['branch']}`)\n"
      f"- Concepts analyzed: **{m['concept_total']}**\n"
      f"- Sources: {s['tracked_total']} tracked, {s['docx_uploads']} docx uploads, "
      f"{s['corpus_files']} corpus files\n"
      f"- Machine model: `closure.json` (deterministic; re-run `make closure` to reproduce)\n"
      f"- Gap totals: {json.dumps(m['gaps'], sort_keys=True)}\n\n"
      "This program is fail-closed: the determination below reflects only evidence physically present "
      "at the baseline commit. No speculative closure is asserted (TRACK-001).")

    # 12 Repository Closure Certificate
    w("12-REPOSITORY-CLOSURE-CERTIFICATE.md", _certificate(m, "Repository"))
    # 13 Vision Closure Certificate
    w("13-VISION-CLOSURE-CERTIFICATE.md", _certificate(m, "Vision"))

    # 14 Final Repository Completeness Report
    w("14-FINAL-REPOSITORY-COMPLETENESS-REPORT.md",
      _hdr("14 — Final Repository Completeness Report", m, "The single-page verdict.") +
      _final_report(m))
    return written


def _sources_docx(m: dict) -> list[str]:
    # -z: see _tracked_paths — quoted octal paths do not resolve on disk.
    return [f for f in _run(["git", "ls-files", "-z", "*.docx"]).split("\0") if f]


def _enrichment_plan(m: dict) -> str:
    g = m["gaps"]
    lines = ["Every open gap is routed to exactly one constitutional destination:\n"]
    lines.append(_fence([
        ["Not-homed concepts", g["not_homed_concepts"], "Assign a canonical home + disposition (no sixth state permitted)"],
        ["  · upload-only", g["upload_only"], "Canonicalize into 02-MASTER / band spec / UKDA store; then SPECIFIED or PLANNED"],
        ["  · conversation-only", g["conversation_only"], "Extract from corpus into a decision record / spec; then classify"],
        ["  · in-repo unhomed", g["in_repo_unhomed"], "Promote the mention into a definitional home (filename/registry/catalog)"],
        ["Orphan concepts", g["orphan_concepts"], "Attach traceability (constitution/spec/impl) or archive with rationale"],
        ["Duplicate canonical homes", g["duplicate_canonical_homes"], "Merge to one home; convert others to links (UCKO-PRIN-0001)"],
        ["UKDA hash duplicates", g["ukda_content_hash_duplicates"], "Remove duplicate object; keep one canonical record"],
    ], ["Gap class", "Count", "Constitutional destination"]))
    lines.append("\nPriority: in-repo-unhomed -> upload-only -> conversation-only -> orphan -> duplicates.")
    return "\n".join(lines)


def _gap_register(m: dict) -> str:
    rows = []
    for r in m["detail"]["in_repo_unhomed"]:
        rows.append([r["id"], "IN-REPO-UNHOMED", "promote mention to a definitional home"])
    for r in m["detail"]["upload_only"]:
        rows.append([r["id"], "UPLOAD-ONLY", "canonicalize into Repository Truth"])
    for r in m["detail"]["conversation_only"]:
        rows.append([r["id"], "CONVERSATION-ONLY", "extract from corpus into a spec/decision"])
    for r in m["detail"]["orphans"]:
        rows.append([r["id"], "ORPHAN", "attach traceability or archive"])
    for r in m["detail"]["duplicate_homes"]:
        rows.append([r["id"], "DUPLICATE-HOME", "merge to one canonical home"])
    if not rows:
        return "_Gap register empty — zero open constitutional gaps at this baseline._"
    rows.sort(key=lambda x: (x[1], x[0]))
    return (f"Open gaps: **{len(rows)}**.\n\n" +
            _fence([[i + 1, *row] for i, row in enumerate(rows[:800])],
                   ["#", "Concept", "Gap class", "Required action"]))


def _certificate(m: dict, kind: str) -> str:
    ok = m["determination"] == "CLOSED"
    verdict = "CLOSED — 100%" if ok else f"NOT-CLOSED — {m['gap_total']} open gap(s)"
    seal = hashlib.sha256(
        json.dumps({"kind": kind, "commit": m["baseline_commit"], "gaps": m["gaps"]},
                   sort_keys=True).encode()).hexdigest()
    body = [
        f"# {kind} Closure Certificate — UAKOS-CLOSURE-002\n",
        f"| Field | Value |", "|---|---|",
        f"| Program | UAKOS-CLOSURE-002 |",
        f"| Certificate | {kind} Closure |",
        f"| Baseline | `{m['baseline_commit']}` (branch `{m['branch']}`) |",
        f"| Determination | **{verdict}** |",
        f"| Concepts | {m['concept_total']} |",
        f"| Seal (sha256) | `{seal}` |",
        f"| Authority | NONE — DERIVED TRUTH (fail-closed, TRACK-001) |",
        "",
    ]
    if ok:
        body.append("All closure invariants hold: zero missing, zero duplicate, zero orphan, "
                     "zero unclassified, zero broken traceability, zero drift. "
                     f"{kind} closure is **CERTIFIED**.")
    else:
        body.append(f"**Certification withheld.** Under the repository's fail-closed law, {kind.lower()} "
                    "closure cannot be certified while open gaps exist. Current gaps:\n")
        body.append("```json\n" + json.dumps(m["gaps"], indent=2, sort_keys=True) + "\n```")
        body.append("\nSee `10-CONSTITUTIONAL-GAP-REGISTER.md` and `09-REPOSITORY-ENRICHMENT-PLAN.md`. "
                    "Re-run `make closure` after enrichment; this certificate self-certifies when gaps reach zero.")
    return "\n".join(body)


def _final_report(m: dict) -> str:
    return (
        f"**Determination: {m['determination']}** — gaps: **{m['gap_total']}**.\n\n"
        + _fence([[k, v] for k, v in m["gaps"].items()], ["Invariant (must be 0)", "Count"])
        + "\n\n## Dispositions\n\n"
        + _fence([[k, v] for k, v in m["dispositions"].items()], ["Disposition", "Concepts"])
        + f"\n\n## Success criteria\n\n"
        + _fence([
            ["Every concept has one canonical home", "PASS" if m["gaps"]["not_homed_concepts"] == 0 else "FAIL"],
            ["Every concept has one disposition", "PASS" if m["gaps"]["not_homed_concepts"] == 0 else "FAIL"],
            ["Zero conversation-only knowledge", "PASS" if m["gaps"]["conversation_only"] == 0 else "FAIL"],
            ["Zero upload-only knowledge", "PASS" if m["gaps"]["upload_only"] == 0 else "FAIL"],
            ["Zero in-repo unhomed knowledge", "PASS" if m["gaps"]["in_repo_unhomed"] == 0 else "FAIL"],
            ["Zero duplicate canonical knowledge", "PASS" if m["gaps"]["duplicate_canonical_homes"] == 0
             and m["gaps"]["ukda_content_hash_duplicates"] == 0 else "FAIL"],
            ["Zero orphan concepts", "PASS" if m["gaps"]["orphan_concepts"] == 0 else "FAIL"],
        ], ["Criterion", "Status"])
        + f"\n\n{'100% Vision-to-Repository Closure achieved.' if m['determination'] == 'CLOSED' else 'Closure not yet achieved — see gap register.'}"
    )


# --------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    gate = "--gate" in argv
    sources = discover_sources()
    concepts, _cert = build_concepts(sources)
    assign(concepts)
    model = build_model(sources, concepts)
    (HERE / "closure.json").write_text(
        json.dumps({k: v for k, v in model.items() if k != "concepts"} | {"concepts": model["concepts"]},
                   indent=2, sort_keys=True, ensure_ascii=False) + "\n", "utf-8")
    written = emit(model)
    print(f"UAKOS-CLOSURE-002: {model['determination']} | concepts={model['concept_total']} "
          f"| gaps={model['gap_total']} {json.dumps(model['gaps'], sort_keys=True)}")
    print(f"wrote {len(written) + 1} artifacts to {HERE}")
    if gate and model["determination"] != "CLOSED":
        print("GATE FAILED: repository closure NOT achieved (fail-closed).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
