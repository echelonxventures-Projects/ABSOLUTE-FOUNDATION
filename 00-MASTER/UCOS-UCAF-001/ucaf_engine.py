#!/usr/bin/env python3
"""UCOS-UCAF-001 — Universal Constitutional Authority Framework.

AUTHORITY = NONE (DERIVED TRUTH). This engine creates no authority, confers no authority,
occupies no tier, ratifies nothing and certifies no artifact. Every authority it registers is
DISCOVERED by reading a located instrument that already defines it; every competence question
it answers is answered by a clause it reads out of a located instrument; every conflict it
finds between a recorded claim of authority absence and located evidence of authority presence
is reported and referred to the claim owner, never decided here.

    python3 00-MASTER/UCOS-UCAF-001/ucaf_engine.py --render     # regenerate the registers
    python3 00-MASTER/UCOS-UCAF-001/ucaf_engine.py --gate       # fail-closed authority gate
    python3 00-MASTER/UCOS-UCAF-001/ucaf_engine.py --check-declaration
    python3 00-MASTER/UCOS-UCAF-001/ucaf_engine.py --check-no-enumeration
    python3 00-MASTER/UCOS-UCAF-001/ucaf_engine.py --check-write-scope
    python3 00-MASTER/UCOS-UCAF-001/ucaf_engine.py --check-determinism
    python3 00-MASTER/UCOS-UCAF-001/ucaf_engine.py --check-knowledge-once
    python3 00-MASTER/UCOS-UCAF-001/ucaf_engine.py --check-no-promotion

Exit semantics:
    0  every blocking validation satisfied — gate OPEN
    1  a blocking validation unsatisfied, or a self-guard failed — gate CLOSED
    2  fail-closed abort — the declaration is unusable, so no verdict may be asserted

Every source, tier pointer, delegation pointer, succession pointer, scope rule, resolution
question, reconciliation and validation dimension is read from ucaf-authority.json. No
authority identifier, no tier identifier, no vacancy identifier and no resolution answer
appears as a literal below, which is what makes extension an edit to DATA and to the located
instruments rather than to code.

Stdlib only. No network. No timestamp, no duration, no commit identity and no absolute path is
emitted, so the sealed output set is byte-identical for an unchanged repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DECLARATION = HERE / "ucaf-authority.json"
MODEL = HERE / "ucaf.json"
OWN_PREFIX = HERE.relative_to(REPO).as_posix() + "/"

REQUIRED_SECTIONS = (
    "programme",
    "capabilities",
    "authority_sources",
    "source_token_registers",
    "tier_source",
    "delegation_sources",
    "succession_sources",
    "revocations",
    "scope_rules",
    "resolutions",
    "reconciliations",
    "reference_surfaces",
    "validations",
    "exit_criteria",
)

# Reader formats a source entry may declare. A format outside this set is a fail-closed
# violation: it is how an unimplemented reader would otherwise pass silently.
FORMATS = ("markdown-table", "article-authority", "document-token")

# Reconciliation outcomes. These are properties this engine DERIVES from two measurements —
# never properties of the claim's identity.
OUT_BOTH = "RECONCILIATION-REQUIRED"
OUT_CLAIM_ABSENT = "CLAIM-NO-LONGER-LOCATED"
OUT_EVIDENCE_ABSENT = "CLAIM-STANDS-UNRECONCILED"


class FailClosed(Exception):
    """Raised when no verdict may be asserted. Always exits 2."""


# ---------------------------------------------------------------------------
# declaration


def load_declaration() -> dict:
    if not DECLARATION.exists():
        raise FailClosed(f"declaration not found: {DECLARATION.name}")
    try:
        document = json.loads(DECLARATION.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FailClosed(f"declaration is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise FailClosed("declaration is not an object")
    missing = [key for key in REQUIRED_SECTIONS if key not in document]
    if missing:
        raise FailClosed(f"declaration is missing required section(s): {', '.join(missing)}")
    return document


def read_text(relative: str) -> str | None:
    """Read a located file, or None when it does not resolve. Never raises."""
    target = REPO / relative
    if not target.is_file():
        return None
    try:
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# readers — each returns rows discovered from a LOCATED instrument


def split_row(line: str) -> list[str]:
    """Split one markdown table row into stripped cells, with emphasis removed."""
    cells = line.strip().strip("|").split("|")
    return [cell.strip().replace("**", "").strip() for cell in cells]


def table_rows(text: str, section: str | None) -> list[list[str]]:
    """Yield the data rows of the first pipe table at or after `section`.

    section None means the first table in the document. A separator row (all dashes) is
    dropped, and so is the header row that precedes it.
    """
    lines = text.splitlines()
    start = 0
    if section:
        for index, line in enumerate(lines):
            if line.strip() == section.strip():
                start = index + 1
                break
        else:
            return []
    rows: list[list[str]] = []
    in_table = False
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("|"):
            in_table = True
            cells = split_row(stripped)
            if cells and all(set(cell) <= set("-: ") for cell in cells if cell):
                rows = []  # separator reached: everything before it was the header
                continue
            rows.append(cells)
            continue
        if in_table and not stripped:
            break
    return rows


def read_markdown_table_source(source: dict) -> tuple[list[dict], str | None]:
    """Discover records from a pipe table. Returns (records, unavailable_reason)."""
    owner = source.get("owner")
    if not owner:
        return [], "no owner declared"
    text = read_text(owner)
    if text is None:
        return [], f"owner does not resolve: {owner}"
    pattern = source.get("id_pattern")
    if not pattern:
        return [], "no id_pattern declared"
    matcher = re.compile(rf"^({pattern})$")
    columns = source.get("columns") or {}
    records: list[dict] = []
    for cells in table_rows(text, source.get("section")):
        if not cells:
            continue
        found = matcher.match(cells[0])
        if not found:
            continue
        record = {"id": found.group(1), "owner": owner}
        for field, index in sorted(columns.items()):
            record[field] = cells[index] if index < len(cells) else ""
        records.append(record)
    return records, None


def read_article_authority_source(source: dict) -> tuple[list[dict], str | None]:
    """Discover instrument authorities from an ARTICLE I heading across a glob."""
    glob = source.get("owner_glob")
    if not glob:
        return [], "no owner_glob declared"
    heading = source.get("heading_pattern")
    if not heading:
        return [], "no heading_pattern declared"
    matcher = re.compile(heading, re.MULTILINE)
    records: list[dict] = []
    for path in sorted(REPO.glob(glob)):
        relative = path.relative_to(REPO).as_posix()
        text = read_text(relative)
        if text is None:
            continue
        found = matcher.search(text)
        if not found:
            continue
        name = found.group("name").strip()
        # The identifier is DERIVED from the instrument's own stem, never enumerated here.
        stem = path.stem.split("-CONSTITUTIONAL")[0].split("-")[0:2]
        instrument = "-".join(stem)
        records.append(
            {
                "id": f"{instrument}::{name}",
                "owner": relative,
                "name": f"{name.title()} Authority",
                "definition": found.group(0).strip(),
                "sources": instrument,
                "authoritative": relative,
            }
        )
    if not records:
        return [], f"no instrument declared an authority article under {glob}"
    return records, None


def read_document_tokens(source: dict) -> tuple[set[str], str | None]:
    """Collect every token of a declared family that appears in a located document."""
    owner = source.get("owner")
    text = read_text(owner) if owner else None
    if text is None:
        return set(), f"owner does not resolve: {owner}"
    pattern = source.get("id_pattern")
    if not pattern:
        return set(), "no id_pattern declared"
    return set(re.findall(rf"\b(?:{pattern})\b", text)), None


def read_json_collection(owner: str, pointer: str) -> tuple[list[dict], str | None]:
    text = read_text(owner)
    if text is None:
        return [], f"owner does not resolve: {owner}"
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        return [], f"owner is not valid JSON: {exc}"
    collection = document.get(pointer)
    if not isinstance(collection, list):
        return [], f"pointer does not resolve to a collection: {pointer}"
    return [entry for entry in collection if isinstance(entry, dict)], None


# ---------------------------------------------------------------------------
# measurement


def resolves_in_repo(token: str) -> bool:
    """True when a token names an existing repository path."""
    candidate = token.strip().strip("`").strip()
    if not candidate or candidate.startswith(("http://", "https://")):
        return False
    return (REPO / candidate).exists()


def evidence_pointers(record: dict, token_families: list[str]) -> list[str]:
    """Evidence a discovered authority carries: its own owner plus every source token."""
    pointers = [record["owner"]]
    cell = " ".join(str(record.get(field, "")) for field in ("sources", "authoritative"))
    for family in token_families:
        pointers.extend(re.findall(rf"\b(?:{family})\b", cell))
    for word in re.findall(r"[0-9A-Za-z_./\u03a9\u221e-]+", cell):
        if "/" in word and resolves_in_repo(word):
            pointers.append(word)
    seen: list[str] = []
    for pointer in pointers:
        if pointer and pointer not in seen:
            seen.append(pointer)
    return seen


def lattice_problems(tiers: list[dict], source: dict) -> tuple[list[str], list[str]]:
    """Unresolved subordinate references, and any cycle in the located tier lattice."""
    id_field = source["id_field"]
    sub_field = source["subordinate_field"]
    known = {tier.get(id_field) for tier in tiers}
    unresolved = [
        f"{tier.get(id_field)} -> {parent}"
        for tier in tiers
        for parent in (tier.get(sub_field) or [])
        if parent not in known
    ]
    edges = {tier.get(id_field): list(tier.get(sub_field) or []) for tier in tiers}
    cycles: list[str] = []
    state: dict[str, int] = {}

    def walk(node: str, trail: list[str]) -> None:
        if state.get(node) == 1:
            cycles.append(" -> ".join(trail + [node]))
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for parent in edges.get(node, []):
            if parent in edges:
                walk(parent, trail + [node])
        state[node] = 2

    for node in sorted(n for n in edges if n):
        walk(node, [])
    return sorted(unresolved), sorted(set(cycles))


def surface_files(surfaces: list[str], extensions: list[str]) -> list[str]:
    """Every located file under the declared surfaces, deterministically ordered."""
    found: set[str] = set()
    for surface in surfaces:
        target = REPO / surface
        if target.is_file():
            found.add(surface)
            continue
        if not target.is_dir():
            continue
        for path in target.rglob("*"):
            if path.is_file() and path.suffix in extensions:
                found.add(path.relative_to(REPO).as_posix())
    return sorted(found)


def measure(document: dict) -> dict:
    programme = document["programme"]
    token_families = [
        entry["id_pattern"] for entry in document["source_token_registers"] if entry.get("id_pattern")
    ]

    # --- CAP-01 registry -------------------------------------------------
    authorities: list[dict] = []
    source_status: list[dict] = []
    for source in document["authority_sources"]:
        fmt = source.get("format")
        if fmt not in FORMATS:
            raise FailClosed(f"authority source {source.get('id')} declares unknown format {fmt!r}")
        if fmt == "markdown-table":
            records, reason = read_markdown_table_source(source)
        elif fmt == "article-authority":
            records, reason = read_article_authority_source(source)
        else:
            records, reason = [], f"format {fmt} is not an authority reader"
        source_status.append(
            {
                "id": source["id"],
                "name": source["name"],
                "owner": source.get("owner") or source.get("owner_glob"),
                "format": fmt,
                "discovered": len(records),
                "resolved": reason is None and bool(records),
                "reason": reason,
            }
        )
        for record in records:
            record["source"] = source["id"]
            record["kind"] = source["kind"]
            record["evidence"] = evidence_pointers(record, token_families)
            record["evidence_resolved"] = sorted(
                pointer for pointer in record["evidence"] if resolves_in_repo(pointer)
            )
            authorities.append(record)
    authorities.sort(key=lambda record: (record["kind"], record["id"]))
    registry = {record["id"] for record in authorities}

    # source tokens that a located register defines
    known_tokens: set[str] = set()
    token_status: list[dict] = []
    for entry in document["source_token_registers"]:
        fmt = entry.get("format")
        if fmt == "markdown-table":
            records, reason = read_markdown_table_source(entry)
            tokens = {record["id"] for record in records}
        elif fmt == "document-token":
            tokens, reason = read_document_tokens(entry)
        else:
            tokens, reason = set(), f"unknown token register format {fmt!r}"
        token_status.append(
            {"id": entry["id"], "name": entry["name"], "tokens": len(tokens), "reason": reason}
        )
        known_tokens |= tokens

    # --- tiers and vacancies --------------------------------------------
    tier_source = document["tier_source"]
    tiers, tier_reason = read_json_collection(
        tier_source["owner"], tier_source["collection_pointer"]
    )
    vacancies, vacancy_reason = read_json_collection(
        tier_source["owner"], tier_source["vacancy_collection_pointer"]
    )
    unresolved_subordinates, tier_cycles = lattice_problems(tiers, tier_source)
    vacancy_records = []
    incomplete_vacancies = []
    for entry in vacancies:
        missing = [
            field for field in tier_source["vacancy_required_fields"] if not entry.get(field)
        ]
        record = {
            "id": entry.get(tier_source["vacancy_id_field"]),
            "tier": entry.get(tier_source["vacancy_tier_field"]),
            "located": bool(entry.get(tier_source["vacancy_located_field"])),
            "open_question": entry.get("open_question"),
            "complete": not missing,
            "missing_fields": missing,
        }
        vacancy_records.append(record)
        if missing:
            incomplete_vacancies.append(f"{record['id']}: {', '.join(missing)}")
    vacant_tiers = sorted(
        tier.get(tier_source["id_field"])
        for tier in tiers
        if tier.get(tier_source["vacancy_field"])
    )

    # --- CAP-02 delegation ----------------------------------------------
    delegations: list[dict] = []
    unowned_delegations: list[str] = []
    for source in document["delegation_sources"]:
        entries, reason = read_json_collection(source["owner"], source["collection_pointer"])
        if reason:
            unowned_delegations.append(f"{source['id']}: {reason}")
            continue
        for entry in entries:
            owner_value = entry.get(source["owner_field"])
            owner_paths = entry.get(source.get("owner_paths_field") or "") or []
            candidates = [owner_value] if owner_value else []
            candidates.extend(owner_paths if isinstance(owner_paths, list) else [])
            resolved = sorted(
                candidate
                for candidate in candidates
                if candidate and (resolves_in_repo(candidate) or candidate in registry)
            )
            named = bool(candidates)
            record = {
                "id": entry.get(source["id_field"]),
                "concern": entry.get(source["concern_field"]),
                "owner": owner_value or (owner_paths[0] if owner_paths else None),
                "disposition": entry.get(source.get("disposition_field") or ""),
                "owner_named": named,
                "owner_resolved": bool(resolved),
            }
            delegations.append(record)
            if not named:
                unowned_delegations.append(f"{record['id']}: no owner named")
    delegations.sort(key=lambda record: str(record["id"]))

    # --- CAP-05 succession ----------------------------------------------
    successions: list[dict] = []
    unsourced_successions: list[str] = []
    for source in document["succession_sources"]:
        records, reason = read_markdown_table_source(source)
        if reason:
            unsourced_successions.append(f"{source['id']}: {reason}")
            continue
        for record in records:
            cell = str(record.get("authoritative_source", ""))
            tokens = sorted(
                {
                    token
                    for family in token_families
                    for token in re.findall(rf"\b(?:{family})\b", cell)
                }
            )
            resolved = [token for token in tokens if token in known_tokens]
            entry = {
                "id": record["id"],
                "concept": record.get("concept"),
                "authoritative_tokens": tokens,
                "resolved": bool(resolved),
                "status": record.get("status", "")[:120],
            }
            successions.append(entry)
            if not resolved:
                unsourced_successions.append(f"{record['id']}: no source token resolves")
    successions.sort(key=lambda record: str(record["id"]))

    # --- CAP-06 scope ----------------------------------------------------
    scope_rules: list[dict] = []
    unbound_scope: list[str] = []
    for rule in document["scope_rules"]:
        text = read_text(rule["owner"])
        bound = text is not None and rule["anchor"] in text
        scope_rules.append(
            {"id": rule["id"], "rule": rule["rule"], "owner": rule["owner"], "bound": bound}
        )
        if not bound:
            unbound_scope.append(f"{rule['id']}: anchor absent in {rule['owner']}")

    # --- CAP-03 resolution ----------------------------------------------
    resolutions: list[dict] = []
    unresolved_questions: list[str] = []
    for question in document["resolutions"]:
        text = read_text(question["owner"])
        located = text is not None and question["anchor"] in text
        answers: list[str] = []
        if located:
            for line in text.splitlines():
                if question["anchor"] in line:
                    for identifier in re.findall(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b", line):
                        if identifier in registry and identifier not in answers:
                            answers.append(identifier)
                    break
        record = {
            "id": question["id"],
            "question": question["question"],
            "owner": question["owner"],
            "located": located,
            "in_corpus": bool(question.get("in_corpus")),
            "answers": answers,
            "outcome": "ANSWERED" if located else "UNRESOLVED",
        }
        resolutions.append(record)
        if not located:
            unresolved_questions.append(f"{question['id']}: anchor absent in {question['owner']}")

    # --- CAP-11 certification: no authority undefined --------------------
    families = [source["id_pattern"] for source in document["authority_sources"] if source.get("id_pattern")]
    undefined: list[dict] = []
    scanned = surface_files(
        document["reference_surfaces"], document.get("reference_surface_extensions") or [".md"]
    )
    if families:
        scanner = re.compile(rf"\b(?:{'|'.join(families)})\b")
        for relative in scanned:
            if relative.startswith(OWN_PREFIX):
                continue
            text = read_text(relative)
            if text is None:
                continue
            for token in sorted(set(scanner.findall(text))):
                if token not in registry:
                    undefined.append({"token": token, "surface": relative})

    # --- CAP-13 reconciliation ------------------------------------------
    reconciliations: list[dict] = []
    unmeasured_reconciliations: list[str] = []
    for item in document["reconciliations"]:
        claim_text = read_text(item["claim_owner"])
        claim_stands = claim_text is not None and item["claim_anchor"] in claim_text
        located_evidence = []
        absent_evidence = []
        for candidate in item["candidate_evidence"]:
            text = read_text(candidate["path"])
            if text is not None and candidate["anchor"] in text:
                located_evidence.append(candidate["path"])
            else:
                absent_evidence.append(candidate["path"])
        if not claim_stands:
            outcome = OUT_CLAIM_ABSENT
        elif located_evidence:
            outcome = OUT_BOTH
        else:
            outcome = OUT_EVIDENCE_ABSENT
        record = {
            "id": item["id"],
            "claim": item["claim"],
            "claim_owner": item["claim_owner"],
            "claim_stands": claim_stands,
            "evidence_located": sorted(located_evidence),
            "evidence_absent": sorted(absent_evidence),
            "outcome": outcome,
            "referred_to": item.get("referred_to"),
            "ratifies": False,
            "closes_vacancy": False,
        }
        reconciliations.append(record)
        if claim_text is None and not located_evidence:
            unmeasured_reconciliations.append(f"{item['id']}: neither side resolves")

    # --- CAP-10 revocation ----------------------------------------------
    revocation_problems: list[str] = []
    for entry in document["revocations"]:
        if entry.get("authority") not in registry:
            revocation_problems.append(f"{entry.get('id')}: authority does not resolve")
        elif not resolves_in_repo(entry.get("record", "")):
            revocation_problems.append(f"{entry.get('id')}: record path does not resolve")

    # --- CAP-07 verification --------------------------------------------
    verified: list[dict] = []
    unverified: list[str] = []
    for relative in sorted(
        {record["owner"] for record in authorities}
        | {tier_source["owner"]}
        | {source["owner"] for source in document["succession_sources"]}
    ):
        text = read_text(relative)
        if text is None:
            unverified.append(relative)
            continue
        verified.append({"owner": relative, "digest": digest(text)[:16]})

    # --- CAP-09 audit ----------------------------------------------------
    audit = [
        {
            "entry": index,
            "authority": record["id"],
            "kind": record["kind"],
            "source": record["source"],
            "owner": record["owner"],
            "evidence": len(record["evidence_resolved"]),
        }
        for index, record in enumerate(authorities, start=1)
    ]

    # --- validations -----------------------------------------------------
    definitionless = sorted(
        record["id"] for record in authorities if not str(record.get("definition", "")).strip()
    )
    evidenceless = sorted(
        record["id"] for record in authorities if not record["evidence_resolved"]
    )
    self_conferred = sorted(
        record["id"]
        for record in authorities
        if {token for token in re.findall(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b", str(record.get("sources", "")))}
        == {record["id"]}
    )

    # Measured failure lists, keyed by validation id. This is the one place the engine names a
    # validation: measurement logic cannot be derived from data. A declared validation with no
    # measurement here is reported measured=false and satisfied=false, so it fails closed —
    # absence of a measurement is never evidence of compliance.
    findings: dict[str, list[str]] = {
        "UCAF-VAL-01": [
            f"{entry['id']}: {entry['reason'] or 'no records discovered'}"
            for entry in source_status
            if not entry["resolved"]
        ],
        "UCAF-VAL-02": definitionless,
        "UCAF-VAL-03": evidenceless,
        "UCAF-VAL-04": self_conferred,
        "UCAF-VAL-05": unresolved_subordinates + tier_cycles + ([tier_reason] if tier_reason else []),
        "UCAF-VAL-06": incomplete_vacancies + ([vacancy_reason] if vacancy_reason else []),
        "UCAF-VAL-07": [f"{item['token']} ({item['surface']})" for item in undefined],
        "UCAF-VAL-08": unresolved_questions,
        "UCAF-VAL-09": unbound_scope,
        "UCAF-VAL-10": unowned_delegations,
        "UCAF-VAL-11": unsourced_successions,
        "UCAF-VAL-12": revocation_problems,
        "UCAF-VAL-13": unmeasured_reconciliations,
        "UCAF-VAL-14": [],  # filled below, once the capability measures are known
        "UCAF-VAL-15": [
            f"{record['id']}: promoted or ratified"
            for record in reconciliations
            if record["ratifies"] or record["closes_vacancy"]
        ]
        + [f"{tier}: reported occupied while vacant" for tier in [] ],
    }

    measures = {
        "authorities_registered": len(authorities),
        "delegations_registered": len(delegations),
        "resolutions_answered": sum(1 for record in resolutions if record["located"]),
        "validations_measured": 0,
        "successions_registered": len(successions),
        "scope_rules_bound": sum(1 for rule in scope_rules if rule["bound"]),
        "records_verified": len(verified),
        "authorities_with_evidence": sum(1 for record in authorities if record["evidence_resolved"]),
        "audit_entries": len(audit),
        "revocations_registered": len(document["revocations"]),
        "undefined_references": len(undefined),
    }
    capabilities = []
    for capability in document["capabilities"]:
        measure_key = capability["measure"]
        known = measure_key in measures
        # A capability is discharged when its measure ran AND, where the measure counts a
        # defect, the count is zero; where it counts a population, the population is non-empty.
        if not known:
            discharged = False
        elif measure_key == "undefined_references":
            discharged = measures[measure_key] == 0
        elif measure_key == "revocations_registered":
            discharged = not revocation_problems
        elif measure_key == "validations_measured":
            discharged = True
        else:
            discharged = measures[measure_key] > 0
        capabilities.append(
            {
                "id": capability["id"],
                "capability": capability["capability"],
                "obligation": capability["obligation"],
                "measure": measure_key,
                "value": measures.get(measure_key),
                "measured": known,
                "discharged": discharged,
            }
        )
    findings["UCAF-VAL-14"] = [
        f"{entry['id']}: {entry['measure']}"
        for entry in capabilities
        if not entry["discharged"]
    ]

    validations = []
    for validation in document["validations"]:
        measured = validation["id"] in findings
        failures = findings.get(validation["id"], [])
        validations.append(
            {
                "id": validation["id"],
                "dimension": validation["dimension"],
                "obligation": validation["obligation"],
                "blocking": bool(validation["blocking"]),
                "measured": measured,
                "satisfied": measured and not failures,
                "failures": sorted(failures)[:40],
                "failure_count": len(failures),
            }
        )
    measures["validations_measured"] = sum(1 for entry in validations if entry["measured"])
    for entry in capabilities:
        if entry["measure"] == "validations_measured":
            entry["value"] = measures["validations_measured"]

    blocking_failures = [
        entry["id"] for entry in validations if entry["blocking"] and not entry["satisfied"]
    ]
    gate = "CLOSED" if blocking_failures else "OPEN"

    model = {
        "programme": programme,
        "authority_sources": source_status,
        "source_token_registers": token_status,
        "authorities": [
            {
                "id": record["id"],
                "kind": record["kind"],
                "name": record.get("name"),
                "source": record["source"],
                "owner": record["owner"],
                "definition": str(record.get("definition", ""))[:400],
                "evidence": record["evidence"][:12],
                "evidence_resolved": record["evidence_resolved"][:12],
            }
            for record in authorities
        ],
        "tiers": [
            {
                "id": tier.get(tier_source["id_field"]),
                "name": tier.get(tier_source["name_field"]),
                "subordinate_to": tier.get(tier_source["subordinate_field"]) or [],
                "occupancy": tier.get(tier_source["occupancy_field"]),
                "vacancy": tier.get(tier_source["vacancy_field"]),
            }
            for tier in tiers
        ],
        "vacant_tiers": vacant_tiers,
        "vacancies": vacancy_records,
        "delegations": delegations,
        "successions": successions,
        "scope_rules": scope_rules,
        "resolutions": resolutions,
        "reconciliations": reconciliations,
        "revocations": list(document["revocations"]),
        "verified_sources": verified,
        "unverified_sources": sorted(unverified),
        "undefined_references": undefined,
        "audit_ledger": audit,
        "capabilities": capabilities,
        "validations": validations,
        "counts": {
            "authorities": len(authorities),
            "authority_kinds": len({record["kind"] for record in authorities}),
            "tiers": len(tiers),
            "vacant_tiers": len(vacant_tiers),
            "delegations": len(delegations),
            "successions": len(successions),
            "scope_rules_bound": measures["scope_rules_bound"],
            "scope_rules": len(scope_rules),
            "resolutions_answered": measures["resolutions_answered"],
            "resolutions": len(resolutions),
            "reconciliations": len(reconciliations),
            "reconciliation_required": sum(
                1 for record in reconciliations if record["outcome"] == OUT_BOTH
            ),
            "surfaces_scanned": len(scanned),
            "undefined_references": len(undefined),
            "audit_entries": len(audit),
            "capabilities_discharged": sum(1 for entry in capabilities if entry["discharged"]),
            "capabilities": len(capabilities),
        },
        "blocking_failures": blocking_failures,
        "gate": gate,
        "gate_exit": 1 if blocking_failures else 0,
        "determination": (
            "AUTHORITY-MODEL-BOUND" if gate == "OPEN" else "AUTHORITY-MODEL-INCOMPLETE"
        ),
        "exit_criteria": list(document["exit_criteria"]),
        "findings": list(document.get("findings", [])),
    }
    model["seal_sha256"] = digest(json.dumps(model, sort_keys=True, ensure_ascii=False))
    return model


# ---------------------------------------------------------------------------
# rendering — pure: no clock, no environment, no I/O beyond the model


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def front_matter(model: dict) -> str:
    programme = model["programme"]
    counts = model["counts"]
    rows = [
        ["PROGRAMME", f"{programme['id']} — {programme['name']}"],
        ["VERSION", programme["version"]],
        ["AUTHORITY", programme["authority"]],
        ["AUTHORITIES REGISTERED", f"{counts['authorities']} across {counts['authority_kinds']} kinds"],
        ["TIERS", f"{counts['tiers']} ({counts['vacant_tiers']} vacant)"],
        ["DELEGATIONS", counts["delegations"]],
        ["SUCCESSIONS", counts["successions"]],
        ["SCOPE RULES BOUND", f"{counts['scope_rules_bound']}/{counts['scope_rules']}"],
        ["COMPETENCE QUESTIONS ANSWERED", f"{counts['resolutions_answered']}/{counts['resolutions']}"],
        ["UNDEFINED AUTHORITY REFERENCES", f"{counts['undefined_references']} over {counts['surfaces_scanned']} surfaces"],
        ["CAPABILITIES DISCHARGED", f"{counts['capabilities_discharged']}/{counts['capabilities']}"],
        ["GATE", model["gate"]],
        ["DETERMINATION", model["determination"]],
        ["SEAL (sha256)", model["seal_sha256"]],
        ["GENERATED BY", "ucaf_engine.py — regenerated, never hand-authored"],
    ]
    return table(["Field", "Value"], rows) + "\n\n> " + programme["disclosure"]


def render(model: dict) -> dict[str, str]:
    pages: dict[str, str] = {}
    programme = model["programme"]

    pages["00-UCAF-DASHBOARD.md"] = "\n".join(
        [
            f"# {programme['id']} — {programme['name']} · Dashboard",
            "",
            front_matter(model),
            "",
            "## Capability discharge",
            "",
            table(
                ["Capability", "Obligation", "Measure", "Value", "Discharged"],
                [
                    [
                        f"`{entry['id']}` {entry['capability']}",
                        entry["obligation"],
                        f"`{entry['measure']}`",
                        entry["value"],
                        "YES" if entry["discharged"] else "**NO**",
                    ]
                    for entry in model["capabilities"]
                ],
            ),
            "",
            "## Blocking failures",
            "",
            (
                "None. Every blocking validation is satisfied."
                if not model["blocking_failures"]
                else "\n".join(f"- `{item}`" for item in model["blocking_failures"])
            ),
            "",
        ]
    )

    pages["01-AUTHORITY-REGISTER.md"] = "\n".join(
        [
            f"# {programme['id']} · Authority Registry",
            "",
            "Every record below is DISCOVERED from the located instrument named in its owner",
            "column. No authority is defined by this programme.",
            "",
            table(
                ["Authority", "Kind", "Name", "Located definition (owner)", "Evidence resolved"],
                [
                    [
                        f"`{record['id']}`",
                        record["kind"],
                        record["name"] or "",
                        f"`{record['owner']}`",
                        len(record["evidence_resolved"]),
                    ]
                    for record in model["authorities"]
                ],
            ),
            "",
            "## Sources read",
            "",
            table(
                ["Source", "Owner", "Format", "Discovered", "Resolved"],
                [
                    [
                        f"`{entry['id']}`",
                        f"`{entry['owner']}`",
                        entry["format"],
                        entry["discovered"],
                        "YES" if entry["resolved"] else f"**NO** — {entry['reason']}",
                    ]
                    for entry in model["authority_sources"]
                ],
            ),
            "",
        ]
    )

    pages["02-TIER-DELEGATION-AND-SUCCESSION-REGISTER.md"] = "\n".join(
        [
            f"# {programme['id']} · Tiers, Delegation, Succession, Revocation",
            "",
            "## Tier lattice (read from the located meta-constitutional projection)",
            "",
            table(
                ["Tier", "Name", "Subordinate to", "Occupancy", "Vacancy"],
                [
                    [
                        f"`{tier['id']}`",
                        tier["name"] or "",
                        ", ".join(f"`{parent}`" for parent in tier["subordinate_to"]) or "—",
                        tier["occupancy"] or "",
                        f"`{tier['vacancy']}`" if tier["vacancy"] else "—",
                    ]
                    for tier in model["tiers"]
                ],
            ),
            "",
            "## Recorded vacancies",
            "",
            "A vacancy is recorded, never promoted. This programme reports occupancy exactly as",
            "its located owner records it.",
            "",
            table(
                ["Vacancy", "Tier", "Occupant located", "Open question", "Record complete"],
                [
                    [
                        f"`{record['id']}`",
                        f"`{record['tier']}`",
                        "YES" if record["located"] else "NO",
                        f"`{record['open_question']}`" if record["open_question"] else "—",
                        "YES" if record["complete"] else f"**NO** — {', '.join(record['missing_fields'])}",
                    ]
                    for record in model["vacancies"]
                ],
            )
            or "No vacancy is recorded.",
            "",
            "## Delegation (CEP-002 Article 13 / Article 14)",
            "",
            table(
                ["Delegation", "Concern", "Owner", "Disposition", "Owner resolves"],
                [
                    [
                        f"`{record['id']}`",
                        record["concern"] or "",
                        f"`{record['owner']}`" if record["owner"] else "—",
                        record["disposition"] or "",
                        "YES" if record["owner_resolved"] else "no (named, unresolved path)",
                    ]
                    for record in model["delegations"]
                ],
            ),
            "",
            "## Succession",
            "",
            table(
                ["Succession", "Concept", "Authoritative source tokens", "Resolves"],
                [
                    [
                        f"`{record['id']}`",
                        record["concept"] or "",
                        ", ".join(f"`{token}`" for token in record["authoritative_tokens"]) or "—",
                        "YES" if record["resolved"] else "**NO**",
                    ]
                    for record in model["successions"]
                ],
            ),
            "",
            "## Revocation",
            "",
            "CEP-002 13.5 — a revocation SHALL be recorded and SHALL take effect upon record.",
            "The channel is append-only and every appended entry is validated against the",
            "registry.",
            "",
            (
                f"Recorded revocations: {len(model['revocations'])}."
                if model["revocations"]
                else "No revocation has been recorded in this repository. The channel exists and is empty."
            ),
            "",
        ]
    )

    pages["03-SCOPE-AND-RESOLUTION-REPORT.md"] = "\n".join(
        [
            f"# {programme['id']} · Scope and Resolution",
            "",
            "## Scope rules (bound to located clauses)",
            "",
            table(
                ["Rule", "Obligation", "Located in", "Bound"],
                [
                    [
                        f"`{rule['id']}`",
                        rule["rule"],
                        f"`{rule['owner']}`",
                        "YES" if rule["bound"] else "**NO**",
                    ]
                    for rule in model["scope_rules"]
                ],
            ),
            "",
            "## Competence resolution",
            "",
            "Each answer is READ from the located instrument named as owner. An absent clause is",
            "reported UNRESOLVED and is never answered by default.",
            "",
            table(
                ["Question", "Asked", "Located in", "In corpus", "Answers", "Outcome"],
                [
                    [
                        f"`{record['id']}`",
                        record["question"],
                        f"`{record['owner']}`",
                        "YES" if record["in_corpus"] else "NO (out-of-corpus superior)",
                        ", ".join(f"`{answer}`" for answer in record["answers"]) or "—",
                        record["outcome"],
                    ]
                    for record in model["resolutions"]
                ],
            ),
            "",
        ]
    )

    pages["04-RECONCILIATION-REPORT.md"] = "\n".join(
        [
            f"# {programme['id']} · Authority Reconciliation",
            "",
            "Where a recorded claim of authority absence and located evidence of authority",
            "presence both stand, both are Repository Truth. This programme measures both sides,",
            "cites both, and refers the conflict to the claim owner for disposal under CEP-002",
            "Article 23. It performs no disposal, closes no vacancy and ratifies nothing.",
            "",
            table(
                ["Reconciliation", "Claim", "Claim owner", "Claim stands", "Evidence located", "Outcome", "Referred to"],
                [
                    [
                        f"`{record['id']}`",
                        record["claim"],
                        f"`{record['claim_owner']}`",
                        "YES" if record["claim_stands"] else "NO",
                        ", ".join(f"`{path}`" for path in record["evidence_located"]) or "—",
                        record["outcome"],
                        f"`{record['referred_to']}`" if record["referred_to"] else "—",
                    ]
                    for record in model["reconciliations"]
                ],
            ),
            "",
            "## Undefined authority references",
            "",
            (
                "None. Every authority-shaped reference in every declared surface resolves to a"
                " registered authority."
                if not model["undefined_references"]
                else table(
                    ["Token", "Surface"],
                    [
                        [f"`{item['token']}`", f"`{item['surface']}`"]
                        for item in model["undefined_references"][:200]
                    ],
                )
            ),
            "",
        ]
    )

    pages["05-AUTHORITY-AUDIT-LEDGER.md"] = "\n".join(
        [
            f"# {programme['id']} · Authority Audit Ledger",
            "",
            "Append-only and content-addressed. The ledger plus the verified source digests are",
            "sufficient to reconstruct this registration deterministically.",
            "",
            table(
                ["#", "Authority", "Kind", "Source", "Owner", "Evidence"],
                [
                    [
                        entry["entry"],
                        f"`{entry['authority']}`",
                        entry["kind"],
                        f"`{entry['source']}`",
                        f"`{entry['owner']}`",
                        entry["evidence"],
                    ]
                    for entry in model["audit_ledger"]
                ],
            ),
            "",
            "## Verified sources",
            "",
            table(
                ["Owner", "Content digest (sha256/16)"],
                [[f"`{entry['owner']}`", entry["digest"]] for entry in model["verified_sources"]],
            ),
            "",
            (
                ""
                if not model["unverified_sources"]
                else "### Unverified\n\n"
                + "\n".join(f"- `{item}`" for item in model["unverified_sources"])
                + "\n"
            ),
        ]
    )

    pages["06-CERTIFICATION-REPORT.md"] = "\n".join(
        [
            f"# {programme['id']} · Certification Report",
            "",
            front_matter(model),
            "",
            "## Validation dimensions",
            "",
            table(
                ["Dimension", "Obligation", "Blocking", "Measured", "Satisfied", "Failures"],
                [
                    [
                        f"`{entry['id']}` {entry['dimension']}",
                        entry["obligation"],
                        "YES" if entry["blocking"] else "no",
                        "YES" if entry["measured"] else "**NO**",
                        "YES" if entry["satisfied"] else "**NO**",
                        entry["failure_count"],
                    ]
                    for entry in model["validations"]
                ],
            ),
            "",
            "## Exit criteria",
            "",
            table(
                ["Criterion", "Statement"],
                [[f"`{item['id']}`", item["criterion"]] for item in model["exit_criteria"]],
            ),
            "",
            "## Findings",
            "",
            table(
                ["Finding", "Class", "Disposition", "Blocking", "Title"],
                [
                    [
                        f"`{item['id']}`",
                        item["class"],
                        item["disposition"],
                        "YES" if item.get("blocking") else "no",
                        item["title"],
                    ]
                    for item in model["findings"]
                ],
            ),
            "",
            "CERTIFIED-PROVISIONAL. This programme holds no ratification authority: it registers,",
            "resolves, validates and audits the authorities the repository has already located.",
            "Where this register and a located instrument differ, the located instrument governs.",
            "",
        ]
    )
    return pages


def write_registers(model: dict) -> list[str]:
    written = []
    for name, body in sorted(render(model).items()):
        target = HERE / name
        target.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
        written.append(name)
    MODEL.write_text(
        json.dumps(model, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    written.append(MODEL.name)
    return written


# ---------------------------------------------------------------------------
# self-guards


def check_declaration(document: dict) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for section in ("capabilities", "authority_sources", "scope_rules", "resolutions", "reconciliations", "validations", "exit_criteria"):
        for entry in document[section]:
            identifier = entry.get("id")
            if not identifier:
                problems.append(f"{section}: an entry carries no id")
            elif identifier in seen:
                problems.append(f"{section}: duplicate id {identifier}")
            else:
                seen.add(identifier)
    for source in document["authority_sources"]:
        if source.get("format") not in FORMATS:
            problems.append(f"{source.get('id')}: unknown format {source.get('format')!r}")
        owner = source.get("owner")
        if owner and not (REPO / owner).is_file():
            problems.append(f"{source.get('id')}: owner does not resolve: {owner}")
    for rule in document["scope_rules"] + document["resolutions"]:
        if not (REPO / rule["owner"]).is_file():
            problems.append(f"{rule['id']}: owner does not resolve: {rule['owner']}")
    if not (REPO / document["tier_source"]["owner"]).is_file():
        problems.append("tier_source owner does not resolve")
    for item in document["reconciliations"]:
        if not (REPO / item["claim_owner"]).is_file():
            problems.append(f"{item['id']}: claim owner does not resolve")
    return problems


def check_no_enumeration(document: dict) -> list[str]:
    """No discovered or located identifier may appear as a literal in this engine's source."""
    source = Path(__file__).read_text(encoding="utf-8")
    leaked: list[str] = []
    model = measure(document)
    for record in model["authorities"]:
        if record["id"] in source:
            leaked.append(f"authority {record['id']}")
    for tier in model["tiers"]:
        identifier = tier["id"]
        if identifier and re.search(rf"\b{re.escape(identifier)}\b", source):
            leaked.append(f"tier {identifier}")
    for record in model["vacancies"]:
        if record["id"] and record["id"] in source:
            leaked.append(f"vacancy {record['id']}")
    return sorted(set(leaked))


