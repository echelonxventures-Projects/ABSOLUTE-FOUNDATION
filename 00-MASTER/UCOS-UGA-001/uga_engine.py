#!/usr/bin/env python3
"""UCOS-UGA-001 — Universal Governance Assimilation Engine.

Brings every version-controlled object that is NOT a corpus document under the
SAME constitutional control the corpus already has: identity, ownership,
lifecycle, dependency closure, evidence boundary, audit history, validation.

WHY THIS EXISTS
---------------
`00-BOOK/tools/config.py::INCLUDE_EXTENSIONS` is (.md, .txt, .docx, .json). The
registration boundary is document-only, so at the time of authoring 1936
version-controlled executable and configuration objects — including all 29
producers named by the generated-artifact registry — had no universal identity,
no owner and no lifecycle. The corpus governed its artifacts by naming engines
that were themselves anonymous.

The identity authority, audit universe, evidence universe and relationship graph
already existed and already worked. What was missing was a TERM for a thing that
executes rather than a thing that is read. This engine adds the object class, not
a parallel government.

ONE IDENTITY AUTHORITY
----------------------
Identities are minted from `00-BOOK/DATA/id-ledger.json` using the SAME
`category_seq` counter as the corpus, into an append-only `by_object` map. This
is the construction EXEC-REG-001 already established for `by_execution`. No page
range is consumed: pages are a BOOK concept, so `page_cursor` is never touched
and the corpus page layout is bit-for-bit unaffected. `ukb.py cmd_build` iterates
the document eligibility universe (never the ledger), and `load_ledger` preserves
unknown keys, so `by_object` is invisible to the corpus transaction by
construction rather than by convention.

DETERMINISM
-----------
No output contains a wall clock. Every timestamp emitted is a `first_seen` frozen
in the append-only ledger at mint time. A second run with no repository change is
a no-op on disk, which is what makes Phase-8 fixed point and Phase-9 pristine
clone checkable by plain byte comparison.

USAGE
    uga_engine.py run     mint identities and emit all surfaces
    uga_engine.py gate    verify invariants; mutate nothing; exit 1 on violation
    uga_engine.py stats   print the current measured state
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

DECLARATION = os.path.join(HERE, "uga-declaration.json")
LEDGER_PATH = os.path.join(REPO, "00-BOOK", "DATA", "id-ledger.json")
ARTIFACTS_PATH = os.path.join(REPO, "00-BOOK", "DATA", "artifacts.json")
GENREG_PATH = os.path.join(REPO, "00-BOOK", "DATA", "generated-artifact-registry.json")
EVIDENCE_PATH = os.path.join(REPO, "00-BOOK", "DATA", "evidence-universe.json")

OUT = {
    "inventory":    os.path.join(HERE, "00-EXISTENCE-INVENTORY.json"),
    "executables":  os.path.join(HERE, "01-EXECUTABLE-OBJECT-REGISTRY.json"),
    "universal":    os.path.join(HERE, "02-UNIVERSAL-OBJECT-REGISTRY.json"),
    "audit":        os.path.join(HERE, "03-AUDIT-UNIVERSE.json"),
    "graph":        os.path.join(HERE, "04-RELATIONSHIP-GRAPH.json"),
    "invariants":   os.path.join(HERE, "05-GOVERNANCE-INVARIANTS.json"),
    "observation":  os.path.join(HERE, "06-SELF-OBSERVATION.json"),
    "certification": os.path.join(HERE, "07-CERTIFICATION.json"),
    "dashboard":    os.path.join(HERE, "00-UGA-DASHBOARD.md"),
}

# Trees whose Python packages participate in intra-repository import resolution.
CODE_ROOTS = ("engine", "platform", "service", "data", "application",
              "infrastructure", "intelligence", "realization", "scripts")

CONFIG_EXT = (".yml", ".yaml", ".toml", ".cfg", ".ini", ".gitignore")
EXEC_EXT = (".py", ".sh")


# ---------------------------------------------------------------------------
# io helpers
# ---------------------------------------------------------------------------
def _load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        if default is None:
            raise
        return default


def _dump(path, obj):
    """Write pretty deterministic JSON. Returns True when the bytes changed."""
    text = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    return _write_text(path, text)


def _write_text(path, text):
    try:
        with open(path, encoding="utf-8") as fh:
            if fh.read() == text:
                return False
    except FileNotFoundError:
        pass
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return True


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_file(abspath: str) -> str | None:
    try:
        with open(abspath, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def _digest_of(obj) -> str:
    """Stable content digest of a JSON-able structure."""
    return _sha256_bytes(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode())


def _git_ls():
    """The repository artifact boundary, as version control declares it.

    `-z` is mandatory, not stylistic: without it git QUOTES any path containing a
    non-ASCII byte, and 116 paths in this repository carry Ω/∞ in their names. The
    quoted form is a different string, so those objects would be minted identities
    under a name no lookup could ever match — an anonymous object wearing a
    plausible label, which is the exact failure this programme exists to forbid.
    """
    out = subprocess.run(  # noqa: S603 — fixed argv, no shell, no user input
        ["git", "-C", REPO, "ls-files", "-z", "--cached",  # noqa: S607 — resolved from PATH, as CI does
         "--exclude-standard"],
        capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise SystemExit("UGA: not a git work tree — the repository artifact boundary "
                         "is undefined. Refusing to guess (fails closed).")
    return sorted(p for p in out.stdout.split("\0") if p)


# ---------------------------------------------------------------------------
# EPOCH 0 — Existence Discovery
# ---------------------------------------------------------------------------
def classify_object(rel: str, registered_docs: set, generated_paths: set) -> tuple[str, str]:
    """(object_class, lifecycle) — TOTAL over the version-controlled boundary.

    Every branch returns; the final branch is unconditional. 'UNKNOWN' is therefore
    structurally unreachable, which is what makes the Epoch-0 success condition
    (unknown_objects == 0) a property of the classifier rather than a lucky
    measurement of today's file set.
    """
    lifecycle = "GENERATED" if rel in generated_paths else "AUTHORED"

    if rel in registered_docs:
        return "DOCUMENT_ARTIFACT", lifecycle
    if rel.startswith(("00-BOOK/tools/", "00-BOOK/DATA/")):
        return "TOOLING_OBJECT", lifecycle
    if rel.endswith(".py") or rel.endswith(".sh"):
        base = os.path.basename(rel)
        is_test = ("/tests/" in f"/{rel}" or rel.startswith("tests/")
                   or base.startswith("test_") or base.endswith("_test.py"))
        return ("TEST_OBJECT" if is_test else "EXECUTABLE_OBJECT"), lifecycle
    if rel.endswith(CONFIG_EXT):
        return "CONFIGURATION_OBJECT", lifecycle
    if rel.endswith(".json"):
        return "DATA_OBJECT", lifecycle
    # Unconditional terminal branch: a readable document that the corpus registry
    # does NOT carry — Operational Memory under 00-MASTER/ and the generated
    # projections under 00-BOOK/CONTROL-TOWER, REGISTRIES, VOLUMES and PORTAL.
    # Excluded from CORPUS REGISTRATION by declared authority, which is a statement
    # about which register lists them — never a licence to exist anonymously.
    return "EXCLUDED_DOCUMENT", lifecycle


def derive_owner(rel: str) -> str:
    """TOTAL ownership function. The last rule is unconditional."""
    parts = rel.split("/")
    if rel.startswith("00-BOOK/tools/") or rel.startswith("00-BOOK/DATA/"):
        return "UCOS-UKB-TOOLING"
    if parts[0] == "00-MASTER" and len(parts) > 2:
        return parts[1]
    if len(parts) > 2:
        return f"{parts[0]}/{parts[1]}"
    if len(parts) == 2:
        return parts[0]
    return "UCOS-REPOSITORY-ROOT"


def epoch0_discovery(paths, registered_docs, generated_paths):
    objects = []
    for rel in paths:
        klass, lifecycle = classify_object(rel, registered_docs, generated_paths)
        objects.append({
            "path": rel,
            "object_class": klass,
            "lifecycle": lifecycle,
            "owner": derive_owner(rel),
        })
    return objects


# ---------------------------------------------------------------------------
# EPOCH 1 — Universal Identity Authority (shared ledger, append-only)
# ---------------------------------------------------------------------------
ID_CATEGORY = {
    "EXECUTABLE_OBJECT": "ENGINE",
    "TEST_OBJECT": "TESTOBJ",
    "CONFIGURATION_OBJECT": "CONFIG",
    "TOOLING_OBJECT": "TOOLING",
    "DATA_OBJECT": "DATAOBJ",
    "EXCLUDED_DOCUMENT": "EXDOC",
}


def epoch1_identity(objects, ledger, mint: bool, now: str):
    """Mint a universal identity for every object of a governed class.

    Shares the corpus `category_seq` counter. Consumes NO page range. Append-only:
    an existing entry is returned untouched, so an identity is permanent and is
    never reissued to a different path.
    """
    by_object = ledger.setdefault("by_object", {})
    seq = ledger.setdefault("category_seq", {})
    doc_ids = ledger.get("by_path", {})

    minted, anonymous = [], []
    for o in objects:
        rel = o["path"]
        if o["object_class"] == "DOCUMENT_ARTIFACT":
            # Governed by UMB-IMP-001. Read its identity; never mint one here.
            entry = doc_ids.get(rel)
            o["universal_id"] = entry["universal_id"] if entry else None
            o["identity_authority"] = "UMB-IMP-001"
            if not o["universal_id"]:
                anonymous.append(rel)
            continue

        o["identity_authority"] = "UCOS-UGA-001"
        existing = by_object.get(rel)
        if existing:
            o["universal_id"] = existing["universal_id"]
            o["first_seen"] = existing["first_seen"]
            continue
        if not mint:
            o["universal_id"] = None
            anonymous.append(rel)
            continue
        cat = ID_CATEGORY[o["object_class"]]
        n = seq.get(cat, 0) + 1
        seq[cat] = n
        uid = f"UCOS-{cat}-{n:06d}"
        by_object[rel] = {
            "universal_id": uid,
            "object_class": o["object_class"],
            "category": cat,
            "first_seen": now,
        }
        o["universal_id"] = uid
        o["first_seen"] = now
        minted.append(rel)

    # RETIRED: minted previously, no longer carried by version control. Identity is
    # retained and never reissued (append-only).
    live = {o["path"] for o in objects}
    retired = sorted(p for p in by_object if p not in live)
    return minted, anonymous, retired


# ---------------------------------------------------------------------------
# EPOCH 4 (computed early — the registry embeds dependencies)
# ---------------------------------------------------------------------------
def _module_name(rel: str) -> str | None:
    if not rel.endswith(".py"):
        return None
    mod = rel[:-3].replace("/", ".")
    if mod.endswith(".__init__"):
        mod = mod[: -len(".__init__")]
    return mod


def build_import_index(paths):
    index = {}
    for rel in paths:
        mod = _module_name(rel)
        if mod and rel.split("/")[0] in CODE_ROOTS:
            index[mod] = rel
    return index


def python_imports(abspath: str, rel: str, index: dict, tracked: set) -> list[str]:
    """Intra-repository import edges, resolved to real paths.

    Only edges that RESOLVE to a version-controlled module are emitted. Stdlib and
    third-party imports are outside the repository boundary and are not repository
    dependencies.

    Two resolution modes, because this repository uses both. Package-qualified
    imports (`from engine.knowledge import seed`) resolve through the module index.
    SCRIPT-STYLE SIBLING imports (`import config as C`, how 00-BOOK/tools and the
    00-MASTER engines are written) resolve against the importing file's own
    directory — without this, the governance tooling's own dependency edges are
    invisible, and a dependency nobody can see is the hidden dependency Epoch 4
    exists to eliminate.
    """
    try:
        with open(abspath, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=rel)
    except (OSError, SyntaxError, ValueError):
        return []

    pkg = (_module_name(rel) or "").rsplit(".", 1)[0]
    here = os.path.dirname(rel)
    found = set()

    def resolve(mod: str):
        if not mod:
            return
        if mod in index:
            found.add(index[mod])
            return
        # `from pkg.mod import name` where name is itself a module
        parent = mod.rsplit(".", 1)[0]
        if parent in index:
            found.add(index[parent])
            return
        # script-style sibling module in the importing file's own directory
        top = mod.split(".")[0]
        for cand in (f"{top}.py", os.path.join(top, "__init__.py")):
            sib = os.path.join(here, cand) if here else cand
            sib = os.path.normpath(sib)
            if sib in tracked and sib != rel:
                found.add(sib)
                return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                resolve(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:                      # relative import
                base = pkg.split(".")
                up = node.level - 1
                base = base[: len(base) - up] if up else base
                target = ".".join([*base, node.module] if node.module else base)
            else:
                target = node.module or ""
            resolve(target)
            if node.module or node.level:
                for a in node.names:
                    resolve(f"{target}.{a.name}")
    return sorted(found)


# ---------------------------------------------------------------------------
# EPOCH 2/3 — Universal Object Registry + evidence boundary
# ---------------------------------------------------------------------------
EVIDENCE_FOR_CLASS = {
    # Which evidence class a governance record about this object belongs to.
    # Closed set from UCOS-EVIDENCE-UNIVERSE-001; no sixth class is created.
    "EXECUTABLE_OBJECT": "VALIDATION",
    "TEST_OBJECT": "VALIDATION",
    "CONFIGURATION_OBJECT": "VALIDATION",
    "TOOLING_OBJECT": "VALIDATION",
    "DATA_OBJECT": "VALIDATION",
    "DOCUMENT_ARTIFACT": "VALIDATION",
    "EXCLUDED_DOCUMENT": "VALIDATION",
}


def epoch2_registry(objects, index, producer_of, consumers_of, decl, tracked):
    # This engine's OWN emitted surfaces. Once they are version-controlled they are
    # objects like any other and MUST hold identity — but their content_hash is
    # deliberately null, because a file cannot contain its own hash: recording it
    # would change the bytes, which changes the hash, a self-reference with no
    # fixpoint. The repository already met this exact relation with the UCOS-RIE-001
    # outputs and resolved it by removing them from registration; identity is kept
    # here and only the unsatisfiable field is withheld, which is the narrower cut.
    own_surfaces = {os.path.relpath(p, REPO) for p in OUT.values()}

    entries = []
    for o in objects:
        rel = o["path"]
        abspath = os.path.join(REPO, rel)
        deps = []
        if rel.endswith(".py"):
            deps = python_imports(abspath, rel, index, tracked)

        governed = o["object_class"] != "DOCUMENT_ARTIFACT"
        entries.append({
            "universal_id": o["universal_id"],
            "path": rel,
            "object_class": o["object_class"],
            "owner": o["owner"],
            "producer": producer_of.get(rel, "HUMAN_AUTHORED"),
            "identity_authority": o["identity_authority"],
            "lifecycle": o["lifecycle"],
            "dependencies": deps,
            "produces": sorted(consumers_of.get(rel, [])),
            "evidence_class": EVIDENCE_FOR_CLASS[o["object_class"]],
            "evidence_boundary": "NON_CANONICAL",
            "validation_contract": (
                "UCOS-UGA-001 §UGA-INV-01..10" if governed else "UMB-IMP-001 ENFORCEMENT_GATES"),
            "certification_status": "GOVERNED",
            "content_hash": None if rel in own_surfaces else _sha256_file(abspath),
            "content_hash_withheld": (
                "SELF_REFERENTIAL — this engine emits this surface; a file cannot "
                "contain its own hash." if rel in own_surfaces else None),
            "first_seen": o.get("first_seen"),
        })
    entries.sort(key=lambda e: e["path"])
    return entries


# ---------------------------------------------------------------------------
# EPOCH 5 — executable governance invariants
# ---------------------------------------------------------------------------
def epoch5_invariants(entries, objects, genreg, evidence, decl, audit_events, retired):
    """Evaluate all ten invariants. Every one is a real measurement over real state
    and every one fails closed: an unmeasurable input is a violation, never a pass.
    """
    inv = []

    def add(iid, name, violations, measured, note=""):
        inv.append({
            "id": iid,
            "name": name,
            "result": "PASS" if not violations else "FAIL",
            "measured": measured,
            "violation_count": len(violations),
            "violations": sorted(violations)[:25],
            "violations_truncated": max(0, len(violations) - 25),
            "note": note,
        })

    # 01 — every object has a universal id
    v = [e["path"] for e in entries if not e["universal_id"]]
    add("UGA-INV-01", "EVERY_OBJECT_HAS_UNIVERSAL_ID", v, len(entries))

    # 02 — every object has an owner
    v = [e["path"] for e in entries if not e["owner"]]
    add("UGA-INV-02", "EVERY_OBJECT_HAS_OWNER", v, len(entries))

    # 03 — every object registered (registry covers the whole boundary)
    reg_paths = {e["path"] for e in entries}
    v = [o["path"] for o in objects if o["path"] not in reg_paths]
    add("UGA-INV-03", "EVERY_OBJECT_REGISTERED", v, len(objects))

    # 04 — every canonical generated artifact declares an input closure
    gen = genreg["entries"]
    v = [e["canonical_path"] for e in gen
         if e.get("canonical_identity_role") == "CANONICAL" and not e.get("input_closure")]
    add("UGA-INV-04", "EVERY_CANONICAL_ARTIFACT_HAS_INPUT_CLOSURE", v, len(gen))

    # 05 — every generated input names a producer, and that producer now has identity
    by_path = {e["path"]: e for e in entries}
    gen_inputs = genreg.get("generated_inputs", [])
    v = []
    for gi in gen_inputs:
        p = gi.get("producer")
        if not p:
            v.append(f"{gi.get('path')}: no producer declared")
        elif p not in by_path or not by_path[p]["universal_id"]:
            v.append(f"{gi.get('path')}: producer {p} has no universal identity")
    add("UGA-INV-05", "EVERY_GENERATED_INPUT_HAS_PRODUCER", v, len(gen_inputs),
        "Strengthened by this programme: a producer must now be an IDENTIFIED OBJECT, "
        "not merely a declared path string. Before assimilation all 29 declared "
        "producers were anonymous.")

    # 06 — every generated input has a bootstrap path a pristine clone can actually run.
    # Verified against the CONTENTS of the bootstrap script, not against a self-report:
    # a registry field claiming a bootstrap exists is exactly the assertion under test.
    boot_src = ""
    for cand in ("scripts/generate-prerequisites.sh",):
        try:
            with open(os.path.join(REPO, cand), encoding="utf-8") as fh:
                boot_src += fh.read()
        except OSError:
            pass
    v = []
    for gi in gen_inputs:
        path, prod = gi.get("path"), gi.get("producer") or ""
        if gi.get("tracked") is True:
            continue          # committed with the corpus; a clone already has the bytes
        module = prod[:-3].replace("/", ".") if prod.endswith(".py") else ""
        package = module.rsplit(".", 1)[0] if "." in module else ""
        invoked = bool(prod and prod in boot_src)
        if not invoked and package:
            invoked = f"-m {package}" in boot_src
        if not invoked:
            v.append(f"{path}: producer {prod or '(none)'} is not invoked by "
                     f"scripts/generate-prerequisites.sh")
    add("UGA-INV-06", "EVERY_GENERATED_INPUT_HAS_BOOTSTRAP_PATH", v, len(gen_inputs),
        "Pre-existing DECLARED-OPEN condition, recorded by the generated-artifact "
        "registry itself in `bootstrap_gaps`. Not introduced by this programme. "
        "Measured by reading the bootstrap script rather than trusting the registry's "
        "own claim — which also showed the registry's gap note to be STALE: "
        "provenance_engine.py IS invoked, so realization/ is the only true gap.")

    # 07 — every certification surface has a declared evidence boundary
    declared = {s["path"]: s for s in decl["evidence_binding"]["surfaces"]}
    emitted = [p for k, p in OUT.items()]
    v = [os.path.relpath(p, REPO) for p in emitted
         if os.path.relpath(p, REPO) not in declared]
    add("UGA-INV-07", "EVERY_CERTIFICATION_HAS_EVIDENCE_BOUNDARY", v, len(emitted))

    # 08 — no canonical artifact depends on an unclassified observation
    allowed = set(genreg["input_classifications"])
    v = []
    for e in gen:
        if e.get("canonical_identity_role") != "CANONICAL":
            continue
        cls = e.get("input_classification", {})
        for dep in e.get("input_closure", []):
            c = cls.get(dep)
            if c is None or c == "UNKNOWN" or c not in allowed:
                v.append(f"{e['canonical_path']} <- {dep} ({c})")
    add("UGA-INV-08", "NO_CANONICAL_ARTIFACT_DEPENDS_ON_UNCLASSIFIED_OBSERVATION", v, len(gen))

    # 09 — no STRUCTURAL dependence on a finite instance
    fi = decl["finite_instance_tokens"]
    tokens = [t.lower() for t in fi["tokens"]]
    structural = []
    structural += list(decl["object_classes"])
    structural += [r["pattern"] for r in decl["ownership_rules"]]
    structural += [r["owner"] for r in decl["ownership_rules"]]
    structural += list(decl["lifecycle_states"])
    structural += [i["name"] for i in decl["invariants"]]
    structural += list(ID_CATEGORY.values())
    structural += sorted({e["object_class"] for e in entries})
    v = [f"{s}: contains '{t}'" for s in structural for t in tokens if t in s.lower()]
    add("UGA-INV-09", "NO_ARCHITECTURE_DEPENDS_ON_FINITE_INSTANCE", v, len(structural),
        fi["why_scoped"])

    # 10 — every mutation has an audit event
    mutated = {e["path"] for e in entries if e["identity_authority"] == "UCOS-UGA-001"}
    audited = {ev["object_path"] for ev in audit_events}
    v = sorted(mutated - audited)
    add("UGA-INV-10", "EVERY_MUTATION_HAS_AUDIT_EVENT", v, len(mutated))

    return inv


# ---------------------------------------------------------------------------
# EPOCHS 6-9 — self observation, analysis, planning, evolution
# ---------------------------------------------------------------------------
def epochs6_9(entries, invariants, objects, retired):
    import collections
    by_class = collections.Counter(e["object_class"] for e in entries)
    by_owner = collections.Counter(e["owner"] for e in entries)
    by_life = collections.Counter(e["lifecycle"] for e in entries)

    observation = {
        "total_objects": len(entries),
        "by_object_class": dict(sorted(by_class.items())),
        "by_lifecycle": dict(sorted(by_life.items())),
        "distinct_owners": len(by_owner),
        "top_owners": [{"owner": o, "objects": n} for o, n in by_owner.most_common(10)],
        "objects_with_dependencies": sum(1 for e in entries if e["dependencies"]),
        "dependency_edges": sum(len(e["dependencies"]) for e in entries),
        "producers_bound_to_outputs": sum(1 for e in entries if e["produces"]),
        "retired_identities": len(retired),
    }

    # Analysis — a deviation is a failing invariant. Each is classified by whether
    # this programme introduced it or merely made a pre-existing condition visible.
    deviations = []
    for i in invariants:
        if i["result"] == "PASS":
            continue
        pre_existing = i["id"] in ("UGA-INV-06",)
        deviations.append({
            "invariant": i["id"],
            "name": i["name"],
            "violation_count": i["violation_count"],
            "origin": "PRE_EXISTING_DECLARED" if pre_existing else "INTRODUCED_OR_LATENT",
            "severity": "BLOCKING" if not pre_existing else "DECLARED_OPEN",
        })

    # Planning — every deviation gets a remediation with an owner and an evidence path.
    plans = []
    for d in deviations:
        plans.append({
            "invariant": d["invariant"],
            "action": {
                "UGA-INV-01": "Run `uga_engine.py run` to mint identities for unminted "
                              "objects.",
                "UGA-INV-02": "Extend ownership_rules in uga-declaration.json; the rule "
                              "set must stay total.",
                "UGA-INV-03": "Re-run the engine; the registry is derived from the same "
                              "boundary it checks.",
                "UGA-INV-04": "Author the missing input_closure in the generated-artifact "
                              "registry.",
                "UGA-INV-05": "Declare the producer, then re-run so it is minted an "
                              "identity.",
                "UGA-INV-06": "Add the missing producer invocation to "
                              "scripts/generate-prerequisites.sh so a pristine clone can "
                              "obtain the input.",
                "UGA-INV-07": "Declare the new surface in uga-declaration.json "
                              "evidence_binding.",
                "UGA-INV-08": "Classify the input in the generated-artifact registry "
                              "input_classification map.",
                "UGA-INV-09": "Remove the finite instance from the structural term; "
                              "express it as a context value.",
                "UGA-INV-10": "Re-run the engine; audit events are derived from ledger "
                              "first_seen.",
            }.get(d["invariant"], "Investigate."),
            "owner": "UCOS-UGA-001",
            "evidence": os.path.relpath(OUT["invariants"], REPO),
        })

    # Evolution — controlled only. The engine proposes; it never self-approves.
    evolution = {
        "model": ["Observation", "Analysis", "Proposal", "Impact Assessment", "Approval",
                  "Implementation", "Verification", "Certification", "Knowledge Update"],
        "stage_reached": "Proposal",
        "rule": "This engine emits proposals as evidence (IMPROVEMENT class). It holds no "
                "approval authority and mutates no object outside its own surfaces and the "
                "append-only identity ledger. Uncontrolled evolution is structurally "
                "impossible because the engine has no write path to any other object.",
        "approval_authority": "HUMAN_AUTHORED_DECISION",
        "proposals": plans,
    }
    return observation, deviations, plans, evolution


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def build(mint: bool):
    decl = _load(DECLARATION)
    ledger = _load(LEDGER_PATH)
    genreg = _load(GENREG_PATH)
    evidence = _load(EVIDENCE_PATH)
    artifacts = _load(ARTIFACTS_PATH, {"artifacts": []})

    registered_docs = {a["path"] for a in artifacts.get("artifacts", [])}
    generated_paths = {e["canonical_path"] for e in genreg["entries"]}
    producer_of = {e["canonical_path"]: e.get("producer") or "UNDECLARED"
                   for e in genreg["entries"]}
    consumers_of = {}
    for e in genreg["entries"]:
        p = e.get("producer")
        if p:
            consumers_of.setdefault(p, []).append(e["canonical_path"])
    # generated_inputs are produced outputs too — they are the inputs OTHER artifacts
    # consume. Binding only `entries` left the producers of the bootstrap inputs
    # (engine/knowledge/seed.py -> knowledge/, and eight more) recorded as producing
    # nothing, which is the reverse of the truth.
    for gi in genreg.get("generated_inputs", []):
        p, path = gi.get("producer"), gi.get("path")
        if p and path:
            consumers_of.setdefault(p, []).append(path)

    paths = _git_ls()

    # A deterministic mint stamp: derived from the boundary itself, never the clock.
    # Two clones of the same commit mint the same first_seen, so the ledger is a
    # function of the commit rather than of when the engine happened to run.
    head = subprocess.run(  # noqa: S603 — fixed argv, no shell, no user input
        ["git", "-C", REPO, "rev-parse", "HEAD"],  # noqa: S607 — resolved from PATH, as CI does
        capture_output=True, text=True, check=False).stdout.strip()
    now = f"commit:{head[:12]}" if head else "commit:unknown"

    objects = epoch0_discovery(paths, registered_docs, generated_paths)
    unknown = [o["path"] for o in objects if o["object_class"] == "UNKNOWN"]
    minted, anonymous, retired = epoch1_identity(objects, ledger, mint, now)

    index = build_import_index(paths)
    entries = epoch2_registry(objects, index, producer_of, consumers_of, decl, set(paths))

    # EPOCH 3 — audit universe. Derived from the append-only ledger, so it is
    # deterministic: the event time is the frozen first_seen, not the current clock.
    by_object = ledger.get("by_object", {})
    audit_events = []
    for rel in sorted(by_object):
        rec = by_object[rel]
        audit_events.append({
            "event_id": f"UGA-AUD-{_sha256_bytes(rel.encode())[:12]}",
            "timestamp": rec["first_seen"],
            "actor": "UCOS-UGA-001",
            "action": "IDENTITY_MINTED",
            "object_id": rec["universal_id"],
            "object_path": rel,
            "before_state": "ANONYMOUS",
            "after_state": rec["universal_id"],
            "evidence_reference": os.path.relpath(OUT["executables"], REPO),
            "validation_result": "ADMITTED",
            "status": "RETIRED" if rel in set(retired) else "ACTIVE",
        })

    invariants = epoch5_invariants(entries, objects, genreg, evidence, decl,
                                   audit_events, retired)
    observation, deviations, plans, evolution = epochs6_9(entries, invariants,
                                                          objects, retired)

    # EPOCH 4 — relationship graph
    rel_edges = []
    for e in entries:
        uid = e["universal_id"] or e["path"]
        rel_edges.append({"from": uid, "kind": "owned_by", "to": e["owner"]})
        rel_edges.append({"from": uid, "kind": "produced_by", "to": e["producer"]})
        rel_edges.append({"from": uid, "kind": "validated_by", "to": e["validation_contract"]})
        rel_edges.append({"from": uid, "kind": "evidenced_by", "to": e["evidence_class"]})
        for d in e["dependencies"]:
            rel_edges.append({"from": uid, "kind": "depends_on", "to": d})
        for p in e["produces"]:
            rel_edges.append({"from": uid, "kind": "produces", "to": p})
    rel_edges.sort(key=lambda r: (r["from"], r["kind"], r["to"]))

    return dict(decl=decl, ledger=ledger, objects=objects, entries=entries,
                minted=minted, anonymous=anonymous, retired=retired, unknown=unknown,
                audit_events=audit_events, invariants=invariants,
                observation=observation, deviations=deviations, plans=plans,
                evolution=evolution, rel_edges=rel_edges, genreg=genreg,
                registered_docs=registered_docs, now=now)


def emit(st):
    decl = st["decl"]
    entries = st["entries"]
    changed = []

    def w(key, obj):
        if _dump(OUT[key], obj):
            changed.append(os.path.relpath(OUT[key], REPO))

    hdr = {
        "artifact_id": "UCOS-UGA-001",
        "authority": "NONE — DERIVED TRUTH. Measurement of repository state.",
        "producer": "00-MASTER/UCOS-UGA-001/uga_engine.py",
        "determinism": "No wall clock. Timestamps are ledger first_seen values.",
    }

    w("inventory", {**hdr, "epoch": "0 — Existence Discovery",
                    "success_condition": "unknown_objects == 0",
                    "total_objects": len(st["objects"]),
                    "unknown_objects": len(st["unknown"]),
                    "classifier_property": "TOTAL — the final branch is unconditional, so "
                                           "UNKNOWN is structurally unreachable.",
                    "objects": st["objects"]})

    exec_entries = [e for e in entries if e["identity_authority"] == "UCOS-UGA-001"]
    w("executables", {**hdr, "epoch": "1-2 — Identity + Executable Object Registry",
                      "count": len(exec_entries),
                      "identity_authority": decl["one_identity_authority"],
                      "entries": exec_entries})

    w("universal", {**hdr, "epoch": "2 — Universal Object Registry (union view)",
                    "why": "The single source of truth for EXISTENCE. It unions the "
                           "document class governed by UMB-IMP-001 with the object classes "
                           "governed by UCOS-UGA-001. It is a VIEW, not a second registry: "
                           "it stores no identity of its own and mints nothing.",
                    "count": len(entries),
                    "by_authority": {
                        "UMB-IMP-001": sum(1 for e in entries
                                           if e["identity_authority"] == "UMB-IMP-001"),
                        "UCOS-UGA-001": len(exec_entries)},
                    "entries": entries})

    w("audit", {**hdr, "epoch": "3 — Audit Universe", "evidence_class": "AUDIT",
                "count": len(st["audit_events"]), "events": st["audit_events"]})

    w("graph", {**hdr, "epoch": "4 — Relationship Graph",
                "relationship_kinds": ["owned_by", "produced_by", "depends_on",
                                       "produces", "validated_by", "evidenced_by"],
                "count": len(st["rel_edges"]), "relationships": st["rel_edges"]})

    passed = sum(1 for i in st["invariants"] if i["result"] == "PASS")
    w("invariants", {**hdr, "epoch": "5 — Governance Enforcement",
                     "gate": "FAIL_CLOSED",
                     "passed": passed, "total": len(st["invariants"]),
                     "result": "PASS" if passed == len(st["invariants"]) else "FAIL",
                     "invariants": st["invariants"]})

    w("observation", {**hdr, "epoch": "6-9 — Self Observation / Analysis / Planning / Evolution",
                      "evidence_class": "IMPROVEMENT",
                      "may_influence_certification": False,
                      "observation": st["observation"],
                      "analysis": {"deviations": st["deviations"]},
                      "planning": {"plans": st["plans"]},
                      "evolution": st["evolution"]})

    # EPOCH 10-11 — certification
    proof = {
        "existence_digest": _digest_of([o["path"] for o in st["objects"]]),
        "identity_digest": _digest_of({e["path"]: e["universal_id"] for e in entries}),
        "registry_digest": _digest_of(entries),
        "graph_digest": _digest_of(st["rel_edges"]),
        "invariant_digest": _digest_of(st["invariants"]),
    }
    blocking = [d for d in st["deviations"] if d["severity"] == "BLOCKING"]
    w("certification", {**hdr, "epoch": "10-11 — Certification / Phase 8 / Phase 9",
                        "verdict": "CERTIFIED" if not blocking else "NOT_CERTIFIED",
                        "blocking_deviations": blocking,
                        "declared_open": [d for d in st["deviations"]
                                          if d["severity"] == "DECLARED_OPEN"],
                        "proof": proof,
                        "fixed_point_property": "Outputs contain no wall clock, so a second "
                                                "run over an unchanged repository rewrites no "
                                                "byte. Fixed point is checkable by comparison.",
                        "scope": {
                            "objects_governed": len(entries),
                            "minted_by_this_programme": len(exec_entries),
                            "corpus_bytes_touched": 0,
                        }})

    # dashboard
    obs = st["observation"]
    lines = [
        "# UCOS-UGA-001 — Universal Governance Assimilation Dashboard",
        "",
        "**Authority:** NONE — DERIVED TRUTH.  ",
        "**Producer:** `00-MASTER/UCOS-UGA-001/uga_engine.py`  ",
        "**Determinism:** no wall clock; timestamps are append-only ledger `first_seen` values.",
        "",
        "## Governed existence",
        "",
        "| Object class | Count | Identity authority |",
        "|---|---:|---|",
    ]
    auth_for = {"DOCUMENT_ARTIFACT": "UMB-IMP-001"}
    for k, n in obs["by_object_class"].items():
        lines.append(f"| {k} | {n} | {auth_for.get(k, 'UCOS-UGA-001')} |")
    lines += [
        f"| **TOTAL** | **{obs['total_objects']}** | one shared ledger |",
        "",
        "## Invariants",
        "",
        "| ID | Invariant | Result | Violations |",
        "|---|---|---|---:|",
    ]
    for i in st["invariants"]:
        mark = "PASS" if i["result"] == "PASS" else "**FAIL**"
        lines.append(f"| {i['id']} | `{i['name']}` | {mark} | {i['violation_count']} |")
    lines += [
        "",
        "## Graph",
        "",
        f"- relationship edges: **{len(st['rel_edges'])}**",
        f"- dependency edges: **{obs['dependency_edges']}**",
        f"- producers bound to declared outputs: **{obs['producers_bound_to_outputs']}**",
        f"- distinct owners: **{obs['distinct_owners']}**",
        "",
        "## Corpus impact",
        "",
        "- corpus bytes touched: **0** — no page range consumed, `artifacts.json` untouched.",
        "",
    ]
    if _write_text(OUT["dashboard"], "\n".join(lines)):
        changed.append(os.path.relpath(OUT["dashboard"], REPO))

    return changed


def cmd_run(args):
    st = build(mint=True)
    # Persist the shared ledger FIRST: an identity must exist before the registry
    # that references it, never after.
    minted = len(st["minted"])
    if _dump(LEDGER_PATH, st["ledger"]):
        print(f"identity ledger updated: {minted} minted")
        # The ledger is itself a governed TOOLING_OBJECT, so the registry records a
        # content_hash for it — and minting is what just changed those bytes. The
        # first pass therefore recorded the PRE-mint hash of a file that minting
        # mutated: a self-referential output that only settles on a second run.
        # A pristine clone runs the engine ONCE, so "converges eventually" is not a
        # fixed point. Re-derive against the persisted ledger so a single run is
        # internally consistent and the second run is a no-op by construction.
        st = build(mint=False)
    changed = emit(st)
    st["minted"] = [None] * minted          # preserve the count for the report
    print(f"UGA run — objects={len(st['entries'])} minted={len(st['minted'])} "
          f"retired={len(st['retired'])}")
    passed = sum(1 for i in st["invariants"] if i["result"] == "PASS")
    print(f"invariants {passed}/{len(st['invariants'])} passing")
    print(f"surfaces rewritten: {len(changed)}" + (f" -> {changed}" if changed else " (no-op)"))
    return 0


def cmd_gate(args):
    """Verify without mutating. Fails closed."""
    st = build(mint=False)
    bad = [i for i in st["invariants"] if i["result"] == "FAIL"]
    # EVERY invariant blocks. UGA-INV-06 was carried as a non-blocking DECLARED-OPEN
    # condition while `realization/` had a producer but no bootstrap path. That gap is
    # discharged — the producer was made deterministic and added to
    # scripts/generate-prerequisites.sh — so the exemption is removed with it. Keeping a
    # carve-out for a condition that no longer exists would mean a future regression in
    # the bootstrap could never fail this gate, which is the exemption outliving its
    # reason: exactly how a gate quietly stops gating.
    blocking = bad
    print("UCOS-UGA-001 Governance Gate")
    print("-" * 60)
    for i in st["invariants"]:
        print(f"  [{i['result']:4s}] {i['id']}  {i['name']}  "
              f"(violations={i['violation_count']}, measured={i['measured']})")
    print("-" * 60)
    if st["anonymous"]:
        print(f"  ANONYMOUS OBJECTS: {len(st['anonymous'])} — run `uga_engine.py run`")
    if blocking:
        print(f"GATE FAILED — {len(blocking)} blocking invariant(s).")
        for i in blocking:
            for v in i["violations"][:10]:
                print(f"    {i['id']}: {v}")
        return 1
    print("GATE PASSED — no anonymous, unowned, unregistered or unaudited object.")
    return 0


def cmd_stats(args):
    st = build(mint=False)
    print(json.dumps(st["observation"], indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description="UCOS-UGA-001 Universal Governance Assimilation")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="mint identities and emit all surfaces")
    sub.add_parser("gate", help="verify invariants, mutate nothing")
    sub.add_parser("stats", help="print measured state")
    args = ap.parse_args()
    return {"run": cmd_run, "gate": cmd_gate, "stats": cmd_stats}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
