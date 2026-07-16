"""EC-1 Runtime Assembly (EPIC-005) — IMP-007 §8 deployable runtime units.

Public API surface for the Runtime Assembly engine: it transforms a **published
compiler package** (EPIC-003, TASK-000027) into a deployable, reversible
:class:`RuntimeUnit` for the IMP-008 Runtime Platform, and generates the
deployment and rollback definitions that carry it.

The engine is additive engineering code built on the EC-1 Foundation (EPIC-001),
the Registry Adapter (EPIC-002), the Universal Compiler (EPIC-003), and the
Determinism Framework (EPIC-004), all reused verbatim (Mandatory Rule 4). It binds
only registered, certified components (§15), validates provenance/signature/SBOM
before emitting anything (§1/§12), references secrets only (SEC-04), generates
deterministic descriptors (§5), produces reversible checkpoint-based rollback
(IP-08), and stamps every unit with the EC-1 provisional-state disclosure
(DE-05 / C-05). It produces deployable *definitions* only — never a live system.

Tasks: TASK-000034 (assembly engine), TASK-000035 (deployment + rollback),
TASK-000036 (provisional-state disclosure), TASK-000037 (assembly validation).
"""

from __future__ import annotations

from engine.runtime.assembly import (
    DEFAULT_RESOURCES,
    RUNTIME_DESCRIPTOR_FORMAT,
    ClosureEntry,
    PublishedPackage,
    RuntimeUnit,
    SecretBinding,
    assemble,
    k8s_name,
)
from engine.runtime.deploy import (
    ROLLBACK_STRATEGY,
    DeploymentDescriptor,
    RollbackDescriptor,
    dependency_closure_record,
    descriptor,
    rollback,
)
from engine.runtime.disclosure import (
    DISCLOSURE_GATE,
    DISCLOSURE_ID,
    DISCLOSURE_STANDARD,
    DISCLOSURE_STATEMENT,
    build_disclosure,
    disclosure_present,
    inject_provisional_state,
    require_disclosure,
)
from engine.runtime.errors import (
    DependencyClosureError,
    DeploymentError,
    DisclosureError,
    ProvenanceValidationError,
    RuntimeAssemblyError,
    SBOMValidationError,
    SecretExposureError,
    SignatureValidationError,
)

__all__ = [
    # assembly
    "assemble",
    "RuntimeUnit",
    "PublishedPackage",
    "ClosureEntry",
    "SecretBinding",
    "RUNTIME_DESCRIPTOR_FORMAT",
    "DEFAULT_RESOURCES",
    "k8s_name",
    # deployment + rollback
    "descriptor",
    "rollback",
    "dependency_closure_record",
    "DeploymentDescriptor",
    "RollbackDescriptor",
    "ROLLBACK_STRATEGY",
    # disclosure
    "inject_provisional_state",
    "build_disclosure",
    "disclosure_present",
    "require_disclosure",
    "DISCLOSURE_ID",
    "DISCLOSURE_STANDARD",
    "DISCLOSURE_GATE",
    "DISCLOSURE_STATEMENT",
    # errors
    "RuntimeAssemblyError",
    "ProvenanceValidationError",
    "SignatureValidationError",
    "SBOMValidationError",
    "DependencyClosureError",
    "SecretExposureError",
    "DisclosureError",
    "DeploymentError",
]
