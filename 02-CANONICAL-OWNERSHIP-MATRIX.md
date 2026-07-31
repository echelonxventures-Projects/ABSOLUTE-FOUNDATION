# 02 — CANONICAL OWNERSHIP MATRIX

> **Mission:** Context Assimilation · **Baseline:** `ab78f35` · **Branch:** governance-reconciliation · **Date:** 2026-07-23
> **Mode:** READ-ONLY. No modification, no implementation, no commits, no tags, no push.
> **Authority:** Repository Truth is ABSOLUTE. Single Canonical Ownership — each concept has exactly one owner.

---

## 1. Purpose

Establish the **single canonical owner** for every concept touched by the finalized decisions, so integration reuses the owner rather than creating a parallel artifact. Confirms Single Canonical Ownership and exposes any unowned concept.

---

## 2. Canonical ownership matrix

| Concept domain | Canonical owner (existing artifact) | Repository location | Ownership status |
|---|---|---|---|
| Platform (constitution/theory) | PLATFORM-001 / PLATFORM-002 | `09-PLATFORM/` | **OWNED** |
| Platform meta-model | PLATFORM-005-UNIVERSAL-PLATFORM-META-MODEL | `09-PLATFORM/` | **OWNED** |
| Platform composition | PLATFORM-010-UNIVERSAL-PLATFORM-COMPOSITION-ARCHITECTURE | `09-PLATFORM/` | **OWNED** |
| Platform capability/component/service | PLATFORM-006/007/008 | `09-PLATFORM/` | **OWNED** |
| Platform master registry | PLATFORM-018-PLATFORM-MASTER-REGISTRY | `09-PLATFORM/` | **OWNED** |
| Foundation architecture / composition | IMP-001 UCOS-Ω∞-FOUNDATION-ARCHITECTURE | `06-IMPLEMENTATION/` | **OWNED** |
| Repository architecture | IMP-002 UCOS-Ω∞-REPOSITORY-ARCHITECTURE | `06-IMPLEMENTATION/` | **OWNED** |
| Blueprint / Platform Blueprint / blueprint catalog | EC2-EPIC-006-BLUEPRINT-CATALOG-IMPLEMENTATION | `06-IMPLEMENTATION/` | **OWNED** |
| Universal compiler / composition engine | UCOS-Ω∞-UNIVERSAL-COMPILER | `06-IMPLEMENTATION/` | **OWNED** |
| Universe model / foundation | S2-03-UNIVERSE-FOUNDATION-BINDING; ARCH-001 universe capabilities (112) | `00-CEP/`; ARCH family | **OWNED** |
| Registry federation / registry-first | S2-02-REGISTRY-FEDERATION-ARCHITECTURE; UCOS-Ω∞-REGISTRY-PLATFORM | `00-CEP/`; `06-IMPLEMENTATION/` | **OWNED** |
| Canonical registries (artifact/page/graph/cert/lineage/volume) | `00-BOOK/REGISTRIES/*` | `00-BOOK/REGISTRIES/` | **OWNED** |
| Registry as institutional memory / lineage | UMB-010 LINEAGE-ARCHITECTURE; UMB-008 CHANGE-ARCHITECTURE; UCI-001 | `00-BOOK/MASTER-BOOK/`; `00-BOOK/CONTROL-TOWER/` | **OWNED** |
| Context Assimilation Gate | USIS-WAVE1 context-assimilation framework (`*-CONTEXT-ASSIMILATION.md`) | `00-MASTER/UCOS-USIS-WAVE1/` | **OWNED** |
| Canonical Ownership model / Knowledge Once | RA-003 KNOWLEDGE-ONCE-CERTIFICATION; closure engine; CEP-001 | `00-MASTER/RA-003/`; `00-CEP/` | **OWNED** |
| Meta-ontology / meta-model substrate | METACLASS family (91, IMPLEMENTED) | closure.json / corpus | **OWNED** |
| Ontology / taxonomy | per-family `*-003`/`*-004`; ONTOLOGY-REGISTER; ONTOLOGY-PLATFORM | family zones; `01-WORKING/`; `06-IMPLEMENTATION/` | **OWNED** |
| Certification gate (EC-3) | CEP-005 + CERTIFICATION-REGISTRY | `00-CEP/`; `00-BOOK/REGISTRIES/` | **OWNED** |
| Freeze | CEP-007 CONSTITUTIONAL-FREEZE-CONSTITUTION + Freeze Registry | `00-CEP/` | **OWNED** |
| Evolution / amendment / extension | CEP-009 AMENDMENT-EVOLUTION-CONSTITUTION | `00-CEP/` | **OWNED** (extended by ADDENDUM B — see §2 addendum 2026-07-31) |
| Implementation sequence / manifest / execution control | IMG-001; IEC-001; IMP-000 master plan; 09-IMPLEMENTATION-SEQUENCE-DETERMINATION | repo root; `00-MASTER/` | **OWNED** |
| Application factory | UCOS-Ω∞-APPLICATION-FACTORY | `06-IMPLEMENTATION/` | **OWNED** |
| **Meta-Platform (as named concept)** | *(conceptual: PLATFORM-005 meta-model + METACLASS)* — no named owner | — | **CONCEPTUAL / UNNAMED** |
| **Platform Builder (as named concept)** | *(conceptual: PLATFORM-010 composition + APPLICATION-FACTORY + engine factories)* — no named owner | — | **CONCEPTUAL / UNNAMED** |
| **Constitutional Reuse Gate** | *(nascent: 1 file; related to CEP + Context Assimilation Gate)* | — | **WEAK / TO FORMALIZE** |
| **Nucleus model** | *(none)* | — | **UNOWNED (genuine gap)** |
| **Nucleus ↔ Universe ownership** | *(Universe owned; Nucleus unowned)* | — | **PARTIAL (binding needed)** |
| Constitutional decision assimilation (lifecycle · disposition · evidence gate) | CEP-002 **Article 28** (added by CEP-002-AMD-002); machine-readable overlay + engine at UCDA-000001 | `00-CEP/`; `00-MASTER/UCDA-000001/` | **OWNED** |
| Decision register (constitutional) | UCOS-Ω∞-CONSTITUTIONAL-DECISION-REGISTER; UCOS-Ω∞-CONSTITUTIONAL-ADJUDICATION-RECORD | `02-MASTER/` | **OWNED** |
| Decision record set (architectural/technology) | `adr/` (ADR-NNNN, template `adr/0000-template.md`) | `adr/` | **OWNED** |
| Decision index (operational memory) | MCP-004-MASTER-DECISIONS (append-only index, AUTHORITY = NONE) | `00-MASTER/` | **OWNED** |
| Canonical decision store (machine-readable) | `knowledge/decisions.json` (UKDA-DEC family, UKB per CMG-DLG-17) | `knowledge/` | **OWNED** |

