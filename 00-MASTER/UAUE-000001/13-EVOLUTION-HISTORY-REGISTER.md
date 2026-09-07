# Evolution History Register

> **Register:** `13-EVOLUTION-HISTORY-REGISTER.md` (ordinal 13)  
> **Programme:** UAUE-000001 v1.0.0  
> **Renderer:** `history`  
> **AUTHORITY = NONE — DERIVED TRUTH**  
> **Declaration digest:** `eb31205bea13edee`  
> **Regenerate:** `make uaue-render` — this file is a projection and never a source.

*who, what, why, when in logical time, where, context, evidence, decision, impact, validation, certification*

The canonical history is the JSON projection named by the declaration's `history` block. This register summarises it and never restates its records: a second copy of an append-only ledger is a second ledger, and the two could disagree.

## Projection

| Property | Value |
|---|---|
| canonical file | `00-MASTER/UAUE-000001/UAUE-EVOLUTION-HISTORY.json` |
| schema | ucos-uaue-evolution-history v1.0.0 |
| append only | PASS |
| ledger owner | engine/uckp/evolution.py::EvolutionLedger |
| written through | to_document |
| read back through | from_document |
| projection digest | dd416e47c6b480a5 |

## Ledger counts

| Count | Value |
|---|---|
| completed_cycles | 54 |
| cycles | 54 |
| findings | 8910 |
| records | 810 |

## Recorded dimensions

`when` is logical (`cycle=N stage=S ordinal=K`) and never a timestamp, so the history replays byte-identically.

| Dimension |
|---|
| who |
| what |
| why |
| when |
| where |
| context |
| evidence |
| decision |
| impact |
| validation |
| certification |

## Queryable keys

| Key |
|---|
| evolution_id |
| subject_identity |
| candidate_class |
| phase |
| canonical_stage |
| cycle |
| lifecycle_state |
