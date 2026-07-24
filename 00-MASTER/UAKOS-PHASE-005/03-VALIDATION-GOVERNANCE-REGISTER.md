# 03 — Validation Governance Register

> PROGRAM **UAKOS PHASE-005** — Constitutional Implementation Execution Governance · baseline `57d91b7` (branch `governance-reconciliation`) · consumes FREEZE A+B+C+D · AUTHORITY = **NONE (DERIVED / GOVERNANCE)** · **READ-ONLY** · generated `2026-07-23T06:26:34Z` by `phase5_gov.py`.
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
| SPECIFY | V-PRE:freeze-check \| V-POST:spec-lint+traceability |
| IMPLEMENT | V-PRE:freeze+prereq \| V-IN:unit-tests \| V-POST:integration+runtime+evidence |
| CERTIFY | V-PRE:regression \| V-POST:certification-evidence |

Units requiring in-execution test validation (IMPLEMENT): **112**.
