# 11 — Machine Audit Register

> PROGRAM **UAKOS PHASE-001A-R1** — Constitutional Baseline Re-Certification · closure baseline `8444c995` (branch `integration/recovery-001`) · corrected Authoritative-Origin model (Phase-001B) · AUTHORITY = **NONE (DERIVED / CERTIFIED TRUTH)** · **READ-ONLY** · derived from provenance baseline `8444c995` by `cert_engine.py`.
>
> Automated verification: input identity (SHA-256), deterministic assertions, machine reproducibility.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-001A-R1/cert_engine.py`.

- Input `provenance.json` SHA-256: `dab0659c1a12301a456552b765168e76a57dfabf60b6586fb90aac04a4e90372`
- Input `closure.json` SHA-256: `6e995dbfe69893740ab4b3fceba67c169d00c80a8b093cd43654e0b41084bf61`
- Objects certified: **550** (== closure concept_total **550**)

| Machine assertion | Result |
|---|---|
| every object has exactly one origin | PASS |
| every origin in allowed taxonomy | PASS |
| no UNKNOWN origin | PASS |
| no NONE origin | PASS |
| object_total == closure concept_total | PASS |
| knowledge loss == 0 | PASS |
| deterministic re-run (inputs hash-pinned) | PASS |

All assertions are recomputed on every run from the two hash-pinned inputs; the audit is fully machine-reproducible and stateless.