> **Addendum (2026-07-26, CDAF-001).** Three rows above are superseded by Repository Truth and are retained for lineage: the **Nucleus model** is no longer unowned — it is canonicalized at `00-MASTER/UCOS-NUCLEUS-001/02-NUCLEUS-CONSTITUTIONAL-MODEL.md` and registered in `00-CMG/CMG-REGISTRY.json` as `NUCLEUS-001-02`; the **Nucleus ↔ Universe ownership** binding exists at `00-MASTER/UCOS-NUCLEUS-001/03-CANONICAL-NUCLEI-CATALOG-AND-OWNERSHIP.md` + `05-PLATFORM-CONFIG-AND-UNIVERSE-COMPOSITION.md`; the **Constitutional Reuse Gate** remains TO FORMALIZE and is now a registered work package (`WP-UCDA-005`) rather than an open note. Each of these is a dispositioned decision in `00-MASTER/UCDA-000001/ucda-decisions.json` (`DEC-ADAM-03`, `DEC-ADAM-05`, `DEC-ADAM-10`), and the parallel-gate alternative is recorded as REJECTED WITH CONSTITUTIONAL JUSTIFICATION (`DEC-ADAM-10R`).

> **Addendum (2026-07-31, `UCEF-000001` / `CEP-009-AMD-001`).** The row *Evolution / amendment / extension → `CEP-009`* is **unchanged and reaffirmed**; no owner is added, moved, or split. What is recorded here is that `CEP-009` has been **EXTENDED**, not replaced: the concern *"the canonical lifecycle by which any future constitutional construct is introduced, and the acceptance properties it must satisfy"* lay within `CEP-009`'s declared scope (Art II.1) and was unaddressed there, so it was dispositioned **EXTEND** under `00-CMG/CMG-000001` LXXVII.2(b) and legislated as `CEP-009` **ADDENDUM B** (version 1.0 → 1.1; `00-CMG/CMG-REGISTRY.json` updated in the same change per `CMG-000001` XLIII.2(f)). **CREATE was rejected:** `CMG-000001` Articles LXXVI–LXXVII already own construct admission and `CMG-GAP-09` is recorded **CLOSED** by them, so a second admission mechanism would breach `CMG-INV-02` (no parallel authority) and `CMG-L-14` (no parallel machinery). ADDENDUM B creates **no authority, no registry, no lifecycle and no namespace** (`CMG-000001` XLI.5) — each of its fifteen lifecycle stages and sixteen acceptance properties binds to an owner already named in this matrix. The executable measurement is `00-MASTER/UCEF-000001/` (`AUTHORITY = NONE — DERIVED TRUTH`, gate `make ucef-gate`), which asserts nothing and holds no authority over constitutional content (`CEP-009` Art XVI.5).

