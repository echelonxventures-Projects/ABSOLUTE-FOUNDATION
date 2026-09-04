# ADR-0039: Fourteen agnosticism axes, each proven, abstracted, bypassed or declared absent

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-09-04 |
| Deciders | Constitutional Authority · UCOS Ω∞ |
| Technology Constitution refs | `UCKP-ART-09`, `UCKP-ART-10`, `UCKP-ART-20` |
| Supersedes | none |

## Context

Agnosticism is declared across the corpus and was never measured. Measured this session against
one bar — *an abstraction with one implementation is an assumption; an abstraction its own
callers bypass is decoration* — fourteen axes score: 2 proven, 4 abstracted, 4 bypassed,
4 hardcoded.

Concrete findings: 20 non-test modules invoke `git` directly against 2 that use the git
provider; 1,732 direct `sha256` call sites against a crypto-agility registry that governs
almost none of them; `DeploymentDescriptor.kubernetes` is a typed field rather than a provider;
and there is no numeric-system reference domain.

## Decision

Each axis carries a disposition, and four become `DECLARED_ABSENT` under `ADR-0030` rather than
remaining unproven claims:

- **human language** — no message catalogue exists and determinism forces `LC_ALL=C`;
- **infrastructure** — Kubernetes is in the data model;
- **numerics** — no numeric-system domain is registered;
- **OS/shell** — POSIX is assumed by every entry point.

**Version control** is declared git-bound with a reason: `git ls-files` *is* the discovery
boundary and `git archive` defines pristine-clone certification, so substituting a VCS is three
constitutional redefinitions rather than an adapter swap.

The remaining axes keep their measured status and close by acquiring a second implementation.

## Alternatives rejected

**Claim the axes and defer proof.** Rejected — an unproven claim is what generates the next
audit, and this ADR exists because one did.

**Drop the agnosticism goal.** Rejected: the axes that are proven — time and measurement — are
genuinely proven, and the property is the architecture's point.

## Revisit conditions

- A second implementation lands on any axis, which moves it from abstracted to proven and
  should be recorded as a movement rather than a silent upgrade.
- The interpreter moves to a version where `sys.monitoring` can measure branches, which would
  reopen the coverage-provider axis that is currently blocked.

## Consequences

Four axes stop being claimed and start being citable. `CoverageProvider` becomes a concrete
declared absence rather than a theoretical gap: `COVERAGE_CORE=sysmon` is silently ignored at
the current pins because `sys.monitoring` cannot measure branches before Python 3.14, which is
one implementation's constraint presenting as the system's ceiling.

## Compliance

`ART-09` (persistence abstraction) and `ART-10` (execution abstraction) require one contract
per mechanism; this decision records which of them currently have one implementation and says
so rather than implying otherwise. `ART-20` (perpetual validity) is served by declaring the
absences, since an undeclared assumption is what fails first when the environment moves.

## Validation evidence

Counts measured at this commit by direct search over `engine`, `platform`, `intelligence`,
`infrastructure` and `service`, excluding tests. The `sysmon` constraint is read directly from
`coverage/core.py`: `branch_right_left = pep669 and (PYVERSION > (3, 14, 0, "alpha", 5, 0))`.
