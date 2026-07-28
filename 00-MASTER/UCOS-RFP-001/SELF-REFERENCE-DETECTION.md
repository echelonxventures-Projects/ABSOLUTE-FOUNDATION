# UCOS-RFP-001 — SELF-REFERENCE DETECTION

> GENERATED FROM `rfp-declaration.json` BY UCOS-RFP-001 — DO NOT EDIT BY HAND.
> Regenerate with `make rfp`. AUTHORITY = NONE (DERIVED TRUTH).
>
> This projection records the DECLARATION only. It carries no commit identity
> (RFP-2) and no observation of the working tree (RFP-3) — including the
> fixed-point verdict itself, which is carried by the gate's exit code and
> standard output. An artifact asserting "the repository is a fixed point"
> would falsify that sentence by being written.

## Detection is architectural

No detector matches a path, a lane, a producer or a field name. Each observes either the BEHAVIOUR of a producer across executions or the BYTES a producer wrote in its own delta. Consequently an authored document that merely cites a commit is never flagged: a citation appears in no producer's delta.

## Topologies

| ID | Topology | Principle | Severity | Detector | Signature |
|---|---|---|---|---|---|
| CYC-OBSERVE | Self-observation cycle | RFP-3 | CRITICAL | `pass_instability` | The producer's output differs between two consecutive executions at ONE unchanged commit. Only an input the producer itself perturbs can do that; the working tree is the input it perturbs by writing. |
| CYC-COMMIT | Commit-identity cycle | RFP-2 | CRITICAL | `commit_token_in_delta` | The bytes a producer writes contain a hex token that this repository's object database resolves to a commit. Only `git rev-parse`-class input produces that, and the artifact is inside a commit it cannot name. |
| CYC-HASH | Hash cycle | RFP-4 | CRITICAL | `mutual_hash_in_delta` | Within one pipeline pass, artifact A's written bytes contain the content hash of artifact B while B's written bytes contain the content hash of A. |
| CYC-REGISTER | Registration cycle | RFP-5 | CRITICAL | `foreign_projection_write` | A producer that does not own the registration projections nevertheless causes them to change — so a non-canonical artifact is carrying a registered identity. |
| CYC-RECURSE | Recursive generator | RFP-6 | CRITICAL | `reentrancy` | A producer re-enters itself, directly or through an aggregate that invokes it. |
| CYC-UNDECLARED | Undeclared producer | RFP-6 | HIGH | `unattributed_residue` | Tracked content changed during a pipeline pass but no declared stage's write zone contains it. |

## Remediation

| ID | Remediation |
|---|---|
| CYC-OBSERVE | Stop persisting the observation. Keep it as an input to the gate verdict and to standard output. |
| CYC-COMMIT | Remove the commit identity from the emitted bytes. Version control already records it. |
| CYC-HASH | Break the mutual embedding: one side must derive from the other, never both. |
| CYC-REGISTER | Withdraw the class from registration through the declared admission authority. |
| CYC-RECURSE | Declare the stage non-reentrant; the aggregate must exclude itself from its own pipeline. |
| CYC-UNDECLARED | Declare the producer as a pipeline stage, or stop it from writing tracked content. |

## Why behaviour, not inspection

A producer that reads repository state cannot be recognised from its source without enumerating the calls it might make; the set of such calls is open. What is closed is the OBSERVABLE consequence: an output that changes at an unchanged commit, or an output containing an identity only the object database can mint. Detecting the consequence catches every present and future mechanism that produces it.

---

*Regenerate with `make rfp`.*