---

## 3. Ownership integrity checks

| Check | Result | Evidence |
|---|---|---|
| Single canonical ownership (no dual owners) | **PASS** | `duplicate_canonical_homes = 0`; each concept above maps to one owner |
| No overlapping ownership among existing owners | **PASS** | zones are role-partitioned (constitution vs registry vs catalog vs platform) |
| No orphan ownership | **PASS** | `orphan_concepts = 0` for all 431 concepts |
| Unowned concepts identified | **3** | Nucleus model; (Meta-Platform, Platform Builder = unnamed but conceptually owned) |

---

## 4. Ownership determination

- **OWNED (reuse target exists):** the large majority of decision domains map cleanly to a single existing canonical owner.
- **CONCEPTUAL / UNNAMED:** Meta-Platform and Platform Builder are new *names* for capabilities whose canonical owner already exists (platform meta-model / composition). They must be assimilated by **EXTEND/REFERENCE** into those owners — **not** by creating parallel artifacts (duplication risk).
- **UNOWNED:** the **Nucleus model** has no canonical owner and is the one genuine candidate for a NEW artifact (or EXTEND of FOUNDATION/Universe if it proves to be a renaming). The **Nucleus↔Universe ownership binding** follows once Nucleus is canonicalized.
- **WEAK:** the **Constitutional Reuse Gate** should be formalized by EXTEND of the existing Context Assimilation Gate / CEP reuse principles rather than a new parallel gate.

Per-decision method is specified in `03-ARCHITECTURAL-DECISION-ASSIMILATION-MATRIX.md`.

Per-decision **constitutional disposition** is specified in `00-MASTER/UCDA-000001/ucda-decisions.json` and rendered at `00-MASTER/UCDA-000001/01-CONSTITUTIONAL-DECISION-REGISTER.md`, under `00-CEP/CEP-002` Article 28. Ownership without a disposition is incomplete: an owned concept whose decision is undispositioned closes the Implementation Evidence Gate (Art 28.14, 28.18).

---
*End of 02-CANONICAL-OWNERSHIP-MATRIX.md*
