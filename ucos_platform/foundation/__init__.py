"""UCOS EC-2 Platform Foundation (EC2-EPIC-001) — the reusable platform substrate.

The first implementation epic of the EC-2 Platform Realization Program. It
establishes the foundational framework every subsequent EC-2 epic builds on, as an
**additive** layer over the certified EC-1 engine — it consumes EC-1 only through
published contracts, never modifies it, never writes to the certified corpus
(DP-03), and preserves determinism end to end.

Deliverables (EC2-TASK-000055…000062):
    * **contracts** (TASK-000055) — versioned platform contract surface + canonical
      hashing, reusing EC-1 ``Version``/``Contract``/``ContractRegistry``.
    * **config** (TASK-000056) — typed, immutable platform configuration wrapping the
      EC-1 loader (secrets by reference only).
    * **identity** (TASK-000057) — the platform identity model: roles, permissions,
      immutable content-addressed principals.
    * **services** (TASK-000058) — the deterministic platform service registry.
    * **dependencies** (TASK-000059) — the deterministic, acyclic dependency model.
    * **events** (TASK-000060) — the immutable event model + append-only event bus.
    * **capabilities** (TASK-000061) — the platform + EC-1 engine capability model
      (the encoded EC-1 ↔ EC-2 boundary).
    * **bootstrap** (TASK-000062) — deterministic composition into a ``PlatformContext``.

This epic is **foundation only**: no UI, portal, workspace, dashboard, or runtime
operation is implemented here.
"""

from __future__ import annotations

from ucos_platform.foundation.bootstrap import (
    BOOTSTRAP_EVENT,
    PlatformContext,
    bootstrap_platform,
)
from ucos_platform.foundation.capabilities import (
    Capability,
    CapabilityCatalog,
    CapabilityKind,
    default_capability_catalog,
    default_engine_capabilities,
    default_platform_capabilities,
)
from ucos_platform.foundation.config import (
    Environment,
    PlatformConfig,
    SecretRef,
    load_platform_config,
)
from ucos_platform.foundation.contracts import (
    ENGINE_CONTRACTS,
    PLATFORM_CONTRACT_VERSION,
    PLATFORM_NAME,
    PLATFORM_PROGRAM_ID,
    Contract,
    ContractRef,
    ContractRegistry,
    Version,
    canonical_json,
    content_hash,
    platform_contract,
    platform_contract_registry,
)
from ucos_platform.foundation.dependencies import DependencyGraph, DependencyNode
from ucos_platform.foundation.errors import (
    BootstrapError,
    CapabilityError,
    DependencyError,
    EventError,
    PlatformConfigError,
    PlatformContractError,
    PlatformError,
    PlatformIdentityError,
    ServiceRegistrationError,
    ServiceResolutionError,
)
from ucos_platform.foundation.events import EventBus, EventHandler, PlatformEvent
from ucos_platform.foundation.identity import (
    READ_ONLY_ROLES,
    SCOPED_ROLES,
    Permission,
    Principal,
    Role,
    all_roles,
)
from ucos_platform.foundation.services import (
    ServiceDescriptor,
    ServiceProvider,
    ServiceRegistry,
)

__all__ = [
    # contracts (TASK-000055)
    "PLATFORM_CONTRACT_VERSION",
    "PLATFORM_NAME",
    "PLATFORM_PROGRAM_ID",
    "Version",
    "Contract",
    "ContractRegistry",
    "ContractRef",
    "platform_contract",
    "platform_contract_registry",
    "canonical_json",
    "content_hash",
    "ENGINE_CONTRACTS",
    # config (TASK-000056)
    "Environment",
    "SecretRef",
    "PlatformConfig",
    "load_platform_config",
    # identity (TASK-000057)
    "Role",
    "Permission",
    "Principal",
    "SCOPED_ROLES",
    "READ_ONLY_ROLES",
    "all_roles",
    # services (TASK-000058)
    "ServiceProvider",
    "ServiceDescriptor",
    "ServiceRegistry",
    # dependencies (TASK-000059)
    "DependencyNode",
    "DependencyGraph",
    # events (TASK-000060)
    "EventHandler",
    "PlatformEvent",
    "EventBus",
    # capabilities (TASK-000061)
    "CapabilityKind",
    "Capability",
    "CapabilityCatalog",
    "default_engine_capabilities",
    "default_platform_capabilities",
    "default_capability_catalog",
    # bootstrap (TASK-000062)
    "BOOTSTRAP_EVENT",
    "PlatformContext",
    "bootstrap_platform",
    # errors (TASK-000055)
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
