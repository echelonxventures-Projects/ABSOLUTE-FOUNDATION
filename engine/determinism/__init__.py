"""EC-1 Determinism Framework (EPIC-004) — constitutional determinism, measured.

Proves that identical certified blueprint inputs produce byte-identical outputs
across independent executions (IMP-007 §5). Built additively on the EC-1
Foundation (EPIC-001), Registry Adapter (EPIC-002), and Universal Compiler
(EPIC-003), which it reuses verbatim (Mandatory Rule 4). It writes only to
caller-provided locations and never to the certified corpus (DP-03).

Tasks: TASK-000031 (hermetic build controls), TASK-000032 (reproducibility
harness), TASK-000033 (determinism CI gate).
"""

from __future__ import annotations

from engine.determinism.errors import (
    BlueprintResolutionError,
    DependencyLockError,
    DeterminismError,
    HermeticViolation,
    NonDeterministicOutputError,
    ReproducibilityError,
    ToolchainError,
)
from engine.determinism.hermetic import (
    NORMALIZED_ENVIRONMENT,
    NORMALIZED_LOCALE,
    NORMALIZED_TIMESTAMP,
    NORMALIZED_TIMEZONE,
    PINNED_PYTHON,
    PYTHON_REQUIRES,
    SOURCE_DATE_EPOCH,
    DependencyLockReport,
    HermeticEnvironment,
    hermetic_env,
)
from engine.determinism.reproduce import (
    CATEGORIES,
    DEFAULT_BLUEPRINTS_DIR,
    DEFAULT_SIGNING_KEY,
    BlueprintProvider,
    DirectoryBlueprintProvider,
    FileDiff,
    ReproducibilityResult,
    compare_builds,
    double_build,
)

__all__ = [
    # hermetic controls
    "hermetic_env",
    "HermeticEnvironment",
    "DependencyLockReport",
    "PINNED_PYTHON",
    "PYTHON_REQUIRES",
    "SOURCE_DATE_EPOCH",
    "NORMALIZED_TIMESTAMP",
    "NORMALIZED_LOCALE",
    "NORMALIZED_TIMEZONE",
    "NORMALIZED_ENVIRONMENT",
    # reproducibility harness
    "double_build",
    "compare_builds",
    "ReproducibilityResult",
    "FileDiff",
    "BlueprintProvider",
    "DirectoryBlueprintProvider",
    "DEFAULT_BLUEPRINTS_DIR",
    "DEFAULT_SIGNING_KEY",
    "CATEGORIES",
    # errors
    "DeterminismError",
    "ToolchainError",
    "DependencyLockError",
    "HermeticViolation",
    "BlueprintResolutionError",
    "ReproducibilityError",
    "NonDeterministicOutputError",
]
