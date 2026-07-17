"""EC2-CAP-SEC-001 — Security Runtime bootstrap (composition entry points).

Composes the implemented Security Runtime sub-capabilities onto a
:class:`~platform.foundation.bootstrap.PlatformContext`, additively and
deterministically:

    * :func:`bootstrap_security_classification` — **SEC-CLASS** (Phase 1): reuses the
      certified L7 Identity Layer as the enforcement seam the classification runtime
      resolves references against (no authorization logic created/invoked); publishes
      the SEC-CLASS contracts; emits ``security.classification.bootstrap.completed``.
    * :func:`bootstrap_security_intelligence` — **SEC-INTEL** (Phase 2): builds the
      record-only intelligence runtime bound to the context event bus; publishes the
      SEC-INTEL contracts; emits ``security.intelligence.bootstrap.completed``.

Each composition binds its service to the context event bus so every recorded action
is a governed event the L8 Observability Layer can audit (PC-16).

Scope guardrail: these compose **SEC-CLASS and SEC-INTEL only**. They start no server,
open no socket, render no UI, write nothing to the certified corpus (DP-03), and
implement no not-yet-authorized sub-capability (SEC-REG / SEC-OBS / SEC-CERT /
SEC-ZONE). They authorize, ratify, and enact nothing (RG-02 / AR-04).
"""

from __future__ import annotations

from platform.foundation.services import ServiceDescriptor
from platform.identity.service import AuthorizationService, bootstrap_identity
from platform.security.contracts import (
    SECURITY_CLASSIFICATION_CONTRACTS,
    SECURITY_INTELLIGENCE_CONTRACTS,
    default_security_classification_contracts,
    default_security_intelligence_contracts,
)
from platform.security.errors import SecurityBootstrapError
from platform.security.intelligence import (
    SecurityIntelligenceService,
    build_security_intelligence_service,
)
from platform.security.service import (
    SecurityClassificationService,
    build_security_classification_service,
)
from typing import Any

#: The event emitted when the Security Classification Runtime is composed.
SECURITY_CLASSIFICATION_BOOTSTRAP_EVENT = "security.classification.bootstrap.completed"

#: The event emitted when the Security Intelligence Runtime is composed.
SECURITY_INTELLIGENCE_BOOTSTRAP_EVENT = "security.intelligence.bootstrap.completed"


def bootstrap_security_classification(
    context: Any,
    *,
    authorization: AuthorizationService | None = None,
) -> SecurityClassificationService:
    """Compose the Security Classification Runtime onto a :class:`PlatformContext`.

    Args:
        context: the composed Platform Foundation context (provides ``services``,
            ``events``, and ``program_id``).
        authorization: an already-composed L7 :class:`AuthorizationService`; when
            ``None`` the certified Identity Layer is bootstrapped onto ``context``
            (idempotent) and reused as the enforcement seam.

    Raises:
        SecurityBootstrapError: on any composition failure (fail-closed).
    """
    try:
        seam = authorization if authorization is not None else bootstrap_identity(context)
        service = build_security_classification_service(
            authorization=seam, events=context.events
        )

        contracts = {c.name: c for c in default_security_classification_contracts()}
        for ref in SECURITY_CLASSIFICATION_CONTRACTS:
            if ref.name in context.services:
                continue
            context.services.register(
                ServiceDescriptor(
                    name=ref.name,
                    contract=contracts[ref.name],
                    capabilities=("PC-02", "PC-16"),
                    description=f"Security Classification Runtime service: {ref.name}.",
                ),
                provider=lambda svc=service: svc,
            )
    except SecurityBootstrapError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalize into a fail-closed error
        raise SecurityBootstrapError(
            "security classification runtime bootstrap failed", detail=str(exc)
        ) from exc

    context.events.publish(
        SECURITY_CLASSIFICATION_BOOTSTRAP_EVENT,
        source="platform.security.bootstrap",
        subject=context.program_id,
        payload={
            "classification_contracts": [ref.name for ref in SECURITY_CLASSIFICATION_CONTRACTS],
            "authorization_bound": service.authorization_bound,
            "ledger_fingerprint": service.ledger.fingerprint(),
        },
    )
    return service


def bootstrap_security_intelligence(
    context: Any,
) -> SecurityIntelligenceService:
    """Compose the Security Intelligence Runtime onto a :class:`PlatformContext`.

    Builds the :class:`~platform.security.intelligence.SecurityIntelligenceService`
    bound to the context event bus (so every recorded finding and roll-up is a
    governed event the L8 Observability Layer can audit), publishes the SEC-INTEL
    contracts into the foundation service registry (contract-first, PL-05), and emits
    a deterministic ``security.intelligence.bootstrap.completed`` event. It records
    and rolls up only; it authorizes, ratifies, and enacts nothing (RG-02 / AR-04),
    stores no secret value (SEC-04 / RR-07), and writes nothing to the corpus (DP-03).

    Raises:
        SecurityBootstrapError: on any composition failure (fail-closed).
    """
    try:
        service = build_security_intelligence_service(events=context.events)

        contracts = {c.name: c for c in default_security_intelligence_contracts()}
        for ref in SECURITY_INTELLIGENCE_CONTRACTS:
            if ref.name in context.services:
                continue
            context.services.register(
                ServiceDescriptor(
                    name=ref.name,
                    contract=contracts[ref.name],
                    capabilities=("PC-02", "PC-16"),
                    description=f"Security Intelligence Runtime service: {ref.name}.",
                ),
                provider=lambda svc=service: svc,
            )
    except SecurityBootstrapError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalize into a fail-closed error
        raise SecurityBootstrapError(
            "security intelligence runtime bootstrap failed", detail=str(exc)
        ) from exc

    context.events.publish(
        SECURITY_INTELLIGENCE_BOOTSTRAP_EVENT,
        source="platform.security.bootstrap",
        subject=context.program_id,
        payload={
            "intelligence_contracts": [ref.name for ref in SECURITY_INTELLIGENCE_CONTRACTS],
            "ledger_fingerprint": service.ledger.fingerprint(),
        },
    )
    return service


__all__ = [
    "SECURITY_CLASSIFICATION_BOOTSTRAP_EVENT",
    "bootstrap_security_classification",
    "SECURITY_INTELLIGENCE_BOOTSTRAP_EVENT",
    "bootstrap_security_intelligence",
]
