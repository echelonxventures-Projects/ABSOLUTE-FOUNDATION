# 05 — Execution Stream Register

> PROGRAM **UAKOS PHASE-003R** — Universal Realization Model Determination · baseline `57d91b7` (branch `governance-reconciliation`) · corrects the Wave-002 category error · consumes FREEZE A–F (read-only) · AUTHORITY = **NONE (DERIVED)** · **READ-ONLY** · generated `2026-07-23T06:56:11Z` by `phase3r_engine.py`.
>
> The single execution stream is replaced by constitutional streams; each carries only compatible realization types.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-003R/phase3r_engine.py`.

| Execution stream | Objects | Eligibility | Realization types |
|---|---|---|---|
| Documentation | 41 | not software | ARCHITECTURE_SPECIFICATION, LIFECYCLE_PHASE, PROGRAM_EPIC |
| Governance | 82 | not software | ADMISSION_GATE, CONSTITUTIONAL_EVIDENCE_PRINCIPLE, CONSTITUTIONAL_EVOL |
| Infrastructure | 19 | software-eligible | INFRASTRUCTURE_COMPONENT |
| Knowledge | 124 | not software | MASTER_CONTEXT_PROTOCOL, META_MODEL, ONTOLOGY |
| Registry | 53 | not software | EXECUTION_BAND_UNIT |
| Software | 112 | software-eligible | APPLICATION, DATA_MODEL, PLATFORM_COMPONENT, RUNTIME_COMPONENT, SERVIC |

- **Software-eligible streams:** Software, Infrastructure → **131** objects.
- **Non-software streams:** Governance, Knowledge, Registry, Documentation → **300** objects (never software-implemented).
