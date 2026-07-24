# 10 — Evidence Completeness Register

> PROGRAM **UAKOS PHASE-001B** — Universal Constitutional Provenance Reconstruction · closure baseline `57d91b7` (branch `governance-reconciliation`) · AUTHORITY = **NONE (DERIVED / RECONSTRUCTED TRUTH)** · **READ-ONLY** · generated `2026-07-23T05:33:10Z` by `provenance_engine.py` + `emit_registers.py`.
>
> Per knowledge object, which of the 9 provenance-chain links are present, and the aggregate completeness distribution.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-001B/provenance_engine.py && python3 00-MASTER/UAKOS-PHASE-001B/emit_registers.py`.

### Chain-link fill rates (across all 431 objects)

| Chain link | Objects with link | Fill rate |
|---|---|---|
| source_document | 431 | 100.0% |
| page | 85 | 19.7% |
| section | 82 | 19.0% |
| paragraph | 85 | 19.7% |
| original_text | 85 | 19.7% |
| knowledge_object | 431 | 100.0% |
| repository_evidence | 431 | 100.0% |
| validation_evidence | 431 | 100.0% |
| certification_evidence | 240 | 55.7% |

### Completeness distribution (fraction of 9 links present)

| Completeness | Objects |
|---|---|
| 1.000 | 32 |
| 0.889 | 50 |
| 0.778 | 3 |
| 0.556 | 208 |
| 0.444 | 138 |

Objects with a **complete** 9-link chain: **32 / 431**. The dominant missing links are the source-document layer (page/section/paragraph/original_text) for repository-minted identifiers — consistent with Register 09.

### Objects with a fully complete provenance chain

| Concept | Family | Quality |
|---|---|---|
| DATA-001 | DATA | PARTIALLY_RECOVERED |
| DATA-005 | DATA | PARTIALLY_RECOVERED |
| DATA-006 | DATA | PARTIALLY_RECOVERED |
| DATA-007 | DATA | PARTIALLY_RECOVERED |
| DATA-008 | DATA | PARTIALLY_RECOVERED |
| DATA-009 | DATA | PARTIALLY_RECOVERED |
| DATA-010 | DATA | PARTIALLY_RECOVERED |
| DATA-011 | DATA | PARTIALLY_RECOVERED |
| DATA-012 | DATA | PARTIALLY_RECOVERED |
| DATA-013 | DATA | PARTIALLY_RECOVERED |
| DATA-014 | DATA | PARTIALLY_RECOVERED |
| GOV-001 | GOV | PARTIALLY_RECOVERED |
| PLATFORM-006 | PLATFORM | PARTIALLY_RECOVERED |
| PLATFORM-009 | PLATFORM | PARTIALLY_RECOVERED |
| PLATFORM-010 | PLATFORM | PARTIALLY_RECOVERED |
| PLATFORM-012 | PLATFORM | PARTIALLY_RECOVERED |
| RUNTIME-006 | RUNTIME | PARTIALLY_RECOVERED |
| RUNTIME-007 | RUNTIME | PARTIALLY_RECOVERED |
| RUNTIME-008 | RUNTIME | PARTIALLY_RECOVERED |
| RUNTIME-009 | RUNTIME | PARTIALLY_RECOVERED |
| RUNTIME-010 | RUNTIME | PARTIALLY_RECOVERED |
| SERVICE-001 | SERVICE | PARTIALLY_RECOVERED |
| SERVICE-003 | SERVICE | PARTIALLY_RECOVERED |
| SERVICE-004 | SERVICE | PARTIALLY_RECOVERED |
| SERVICE-005 | SERVICE | PARTIALLY_RECOVERED |
| SERVICE-006 | SERVICE | PARTIALLY_RECOVERED |
| SERVICE-007 | SERVICE | PARTIALLY_RECOVERED |
| SERVICE-008 | SERVICE | PARTIALLY_RECOVERED |
| SERVICE-009 | SERVICE | PARTIALLY_RECOVERED |
| SERVICE-010 | SERVICE | PARTIALLY_RECOVERED |
| SERVICE-011 | SERVICE | PARTIALLY_RECOVERED |
| SERVICE-012 | SERVICE | PARTIALLY_RECOVERED |