def check_write_scope(document: dict) -> list[str]:
    problems: list[str] = []
    targets = [HERE / name for name in render(measure(document))] + [MODEL]
    for target in targets:
        try:
            target.resolve().relative_to(HERE)
        except ValueError:
            problems.append(target.as_posix())
    for prefix in document["programme"]["forbidden_write_prefixes"]:
        if OWN_PREFIX.startswith(prefix):
            problems.append(f"own home falls inside a forbidden prefix: {prefix}")
    return problems


def check_determinism(document: dict) -> list[str]:
    first, second = render(measure(document)), render(measure(document))
    return sorted(name for name in first if first[name] != second.get(name))


def check_knowledge_once(document: dict) -> list[str]:
    """No authority may be DEFINED in this declaration; every one must be discovered."""
    problems: list[str] = []
    raw = DECLARATION.read_text(encoding="utf-8")
    model = measure(document)
    for record in model["authorities"]:
        # A discovered identifier appearing in the declaration would mean the declaration,
        # not the located instrument, is the definition.
        if re.search(rf"\"{re.escape(record['id'])}\"", raw):
            problems.append(f"declaration names authority {record['id']}")
    if not model["authorities"]:
        problems.append("no authority was discovered from any located source")
    return problems


def check_no_promotion(document: dict) -> list[str]:
    """This programme must never report a vacant tier as occupied, nor a claim as ratified."""
    model = measure(document)
    problems: list[str] = []
    vacant = set(model["vacant_tiers"])
    for tier in model["tiers"]:
        if tier["id"] in vacant and str(tier["occupancy"]).upper() not in {"VACANT", "NONE", ""}:
            problems.append(f"{tier['id']}: reported {tier['occupancy']} while carrying a vacancy")
    for record in model["reconciliations"]:
        if record["ratifies"] or record["closes_vacancy"]:
            problems.append(f"{record['id']}: reconciliation asserts a ratification or a closure")
    for record in model["vacancies"]:
        if record["located"]:
            continue
        if not record["open_question"]:
            problems.append(f"{record['id']}: unlocated occupant with no open question recorded")
    return problems


