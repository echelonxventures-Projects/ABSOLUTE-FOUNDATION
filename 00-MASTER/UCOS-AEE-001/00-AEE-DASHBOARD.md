# UCOS-AEE-001 — Autonomous Evolution Loop Dashboard

| Field | Value |
|---|---|
| PROGRAMME | `UCOS-AEE-001` — Autonomous Evolution Engine v1.0 |
| AUTHORITY | **NONE — DERIVED TRUTH. This programme legislates nothing, registers nothing, certifies nothing and owns no capability. It sequences located owners, reads their sealed determinations, and asserts convergence over what they report.** |
| TIER | `standard` |
| DETERMINATION | **NOT-CONVERGED** |
| SEAL | `6772107f3817529692f1e73b4b656baf` |
| REPOSITORY ANCHOR | the containing commit — owned by version control, never restated here |

> The continuously regenerated view of the loop. This programme has no terminal state: actuate the located owners, read what they determined, classify and decide every divergence, compare against the previous reading, repeat.

---

## Convergence

| Criterion | Measure | Expect | Measured | Verdict |
|---|---|---|---|---|
| `CONV-01` | `unstable_transitions` | `0` | `0` | SATISFIED |
| `CONV-02` | `blocking_violations` | `0` | `5` | **VIOLATED** |
| `CONV-03` | `actuator_failures` | `0` | `0` | SATISFIED |
| `CONV-04` | `unresolved_mandate_bindings` | `0` | `0` | SATISFIED |
| `CONV-05` | `unclassified_findings` | `0` | `0` | SATISFIED |
| `CONV-06` | `unattributed_residue` | `0` | `0` | SATISFIED |
| `CONV-07` | `unresolved_pointers` | `0` | `0` | SATISFIED |

## Loop state

| Dimension | Value |
|---|---|
| Iterations executed | 4 |
| Consecutive iterations sharing one observation vector | 4 (required 2) |
| Observations declared | 38 |
| Observations satisfied | 32 |
| Actuators in scope | 17 |
| Located loop mandates read | 57 |
| Mandates discharged | 57 |
| Findings discovered | 6 |
| Unsatisfied blocking criteria | `CONV-02` |
| Gate exit code | 1 |

## Certification ceiling

The maximum attainable verdict is **CONVERGED-PROVISIONAL** while the following stand:

- `AEE-F-001` — A certification ceiling stands: the aggregate certifier reports standing located findings
- `AEE-F-002` — Convergence here is over the observation vector, not over the repository's bytes
- `AEE-F-003` — Cadence is bound to continuous integration, not to a resident process
- `OBS-AGGREGATE-CEILING` — No standing finding bounds the attainable certification (decision `ESCALATE`)

---

*Regenerate with `make aee`. Enforce with `make aee-gate`.*
