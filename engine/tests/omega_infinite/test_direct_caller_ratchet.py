"""INV-AGN-02 — a new bypass is refused, and every declared capability is kept.

Two properties, and the second is what makes the first honest. A ratchet on direct callers only
means something if the provider can actually answer the questions those callers ask; before the
capability dispatch existed it declared five capabilities and delivered one, so a caller needing a
content hash had no alternative and counting it as a bypass would have charged the provider's own
gap to its callers.
"""

from __future__ import annotations

import pytest

from engine.omega_infinite.capability import (
    AUTHORITY_METADATA,
    CONTENT_HASHING,
    REMOTE_STORAGE,
    WORKING_TREE_STATE,
    CapabilityError,
)
from engine.omega_infinite.direct_callers import (
    DECLARED_DIRECT,
    DIRECT_CALLER_CEILING,
    direct_callers,
)
from engine.omega_infinite.git_provider import GitDiscoveryProvider
from engine.omega_infinite.provider import ProviderError, Selector


@pytest.fixture(scope="module")
def provider():
    return GitDiscoveryProvider(root=".")


def test_no_provider_declares_a_capability_it_cannot_deliver(provider) -> None:
    """The root defect, now a refusal.

    Measured before this existed: five capabilities declared, one deliverable. AUTHORITY_METADATA
    was described in the provider's own docstring as exposed "on request", and there was no
    request to make. A declaration that costs nothing is the shape ENVELOPE_ONLY names.
    """
    assert provider.verify_capabilities() == ()


def test_every_declared_capability_returns_something(provider) -> None:
    for capability in (WORKING_TREE_STATE, CONTENT_HASHING, AUTHORITY_METADATA):
        assert provider.supply(capability, Selector(patterns=("engine/conformance/*",))) is not None


def test_an_undeclared_capability_is_refused(provider) -> None:
    """The provider answers for what it claims and refuses what it does not.

    The exception type is named rather than caught broadly: `pytest.raises(Exception)` would pass
    on a TypeError from a typo, which is how a refusal path can look tested while being broken —
    and the refusal path in `supply` WAS broken exactly that way when first written.
    """
    with pytest.raises(CapabilityError):
        provider.supply(REMOTE_STORAGE)


def test_supplying_a_declared_capability_without_a_method_is_refused() -> None:
    """The failing case that licenses the first test.

    Without this, `verify_capabilities` returning empty could mean the check is sound or that
    nothing can fail it. This constructs a provider that declares a capability and supplies no
    method, and asserts the refusal by name.
    """
    from engine.omega_infinite.capability import TRACKED_CONTENT, CapabilitySet
    from engine.omega_infinite.provider import BaseProvider

    class Hollow(BaseProvider):
        def identifier(self) -> str:
            return "hollow"

        def capabilities(self) -> CapabilitySet:
            return CapabilitySet.of(TRACKED_CONTENT, CONTENT_HASHING)

    hollow = Hollow()
    assert hollow.verify_capabilities() == ("CONTENT_HASHING",)
    with pytest.raises(ProviderError, match="supplies no"):
        hollow.supply(CONTENT_HASHING)


def test_direct_callers_may_only_fall() -> None:
    """A new module reaching past the provider is refused.

    THIS IS THE RECURRENCE GUARD. Nine execution adapters accumulated behind a contract nothing
    could fail; a direct caller costs nothing to add for the same reason, until something counts
    them. A fall must be recorded in MOVEMENTS so the ceiling tracks the work rather than drifting.
    """
    measured = direct_callers()
    assert len(measured) <= DIRECT_CALLER_CEILING, (
        "a module reached past the provider for a question it now answers. Route it through "
        "`supply`, or declare it in DECLARED_DIRECT with a reason:\n  "
        + "\n  ".join(m for m in measured)
    )


def test_a_fall_must_be_recorded() -> None:
    """The other side of the ratchet: the ceiling may not sit above the measurement."""
    measured = len(direct_callers())
    assert measured == DIRECT_CALLER_CEILING, (
        f"the ceiling is {DIRECT_CALLER_CEILING} and {measured} callers remain. A fall is welcome "
        "and must be recorded in MOVEMENTS with what was migrated and where it went."
    )


def test_every_declared_exception_states_a_reason() -> None:
    """An exemption without a stated reason is a silent one."""
    assert DECLARED_DIRECT
    assert all(len(reason) > 40 for reason in DECLARED_DIRECT.values())
