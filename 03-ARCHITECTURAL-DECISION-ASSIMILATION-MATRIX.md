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

## 6. Constitutional Architecture Evolution Mission — mandate rows (added 2026-07-29, CAEM-001)

A second architectural mandate was issued after §2 was closed: the **Constitutional Architecture Evolution Mission**, requiring ten "Universal Fabrics", a "Universal Constitutional Asset" blueprint, a "Universal Idea Box", an "Operational Ecosystem Model" and a refactor of "MCOS", under the rules *zero loss · zero duplication · zero regression · zero hard-coding* and the explicit prohibitions **DO NOT create parallel architecture** and **DO NOT duplicate concepts**.

Its Phase-0 assimilation and Phase-1 gap analysis are recorded at `00-MASTER/CAEM-001/` (AUTHORITY = NONE, DERIVED TRUTH). This section is where those decisions are **registered**, so that each one has a located register entry and can be dispositioned by the overlay at `00-MASTER/UCDA-000001/ucda-decisions.json` under CEP-002 Article 28. No decision originates in the overlay.

The vocabulary finding governs every row: the token `Fabric` has **zero** occurrences across the tracked corpus, `MCOS` has **zero**, `Universal Constitutional Asset`/`UCA-` have zero. **These are new labels, not new concepts.** Twelve of the thirteen mandated concepts resolve onto an existing canonical owner; one — the Universal Idea Box — is the only unowned concept in the mandate.

| Register id | Mandated concept | Canonical owner (located) | Method | Standing at this baseline |
|---|---|---|---|---|
| `DEC-CAEM-01` | Universal Idea Box — one immutable intake for every idea, observation, bug, question, proposal, feedback, AI suggestion; **no direct routing, no premature classification** | *(none — the only unowned concept)* | **NEW** additive surface | absent; existing intake is classified-on-entry, the inverse of the mandate |
| `DEC-CAEM-02` | Universal Analysis Fabric — 25 named analyses, extensible | `platform/validation_intelligence/analyzers.py` (7 open dimensions) + 3 further located analysis owners | **EXTEND** by binding declaration | partial — no registry enumerates which analyses exist |
| `DEC-CAEM-03` | Universal Validation Fabric | `engine/validation/**` · `platform/universal_validation/**` · `platform/validation_intelligence/**`; completeness authority **CCE** | **REFERENCE** | present-canonical (three-tier) |
| `DEC-CAEM-04` | Universal Innovation Fabric — research → patent → publication → standards | `intelligence/research/**` · `intelligence/publication/**` · `15-UNIVERSAL-SCIENCE-INTELLIGENCE/` + fail-closed gate | **REFERENCE** | present-canonical |
| `DEC-CAEM-05` | Universal Commercial Fabric — every asset meterable and billable | `platform/commercial_intelligence/**` + `00-MASTER/UCMI-000001/` + MIP Part 13 | **EXTEND** | partial — metering/billing are specification-only |
| `DEC-CAEM-06` | Universal Context Fabric — no Earth/country/language/currency/calendar/tax/technology assumption | `engine/context/**` (12 context laws `CXL-01…CXL-12`) | **REFERENCE** | present-canonical; the mandate is already stated in law |
| `DEC-CAEM-07` | Universal Registry Fabric — everything registered | MIP Part 7 · `REG-AUTO-001` · `00-BOOK/tools/` · `engine/registry/**` | **REFERENCE** | present-canonical; a second registry is prohibited |
| `DEC-CAEM-08` | Universal Knowledge Fabric — Knowledge Once, single canonical source, graphs | `00-BOOK/UCOS-BOOK-000000` · `UCKO-PRIN-0001` · `engine/graph/**` | **REFERENCE** | present-canonical; restating Knowledge Once elsewhere would itself breach it |
| `DEC-CAEM-09` | Universal Evolution Fabric | `00-MASTER/UEI-000001/` · `00-MASTER/UCCEP-000000/` · `00-CEP/CEP-009` | **REFERENCE** | present-canonical; 15 evolution capabilities already bound |
| `DEC-CAEM-10` | Universal Digital Twin — twin of ideas, analysis, validation, innovation, commercialisation as well as corpus | `00-BOOK/DATA/twin.json` · `00-BOOK/tools/ukbx.py` · `UMB-017` | **EXTEND, do not recreate** (`adr/0002` DELIVERABLE 10) | partial — narrow subject set, largely fixture-fed |
| `DEC-CAEM-11` | Universal Constitutional Asset — one blueprint every asset inherits (31 facets) | design half = MIP Cross-Cutting Capability Contract; lifecycle half = `UCIC-001` | **COMPOSE** (pointer-only index) | partial — coverage exists, consolidated statement does not |
| `DEC-CAEM-12` | Operational Ecosystem Model — unlimited operational ecosystems, no hard-coded business domain | MIP Part 43 `LAW P43-001/002` · `platform/generation/**` | **EXTEND** (registry content, not a new family) | law present, runtime absent; **zero hard-coded verticals verified** |
| `DEC-CAEM-13` | "MCOS" → refactor into a Universal Engineering Civilization | `00-MASTER/MCS-000` + `MCP-001…007` | **RESOLVE NAME** | `MCOS` does not exist; it resolves to MCS |
| `DEC-CAEM-14` | Validation must produce confidence, assumptions, alternatives, human-review record and continuous revalidation | `UCIC-001` Output 5 (Universal Evidence Model) | **EXTEND** via `CEP-009` | partial — five products unmodelled; confidence needs a constitutional clarification first |
| `DEC-CAEM-15` | Hard-code no business domain, technology, currency, calendar or geography | MIP Part 43 `LAW P43-001` · `engine/context/constitution.py` `CXL-02` | **REFERENCE** | the central prohibition is satisfied for business domains |
| `DEC-CAEM-16` | The verified live hard-codings must be dispositioned, not patched | `UCOS-ACFV-000001` finding register | **EXTEND** the finding register | open — all sit inside frozen/certified zones |
| `DEC-CAEM-17` | The program control plane must be reconciled to the measured baseline before any successor plans against it | `00-MASTER/MCP-002` under `MCP-007` §04.B | **EXTEND** (operator act) | open — control plane materially stale |
| `DEC-CAEM-18` | The registration-schema namespace ceiling must be dispositioned — amended or formally deferred — and schema validation wired so it cannot regress silently | `00-BOOK/SCHEMAS/artifact.schema.json` + `00-BOOK/tools/ukb.py`; wiring half already owned by `UCCEP-F-006` / `WP-UCCEP-004` | **EXTEND** via `CEP-009` or defer under `CEP-002` Art 27 | open — the sole blocking failure of the aggregate constitutional gate |

