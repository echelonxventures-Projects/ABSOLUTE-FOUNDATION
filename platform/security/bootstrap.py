"""EC2-CAP-SEC-001 / SEC-CLASS — Security Classification bootstrap (Phase 1).

Composes the **Security Classification Runtime** onto a
:class:`~platform.foundation.bootstrap.PlatformContext`, additively and
deterministically. The bootstrap:

    1. reuses the certified L7 Identity Layer (``bootstrap_identity``) as the
       enforcement seam the classification runtime resolves references against — no
       authorization logic is created or invoked here;
    2. builds the :class:`~platform.security.service.SecurityClassificationService`
       bound to the context event bus (so every recorded classification is a governed
       event the L8 Observability Layer can audit) and to the L7 seam (reference-only);
    3. publishes the SEC-CLASS contracts into the foundation service registry
       (contract-first, PL-05);
    4. emits a deterministic ``security.classification.bootstrap.completed`` event.

Scope guardrail: this composes **SEC-CLASS only**. It starts no server, opens no
socket, renders no UI, writes nothing to the certified corpus (DP-03), and implements
no other Security Runtime sub-capability (SEC-INTEL / SEC-REG / SEC-OBS / SEC-CERT /
SEC-ZONE are later phases). It authorizes nothing (RG-02 / AR-04).
"""

from __future__ import annotations

from platform.foundation.services import ServiceDescriptor
from platform.identity.service import AuthorizationService, bootstrap_identity
from platform.security.contracts import (
    SECURITY_CLASSIFICATION_CONTRACTS,
    default_security_classification_contracts,
)
from platform.security.errors import SecurityBootstrapError
from platform.security.service import (
    SecurityClassificationService,
    build_security_classification_service,
)
from typing import Any

#: The event emitted when the Security Classification Runtime is composed.
SECURITY_CLASSIFICATION_BOOTSTRAP_EVENT = "security.classification.bootstrap.completed"


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


__all__ = [
    "SECURITY_CLASSIFICATION_BOOTSTRAP_EVENT",
    "bootstrap_security_classification",
]
