# MCP-004 — MASTER DECISIONS (UCOS Ω∞)

| Field | Value |
|-------|-------|
| ARTIFACT ID | MCP-004 |
| ARTIFACT | Master Decisions — Architectural & Program Decision Index of UCOS Ω∞ |
| CLASSIFICATION | MCS COMPONENT 4 — decision register index; append-only |
| STATUS | ACTIVE · LIVING |
| AUTHORITY | **NONE — DERIVED TRUTH.** MCS **indexes** decisions held in their authoritative registers; it authors none. |
| ANSWERS | *Why is it this way — what was decided, why, and is it still in force?* |
| PART OF | Master Context System (`00-MASTER/`), governed by `MCS-000` |
| BASELINE | 2026-07-18 · branch `governance-reconciliation` · HEAD `5874ede` |
| CONFLICT RULE | Where any statement conflicts with a higher frozen or governing instrument, the higher instrument governs. |

> **Scope.** MCP-004 is an **index** of ratified/recorded decisions, each pointing to its authoritative register. *Never revisit a recorded decision unless a defect is proven* (the only backward transition is a defect-driven REOPEN — `MCS-000 §05`). New decisions are appended to their authoritative register **first**, then indexed here.

**Authoritative registers indexed by this component:**
- Constitutional: `02-MASTER/UCOS-Ω∞-CONSTITUTIONAL-DECISION-REGISTER.md`
- Implementation/technology: `adr/` (e.g. `adr/0001-foundation-technology-stack.md`)
- Program/governance/EC: `02-MASTER/UCOS-GOV-00N-*`, `02-MASTER/EC-3-*`, `02-MASTER/EC2-*`, Program Tracker §6

---

## SECTION 01 — CONSTITUTIONAL DECISIONS (source: Constitutional Decision Register)

| ID | Title | Decision (summary) | Status | Supersedes |
|----|-------|--------------------|--------|-----------|
| DR-RAT-01 | Status of BEING | BEING is axiom-only (non-layer); layered ontology begins at EXISTENCE | ADJUDICATED (non-final) | — |
| DR-RAT-02 | Root ontology arity | 4-primitive root (EXISTENCE→RELATIONSHIP→TRANSFORMATION beneath BEING axiom) | ADJUDICATED (non-final) | 5-primitive variant (SUP-07) |
| DR-RAT-03 | SPACE-TIME placement | SPACE-TIME is a coordinate axis; root law Ω-LAW-02 retired-as-root | ADJUDICATED (non-final) | — |
| DR-RAT-04 | Canonical invariant set | Layered coexistence (INV02 ordering / INV01 concurring / INV03 integrity) | ADJUDICATED (non-final; residual ordering open) | — |
| DR-RAT-05 | Sovereignty origin | Two-level: invariants *constrain* sovereignty; sovereignty *sources* authority | ADJUDICATED (non-final) | — |
| DR-RAT-06 | Authority-stack model | Flow model (AUTH-08) canonical; SRC-08 layered stack advisory-subordinate | ADJUDICATED (non-final) | — |
| DR-RAT-07 | Evolution gate | Tiered: routine→governance; structural→ratification | ADJUDICATED (non-final) | — |
| DR-RAT-08 | Canonical law-ID scheme | `LAW Ω∞` canonical + concordance for legacy schemes | ADJUDICATED (non-final) | — |
| DR-RAT-09 | `LAW Ω∞` namespace collision | Renumber SRC-07 15-law set out of `LAW Ω∞` (alias) | ADJUDICATED (non-final) | — |
| DR-RAT-10 | Domain/family namespacing | DOMAIN-tag commerce (`LAW-COMM`); family prefixes as sub-namespaces | ADJUDICATED (non-final) | — |
| **DR-RAT-11** | **Document supremacy + ratification authority (KEYSTONE)** | SRC-02 senior *pro tempore*; ratification body must be constituted out-of-corpus | **BLOCKED** | — |

> **Keystone note.** All ten ADJUDICATED decisions are **non-final** and cannot advance to ratification while DR-RAT-11 is BLOCKED. Closing RAT-11 requires an out-of-corpus stakeholder act (constitute a ratification body: membership, quorum, amendment procedure). This is the single largest gate to constitutional finality and is **outside** engineering/CIOA authority. Tracked as MEP-09 (MCP-003) and blocker B-RAT-11 (MCP-002).

