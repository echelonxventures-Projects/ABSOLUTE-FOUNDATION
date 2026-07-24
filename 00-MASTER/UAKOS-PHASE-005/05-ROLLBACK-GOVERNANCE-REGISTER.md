# 05 — Rollback Governance Register

> PROGRAM **UAKOS PHASE-005** — Constitutional Implementation Execution Governance · baseline `ab78f35` (branch `governance-reconciliation`) · consumes FREEZE A+B+C2+D · AUTHORITY = **NONE (DERIVED / GOVERNANCE)** · **READ-ONLY** · generated `2026-07-24T11:28:58Z` by `phase5_gov.py`.
>
> Per execution package: rollback trigger, scope, evidence, validation, certification.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-005/phase5_gov.py`.

| Package | Capability | Wave | Rollback trigger | Rollback scope | Rollback evidence | Rollback validation | Rollback certification |
|---|---|---|---|---|---|---|---|
| EP-001 | Governance/Constitutions | 2 | any gate FAIL / validation regression / dependency breach | 26 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-002 | Operational-Memory | 2 | any gate FAIL / validation regression / dependency breach | 8 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-003 | Governance/Constitutions | 3 | any gate FAIL / validation regression / dependency breach | 2 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-004 | Applications | 5 | any gate FAIL / validation regression / dependency breach | 5 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-005 | Data | 5 | any gate FAIL / validation regression / dependency breach | 1 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-006 | Governance/Constitutions | 5 | any gate FAIL / validation regression / dependency breach | 2 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-007 | Infrastructure | 5 | any gate FAIL / validation regression / dependency breach | 2 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-008 | Operational-Memory | 5 | any gate FAIL / validation regression / dependency breach | 17 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-009 | Platform | 5 | any gate FAIL / validation regression / dependency breach | 11 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-010 | Runtime | 5 | any gate FAIL / validation regression / dependency breach | 7 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-011 | Services | 5 | any gate FAIL / validation regression / dependency breach | 1 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-012 | Applications | 6 | any gate FAIL / validation regression / dependency breach | 2 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-013 | Data | 6 | any gate FAIL / validation regression / dependency breach | 4 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-014 | Governance/Constitutions | 6 | any gate FAIL / validation regression / dependency breach | 2 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-015 | Infrastructure | 6 | any gate FAIL / validation regression / dependency breach | 3 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-016 | Platform | 6 | any gate FAIL / validation regression / dependency breach | 3 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-017 | Runtime | 6 | any gate FAIL / validation regression / dependency breach | 2 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-018 | Services | 6 | any gate FAIL / validation regression / dependency breach | 3 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-019 | Governance/Constitutions | 8 | any gate FAIL / validation regression / dependency breach | 5 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |
| EP-020 | Operational-Memory | 8 | any gate FAIL / validation regression / dependency breach | 12 units (package-atomic) | rollback record + reverted-state attestation | post-rollback re-validation of prior state | no re-certification (state reverts to last certified) |

### Rollback strategy by unit type

| Unit type | Rollback strategy |
|---|---|
| CERTIFY | Revert to PARTIALLY_IMPLEMENTED; quarantine certification evidence. |
| IMPLEMENT | Do not merge partial artifact; object remains SPECIFIED; revert branch. |
| POPULATE | Revert store to prior populated state; population evidence quarantined. |
| RATIFY | Revert to SPECIFIED; no ratification recorded (governance state unchanged). |

_Rollback is package-atomic and evidence-based: no partial package is left in a half-executed state; the repository never advances past the last certified baseline on failure._
