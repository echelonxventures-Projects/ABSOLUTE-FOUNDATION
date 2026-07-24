# 06 — Certification Planning Register

> PROGRAM **UAKOS PHASE-004** — Constitutional Implementation Planning · baseline `57d91b7` (branch `governance-reconciliation`) · consumes FREEZE A + FREEZE B + FREEZE C · AUTHORITY = **NONE (DERIVED / PLANNING)** · **READ-ONLY** · generated `2026-07-23T06:14:29Z` by `phase4_plan.py`.
>
> Certification gates, evidence, acceptance / completion / rollback criteria per unit type.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-004/phase4_plan.py`.

### Certification gate model (reused from the Constitutional Completeness Engine)

| Gate | Evidence requirement | Applies to |
|---|---|---|
| G1 Specification-complete | spec present + traceable | SPECIFY/IMPLEMENT |
| G2 Dependency-closure | tier prerequisites satisfied | IMPLEMENT |
| G5 Traceability | provenance chain rooted | all |
| G6 Evidence | ValidationEvidence + CertificationEvidence | IMPLEMENT/CERTIFY |
| G8 Readiness | evaluate_readiness PASS | CERTIFY |

### Per-unit-type acceptance / completion / rollback

| Unit type | Acceptance criteria | Completion criteria | Rollback criteria |
|---|---|---|---|
| SPECIFY | spec authored in canonical home, origin-cited | G1+G5 pass | revert spec draft (no repo state change) |
| IMPLEMENT | code-root artifact + passing validation | G1+G2+G5+G6 pass | unit remains SPECIFIED; no partial merge |
| CERTIFY | UCOS-CERT evidence token issued | G5+G6+G8 pass | revert to PARTIALLY_IMPLEMENTED; evidence quarantined |

Certification units in plan (WAITING_CERTIFICATION): **46**.
