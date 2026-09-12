"""UCOS-OMEGA-001 — Universal Discovery: governance derived from executable reality.

AUTHORITY = NONE (DERIVED TRUTH). This package legislates nothing and owns no lifecycle. It
measures, and the measurement's only input is ``git ls-files '*.py'``.

THE ONE CLAIM. No governance verdict in this package quantifies over a list a human wrote. Scope,
authority, reachability, disposition and every threshold are functions of the discovered
population, so a top-level tree that does not exist yet is already governed: the commit that
creates ``quantum/`` puts it inside every measurement here, with no edit to any file.

Read ``model.py`` first — it states the five dispositions and the four ratchet kinds, and why
each is a measurement rather than a preference.

THE PACKAGE ROOT IMPORTS NOTHING, AND THE REASON IS A MEASUREMENT. This file used to import
``model`` eagerly, and pytest loads the package before coverage starts because
``engine.universal_discovery.pytest_scope`` is registered with ``-p``. Every line of ``model.py``
that runs at import — the dispositions, the ratchet kinds, the frozen dataclasses — executed
outside the collector and reported as a miss no test could reach: 62 statements, measured in the
combined shard report while the same suite run with an explicit ``--cov`` (which takes the
plugin's early return and imports nothing here) reported them covered. The names below are still
importable as package attributes, in both spellings — ``from engine.universal_discovery import
MEASURED`` and ``engine.universal_discovery.model`` — but they arrive through ``__getattr__``
(PEP 562), so the package root now costs three statements and the modules measure themselves when
real code first asks for them.
"""

from typing import Any

#: The model names this package re-exports, and the module that owns them. A mapping, because a
#: second `from X import ...` here would be the eager import this file exists to end.
_MODEL_NAMES = frozenset(
    {
        "ARCHIVED",
        "AUTHORITY_REQUIRED",
        "CONVERGENT",
        "DENSITY",
        "DISPOSITIONS",
        "ENTROPY",
        "EXEMPTED",
        "GENERATED",
        "MEASURED",
        "MONOTONIC",
        "RATCHET_KINDS",
        "TRANSIENT",
        "Artifact",
        "Observation",
        "OmegaError",
        "Population",
    }
)

__all__ = sorted(_MODEL_NAMES)


def __getattr__(name: str) -> Any:
    """Resolve a re-exported name by importing its owning module, once, on first use."""
    if name in _MODEL_NAMES:
        from engine.universal_discovery import model

        return getattr(model, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(globals()))
