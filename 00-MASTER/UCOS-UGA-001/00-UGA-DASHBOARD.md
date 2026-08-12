# UCOS-UGA-001 — Universal Governance Assimilation Dashboard

**Authority:** NONE — DERIVED TRUTH.  
**Producer:** `00-MASTER/UCOS-UGA-001/uga_engine.py`  
**Determinism:** no wall clock; timestamps are append-only ledger `first_seen` values.

## Governed existence

| Object class | Count | Identity authority |
|---|---:|---|
| CONFIGURATION_OBJECT | 29 | UCOS-UGA-001 |
| DATA_OBJECT | 108 | UCOS-UGA-001 |
| DOCUMENT_ARTIFACT | 1233 | UMB-IMP-001 |
| EXCLUDED_DOCUMENT | 2368 | UCOS-UGA-001 |
| EXECUTABLE_OBJECT | 1186 | UCOS-UGA-001 |
| TEST_OBJECT | 797 | UCOS-UGA-001 |
| TOOLING_OBJECT | 33 | UCOS-UGA-001 |
| **TOTAL** | **5754** | one shared ledger |

## Invariants

| ID | Invariant | Result | Violations |
|---|---|---|---:|
| UGA-INV-01 | `EVERY_OBJECT_HAS_UNIVERSAL_ID` | PASS | 0 |
| UGA-INV-02 | `EVERY_OBJECT_HAS_OWNER` | PASS | 0 |
| UGA-INV-03 | `EVERY_OBJECT_REGISTERED` | PASS | 0 |
| UGA-INV-04 | `EVERY_CANONICAL_ARTIFACT_HAS_INPUT_CLOSURE` | PASS | 0 |
| UGA-INV-05 | `EVERY_GENERATED_INPUT_HAS_PRODUCER` | PASS | 0 |
| UGA-INV-06 | `EVERY_GENERATED_INPUT_HAS_BOOTSTRAP_PATH` | PASS | 0 |
| UGA-INV-07 | `EVERY_CERTIFICATION_HAS_EVIDENCE_BOUNDARY` | PASS | 0 |
| UGA-INV-08 | `NO_CANONICAL_ARTIFACT_DEPENDS_ON_UNCLASSIFIED_OBSERVATION` | PASS | 0 |
| UGA-INV-09 | `NO_ARCHITECTURE_DEPENDS_ON_FINITE_INSTANCE` | PASS | 0 |
| UGA-INV-10 | `EVERY_MUTATION_HAS_AUDIT_EVENT` | PASS | 0 |

## Graph

- relationship edges: **32889**
- dependency edges: **9539**
- producers bound to declared outputs: **40**
- distinct owners: **245**

## Corpus impact

- corpus bytes touched: **0** — no page range consumed, `artifacts.json` untouched.
