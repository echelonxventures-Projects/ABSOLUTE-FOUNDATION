# 03 — Validation Governance Register

> PROGRAM **UAKOS PHASE-005** — Constitutional Implementation Execution Governance · baseline `ab78f35` (branch `governance-reconciliation`) · consumes FREEZE A+B+C2+D · AUTHORITY = **NONE (DERIVED / GOVERNANCE)** · **READ-ONLY** · generated `2026-07-24T11:28:58Z` by `phase5_gov.py`.
>
> Pre / in / post-execution validation, evidence requirements, acceptance thresholds.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-005/phase5_gov.py`.

| Phase | Validation | Evidence requirement | Acceptance threshold |
|---|---|---|---|
| Pre-Execution | FREEZE A–E certified; prerequisite waves complete; spec present + rooted | freeze-seal check, prereq-wave attestation | 100% freezes certified; 0 open prereqs |
| In-Execution | unit tests + incremental conformance (IMPLEMENT units) | test results, build logs | all unit tests green |
| Post-Execution | integration + runtime + compliance validation; evidence capture | integration/runtime results, ValidationEvidence | all post gates PASS |

### Validation gates by unit type

| Unit type | Validation gate sequence |
|---|---|
| CERTIFY | V-PRE:regression \| V-POST:certification-evidence |
| IMPLEMENT | V-PRE:freeze+prereq \| V-IN:unit-tests \| V-POST:integration+runtime+evidence |
| POPULATE | V-PRE:registry-check \| V-POST:population-evidence |
| RATIFY | V-PRE:freeze+specified-check \| V-POST:ratification-conformance |

Units requiring in-execution test validation (IMPLEMENT): **47**.
