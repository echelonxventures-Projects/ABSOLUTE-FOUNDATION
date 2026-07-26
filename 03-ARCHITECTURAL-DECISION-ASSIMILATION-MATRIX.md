# 03 — ARCHITECTURAL DECISION ASSIMILATION MATRIX

> **Mission:** Context Assimilation · **Baseline:** `ab78f35` · **Branch:** governance-reconciliation · **Date:** 2026-07-23
> **Mode:** READ-ONLY. No modification, no implementation, no commits, no tags, no push.
> **Authority:** Repository Truth is ABSOLUTE. Reuse First · Registry First · Composition First. NEW only where no canonical owner exists.

---

## 1. Integration-method legend

| Method | Meaning |
|---|---|
| **REUSE** | decision already fully captured by an existing owner; reference as-is |
| **EXTEND** | decision adds detail to an existing owner; append a section, no new artifact |
| **MERGE** | decision reconciles content across ≥2 existing owners into one owner |
| **REFERENCE** | decision is a cross-cutting binding; add a typed reference/link |
| **NEW** | no canonical owner exists; a new canonical artifact is constitutionally permitted |

---

## 2. Canonical Integration Matrix

Columns: Decision · Canonical Owner · Existing Artifact · Method · Repository Location · Reason · Dependency · Validation Status · Duplication Risk · Overlap Risk · Rework Risk.

| Decision | Canonical Owner | Existing Artifact | Method | Location | Reason | Dependency | Validation | Dup Risk | Overlap Risk | Rework Risk |
|---|---|---|---|---|---|---|---|---|---|---|
| Meta-Platform architecture | Platform meta-model | PLATFORM-005-UNIVERSAL-PLATFORM-META-MODEL | **EXTEND** | `09-PLATFORM/` | meta-layer over platform already owned by platform meta-model + METACLASS | METACLASS; PLATFORM-001 | pending integration | **HIGH if NEW** → LOW via EXTEND | Medium | Low |
| Platform Builder architecture | Platform composition + factory | PLATFORM-010-COMPOSITION-ARCHITECTURE; UCOS-Ω∞-APPLICATION-FACTORY | **EXTEND/REFERENCE** | `09-PLATFORM/`, `06-IMPLEMENTATION/` | "builder" = composition/factory capability already owned | PLATFORM-010; engine factories | pending | **HIGH if NEW** → Low via EXTEND | Medium | Low |
| Nucleus model | *(none)* | — | **NEW** (or EXTEND FOUNDATION if rename) | *(new; candidate `06-IMPLEMENTATION/` or ARCH)* | no canonical owner exists (0 repo matches) | Universe (S2-03); FOUNDATION (IMP-001) | **UNVALIDATED** | Low (unowned) | Medium (vs FOUNDATION/Universe) | Medium |
| Universe model | Universe foundation | S2-03-UNIVERSE-FOUNDATION-BINDING; ARCH-001 (112) | **REUSE** | `00-CEP/`; ARCH | universe fully owned & bound | — | validated (bound) | None | None | None |
| Nucleus ↔ Universe ownership | Universe (owned) + Nucleus (unowned) | S2-03 + (Nucleus NEW) | **NEW binding** (after Nucleus) | *(new ownership binding)* | binding cannot exist until Nucleus canonicalized | Nucleus model | **UNVALIDATED** | Low | Medium | Medium |
| Blueprint-driven platform composition | Blueprint catalog + platform composition | EC2-EPIC-006-BLUEPRINT-CATALOG; PLATFORM-010 | **EXTEND** | `06-IMPLEMENTATION/`, `09-PLATFORM/` | blueprint + composition both owned | PLATFORM-010 | validated | Low | Low | Low |
| Foundation composition | Foundation architecture | IMP-001-FOUNDATION-ARCHITECTURE; PLATFORM-010 | **REUSE/EXTEND** | `06-IMPLEMENTATION/` | foundation composition owned | — | validated | None | Low | None |
| Registry-first implementation | Registry federation + platform | S2-02-REGISTRY-FEDERATION; UCOS-Ω∞-REGISTRY-PLATFORM | **REUSE** | `00-CEP/`, `06-IMPLEMENTATION/` | registry-first already legislated | — | validated | None | None | None |
| Context Assimilation Gate | USIS assimilation framework | UCOS-USIS-WAVE1 `*-CONTEXT-ASSIMILATION.md` | **REUSE/EXTEND** | `00-MASTER/UCOS-USIS-WAVE1/` | gate concept owned (~20 files) | — | validated | Low | Low | Low |
| Constitutional Reuse Gate | Context Assimilation Gate + CEP reuse | USIS assimilation + CEP-001/005 | **EXTEND** | `00-MASTER/UCOS-USIS-WAVE1/`, `00-CEP/` | formalize as facet of existing gate, not a parallel gate | Context Assimilation Gate | pending | **HIGH if NEW** → Low via EXTEND | Medium | Low |
| Canonical Ownership model | Knowledge-Once / RA | RA-003-KNOWLEDGE-ONCE-CERTIFICATION; CEP-001 | **REUSE** | `00-MASTER/RA-003/`, `00-CEP/` | ownership model owned | — | validated | None | None | None |
| Platform Blueprint | Blueprint catalog | EC2-EPIC-006-BLUEPRINT-CATALOG | **REUSE** | `06-IMPLEMENTATION/` | blueprint owned | — | validated | Low | Low | Low |
| Registry as institutional memory | Master-book lineage + registries | UMB-010 LINEAGE; UMB-008 CHANGE; UCI-001; `00-BOOK/REGISTRIES/` | **REUSE** | `00-BOOK/` | institutional-memory role owned | — | validated | None | Low | None |
| Declarative composition | Platform composition + compiler | PLATFORM-010; UCOS-Ω∞-UNIVERSAL-COMPILER | **EXTEND** | `09-PLATFORM/`, `06-IMPLEMENTATION/` | declarative model = facet of composition | compiler | pending | Low | Low | Low |
| Universal composition architecture | Platform composition | PLATFORM-010-UNIVERSAL-PLATFORM-COMPOSITION-ARCHITECTURE | **REUSE** | `09-PLATFORM/` | exact owner exists by name | — | validated | None | None | None |
| Implementation sequence refinement | Manifest + controller + master plan | IMG-001; IEC-001; IMP-000; 09-IMPLEMENTATION-SEQUENCE-DETERMINATION | **EXTEND** | repo root; `00-MASTER/` | sequence owned; refinement appends | IMG-001; IEC-001 | pending | Low | Low | Low |

