# 03 — Dependency Resolution Register

> PROGRAM **UAKOS PHASE-004** — Constitutional Implementation Planning · baseline `ab78f35` (branch `governance-reconciliation`) · consumes FREEZE A + FREEZE B + FREEZE C2 (PHASE-003R realization model) · AUTHORITY = **NONE (DERIVED / PLANNING)** · **READ-ONLY** · generated `2026-07-24T11:20:06Z` by `phase4_plan.py`.
>
> WHY the order holds: constitutional-layering dependency resolution + circular-dependency strategy.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-004/phase4_plan.py`.

### Resolution basis (disclosed)

The 431 certified concept ids are disjoint from the knowledge dependency graph (1079 nodes / 12021 edges), so unit ordering is resolved by the certified **constitutional layering**: CRITICAL (laws/foundation/governance/metaclass) resolve before HIGH (arch/platform/runtime/data/service/application/infrastructure) before MEDIUM. Within a tier, the gap lifecycle resolves specification → implementation → certification. No unit is scheduled before its tier+lifecycle prerequisites.

### Dependencies to resolve first (Wave 1)

| Unit | Knowledge object | Criticality | Type |
|---|---|---|---|
| IU-0001 | CEP-003 | CRITICAL | RATIFY |
| IU-0002 | CEP-009 | CRITICAL | RATIFY |
| IU-0003 | CEP-010 | CRITICAL | RATIFY |
| IU-0004 | GOV-007 | CRITICAL | RATIFY |
| IU-0005 | GOV-008 | CRITICAL | RATIFY |
| IU-0006 | GOV-009 | CRITICAL | RATIFY |
| IU-0007 | GOV-010 | CRITICAL | RATIFY |
| IU-0008 | Ω∞-001 | CRITICAL | RATIFY |
| IU-0009 | Ω∞-002 | CRITICAL | RATIFY |
| IU-0010 | Ω∞-003 | CRITICAL | RATIFY |
| IU-0011 | Ω∞-004 | CRITICAL | RATIFY |
| IU-0012 | Ω∞-005 | CRITICAL | RATIFY |
| IU-0013 | Ω∞-006 | CRITICAL | RATIFY |
| IU-0014 | Ω∞-007 | CRITICAL | RATIFY |
| IU-0015 | Ω∞-008 | CRITICAL | RATIFY |
| IU-0016 | Ω∞-009 | CRITICAL | RATIFY |
| IU-0017 | Ω∞-010 | CRITICAL | RATIFY |
| IU-0018 | Ω∞-011 | CRITICAL | RATIFY |
| IU-0019 | Ω∞-012 | CRITICAL | RATIFY |
| IU-0020 | Ω∞-013 | CRITICAL | RATIFY |
| IU-0021 | Ω∞-014 | CRITICAL | RATIFY |
| IU-0022 | Ω∞-015 | CRITICAL | RATIFY |
| IU-0023 | Ω∞-016 | CRITICAL | RATIFY |
| IU-0024 | Ω∞-017 | CRITICAL | RATIFY |
| IU-0025 | Ω∞-018 | CRITICAL | RATIFY |
| IU-0026 | Ω∞-019 | CRITICAL | RATIFY |
| IU-0027 | Ω∞-020 | CRITICAL | RATIFY |
| IU-0028 | UCOS-COMP-001000 | CRITICAL | IMPLEMENT |
| IU-0029 | UCOS-COMP-001010 | CRITICAL | IMPLEMENT |
| IU-0030 | UCOS-COMP-009010 | CRITICAL | IMPLEMENT |
| IU-0031 | UCOS-GOV-000 | CRITICAL | RATIFY |
| IU-0032 | UCOS-GOV-001 | CRITICAL | RATIFY |
| IU-0033 | UCOS-GOV-003 | CRITICAL | RATIFY |
| IU-0034 | UCOS-GOV-005 | CRITICAL | RATIFY |

### Circular dependency resolution strategy

- Graph-level Depends-On cycles detected: **3 node(s)**.
  - Cycle: `UCOS-ENG-000007 -> UCOS-ENG-000008 -> UCOS-ENG-000007`
  - Cycle: `UCOS-ENG-000007 -> UCOS-ENG-000009 -> UCOS-ENG-000008 -> UCOS-ENG-000007`
  - Cycle: `UCOS-ENG-000008 -> UCOS-ENG-000009 -> UCOS-ENG-000008`
- **Strategy:** cycles are among knowledge-graph artifacts (not concept implementation units); resolve by co-implementing the cyclic set as a single atomic unit and breaking the cycle with an interface/contract seam before certification. No implementation unit in this plan sits on a cycle (disjoint id spaces).

### Prerequisites

- Execution prerequisites: FREEZE A + FREEZE B + FREEZE C2 certified (met).
- Validation prerequisites: per-unit validation plan (Register 05).
- Certification prerequisites: per-unit certification gates (Register 06).
