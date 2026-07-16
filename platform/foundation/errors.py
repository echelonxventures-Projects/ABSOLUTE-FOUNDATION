"""EC2-TASK-000055 — Platform Foundation error taxonomy (EC2-EPIC-001).

The Platform Foundation **reuses** the EC-1 Foundation error discipline
(TASK-000006) additively — it does not fork or modify it. Every platform error is
rooted in :class:`~engine.foundation.obs.errors.FoundationError`, carries a stable,
category-prefixed ``code`` (``EC2-*``) and structured, non-secret ``context`` so
failures are auditable (PL-02, IP-12) and machine-consumable by TRACK-001.

The Platform Foundation is *additive over EC-1*: it consumes the certified EC-1
engine only through published contracts, never modifies it, and never writes to the
certified corpus (DP-03). A malformed platform contract, configuration, identity,
service registration, dependency graph, event, capability, or bootstrap fails loudly
with a specific error. The base class is named :class:`PlatformError` so it never
shadows EC-1 / compiler / validation / certification error hierarchies.
"""

from __future__ import annotations

from engine.foundation.obs.errors import FoundationError


class PlatformError(FoundationError):
    """Base class for all EC-2 Platform Foundation errors."""

    code = "EC2-000"


class PlatformContractError(PlatformError):
    """A platform contract is malformed or violates versioning discipline (AR-03/PL-05)."""

    code = "EC2-CONTRACT-001"


class PlatformConfigError(PlatformError):
    """Platform configuration is invalid, missing, or malformed."""

    code = "EC2-CONFIG-001"


class PlatformIdentityError(PlatformError):
    """A platform principal, role, or permission set is malformed."""

    code = "EC2-IDENTITY-001"


class ServiceRegistrationError(PlatformError):
    """A platform service could not be registered (duplicate or malformed)."""

    code = "EC2-SERVICE-001"


class ServiceResolutionError(PlatformError):
    """A platform service could not be resolved from the registry."""

    code = "EC2-SERVICE-002"


class DependencyError(PlatformError):
    """A platform dependency is unresolved or the dependency graph has a cycle."""

    code = "EC2-DEPENDENCY-001"


class EventError(PlatformError):
    """A platform event or event-bus operation is malformed."""

    code = "EC2-EVENT-001"


class CapabilityError(PlatformError):
    """A platform or engine capability is malformed or references an unknown dependency."""

    code = "EC2-CAPABILITY-001"


class BootstrapError(PlatformError):
    """The platform foundation could not be composed (bootstrap failed, fail-closed)."""

    code = "EC2-BOOTSTRAP-001"


__all__ = [
    "PlatformError",
    "PlatformContractError",
    "PlatformConfigError",
    "PlatformIdentityError",
    "ServiceRegistrationError",
    "ServiceResolutionError",
    "DependencyError",
    "EventError",
    "CapabilityError",
    "BootstrapError",
]
