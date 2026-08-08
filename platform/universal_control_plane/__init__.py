"""UCOS-CTRL-000001 — Universal Control Plane public API.

Import the engines directly; this module re-exports the canonical surface so
callers need only ``from platform.universal_control_plane import <Name>``.
"""

from __future__ import annotations

from platform.universal_control_plane.errors import (
    AssignmentError,
    ControlPlaneError,
    DeterminationError,
    DuplicateObjectError,
    EvidenceError,
    ObjectNotFoundError,
    PromptRenderError,
    RegistrationError,
    ReplayError,
    SchedulerError,
    StateTransitionError,
)
from platform.universal_control_plane.execution import AssignmentEngine, Schedule, Scheduler
from platform.universal_control_plane.intelligence import (
    DashboardEngine,
    MetricsEngine,
    ProgressEngine,
)
from platform.universal_control_plane.ontology import (
    DEFAULT_LIFECYCLE,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_ARCHIVED,
    LIFECYCLE_CANCELLED,
    LIFECYCLE_COMPLETE,
    LIFECYCLE_DRAFT,
    LIFECYCLE_PAUSED,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    AgentRecord,
    Assignment,
    BacklogItem,
    Capability,
    Decision,
    DependencyRecord,
    Determination,
    Evidence,
    Goal,
    HistoryEntry,
    Metric,
    Milestone,
    Objective,
    OwnershipRecord,
    ProgressRecord,
    Prompt,
    ReplayRecord,
    ScheduleEntry,
    Universe,
    Vision,
)
from platform.universal_control_plane.plan import BacklogEngine, PlanEngine, RoadmapEngine
from platform.universal_control_plane.prompt import PromptEngine
from platform.universal_control_plane.registry import (
    AgentRegistry,
    CapabilityRegistry,
    DependencyRegistry,
    OwnershipRegistry,
)
from platform.universal_control_plane.state import StateEngine, Transition
from platform.universal_control_plane.trace import (
    DecisionEngine,
    DeterminationEngine,
    EvidenceEngine,
    HistoryEngine,
    ReplayEngine,
)

__all__ = [
    # Errors
    "ControlPlaneError",
    "RegistrationError",
    "StateTransitionError",
    "ObjectNotFoundError",
    "DuplicateObjectError",
    "AssignmentError",
    "PromptRenderError",
    "DeterminationError",
    "ReplayError",
    "EvidenceError",
    "SchedulerError",
    # Lifecycle constants
    "DEFAULT_LIFECYCLE",
    "LIFECYCLE_DRAFT",
    "LIFECYCLE_ACTIVE",
    "LIFECYCLE_PAUSED",
    "LIFECYCLE_COMPLETE",
    "LIFECYCLE_CANCELLED",
    "LIFECYCLE_ARCHIVED",
    "PRIORITY_CRITICAL",
    "PRIORITY_HIGH",
    "PRIORITY_MEDIUM",
    "PRIORITY_LOW",
    # Domain objects
    "Universe",
    "Capability",
    "OwnershipRecord",
    "DependencyRecord",
    "AgentRecord",
    "Vision",
    "Goal",
    "Objective",
    "Milestone",
    "BacklogItem",
    "Assignment",
    "ScheduleEntry",
    "Prompt",
    "Metric",
    "ProgressRecord",
    "Determination",
    "Decision",
    "Evidence",
    "HistoryEntry",
    "ReplayRecord",
    # Engines
    "StateEngine",
    "Transition",
    "CapabilityRegistry",
    "OwnershipRegistry",
    "DependencyRegistry",
    "AgentRegistry",
    "PlanEngine",
    "RoadmapEngine",
    "BacklogEngine",
    "Scheduler",
    "Schedule",
    "AssignmentEngine",
    "PromptEngine",
    "ProgressEngine",
    "MetricsEngine",
    "DashboardEngine",
    "DeterminationEngine",
    "DecisionEngine",
    "HistoryEngine",
    "ReplayEngine",
    "EvidenceEngine",
]
