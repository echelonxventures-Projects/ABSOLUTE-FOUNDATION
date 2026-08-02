# UCOS-UCAF-001 · Authority Realization

An authority is declared by an instrument and EXERCISED by code. Every token below
is DISCOVERED from the executable plane; none is declared by this programme. Two
properties are measured independently, and the second cannot waive the first.

1. **No collision.** No token minted in the executable plane may be a registered
   constitutional authority. This is the machine form of the prohibition on
   governance asserting, simulating or substituting for constitutional authority.
2. **Classified.** Every discovered token must belong to a declared class recording
   what it is and why it is not a constitutional authority. An undisclosed token
   closes the gate whatever it says.

## Declared token classes

| Class | Token | Class | Constitutional | Basis |
|---|---|---|---|---|
| `UCAF-TC-01` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | no | 00-CEP/CEP-003-CONSTITUTIONAL-EXECUTION-CONSTITUTION.md ARTICLE I.3 — execution authority SHALL NOT govern, ratify, decide constitutional content, or exercise a power reserved to a higher tier. A module minting this token discloses that it acts and holds nothing. |
| `UCAF-TC-02` | `NONE (DERIVED TRUTH)` | DERIVED-TRUTH | no | 00-CMG/CMG-000001 ARTICLE XVI.2 — the derived-truth tier records and asserts nothing. A module minting this token discloses that it computes and refuses rather than legislating. |
| `UCAF-TC-03` | `authority` | DELTA-REGISTER-KEY | no | engine/uckp/state.py — one of the five delta registers a UCKP transition is required to carry. The constant is a register key in a state record, not a claim to hold authority; it is disclosed here rather than filtered in code so that the discovered population is never quietly narrowed. |

## Tokens minted in the executable plane

| Module | Constant | Token | Class | Classified | Collides |
|---|---|---|---|---|---|
| `engine/acceptance/contracts.py` | `ACCEPTANCE_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `engine/certification/contracts.py` | `CERTIFICATION_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `engine/context/__init__.py` | `AUTHORITY` | `NONE (DERIVED TRUTH)` | DERIVED-TRUTH | YES | no |
| `engine/context/certification.py` | `AUTHORITY` | `NONE (DERIVED TRUTH)` | DERIVED-TRUTH | YES | no |
| `engine/governance/contracts.py` | `GOVERNANCE_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `engine/knowledge/certification.py` | `KNOWLEDGE_CERTIFICATION_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `engine/knowledge/ukip/certification.py` | `KNOWLEDGE_INTELLIGENCE_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `engine/runtime/bridge/contracts.py` | `BRIDGE_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `engine/runtime/execution/authorization.py` | `EXECUTION_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `engine/uckp/state.py` | `AUTHORITY` | `authority` | DELTA-REGISTER-KEY | YES | no |
| `engine/universal_certification/contracts.py` | `UCERT_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `platform/commercial_intelligence/contracts.py` | `COMMERCIAL_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `platform/repository_intelligence/contracts.py` | `REPOSITORY_INTELLIGENCE_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `platform/repository_operations/contracts.py` | `OPERATIONS_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `platform/universal_assurance/contracts.py` | `ASSURANCE_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `platform/universal_pipeline/governance.py` | `GOVERNANCE_AUTHORITY` | `NONE (DERIVED TRUTH)` | DERIVED-TRUTH | YES | no |
| `platform/universal_validation/contracts.py` | `VALIDATION_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |
| `platform/validation_intelligence/contracts.py` | `INTELLIGENCE_AUTHORITY` | `ENGINEERING-EXECUTION-ONLY` | ENGINEERING-EXECUTION | YES | no |

## Realization bindings (located authority ↔ the code that exercises it)

| Binding | Authority | Resolves to | Tier | Tier located | Module | Token | Enforced by | Vesting located | Defined by the vesting instrument | Bound |
|---|---|---|---|---|---|---|---|---|---|---|
| `UCAF-RB-01` | Execution Authority | `CEP-003::EXECUTION` | Execution Authority | YES | `engine/runtime/execution/authorization.py` | `ENGINEERING-EXECUTION-ONLY` | `require_authorization` | YES | YES | YES |