---

## SECTION 02 — IMPLEMENTATION & PROGRAM DECISIONS (source: `adr/`, Program Tracker §6, EC/GOV determinations)

| ID | Title | Decision | Status |
|----|-------|----------|--------|
| ADR-0001 | Foundation technology stack | Baseline stack for EC-1/EC-2 realization (`adr/0001-foundation-technology-stack.md`) | ACTIVE |
| IMPDEC-001 | Governance-before-implementation | Establish IMP-000 foundation before any implementation artifact | RECORDED |
| IMPDEC-002 | Provisional encoding | Encode constitutional positions as provisional/versioned, never hard-coded | RECORDED |
| IMPDEC-003 | Dependency sequencing | Sequence per MIP §6 dependency model; IMP-009/010/011 parallel | RECORDED |
| IMPDEC-004 | Gates finality-only | Treat EC-1…EC-6 as finality-only, not build-blocking | RECORDED |
| IMPDEC-005 | Defer vendor choices | Defer specific vendor/framework selections to per-artifact ADRs | RECORDED |
| GOV-001…006 | Corpus authority, traceability, readiness, execution authorization, repository governance reconciliation/correction | Governance-reconciliation determinations | ACTIVE |
| EC-2 CLOSURE | EC-2 platform program closure | PROGRAM CLOSED WITH OBSERVATIONS (engineering-execution scope) | ACTIVE |
| EC-3 CHARTER / AUTH / AP-1 / AP-2 | Bands 10–13 realization lane | Lane CHARTERED → OPEN → executor designated → Band 10 ADMITTED | ACTIVE |
| MCS-DEC-001 | Master Context System establishment | Decompose monolithic MCP-001 into MCS (`00-MASTER/`, MCP-001…007); operational memory, AUTHORITY=NONE; entry path preserved | RECORDED (Mission MCP-002) |
| MCS-DEC-002 | Repository state reconciliation (UCOS-RECON-001) | Canonical repo truth = working-tree projection (436 artifacts/6,021 pages); validate+enforce PASS, 0 drift. **Decision: CANONICAL STATE ESTABLISHED WITH WARNINGS.** 4 conflicts registered (RECON-C1 `00-MASTER` mis-registered as corpus; RECON-C2 canonical projection uncommitted; RECON-C3 MCP-005 stale scale; RECON-C4 CI signals stale). See `00-MASTER/UCOS-RECON-001-REPOSITORY-STATE-RECONCILIATION.md` | RECORDED (Mission UCOS-RECON-001) |
| MCS-DEC-003 | Operational-Memory / Corpus separation (UCOS-RECON-C1) | Resolve RECON-C1: exclude `00-MASTER/` + root redirect from corpus discovery (`config.py EXCLUDE_DIR_PREFIXES`); 14 sticky IDs retained-but-retired (append-only preserved); 436→423 registered; validate+enforce PASS; idempotent. **RECON-C1 CLOSED; Repository Management FROZEN; Repository Management Foundation COMPLETE.** See `00-MASTER/UCOS-RECON-C1-OPERATIONAL-MEMORY-EXCLUSION.md` | RECORDED (Mission UCOS-RECON-C1) |
| MCS-DEC-004 | Universal Capability Implementation Contract (UCOS-EXEC-002) | Adopt `UCIC-001` as the single deterministic 15-stage lifecycle every future capability follows (gates READY_TO_IMPLEMENT→IMPLEMENTED→VALIDATED→CERTIFIED→READY_TO_COMMIT→READY_FOR_PRODUCTION); composes CIOA/CCE/GOV-002/TRACK-001; AUTHORITY=NONE. **Governance, Repository Management, and Execution Methodology FROZEN.** See `00-MASTER/UCIC-001-UNIVERSAL-CAPABILITY-IMPLEMENTATION-CONTRACT.md` | RECORDED (Mission UCOS-EXEC-002) |

---

## SECTION 03 — IMMUTABLE vs REVISABLE

