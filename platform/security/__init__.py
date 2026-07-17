"""UCOS EC-2 Platform Security Runtime (EC2-CAP-SEC-001) — SEC-CLASS (Phase 1).

The Security Runtime is the runtime realization of the existing constitutional
security architecture (``ARCH-SECURITY-001``), determined in
``platform/security/EC2-CAP-SEC-001-DETERMINATION.md``. It is a **governed, additive,
record-only** platform runtime composed over the certified EC-1 engine and the EC-2
Foundation / Identity / Observability layers: it consumes them only through published
contracts, modifies none, never writes to the certified corpus (DP-03), remains
deterministic, and preserves every EC-1 certification.

**This package ships Phase 1 — SEC-CLASS (Security Classification Runtime)** — the
constitutional "enforcement-by-reference seam", and **Phase 2 — SEC-INTEL (Security
Intelligence Runtime)** — the record-only findings/threats/controls/exceptions/
pentest/compliance/audit intelligence surface with automatic evidence-derived roll-up
(UKB-ADV-005; ``finding.schema.json``). SEC-CLASS **classifies, records, traces,
validates, and reports** the subject-layer security classification records (DATA-014 /
SERVICE-014 / APPLICATION-013 / INFRASTRUCTURE-013) and resolves their declared
enforcement obligation to the certified L7
:class:`~platform.identity.service.AuthorizationService` seam **by reference only**.
SEC-INTEL **records, correlates, rolls up, traces, validates, and reports** security
findings and stores **no** secret value (SEC-04 / RR-07; UKB-ADV-005 §6). Neither
**ever** authorizes, ratifies, enacts, governs, overrides, or escalates authority
(RG-02 / AR-04).

Phase 3 — **SEC-REG (Security Registry Runtime)** — realizes the seven constitutional
§17 registries (Security · Identity · Threat · Risk · Evidence · Certification ·
Trust) as append-only, record-only, attributed, queryable stores that never ratify or
enact (RG-02 / RG-05); see :mod:`platform.security.registries`.

Phase 4 — **SEC-OBS (Security Observability Runtime)** — emits the existing
``security`` signal dimension and shapes security telemetry (metric/log/audit)
**through** the certified L8 Observability Layer, preserving reverse-traceability to
the finding/scan that raised each signal (§15; UMB-015 §5); it creates no new signal
dimension and no second telemetry stack; see :mod:`platform.security.observability`.

The remaining Security Runtime sub-capabilities (SEC-CERT / SEC-ZONE) are later,
separately-authorized phases and are **not** present.

Deliverables (SEC-CLASS + SEC-INTEL):
    * **errors** — the ``EC2-SEC-*`` error taxonomy over ``PlatformError``.
    * **contracts** — the classification vocabulary (``ClassificationKind``,
      ``SubjectLayer``, ``EnforcementReference``), the intelligence vocabulary
      (``FindingKind``, ``Severity``, ``FindingState``, ``RollupState``), and the
      published SEC-CLASS / SEC-INTEL contract surfaces.
    * **classification** — the immutable ``SecurityClassification`` record and the
      append-only ``ClassificationLedger``.
    * **intelligence** — the immutable ``SecurityFinding`` record, the append-only
      ``FindingLedger``, the evidence-derived ``compute_rollup``, and the
      ``SecurityIntelligenceService`` + ``SecurityIntelligenceEvidence``.
    * **service** — the ``SecurityClassificationService`` composition root and
      ``SecurityClassificationEvidence``.
    * **bootstrap** — ``bootstrap_security_classification`` and
      ``bootstrap_security_intelligence`` (compose the runtimes onto a
      ``PlatformContext``).

This package carries no constitutional authority; the external gates (EC-1…EC-6)
remain open.
"""

from __future__ import annotations

from platform.security.bootstrap import (
    SECURITY_CLASSIFICATION_BOOTSTRAP_EVENT,
    SECURITY_INTELLIGENCE_BOOTSTRAP_EVENT,
    SECURITY_OBSERVABILITY_BOOTSTRAP_EVENT,
    SECURITY_REGISTRY_BOOTSTRAP_EVENT,
    bootstrap_security_classification,
    bootstrap_security_intelligence,
    bootstrap_security_observability,
    bootstrap_security_registry,
)
from platform.security.classification import (
    ClassificationLedger,
    SecurityClassification,
)
from platform.security.contracts import (
    BLOCKING_SEVERITIES,
    L7_BOUND_KINDS,
    OPEN_FINDING_STATES,
    REGISTRY_SOURCE,
    SECURITY_CLASSIFICATION_CONTRACT_VERSION,
    SECURITY_CLASSIFICATION_CONTRACTS,
    SECURITY_INTELLIGENCE_CONTRACT_VERSION,
    SECURITY_INTELLIGENCE_CONTRACTS,
    SECURITY_OBSERVABILITY_CONTRACT_VERSION,
    SECURITY_OBSERVABILITY_CONTRACTS,
    SECURITY_REGISTRY_CONTRACT_VERSION,
    SECURITY_REGISTRY_CONTRACTS,
    SECURITY_SIGNAL_DIMENSION,
    SUBJECT_LAYER_KINDS,
    SUBJECT_LAYER_SOURCE,
    ClassificationKind,
    EnforcementReference,
    FindingKind,
    FindingState,
    RegistryKind,
    RollupState,
    Severity,
    SubjectLayer,
    all_classification_kinds,
    all_finding_kinds,
    all_finding_states,
    all_registry_kinds,
    all_severities,
    all_subject_layers,
    default_security_classification_contracts,
    default_security_intelligence_contracts,
    default_security_observability_contracts,
    default_security_registry_contracts,
    security_classification_contract,
    security_intelligence_contract,
    security_observability_contract,
    security_registry_contract,
)
from platform.security.errors import (
    ClassificationBindingError,
    ClassificationValidationError,
    EnforcementReferenceError,
    FindingValidationError,
    RegistryEntryError,
    RegistryValidationError,
    SecretLeakError,
    SecurityBootstrapError,
    SecurityClassificationError,
    SecurityContractError,
    SecurityError,
    SecurityFindingError,
    SecurityObservabilityError,
    SecurityRegistryError,
    SecurityRollupError,
    SecuritySignalError,
    SignalTraceabilityError,
)
from platform.security.intelligence import (
    FINDING_RECORDED_EVENT,
    ROLLUP_EVALUATED_EVENT,
    SECRET_LEAK_IDENTIFIER,
    FindingLedger,
    SecurityFinding,
    SecurityIntelligenceEvidence,
    SecurityIntelligenceService,
    SecurityRollup,
    build_security_intelligence_service,
    compute_rollup,
    scan_for_secret,
)
from platform.security.observability import (
    SECURITY_SIGNAL_AUDIT_ACTION,
    SECURITY_SIGNAL_EMITTED_EVENT,
    SECURITY_SIGNAL_METRIC,
    SecurityObservabilityEvidence,
    SecurityObservabilityService,
    SecuritySignal,
    SignalLedger,
    build_security_observability_service,
)
from platform.security.registries import (
    REGISTRY_RECORDED_EVENT,
    AppendOnlyRegistry,
    RegistryEntry,
    SecurityRegistryEvidence,
    SecurityRegistryService,
    SecurityRegistrySet,
    build_security_registry_service,
)
from platform.security.service import (
    CLASSIFICATION_RECORDED_EVENT,
    SecurityClassificationEvidence,
    SecurityClassificationService,
    build_security_classification_service,
)

