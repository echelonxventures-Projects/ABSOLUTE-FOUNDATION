"""ULP — the Universal Lineage Projection.

Identity answers **"what is this?"**. Lineage answers **"how did this become this?"**.
This package answers the second by composing governed records that already answer parts of
it, and by owning none of them.

It is a projection, not an authority. ``UCI-001 Part XVI.5``, carried by lifecycle stage
``UCL-S-0350``, states the law it obeys: *"lineage and evolution are DERIVED projections
over recorded history; no new store is created."* Accordingly this package writes no file,
mints no identifier, opens no counter and declares no relation. Deleting it removes a way
of asking a question; it changes no answer the repository already holds.

Four families, each built from the source that owns that meaning, and each keeping its own
question distinct:

    structure     what contains this?     artifacts.json parent
    dependency    what requires this?     declared metadata rows
    derivation    what produced this?     generated-artifact-registry
    supersession  what replaced this?     change-ledger lineage

Transformation — *what happened to this object* — is carried as an EVENT STREAM and never
as an edge, because an event is not a pointer at another object.
"""

from __future__ import annotations

from engine.lineage.model import (
    Classification,
    Family,
    LineageEdge,
    LineageError,
    LineageEvent,
    LineageProjection,
    RelationRule,
)
from engine.lineage.projection import (
    build,
    digest,
    load_classification,
    to_document,
    validate,
    verify,
)
from engine.lineage.query import answer, origin_of, owner_of

__all__ = [
    "Classification",
    "Family",
    "LineageEdge",
    "LineageError",
    "LineageEvent",
    "LineageProjection",
    "RelationRule",
    "answer",
    "build",
    "digest",
    "load_classification",
    "origin_of",
    "owner_of",
    "to_document",
    "validate",
    "verify",
]
