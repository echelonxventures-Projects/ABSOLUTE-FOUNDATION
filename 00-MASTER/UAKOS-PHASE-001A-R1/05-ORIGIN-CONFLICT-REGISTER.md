# 05 — Origin Conflict Register

> PROGRAM **UAKOS PHASE-001A-R1** — Constitutional Baseline Re-Certification · closure baseline `05342cb` (branch `integration/recovery-001`) · corrected Authoritative-Origin model (Phase-001B) · AUTHORITY = **NONE (DERIVED / CERTIFIED TRUTH)** · **READ-ONLY** · derived from provenance baseline `05342cb` by `cert_engine.py`.
>
> Objects with multiple candidate origins and how uniqueness is enforced. A frozen-source origin outranks a repository home (which becomes a mapping, not a rival origin); additional source appearances are corroborating evidence, not competing origins.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-001A-R1/cert_engine.py`.

- Objects with a source origin **and** a repository mapping (resolved by precedence, not a conflict): **88**
- Objects appearing in >1 source document (corroborating occurrences): **30**
- **True conflicting origins** (two incompatible authoritative origins): **0** — impossible by construction: the selector returns exactly one origin via a total precedence order.
- **Circular origins**: **0** — origins are documents/homes, never other knowledge objects; no origin can reference itself.
- **Invalid origins** (outside the allowed taxonomy): **0**.

### Objects with corroborating (non-authoritative) source occurrences

| Concept | Authoritative origin | Corroborating occ. | Repo mapping |
|---|---|---|---|
| Ω∞-000 | SOURCE_DOCUMENT | 2 | EC-3-B13-P02-UNIVERSAL-UNIVERSE-ARCH |
| Ω∞-001 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-002 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-003 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-004 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-005 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-006 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-007 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-008 | SOURCE_DOCUMENT | 2 | UAKOS-CL003-W1-UNIVERSAL-LAW-CANONIC |
| Ω∞-009 | SOURCE_DOCUMENT | 2 | UAKOS-CL003-W1-UNIVERSAL-LAW-CANONIC |
| Ω∞-010 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-011 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-012 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-013 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-014 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-015 | SOURCE_DOCUMENT | 2 | APP-001-APPLICATION-FOUNDATION-CONST |
| Phase-000 | IMPORTED_REFERENCE | 1 | ChatGPT Chat.docx |
| Phase-021 | IMPORTED_REFERENCE | 1 | ChatGPT Chat.docx |
| Phase-040 | IMPORTED_REFERENCE | 1 | ChatGPT Chat.docx |
| UCOS-COMP-000001 | SOURCE_DOCUMENT | 1 | UCOS-COMP-000001-CONSTITUTIONAL-COMP |
| UCOS-COMP-001000 | SOURCE_DOCUMENT | 1 | roadmap.json |
| UCOS-COMP-001001 | SOURCE_DOCUMENT | 1 | roadmap.json |
| UCOS-COMP-001010 | SOURCE_DOCUMENT | 1 | roadmap.json |
| UCOS-COMP-009009 | SOURCE_DOCUMENT | 1 | roadmap.json |
| UCOS-COMP-009010 | SOURCE_DOCUMENT | 1 | roadmap.json |
| Ω∞-016 | SOURCE_DOCUMENT | 1 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-017 | SOURCE_DOCUMENT | 1 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-018 | SOURCE_DOCUMENT | 1 | UCOS-RAT-001-REPOSITORY-RATIFICATION |
| Ω∞-019 | SOURCE_DOCUMENT | 1 | APP-001-APPLICATION-FOUNDATION-CONST |
| Ω∞-020 | SOURCE_DOCUMENT | 1 | APP-001-APPLICATION-FOUNDATION-CONST |
