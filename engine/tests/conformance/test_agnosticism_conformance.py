"""UAC-000001 — the harness measured, and the reason it is measured rather than trusted.

Ω-4 counted `engine/conformance` as an unreachable artifact the moment it landed: code no
import, plane or entry point reaches. That was correct and is the point of the metric — an
instrument nothing invokes proves nothing, however well it is written. These tests are what
reach it, and `make conformance` is the operator's path to the same measurement.
"""

from __future__ import annotations

import pytest

import engine.uckp.execution  # noqa: F401 - the caller loads what the register names
import engine.uckp.persistence  # noqa: F401
from engine.conformance import (
    PROVEN,
    SINGLE,
    ConformanceError,
    measure,
    measure_axis,
)
from engine.conformance.measure import REGISTER_PATH


def _axis(results, name):
    return next(r for r in results if r.axis == name)


@pytest.fixture(scope="module")
def results():
    return measure(REGISTER_PATH)


def test_the_register_declares_at_least_one_axis(results) -> None:
    assert results, "a register declaring no axis is a fault, not an empty measurement"


def test_persistence_is_proven_because_its_contract_can_refuse_a_placeholder(results) -> None:
    """The axis that licenses the harness: it passes for a reason that can fail.

    PersistenceAdapter demands write() then read() and compares universe digests, so a
    mechanism that records nothing cannot return it. A pass here is evidence; that is what
    makes this axis the right one to validate the instrument against.
    """
    axis = _axis(results, "persistence")
    assert axis.disposition == PROVEN
    assert len(axis.distinct) >= 2
    assert axis.discriminating is True
    assert axis.shared_bodies == ()


def test_execution_is_single_and_no_longer_envelope_only(results) -> None:
    """The verdict this suite was written to make sayable, and then the fix that moved it.

    WRITTEN AS ENVELOPE_ONLY, AND THAT WAS CORRECT AT THE TIME. engine/uckp/execution.py declared
    ten technologies and verify_execution_interchangeable passed over all of them, because no
    adapter overrode `execute` — every call reached the same resolve_operation that produced the
    expected digest, so the check compared Python's answer to Python's answer once per adapter
    name and could not refuse anything.

    THE CONTRACT NOW DISCRIMINATES, so the axis moved. `computes()` defaults to False, claiming
    computation is an act rather than an inheritance, and a claimant returning a different digest
    is named in failures. One adapter claims it. Nine are transcription targets, reported as such
    rather than counted as agreement, and deliberately not deleted: UCKP-ART-17 admits an unknown
    future category by registration, and those declarations are that mechanism working.

    SINGLE IS NOT PROVEN, AND THE TEST SAYS SO. One implementation is an assumption — adr/0039's
    own bar — and this asserts the axis has not quietly been credited with more than it earned.
    """
    axis = _axis(results, "execution")
    assert axis.disposition == SINGLE, "the axis is not PROVEN; one implementation is an assumption"
    assert axis.discriminating is True, "the contract must be able to refuse a false claimant"
    assert len(axis.distinct) == 1


def test_a_second_implementation_is_now_provable_rather_than_assertable(results) -> None:
    """Why the move from ENVELOPE_ONLY to SINGLE is progress and not a relabelling.

    Under ENVELOPE_ONLY no number of implementations could be distinguished, so a Rust engine
    would have passed the interchangeability check by transcribing and computing nothing. The
    axis now carries a discriminator, which is exactly the bar a second implementation must clear
    to move it to PROVEN — by evidence rather than by declaration.
    """
    axis = _axis(results, "execution")
    assert axis.discriminating, "without a discriminator, a second implementation proves nothing"
    assert axis.disposition != PROVEN, "two claimants are required, and there is one"


def test_an_unloaded_contract_is_unmeasurable_and_never_silently_skipped() -> None:
    """The harness imports nothing, so an unloaded contract must say so rather than vanish."""
    with pytest.raises(ConformanceError, match="not loaded|cannot be measured"):
        measure_axis({"axis": "absent", "contract": "no.such.module.Contract"})


def test_the_harness_names_no_technology() -> None:
    """The instrument that measures hardcoding may not hardcode what it measures.

    A technology named in the harness would make one axis privileged and the register
    advisory. Axis modules appear only under __main__, which decides nothing.
    """
    import pathlib

    source = pathlib.Path("engine/conformance/measure.py").read_text(encoding="utf-8")
    body = source.split('if __name__ == "__main__":')[0]
    for token in ("python", "rust", "golang", "sqlite", "postgres", "kubernetes", "git"):
        assert token not in body.lower(), f"the harness names a technology: {token}"
