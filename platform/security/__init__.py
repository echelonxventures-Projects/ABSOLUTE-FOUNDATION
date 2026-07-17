"""UCOS EC-2 Platform Security Runtime (EC2-CAP-SEC-001) — SEC-CLASS (Phase 1).

The Security Runtime is the runtime realization of the existing constitutional
security architecture (``ARCH-SECURITY-001``), determined in
``platform/security/EC2-CAP-SEC-001-DETERMINATION.md``. It is a **governed, additive,
record-only** platform runtime composed over the certified EC-1 engine and the EC-2
Foundation / Identity / Observability layers: it consumes them only through published
contracts, modifies none, never writes to the certified corpus (DP-03), remains
deterministic, and preserves every EC-1 certification.

**This package currently ships only Phase 1 — SEC-CLASS (Security Classification
Runtime)** — the constitutional "enforcement-by-reference seam". SEC-CLASS
**classifies, records, traces, validates, and reports** the subject-layer security
classification records (DATA-014 / SERVICE-014 / APPLICATION-013 / INFRASTRUCTURE-013)
and resolves their declared enforcement obligation to the certified L7
:class:`~platform.identity.service.AuthorizationService` seam **by reference only**.
It **never** authorizes, ratifies, enacts, governs, overrides, or escalates authority
(RG-02 / AR-04).

The remaining Security Runtime sub-capabilities (SEC-INTEL / SEC-REG / SEC-OBS /
SEC-CERT / SEC-ZONE) are later, separately-authorized phases and are **not** present.

Deliverables (SEC-CLASS):
    * **errors** — the ``EC2-SEC-*`` error taxonomy over ``PlatformError``.
    * **contracts** — the classification vocabulary (``ClassificationKind``,
      ``SubjectLayer``, ``EnforcementReference``) and the published SEC-CLASS contract
      surface.
    * **classification** — the immutable ``SecurityClassification`` record and the
      append-only ``ClassificationLedger``.
    * **service** — the ``SecurityClassificationService`` composition root and
      ``SecurityClassificationEvidence``.
    * **bootstrap** — ``bootstrap_security_classification`` (composes identity + the
      classification runtime onto a ``PlatformContext``).

This package carries no constitutional authority; the external gates (EC-1…EC-6)
remain open.
"""

from __future__ import annotations

from platform.security.bootstrap import (
    SECURITY_CLASSIFICATION_BOOTSTRAP_EVENT,
    bootstrap_security_classification,
)
from platform.security.classification import (
    ClassificationLedger,
    SecurityClassification,
)
from platform.security.contracts import (
    L7_BOUND_KINDS,
    SECURITY_CLASSIFICATION_CONTRACT_VERSION,
    SECURITY_CLASSIFICATION_CONTRACTS,
    SUBJECT_LAYER_KINDS,
    SUBJECT_LAYER_SOURCE,
    ClassificationKind,
    EnforcementReference,
    SubjectLayer,
    all_classification_kinds,
    all_subject_layers,
    default_security_classification_contracts,
    security_classification_contract,
)
from platform.security.errors import (
    ClassificationBindingError,
    ClassificationValidationError,
    EnforcementReferenceError,
    SecurityBootstrapError,
    SecurityClassificationError,
    SecurityContractError,
    SecurityError,
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
    # classification
    "SecurityClassification",
    "ClassificationLedger",
    # service
    "CLASSIFICATION_RECORDED_EVENT",
    "SecurityClassificationEvidence",
    "SecurityClassificationService",
    "build_security_classification_service",
    # bootstrap
    "SECURITY_CLASSIFICATION_BOOTSTRAP_EVENT",
    "bootstrap_security_classification",
    # errors
    "SecurityError",
    "SecurityClassificationError",
    "ClassificationBindingError",
    "EnforcementReferenceError",
    "ClassificationValidationError",
    "SecurityContractError",
    "SecurityBootstrapError",
]