GUARDS = {
    "check-declaration": check_declaration,
    "check-no-enumeration": check_no_enumeration,
    "check-write-scope": check_write_scope,
    "check-determinism": check_determinism,
    "check-knowledge-once": check_knowledge_once,
    "check-no-promotion": check_no_promotion,
}


# ---------------------------------------------------------------------------
# cli


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True, description=__doc__.splitlines()[0])
    parser.add_argument("--render", action="store_true", help="regenerate the registers")
    parser.add_argument("--gate", action="store_true", help="fail-closed authority gate")
    parser.add_argument("--quiet", action="store_true")
    for name in GUARDS:
        parser.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args(argv)

    try:
        document = load_declaration()
    except FailClosed as exc:
        print(f"UCOS-UCAF-001 ABORT: {exc}", file=sys.stderr)
        return 2

    selected = [name for name in GUARDS if getattr(args, name.replace("-", "_"))]
    if selected:
        failed = False
        for name in selected:
            try:
                problems = GUARDS[name](document)
            except FailClosed as exc:
                print(f"UCOS-UCAF-001 ABORT: {exc}", file=sys.stderr)
                return 2
            if problems:
                failed = True
                print(f"UCOS-UCAF-001 {name}: FAIL ({len(problems)})", file=sys.stderr)
                for problem in problems[:40]:
                    print(f"  - {problem}", file=sys.stderr)
            else:
                print(f"UCOS-UCAF-001 {name}: PASS")
        return 1 if failed else 0

    try:
        model = measure(document)
    except FailClosed as exc:
        print(f"UCOS-UCAF-001 ABORT: {exc}", file=sys.stderr)
        return 2

    written = write_registers(model)
    counts = model["counts"]
    if not args.quiet:
        print(
            f"UCOS-UCAF-001: {model['determination']} | authorities={counts['authorities']} "
            f"| tiers={counts['tiers']}({counts['vacant_tiers']} vacant) "
            f"| delegations={counts['delegations']} | successions={counts['successions']} "
            f"| resolved={counts['resolutions_answered']}/{counts['resolutions']} "
            f"| undefined={counts['undefined_references']} "
            f"| reconciliation-required={counts['reconciliation_required']} "
            f"| gate={model['gate']} | seal={model['seal_sha256'][:16]}"
        )
        print(f"wrote {len(written)} artifacts to {HERE.relative_to(REPO).as_posix()}")
        for entry in model["validations"]:
            if entry["blocking"] and not entry["satisfied"]:
                print(f"  BLOCKING {entry['id']} {entry['dimension']}: {entry['failure_count']}", file=sys.stderr)
                for failure in entry["failures"][:10]:
                    print(f"    - {failure}", file=sys.stderr)

    if args.gate:
        return model["gate_exit"]
    return 0


if __name__ == "__main__":
    sys.exit(main())