---

## 3. Method distribution

| Method | Count | Decisions |
|---|---|---|
| REUSE | 6 | Universe, Registry-first, Canonical Ownership, Platform Blueprint, Registry-as-memory, Universal composition |
| EXTEND | 6 | Meta-Platform, Blueprint-driven composition, Foundation composition, Constitutional Reuse Gate, Declarative composition, Implementation sequence |
| EXTEND/REFERENCE | 1 | Platform Builder |
| REUSE/EXTEND | 1 | Context Assimilation Gate |
| **NEW** | **2** | **Nucleus model; Nucleus↔Universe ownership binding** |

**NEW is confined to the Nucleus (and its ownership binding) — the only unowned concept.** Every other decision reuses or extends an existing canonical owner. No parallel architecture is created.

---

## 4. Constitutional-rule conformance (per decision)

| Rule | Conformance |
|---|---|
| Reuse First | ✔ — 14 of 16 decisions REUSE/EXTEND existing owners |
| Registry First | ✔ — registry owners reused, not duplicated |
| Composition First | ✔ — composition routed to PLATFORM-010/compiler |
| Zero Duplication | ✔ *by plan* — NEW confined to unowned Nucleus; EXTEND used where owner exists |
| Single Canonical Ownership | ✔ — each decision maps to exactly one owner |
| Zero Parallel Architecture | ✔ — Meta-Platform/Platform-Builder EXTEND platform owners, not fork them |

---

## 5. Constitutional binding — decision disposition (added 2026-07-26, CDAF-001)

This matrix determines the **integration method** for each decision. It does not, by itself, determine each decision's **constitutional disposition**, nor does it block successor work while a decision is left undetermined. Both obligations are now legislated at `00-CEP/CEP-002` **Article 28** (added by **CEP-002-AMD-002**), and every row of §2 is dispositioned in the machine-readable overlay `00-MASTER/UCDA-000001/ucda-decisions.json`.

