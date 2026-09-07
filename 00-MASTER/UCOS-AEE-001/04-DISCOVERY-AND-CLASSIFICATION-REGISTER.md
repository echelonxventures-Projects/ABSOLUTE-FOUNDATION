# UCOS-AEE-001 — Discovery and Classification

| Field | Value |
|---|---|
| PROGRAMME | `UCOS-AEE-001` — Autonomous Evolution Engine v1.0 |
| AUTHORITY | **NONE — DERIVED TRUTH. This programme legislates nothing, registers nothing, certifies nothing and owns no capability. It sequences located owners, reads their sealed determinations, and asserts convergence over what they report.** |
| TIER | `standard` |
| DETERMINATION | **NOT-CONVERGED** |
| SEAL | `2ff2408cf2e5fc57ea4bd931c4faa255` |
| REPOSITORY ANCHOR | the containing commit — owned by version control, never restated here |

> A finding is an observation that diverged from its declared expectation, or a required actuator that did not succeed. The set is discovered from Repository Truth; no finding is listed by hand and none is classified by hand.

---

## Classification rules (ordered; first match wins)

| Rule | Predicate | Class | Decision |
|---|---|---|---|
| `CR-ACTUATOR-FAILURE` | `{"actuator_failure": true}` | Defect correction | `IMPLEMENT` |
| `CR-ESCALATED-CEILING` | `{"escalated": true, "governed": true}` | Constitutional amendment | `ESCALATE` |
| `CR-GOVERNED-GAP` | `{"escalated": false, "governed": true}` | Enhancement | `DEFER` |
| `CR-BLOCKING-REGRESSION` | `{"blocking": true, "governed": false}` | Defect correction | `IMPLEMENT` |
| `CR-RESIDUAL` | `{}` | Enhancement | `DEFER` |

## Findings

| Finding | Subject | Blocking | Class | Rule |
|---|---|---|---|---|
| `OBS-AGGREGATE-CEILING` | No standing finding bounds the attainable certification | no | Constitutional amendment | `CR-ESCALATED-CEILING` |
| `OBS-DECISION-GATE` | The constitutional decision gate is open | yes | Defect correction | `CR-BLOCKING-REGRESSION` |
| `ACT-DECISION-ASSIMILATION` | Constitutional decision register and disposition | yes | Defect correction | `CR-ACTUATOR-FAILURE` |
