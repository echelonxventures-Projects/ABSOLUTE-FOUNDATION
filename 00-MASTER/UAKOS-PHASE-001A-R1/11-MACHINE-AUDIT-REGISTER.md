# 11 — Machine Audit Register

> PROGRAM **UAKOS PHASE-001A-R1** — Constitutional Baseline Re-Certification · closure baseline `57d91b7` (branch `governance-reconciliation`) · corrected Authoritative-Origin model (Phase-001B) · AUTHORITY = **NONE (DERIVED / CERTIFIED TRUTH)** · **READ-ONLY** · generated `2026-07-23T05:42:28Z` by `cert_engine.py`.
>
> Automated verification: input identity (SHA-256), deterministic assertions, machine reproducibility.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-001A-R1/cert_engine.py`.

- Input `provenance.json` SHA-256: `86de7d017f70582d0946fdeb20160099031dd3aa7c9564015a2d31f776545305`
- Input `closure.json` SHA-256: `8977fbb9bf21cca013bf32baac9a7cc0221841b26ceb8053249664d9cbb66457`
- Objects certified: **431** (== closure concept_total **431**)

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