__all__ = [
    # contracts
    "SECURITY_CLASSIFICATION_CONTRACT_VERSION",
    "SECURITY_CLASSIFICATION_CONTRACTS",
    "ClassificationKind",
    "L7_BOUND_KINDS",
    "SubjectLayer",
    "SUBJECT_LAYER_SOURCE",
    "SUBJECT_LAYER_KINDS",
    "EnforcementReference",
    "all_classification_kinds",
    "all_subject_layers",
    "security_classification_contract",
    "default_security_classification_contracts",
    "SECURITY_INTELLIGENCE_CONTRACT_VERSION",
    "SECURITY_INTELLIGENCE_CONTRACTS",
    "FindingKind",
    "Severity",
    "FindingState",
    "RollupState",
    "BLOCKING_SEVERITIES",
    "OPEN_FINDING_STATES",
    "all_finding_kinds",
    "all_severities",
    "all_finding_states",
    "security_intelligence_contract",
    "default_security_intelligence_contracts",
    # SEC-REG
    "SECURITY_REGISTRY_CONTRACT_VERSION",
    "SECURITY_REGISTRY_CONTRACTS",
    "RegistryKind",
    "REGISTRY_SOURCE",
    "all_registry_kinds",
    "security_registry_contract",
    "default_security_registry_contracts",
    # SEC-OBS
    "SECURITY_OBSERVABILITY_CONTRACT_VERSION",
    "SECURITY_OBSERVABILITY_CONTRACTS",
    "SECURITY_SIGNAL_DIMENSION",
    "security_observability_contract",
    "default_security_observability_contracts",
    # classification
    "SecurityClassification",
    "ClassificationLedger",
    # intelligence
    "FINDING_RECORDED_EVENT",
    "ROLLUP_EVALUATED_EVENT",
    "SECRET_LEAK_IDENTIFIER",
    "SecurityFinding",
    "FindingLedger",
    "SecurityRollup",
    "compute_rollup",
    "scan_for_secret",
    "SecurityIntelligenceEvidence",
    "SecurityIntelligenceService",
    "build_security_intelligence_service",
    # registries
    "REGISTRY_RECORDED_EVENT",
    "RegistryEntry",
    "AppendOnlyRegistry",
    "SecurityRegistrySet",
    "SecurityRegistryEvidence",
    "SecurityRegistryService",
    "build_security_registry_service",
    # observability
    "SECURITY_SIGNAL_EMITTED_EVENT",
    "SECURITY_SIGNAL_METRIC",
    "SECURITY_SIGNAL_AUDIT_ACTION",
    "SecuritySignal",
    "SignalLedger",
    "SecurityObservabilityEvidence",
    "SecurityObservabilityService",
    "build_security_observability_service",
    # service
    "CLASSIFICATION_RECORDED_EVENT",
    "SecurityClassificationEvidence",
    "SecurityClassificationService",
    "build_security_classification_service",
    # bootstrap
    "SECURITY_CLASSIFICATION_BOOTSTRAP_EVENT",
    "bootstrap_security_classification",
    "SECURITY_INTELLIGENCE_BOOTSTRAP_EVENT",
    "bootstrap_security_intelligence",
    "SECURITY_REGISTRY_BOOTSTRAP_EVENT",
    "bootstrap_security_registry",
    "SECURITY_OBSERVABILITY_BOOTSTRAP_EVENT",
    "bootstrap_security_observability",
    # errors
    "SecurityError",
    "SecurityClassificationError",
    "ClassificationBindingError",
    "EnforcementReferenceError",
    "ClassificationValidationError",
    "SecurityContractError",
    "SecurityBootstrapError",
    "SecurityFindingError",
    "FindingValidationError",
    "SecretLeakError",
    "SecurityRollupError",
    "SecurityRegistryError",
    "RegistryEntryError",
    "RegistryValidationError",
    "SecurityObservabilityError",
    "SecuritySignalError",
    "SignalTraceabilityError",
]
