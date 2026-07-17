"""EC2-CAP-SEC-001 / SEC-CLASS — Security Runtime error taxonomy (Phase 1).

The Security Runtime **reuses** the EC-2 Platform Foundation error discipline
(:class:`~platform.foundation.errors.PlatformError`) additively — it does not fork or
modify it. Every security error is rooted in :class:`SecurityError`, carries a stable,
category-prefixed ``code`` (``EC2-SEC-*``) and structured, non-secret ``context`` so
failures are auditable (PL-02, IP-12) and machine-consumable.

Scope note (mission boundary): this module ships only the errors the **SEC-CLASS**
(Security Classification Runtime) sub-capability needs. The base
:class:`SecurityError` is defined here because SEC-CLASS requires it; no error for a
future sub-capability (SEC-INTEL / SEC-REG / SEC-OBS / SEC-CERT / SEC-ZONE) is
declared. Every error stores **no** secret value (SEC-04 / RR-07).
"""

from __future__ import annotations

from platform.foundation.errors import PlatformError


class SecurityError(PlatformError):
    """Base class for all EC2-CAP-SEC-001 Security Runtime errors."""

    code = "EC2-SEC-000"


class SecurityClassificationError(SecurityError):
    """A security classification record is malformed or violates non-enforcement."""

    code = "EC2-SEC-CLASS-001"


class ClassificationBindingError(SecurityError):
    """A classification could not be bound to a construct, or the binding is malformed."""

    code = "EC2-SEC-CLASS-002"


class EnforcementReferenceError(SecurityError):
    """A declared enforcement obligation does not resolve to the existing L7 seam."""

    code = "EC2-SEC-CLASS-003"


class ClassificationValidationError(SecurityError):
    """A classification failed meta-validity (typed / identified / non-enforcing / resolvable)."""

    code = "EC2-SEC-CLASS-004"


class SecurityContractError(SecurityError):
    """A security contract is malformed or violates versioning discipline (AR-03/PL-05)."""

    code = "EC2-SEC-CONTRACT-001"


class SecurityBootstrapError(SecurityError):
    """The Security Classification Runtime could not be composed (fail-closed)."""

    code = "EC2-SEC-BOOTSTRAP-001"


__all__ = [
    "SecurityError",
    "SecurityClassificationError",
    "ClassificationBindingError",
    "EnforcementReferenceError",
    "ClassificationValidationError",
    "SecurityContractError",
    "SecurityBootstrapError",
]
