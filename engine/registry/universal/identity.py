"""UCOS-EPIC-001 — Registry Core identity: deterministic IDs + canonical hashing.

The Universal Registry Platform assigns **deterministic** universal identifiers
(Requirement: *Deterministic IDs*). An identifier is a pure function of an
artifact's *identity tuple* — ``(kind, namespace, natural_key)`` — so the same
logical artifact always resolves to the same ``universal_id`` regardless of
version, wall-clock, machine, or registration order. This is what makes the
platform a *single registration authority*: two independent attempts to register
the same thing collapse onto one identity, enabling duplicate detection and a
single canonical version chain (Knowledge Once).

Canonical hashing (``canonical_json`` + SHA-256) is reused for content digests so
that *Knowledge Once* can be enforced by content equality and so the audit trail
is tamper-evident. Stdlib-only (TP-04/TP-05); no wall-clock, RNG, or network on
the determined path (RC-4 determinism).
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from engine.registry.universal.errors import NamespaceError, RegistrationValidationError

# The canonical serialization primitive has exactly one definition, in UCKP Layer Zero
# (UCKP-LAW-0001 Art-13, UCKP-INV-03). ``content_digest`` is this layer's historical
# name for the digest and is kept as an alias, so no caller has to move.
from engine.uckp.canonical import canonical_json, content_hash

#: The fixed identifier authority prefix for every registered artifact.
ID_PREFIX = "UCOS"

#: Length (hex chars) of the deterministic identity digest embedded in an id.
_ID_DIGEST_LEN = 12

#: A namespace is a dotted, lower-case path of ``[a-z0-9-]`` segments, e.g.
#: ``ucos.platform.registry`` — bounded, deterministic, and human-legible.
_NAMESPACE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*$")

#: A natural key is a non-empty, whitespace-free stable business key.
_NATURAL_KEY_RE = re.compile(r"^\S+$")


class RegistryKind(str, Enum):
    """The kinds of artifact the Universal Registry Platform governs.

    Each kind owns a distinct id ``code`` segment (aligned with existing UCOS
    prefixes — Repository Truth) so an identifier is self-describing and the
    thirteen registries never collide in identity space.
    """

    NAMESPACE = "NAMESPACE"
    CAPABILITY = "CAPABILITY"
    DOCUMENT = "DOCUMENT"
    ENGINE = "ENGINE"
    COMPONENT = "COMPONENT"
    API = "API"
    SERVICE = "SERVICE"
    APPLICATION = "APPLICATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    DEPENDENCY = "DEPENDENCY"
    EVIDENCE = "EVIDENCE"
    CERTIFICATION = "CERTIFICATION"
    CONTEXT = "CONTEXT"

    @property
    def code(self) -> str:
        """The id code segment for this kind (e.g. ``SVC`` for ``SERVICE``)."""
        return _KIND_CODES[self]

    @classmethod
    def coerce(cls, value: Any) -> RegistryKind:
        """Return the enum member for ``value`` or raise a validation error."""
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value))
        except ValueError as exc:
            raise RegistrationValidationError(
                "unknown registry kind",
                value=value,
                allowed=[k.value for k in cls],
            ) from exc


#: Kind → id code. Codes reuse the established UCOS native prefixes so registered
#: identities are consistent with the certified corpus vocabulary (Repository
#: Truth). Codes are unique so ``kind`` is recoverable from an identifier.
_KIND_CODES: dict[RegistryKind, str] = {
    RegistryKind.NAMESPACE: "NS",
    RegistryKind.CAPABILITY: "CAP",
    RegistryKind.DOCUMENT: "DOC",
    RegistryKind.ENGINE: "ENG",
    RegistryKind.COMPONENT: "CMP",
    RegistryKind.API: "API",
    RegistryKind.SERVICE: "SVC",
    RegistryKind.APPLICATION: "APP",
    RegistryKind.INFRASTRUCTURE: "INF",
    RegistryKind.DEPENDENCY: "DEP",
    RegistryKind.EVIDENCE: "EVD",
    RegistryKind.CERTIFICATION: "CERT",
    # UCXI-000001 — Universal Context Intelligence registers context as a first-class
    # artifact kind, so context identities are minted by this single registration
    # authority rather than by a parallel identity scheme.
    RegistryKind.CONTEXT: "CTX",
}

#: Reverse map (id code → kind), used to parse/verify identifiers.
_CODE_KINDS: dict[str, RegistryKind] = {code: kind for kind, code in _KIND_CODES.items()}


#: This layer's historical name for the canonical digest. An alias, not a second
#: implementation: one primitive, two names, so the rename never became a fork.
content_digest = content_hash


def normalize_namespace(namespace: Any) -> str:
    """Validate and normalise a namespace string (lower-cased, trimmed).

    Raises:
        NamespaceError: the namespace is empty or not a dotted ``[a-z0-9-]`` path.
    """
    if not isinstance(namespace, str) or not namespace.strip():
        raise NamespaceError("namespace is required", value=namespace)
    candidate = namespace.strip().lower()
    if not _NAMESPACE_RE.match(candidate):
        raise NamespaceError(
            "namespace must be a dotted path of [a-z0-9-] segments",
            value=namespace,
        )
    return candidate


def normalize_natural_key(natural_key: Any) -> str:
    """Validate a natural (business) key: a non-empty, whitespace-free token."""
    if not isinstance(natural_key, str) or not _NATURAL_KEY_RE.match(natural_key.strip()):
        raise RegistrationValidationError(
            "natural_key must be a non-empty, whitespace-free token",
            value=natural_key,
        )
    return natural_key.strip()


def identity_tuple(kind: RegistryKind, namespace: str, natural_key: str) -> tuple[str, str, str]:
    """Return the normalised identity tuple ``(code, namespace, natural_key)``."""
    return (
        RegistryKind.coerce(kind).code,
        normalize_namespace(namespace),
        normalize_natural_key(natural_key),
    )


def deterministic_id(kind: RegistryKind, namespace: str, natural_key: str) -> str:
    """Compute the deterministic ``universal_id`` for an identity tuple.

    The identifier has the shape ``UCOS-<CODE>-<12 hex>`` where the digest is the
    leading 12 hex chars of the SHA-256 over the canonical identity tuple. It is
    **version-independent**: every version of the same artifact shares one id.
    """
    code, ns, key = identity_tuple(kind, namespace, natural_key)
    digest = content_hash([code, ns, key])
    return f"{ID_PREFIX}-{code}-{digest[:_ID_DIGEST_LEN]}"


def parse_kind(universal_id: str) -> RegistryKind:
    """Recover the :class:`RegistryKind` encoded in a ``universal_id``.

    Raises:
        RegistrationValidationError: the id is not a well-formed platform id.
    """
    parts = str(universal_id).split("-")
    if len(parts) != 3 or parts[0] != ID_PREFIX or parts[2] == "" or parts[1] not in _CODE_KINDS:
        raise RegistrationValidationError("not a well-formed universal id", value=universal_id)
    return _CODE_KINDS[parts[1]]


__all__ = [
    "ID_PREFIX",
    "RegistryKind",
    "canonical_json",
    "content_digest",
    "normalize_namespace",
    "normalize_natural_key",
    "identity_tuple",
    "deterministic_id",
    "parse_kind",
]
