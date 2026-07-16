"""TASK-000036 — Provisional-State Disclosure (EPIC-005, DE-05 / C-05 / IP-01).

Every runtime unit the engine assembles must carry the EC-1 **provisional-state
disclosure**: because the external constitutional gates (EC-1…EC-6) remain open,
any deployable artifact produced from a compiled blueprint runs on *provisional
engineering determinations* and asserts **no constitutional finality or authority**
(IP-01, IP-02; Technology Constitution DE-05). This is the enforcement of the
program's core separation between *what may be built* and *what may not be
asserted* (Implementation Master Plan §pipeline).

:func:`inject_provisional_state` stamps a deterministic disclosure onto a
:class:`~engine.runtime.assembly.RuntimeUnit` and embeds the same disclosure into
its runtime descriptor, so the disclosure **survives packaging and deployment
generation** (TASK-000035 copies ``unit.disclosure`` into every deployment and
rollback descriptor and into the generated Kubernetes annotations).

The disclosure is pure data — no secrets, no wall-clock state — so it does not
disturb determinism (IMP-007 §5): identical inputs yield an identical disclosure.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from engine.runtime.errors import DisclosureError

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids an import cycle
    from engine.runtime.assembly import RuntimeUnit

#: Stable identity of the EC-1 provisional-state disclosure.
DISCLOSURE_ID = "EC-1-PROVISIONAL-STATE"

#: Constitution rule that mandates the disclosure and the gate it discloses.
DISCLOSURE_STANDARD = "DE-05"
DISCLOSURE_GATE = "EC-1"

#: The human-readable disclosure statement (IP-01 / DE-05 / C-05).
DISCLOSURE_STATEMENT = (
    "This runtime is generated engineering execution built on provisional "
    "constitutional determinations. The external gates (EC-1) remain open; this "
    "artifact asserts no constitutional finality, authority, or ratification and "
    "holds engineering-execution authority only."
)


def build_disclosure() -> dict[str, Any]:
    """Return the canonical, deterministic EC-1 provisional-state disclosure block."""
    return {
        "disclosure_id": DISCLOSURE_ID,
        "standard": DISCLOSURE_STANDARD,
        "gate": DISCLOSURE_GATE,
        "gate_open": True,
        "asserts_constitutional_finality": False,
        "authority": "ENGINEERING-EXECUTION-ONLY",
        "statement": DISCLOSURE_STATEMENT,
    }


def inject_provisional_state(unit: RuntimeUnit) -> RuntimeUnit:
    """Return a copy of ``unit`` carrying the EC-1 provisional-state disclosure.

    The disclosure is attached to the unit *and* embedded in its runtime
    descriptor under ``provisional_state_disclosure`` so downstream deployment
    generation preserves it (DE-05). The operation is idempotent: re-injecting an
    already-disclosed unit reproduces the identical disclosure.
    """
    disclosure = build_disclosure()
    descriptor = dict(unit.descriptor)
    descriptor["provisional_state_disclosure"] = disclosure
    return replace(unit, disclosure=disclosure, descriptor=descriptor)


def disclosure_present(disclosure: dict[str, Any] | None) -> bool:
    """True iff ``disclosure`` is a well-formed EC-1 provisional-state disclosure."""
    if not isinstance(disclosure, dict):
        return False
    return (
        disclosure.get("disclosure_id") == DISCLOSURE_ID
        and disclosure.get("gate") == DISCLOSURE_GATE
        and disclosure.get("asserts_constitutional_finality") is False
        and bool(disclosure.get("statement"))
    )


def require_disclosure(disclosure: dict[str, Any] | None) -> dict[str, Any]:
    """Return ``disclosure`` if present and well-formed, else raise (DE-05)."""
    if not disclosure_present(disclosure):
        raise DisclosureError(
            "EC-1 provisional-state disclosure is required while gates are open",
            standard=DISCLOSURE_STANDARD,
            gate=DISCLOSURE_GATE,
        )
    return dict(disclosure) if disclosure is not None else {}


__all__ = [
    "DISCLOSURE_ID",
    "DISCLOSURE_STANDARD",
    "DISCLOSURE_GATE",
    "DISCLOSURE_STATEMENT",
    "build_disclosure",
    "inject_provisional_state",
    "disclosure_present",
    "require_disclosure",
]
