# 11 — Machine Audit Register

> PROGRAM **UAKOS PHASE-001A-R1** — Constitutional Baseline Re-Certification · closure baseline `8444c995` (branch `integration/recovery-001`) · corrected Authoritative-Origin model (Phase-001B) · AUTHORITY = **NONE (DERIVED / CERTIFIED TRUTH)** · **READ-ONLY** · derived from provenance baseline `8444c995` by `cert_engine.py`.
>
> Automated verification: input identity (SHA-256), deterministic assertions, machine reproducibility.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-001A-R1/cert_engine.py`.

- Input `provenance.json` SHA-256: `bb893ab79813f7dd297177f12a509478defc4c06f1bd0897995e225c0abbcb45`
- Input `closure.json` SHA-256: `3af7ecf16e4d066b67f3c5b8a4acbdac9789d491354938a8da18cc53c19c9668`
- Objects certified: **549** (== closure concept_total **549**)

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
