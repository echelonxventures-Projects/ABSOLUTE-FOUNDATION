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
| Evolution / amendment / extension | CEP-009 AMENDMENT-EVOLUTION-CONSTITUTION | `00-CEP/` | **OWNED** |
| Implementation sequence / manifest / execution control | IMG-001; IEC-001; IMP-000 master plan; 09-IMPLEMENTATION-SEQUENCE-DETERMINATION | repo root; `00-MASTER/` | **OWNED** |
| Application factory | UCOS-Ω∞-APPLICATION-FACTORY | `06-IMPLEMENTATION/` | **OWNED** |
| **Meta-Platform (as named concept)** | *(conceptual: PLATFORM-005 meta-model + METACLASS)* — no named owner | — | **CONCEPTUAL / UNNAMED** |
| **Platform Builder (as named concept)** | *(conceptual: PLATFORM-010 composition + APPLICATION-FACTORY + engine factories)* — no named owner | — | **CONCEPTUAL / UNNAMED** |
| **Constitutional Reuse Gate** | *(nascent: 1 file; related to CEP + Context Assimilation Gate)* | — | **WEAK / TO FORMALIZE** |
| **Nucleus model** | *(none)* | — | **UNOWNED (genuine gap)** |
| **Nucleus ↔ Universe ownership** | *(Universe owned; Nucleus unowned)* | — | **PARTIAL (binding needed)** |

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

---
*End of 02-CANONICAL-OWNERSHIP-MATRIX.md*