### 6.1 Rejected alternatives (recorded so they cannot be silently revived)

| Register id | Rejected alternative | Constitutional basis |
|---|---|---|
| `DEC-CAEM-00R` | Build the mandated concepts as ten **new** "Universal Fabrics" | §4 Zero Parallel Architecture · `CEP-001` VII.2 · `AEOS-001` deny-list (no second sequencer, completeness engine, capability-state authority, ledger or determinism engine) · `CMG-000001` `CMG-INV-02` (one concern, one owner) · `UCCEP-000006-AUTH-001` **K-07** |
| `DEC-CAEM-13R` | Refactor MCS/"MCOS" to hold the seventeen Engineering Constitution/Governance/Intelligence/Validation/Certification/Evolution/Self-* roles | `MCP-001` §02 (authority hierarchy) and §06 (*no duplicate authority — MCS holds none*); MCS declares `AUTHORITY = NONE` by constitution, so vesting authority in it is an architectural regression |
| `DEC-CAEM-11R` | Author a **third** normative blueprint stating the union of the 31 UCA facets | `UCKO-PRIN-0001` Knowledge Once · `CMG-INV-02` — the union must be a pointer index over the two located owners, not a new normative instrument |

**Method distribution for §6:** REFERENCE 6 · EXTEND 7 · COMPOSE 1 · RESOLVE-NAME 1 · NEW 1 · REJECTED 3. **NEW is confined to the Universal Idea Box.**

---

## 7. Coverage completeness — similarity is not sufficient (added 2026-07-29, FAAC)

§2 and §6 determine each decision's **integration method**, and CEP-002 Article 28.13 determines its **disposition**. Neither, by itself, proves that a decision recorded as *represented by an existing canonical capability* is in fact **fully** represented. A mapping asserted on resemblance alone would let a partially covered decision be closed as complete — the exact failure mode this matrix exists to prevent.

The following rule is therefore registered here and mechanised in the located overlay:

> **CR-1.** A decision may be dispositioned **REPRESENTED BY AN EXISTING CANONICAL CAPABILITY** (`CEP-002` Art 28.13(b)) only where the located owner demonstrably provides **complete** coverage across five dimensions of equivalence: **functional**, **architectural**, **governance**, **lifecycle** and **extensibility**. Where any dimension is unevidenced, the decision is *partially represented*: 28.13(b) is unavailable and the honest disposition is **REGISTERED AS AN IMPLEMENTATION WORK PACKAGE** (28.13(c)) against the named shortfall.

CR-1 introduces no sixth disposition, no second decision register, no new gate apparatus and no new authority. It is an evidence obligation on a disposition the governing Article already closes, measured by the engine that already computes that Article's verdict. Per-dimension evidence is declared as DATA at `00-MASTER/UCDA-000001/ucda-decisions.json` and the measurement is regenerated at `00-MASTER/UCDA-000001/07-ARCHITECTURAL-COVERAGE-MATRIX.md`; a coverage claim that does not resolve against the repository aborts the run fail-closed.

| Register id | Decision |
|---|---|
| `DEC-FAAC-01` | Similarity is not sufficient: 28.13(b) requires proven functional, architectural, governance, lifecycle and extensibility equivalence (**CR-1**) |
| `DEC-FAAC-02` | The Final Architectural Coverage Matrix is a **regenerated determination of the located decision-assimilation owner**, computed from Repository Truth |
| `DEC-FAAC-03R` | *(rejected)* Create a new programme, register or authority to hold the coverage matrix — `CEP-002` Art 28.3 · `CEP-001` VII.2 · `CMG-INV-02` |

---
*End of 03-ARCHITECTURAL-DECISION-ASSIMILATION-MATRIX.md*
