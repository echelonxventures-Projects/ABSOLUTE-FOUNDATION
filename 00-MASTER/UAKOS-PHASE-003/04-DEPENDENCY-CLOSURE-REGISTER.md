# 04 — Dependency Closure Register

> PROGRAM **UAKOS PHASE-003** — Constitutional Implementation Gap Determination · baseline `57d91b7` (branch `governance-reconciliation`) · consumes FREEZE A (certified knowledge) + FREEZE B (Phase-002 implementation baseline) · AUTHORITY = **NONE (DERIVED / EVIDENCE-BASED)** · **READ-ONLY** · generated `2026-07-23T06:15:02Z` by `phase3_gap.py`.
>
> Dependency closure over the authoritative knowledge dependency graph (relationships.json). Concept-level dependency satisfaction is grounded in certified traceability rootedness (orphans=0).
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-003/phase3_gap.py`.

- Dependency graph nodes: **995** · edges: **11822**
- Depends-On edges: **4588** · nodes with dependencies: **258**

| Dependency dimension | Value |
|---|---|
| Satisfied dependencies (edge target present) | 11822 |
| Unsatisfied / missing dependency targets | 0 |
| Blocked dependencies | 0 |
| Circular dependency nodes (Depends-On cycles) | 3 |
| Invalid dependencies (type outside schema) | 0 |
| Dependency closure status | CLOSED |

### Edge type counts

| Edge type | Count |
|---|---|
| Depends-On | 4588 |
| Required-By | 4510 |
| Parent | 994 |
| Child | 994 |
| Consumes | 316 |
| Consumed-By | 316 |
| Authorized-By | 34 |
| Authorizes | 34 |
| Implements | 8 |
| Implemented-By | 8 |
| Traces-To | 5 |
| Traced-From | 5 |
| Evolves-From | 5 |
| Evolves-From-Inverse | 5 |

### Concept-level dependency evidence

The 431 certified concept ids are disjoint from the 995-node knowledge-artifact graph (separate id space). Concept-level dependency satisfaction is therefore evidenced by certified traceability rootedness: orphan concepts = **0**, in-repo-unhomed = **0**, not-homed = **0** → every concept's dependency chain is rooted (no unsatisfied concept-level dependency).
