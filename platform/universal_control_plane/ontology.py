"""UCOS-CTRL-000001 — Universal Control Plane domain model.

Every concept the Control Plane governs is an immutable value object here.
Identity is derived from content (content-addressed); no wall-clock appears in
any identifier — callers supply a logical ``tick`` (monotonic integer).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Identity helpers
# ---------------------------------------------------------------------------


def _digest(payload: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON of *payload*, truncated to 16 hex chars."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _id(namespace: str, natural_key: str, tick: int) -> str:
    return _digest({"ns": namespace, "key": natural_key, "tick": tick})


# ---------------------------------------------------------------------------
# Lifecycle state tokens — open; projects extend via StateEngine.
# ---------------------------------------------------------------------------

LIFECYCLE_DRAFT = "DRAFT"
LIFECYCLE_ACTIVE = "ACTIVE"
LIFECYCLE_PAUSED = "PAUSED"
LIFECYCLE_COMPLETE = "COMPLETE"
LIFECYCLE_CANCELLED = "CANCELLED"
LIFECYCLE_ARCHIVED = "ARCHIVED"

DEFAULT_LIFECYCLE: tuple[str, ...] = (
    LIFECYCLE_DRAFT,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_PAUSED,
    LIFECYCLE_COMPLETE,
    LIFECYCLE_CANCELLED,
    LIFECYCLE_ARCHIVED,
)

# Priority tokens
PRIORITY_CRITICAL = "CRITICAL"
PRIORITY_HIGH = "HIGH"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_LOW = "LOW"


# ---------------------------------------------------------------------------
# Registry objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Universe:
    """A registered sovereign universe in the Control Plane."""

    universe_id: str
    name: str
    description: str = ""
    state: str = LIFECYCLE_ACTIVE
    version: str = "1.0.0"
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.universe", self.universe_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Universe",
            "identity": self.identity,
            "universe_id": self.universe_id,
            "name": self.name,
            "description": self.description,
            "state": self.state,
            "version": self.version,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class Capability:
    """A registered capability owned by a universe."""

    capability_id: str
    universe_id: str
    name: str
    description: str = ""
    state: str = LIFECYCLE_ACTIVE
    version: str = "1.0.0"
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.capability", self.capability_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Capability",
            "identity": self.identity,
            "capability_id": self.capability_id,
            "universe_id": self.universe_id,
            "name": self.name,
            "description": self.description,
            "state": self.state,
            "version": self.version,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class OwnershipRecord:
    """A declared ownership binding: one owner holds one capability."""

    ownership_id: str
    capability_id: str
    owner_id: str
    owner_kind: str  # "Universe" | "Agent" | open token
    rationale: str = ""
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.ownership", self.ownership_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "OwnershipRecord",
            "identity": self.identity,
            "ownership_id": self.ownership_id,
            "capability_id": self.capability_id,
            "owner_id": self.owner_id,
            "owner_kind": self.owner_kind,
            "rationale": self.rationale,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class DependencyRecord:
    """A registered dependency edge: *from_id* depends on *to_id*."""

    dependency_id: str
    from_id: str
    to_id: str
    kind: str = "REQUIRES"  # REQUIRES | EXTENDS | CONSUMES | open token
    optional: bool = False
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.dependency", self.dependency_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "DependencyRecord",
            "identity": self.identity,
            "dependency_id": self.dependency_id,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "dependency_kind": self.kind,
            "optional": self.optional,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class AgentRecord:
    """A registered execution agent."""

    agent_id: str
    name: str
    kind: str = "AUTONOMOUS"  # AUTONOMOUS | HUMAN | HYBRID | open token
    capabilities: tuple[str, ...] = ()
    state: str = LIFECYCLE_ACTIVE
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.agent", self.agent_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "AgentRecord",
            "identity": self.identity,
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_kind": self.kind,
            "capabilities": list(self.capabilities),
            "state": self.state,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


# ---------------------------------------------------------------------------
# Planning hierarchy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Vision:
    """The long-term directional declaration for a universe."""

    vision_id: str
    universe_id: str
    statement: str
    state: str = LIFECYCLE_ACTIVE
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.vision", self.vision_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Vision",
            "identity": self.identity,
            "vision_id": self.vision_id,
            "universe_id": self.universe_id,
            "statement": self.statement,
            "state": self.state,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class Goal:
    """A strategic goal tied to a vision."""

    goal_id: str
    vision_id: str
    title: str
    description: str = ""
    priority: str = PRIORITY_MEDIUM
    state: str = LIFECYCLE_DRAFT
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.goal", self.goal_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Goal",
            "identity": self.identity,
            "goal_id": self.goal_id,
            "vision_id": self.vision_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "state": self.state,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class Objective:
    """A measurable, verifiable target tied to a goal."""

    objective_id: str
    goal_id: str
    title: str
    success_criteria: str
    description: str = ""
    priority: str = PRIORITY_MEDIUM
    state: str = LIFECYCLE_DRAFT
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.objective", self.objective_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Objective",
            "identity": self.identity,
            "objective_id": self.objective_id,
            "goal_id": self.goal_id,
            "title": self.title,
            "success_criteria": self.success_criteria,
            "description": self.description,
            "priority": self.priority,
            "state": self.state,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class Milestone:
    """A verifiable checkpoint with a logical sequence position."""

    milestone_id: str
    universe_id: str
    title: str
    description: str = ""
    sequence: int = 0
    objective_ids: tuple[str, ...] = ()
    state: str = LIFECYCLE_DRAFT
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.milestone", self.milestone_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Milestone",
            "identity": self.identity,
            "milestone_id": self.milestone_id,
            "universe_id": self.universe_id,
            "title": self.title,
            "description": self.description,
            "sequence": self.sequence,
            "objective_ids": list(self.objective_ids),
            "state": self.state,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


# ---------------------------------------------------------------------------
# Execution layer
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BacklogItem:
    """A unit of planned work in the universal backlog."""

    item_id: str
    universe_id: str
    title: str
    description: str = ""
    priority: str = PRIORITY_MEDIUM
    milestone_id: str = ""
    objective_id: str = ""
    state: str = LIFECYCLE_DRAFT
    estimate: int = 0  # logical effort units; meaning is open
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.backlog", self.item_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "BacklogItem",
            "identity": self.identity,
            "item_id": self.item_id,
            "universe_id": self.universe_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "milestone_id": self.milestone_id,
            "objective_id": self.objective_id,
            "state": self.state,
            "estimate": self.estimate,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class Assignment:
    """A binding of a backlog item to an agent."""

    assignment_id: str
    item_id: str
    agent_id: str
    rationale: str = ""
    state: str = LIFECYCLE_ACTIVE
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.assignment", self.assignment_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Assignment",
            "identity": self.identity,
            "assignment_id": self.assignment_id,
            "item_id": self.item_id,
            "agent_id": self.agent_id,
            "rationale": self.rationale,
            "state": self.state,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class ScheduleEntry:
    """A scheduler-produced directive: item at logical position in a wave."""

    entry_id: str
    item_id: str
    agent_id: str
    position: int
    wave: int = 0
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.schedule_entry", self.entry_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "ScheduleEntry",
            "identity": self.identity,
            "entry_id": self.entry_id,
            "item_id": self.item_id,
            "agent_id": self.agent_id,
            "position": self.position,
            "wave": self.wave,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


# ---------------------------------------------------------------------------
# Intelligence and traceability objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Prompt:
    """A generated agent prompt with full context."""

    prompt_id: str
    item_id: str
    agent_id: str
    universe_id: str
    text: str
    context_digest: str = ""
    template_id: str = ""
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.prompt", self.prompt_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Prompt",
            "identity": self.identity,
            "prompt_id": self.prompt_id,
            "item_id": self.item_id,
            "agent_id": self.agent_id,
            "universe_id": self.universe_id,
            "text": self.text,
            "context_digest": self.context_digest,
            "template_id": self.template_id,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class Metric:
    """A single measured value at a logical point in time."""

    metric_id: str
    subject_id: str
    name: str
    value: float
    unit: str = ""
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.metric", self.metric_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Metric",
            "identity": self.identity,
            "metric_id": self.metric_id,
            "subject_id": self.subject_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class ProgressRecord:
    """A measured progress snapshot for a subject."""

    record_id: str
    subject_id: str
    total: int
    completed: int
    state: str = LIFECYCLE_ACTIVE
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.progress", self.record_id, self.tick)

    @property
    def percentage(self) -> float:
        return (self.completed / self.total * 100.0) if self.total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "ProgressRecord",
            "identity": self.identity,
            "record_id": self.record_id,
            "subject_id": self.subject_id,
            "total": self.total,
            "completed": self.completed,
            "percentage": round(self.percentage, 2),
            "state": self.state,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class Determination:
    """A recorded determination: what was measured, what was decided."""

    determination_id: str
    subject_id: str
    verdict: str  # AUTHORIZED | BLOCKED | DEFERRED | open token
    rationale: str
    evidence_ids: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.determination", self.determination_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Determination",
            "identity": self.identity,
            "determination_id": self.determination_id,
            "subject_id": self.subject_id,
            "verdict": self.verdict,
            "rationale": self.rationale,
            "evidence_ids": list(self.evidence_ids),
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class Decision:
    """A recorded decision with rationale and alternatives considered."""

    decision_id: str
    subject_id: str
    title: str
    choice: str
    rationale: str
    alternatives: tuple[str, ...] = ()
    determination_id: str = ""
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.decision", self.decision_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Decision",
            "identity": self.identity,
            "decision_id": self.decision_id,
            "subject_id": self.subject_id,
            "title": self.title,
            "choice": self.choice,
            "rationale": self.rationale,
            "alternatives": list(self.alternatives),
            "determination_id": self.determination_id,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class Evidence:
    """A content-addressed evidence record."""

    evidence_id: str
    subject_id: str
    kind: str  # MEASUREMENT | TEST | AUDIT | REVIEW | open token
    claim: str
    payload_digest: str
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.evidence", self.evidence_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "Evidence",
            "identity": self.identity,
            "evidence_id": self.evidence_id,
            "subject_id": self.subject_id,
            "evidence_kind": self.kind,
            "claim": self.claim,
            "payload_digest": self.payload_digest,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class HistoryEntry:
    """An append-only entry in the control-plane history log."""

    entry_id: str
    subject_id: str
    event: str  # STATE_CHANGED | ASSIGNED | DETERMINED | open token
    detail: str = ""
    actor_id: str = ""
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.history", self.entry_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "HistoryEntry",
            "identity": self.identity,
            "entry_id": self.entry_id,
            "subject_id": self.subject_id,
            "event": self.event,
            "detail": self.detail,
            "actor_id": self.actor_id,
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class ReplayRecord:
    """A replayable execution record binding inputs to outputs."""

    replay_id: str
    subject_id: str
    inputs_digest: str
    outputs_digest: str
    history_ids: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)
    tick: int = 0

    @property
    def identity(self) -> str:
        return _id("ctrl.replay", self.replay_id, self.tick)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "ReplayRecord",
            "identity": self.identity,
            "replay_id": self.replay_id,
            "subject_id": self.subject_id,
            "inputs_digest": self.inputs_digest,
            "outputs_digest": self.outputs_digest,
            "history_ids": list(self.history_ids),
            "tick": self.tick,
            "attributes": dict(self.attributes),
        }