| Matrix row (§2 decision) | Register id | Disposition (CEP-002 Art 28.13) | Carried by |
|---|---|---|---|
| Meta-Platform architecture | `DEC-ADAM-01` | REGISTERED AS AN IMPLEMENTATION WORK PACKAGE | `WP-UCDA-003` |
| Platform Builder architecture | `DEC-ADAM-02` | REGISTERED AS AN IMPLEMENTATION WORK PACKAGE | `WP-UCDA-004` |
| Nucleus model | `DEC-ADAM-03` | IMPLEMENTED | `00-MASTER/UCOS-NUCLEUS-001/02-NUCLEUS-CONSTITUTIONAL-MODEL.md` |
| Universe model | `DEC-ADAM-04` | REPRESENTED BY AN EXISTING CANONICAL CAPABILITY | `00-CEP/STAGE-02-S2-03-UNIVERSE-FOUNDATION-BINDING.md` |
| Nucleus ↔ Universe ownership | `DEC-ADAM-05` | IMPLEMENTED | `00-MASTER/UCOS-NUCLEUS-001/03…`, `05…` |
| Blueprint-driven platform composition | `DEC-ADAM-06` | REPRESENTED BY AN EXISTING CANONICAL CAPABILITY | blueprint catalog |
| Foundation composition | `DEC-ADAM-07` | REPRESENTED BY AN EXISTING CANONICAL CAPABILITY | foundation architecture |
| Registry-first implementation | `DEC-ADAM-08` | REPRESENTED BY AN EXISTING CANONICAL CAPABILITY | registry federation |
| Context Assimilation Gate | `DEC-ADAM-09` | REPRESENTED BY AN EXISTING CANONICAL CAPABILITY | USIS-WAVE1 assimilation |
| Constitutional Reuse Gate (as a facet) | `DEC-ADAM-10` | REGISTERED AS AN IMPLEMENTATION WORK PACKAGE | `WP-UCDA-005` |
| Constitutional Reuse Gate **as a NEW parallel gate** | `DEC-ADAM-10R` | **REJECTED WITH CONSTITUTIONAL JUSTIFICATION** | CEP-002 8.3 · CEP-001 VII.2 · §4 Zero Parallel Architecture |
| Canonical Ownership model | `DEC-ADAM-11` | REPRESENTED BY AN EXISTING CANONICAL CAPABILITY | RA-003 canonical ownership |
| Platform Blueprint | `DEC-ADAM-12` | REPRESENTED BY AN EXISTING CANONICAL CAPABILITY | blueprint catalog constitution |
| Registry as institutional memory | `DEC-ADAM-13` | REPRESENTED BY AN EXISTING CANONICAL CAPABILITY | master knowledge book + ledgers |
| Declarative composition | `DEC-ADAM-14` | REGISTERED AS AN IMPLEMENTATION WORK PACKAGE | `WP-UCDA-006` |
| Universal composition architecture | `DEC-ADAM-15` | REPRESENTED BY AN EXISTING CANONICAL CAPABILITY | PLATFORM-010 |
| Implementation sequence refinement | `DEC-ADAM-16` | REGISTERED AS AN IMPLEMENTATION WORK PACKAGE | `WP-UCDA-007` |

**Reconciliation of §2 against present Repository Truth.** Two rows of §2 recorded at baseline `ab78f35` are superseded by later Repository Truth: the Nucleus model, recorded there as **NEW · UNVALIDATED**, is canonicalized and registered (`DEC-ADAM-03`), and the Nucleus↔Universe ownership binding, recorded as **NEW binding · UNVALIDATED**, exists (`DEC-ADAM-05`). §2 is retained unaltered as the read-only determination it was; the current disposition of each row is the register's, and the register is regenerated from Repository Truth on every run.

**Every row marked "pending" in §2 is now a registered work package** with a named owner, a constitutional route, and an acceptance condition (`00-MASTER/UCDA-000001/05-WORK-PACKAGE-REGISTER.md`). A pending integration is therefore no longer an open note: it is a disposition. Enforcement is the **Implementation Evidence Gate** — `make ucda-gate`, and `G-14` / `CK-DECISION-EVIDENCE` of `00-MASTER/UCCEP-000000/uccep-bindings.json`.

---
*End of 03-ARCHITECTURAL-DECISION-ASSIMILATION-MATRIX.md*
