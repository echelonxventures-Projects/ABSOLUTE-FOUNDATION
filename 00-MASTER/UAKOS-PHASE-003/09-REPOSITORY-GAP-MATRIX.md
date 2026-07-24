# 09 — Repository Gap Matrix

> PROGRAM **UAKOS PHASE-003** — Constitutional Implementation Gap Determination · baseline `57d91b7` (branch `governance-reconciliation`) · consumes FREEZE A (certified knowledge) + FREEZE B (Phase-002 implementation baseline) · AUTHORITY = **NONE (DERIVED / EVIDENCE-BASED)** · **READ-ONLY** · generated `2026-07-23T06:15:02Z` by `phase3_gap.py`.
>
> Cross-tabulation of gap status against implementation status and criticality.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-003/phase3_gap.py`.

### Gap × implementation status

| Gap | Objects | By implementation status |
|---|---|---|
| NO_GAP | 245 | DEPRECATED:1; IMPLEMENTED:231; REJECTED:4; SUPERSEDED:9 |
| IMPLEMENTATION_GAP | 112 | DEFERRED:20; SCHEDULED:7; SPECIFIED:85 |
| SPECIFICATION_GAP | 28 | PARTIALLY_IMPLEMENTED:28 |
| CERTIFICATION_GAP | 46 | PARTIALLY_IMPLEMENTED:46 |

### Gap × criticality

| Gap | CRITICAL | HIGH | MEDIUM | LOW | INFORMATIONAL |
|---|---|---|---|---|---|
| NO_GAP | 0 | 0 | 0 | 0 | 245 |
| IMPLEMENTATION_GAP | 34 | 55 | 23 | 0 | 0 |
| SPECIFICATION_GAP | 0 | 8 | 20 | 0 | 0 |
| CERTIFICATION_GAP | 19 | 22 | 5 | 0 | 0 |
