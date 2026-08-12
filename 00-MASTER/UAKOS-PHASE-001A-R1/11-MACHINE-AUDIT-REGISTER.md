# 11 — Machine Audit Register

> PROGRAM **UAKOS PHASE-001A-R1** — Constitutional Baseline Re-Certification · closure baseline `05342cb` (branch `integration/recovery-001`) · corrected Authoritative-Origin model (Phase-001B) · AUTHORITY = **NONE (DERIVED / CERTIFIED TRUTH)** · **READ-ONLY** · derived from provenance baseline `05342cb` by `cert_engine.py`.
>
> Automated verification: input identity (SHA-256), deterministic assertions, machine reproducibility.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-001A-R1/cert_engine.py`.

- Input `provenance.json` SHA-256: `df0dfd1b03acd973ab095605f68fa472f1de18af30ec150f30fb95376ab738b8`
- Input `closure.json` SHA-256: `a04e420cc4a6964b1351f79752d09a619c6e64b079659539aba3c5984befb00d`
- Objects certified: **447** (== closure concept_total **549**)

| Machine assertion | Result |
|---|---|
| every object has exactly one origin | PASS |
| every origin in allowed taxonomy | PASS |
| no UNKNOWN origin | PASS |
| no NONE origin | PASS |
| object_total == closure concept_total | FAIL |
| knowledge loss == 0 | PASS |
| deterministic re-run (inputs hash-pinned) | PASS |

All assertions are recomputed on every run from the two hash-pinned inputs; the audit is fully machine-reproducible and stateless.