| Class | Members | Rule |
|-------|---------|------|
| **Immutable (pending ratification)** | DR-RAT-01…10 once ratified | Become immutable only upon ratification (blocked by DR-RAT-11) |
| **Immutable (frozen)** | EC-2 CLOSURE scope; EC-1 certification | Frozen; changes are additive-only elsewhere |
| **Revisable by supersession** | IMPDEC-*, ADR-*, GOV-*, MCS-DEC-* | Never edited in place; superseded by a new appended entry citing the prior ID |
| **Blocked** | DR-RAT-11 | Requires out-of-corpus act; kept honestly BLOCKED |

---

## SECTION 04 — REVIEW HISTORY / SUPERSESSIONS

| Decision | Superseded / Reviewed | By | Note |
|----------|-----------------------|----|------|
| 5-primitive root variant (SUP-07) | Superseded | DR-RAT-02 | 4-primitive root adopted |
| Ω-LAW-02 as root | Retired-as-root | DR-RAT-03 | SPACE-TIME reclassified as coordinate axis |
| SRC-08 layered authority stack | Demoted to advisory-subordinate | DR-RAT-06 | AUTH-08 flow model canonical |
| SRC-07 15-law set in `LAW Ω∞` | Renumbered (alias) | DR-RAT-09 | namespace collision resolved |

*No MCS decision has yet been superseded. Append here whenever a decision is reviewed or replaced.*

---

## SECTION 05 — CHANGE LOG (MCP-004 only)

| Date | Change | Reason |
|------|--------|--------|
| 2026-07-18 | MCP-004 established as MCS component 4 (constitutional + implementation/program decision index); added MCS-DEC-001 | Mission MCP-002 decomposition (migrated from root §04) |
| 2026-07-20 | Indexed **EC3-B13-G01 = EC-3 AP-5 Band-13 (Infrastructure) admission determination** (`02-MASTER/EC-3-AP-5-BAND-13-ADMISSION-DETERMINATION.md`): governance-only (AUTHORITY = NONE) per-band admission decision — **BAND 13 ADMITTED · AP-5 SATISFIED · MEP-04 OPEN** (AP5-1…AP5-10 all PASS; the analog of AP-2/AP-3/AP-4). Recorded in its authoritative register (the determination artifact itself) + MCP-002/003/006. Non-blocking observations OBS-C (test-dir lint) + OBS-D (DR-RAT-11 finality) carried. Decision authorizes queue admission only; realization DEFERRED pending explicit authorization. | EC3-B13-G01 — MEP-04 admission (AP-5) |

| 2026-07-20 | Indexed **EC3-B13-P01 = Band-13 (Infrastructure) Master Program Charter & MEP-04 Implementation Roadmap** (`02-MASTER/EC-3-B13-P01-BAND-13-INFRASTRUCTURE-MASTER-PROGRAM-CHARTER.md`): program-governance / planning-only (AUTHORITY = NONE) decision fixing the complete MEP-04 realization execution contract — WBS over the frozen 16-leaf-meta-class inventory; recommended 12-unit concern-granularity spine (U01…U12) + construct-granularity alternative; implementation order + dependency gates; founding DAG; validation/certification(BRC-1…8+BCC-1…8)/freeze(FP-1…6+FE-1…5)/completion/transition strategies. **Key deferred decision: the exact intra-band unit granularity (concern vs construct) and the intra-band order are NOT fixed by the charter — they are CIOA-derived at UCIC-001 Stage 1–3 (CIOA-LAW-004 dependency-derived / LAW-010 sequence-not-authorization); the charter records the recommended default and the invariant construct-level founding DAG that governs correctness under any granularity.** Recorded in its authoritative register (the charter artifact itself) + MCP-002/003/006. Discharges the previously-deferred "Band-13 Program Charter" obligation. Decision plans realization only; EC3-B13-U01 realization DEFERRED pending explicit authorization. | EC3-B13-P01 — MEP-04 Master Program Charter (planning-only) |

*Append-only. Index a decision here only after it is recorded in its authoritative register.*

---

*END OF ARTIFACT — MCP-004 · MASTER DECISIONS · ACTIVE · LIVING · AUTHORITY = NONE (DERIVED TRUTH)*
