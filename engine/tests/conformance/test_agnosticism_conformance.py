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
    ENVELOPE_ONLY,
    PROVEN,
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


def test_execution_is_envelope_only_however_many_adapters_it_declares(results) -> None:
    """The finding this instrument was built to make sayable.

    engine/uckp/execution.py declares ten technologies and verify_execution_interchangeable
    passes over all of them. It cannot do otherwise: nine inherit one transcribe() returning
    identical canonical JSON with a different comment line, and execute() discards the payload
    and calls the Python resolver regardless. Ten names, one implementation, a green test.

    This test asserts the verdict AND its cause, so that adding a tenth adapter does not quietly
    turn it green: the disposition rests on the contract being unable to fail, not on a count.
    """
    axis = _axis(results, "execution")
    assert axis.disposition == ENVELOPE_ONLY
    assert axis.discriminating is False
    assert len(axis.shared_bodies) >= 2, "the shared bodies are the evidence, and must be named"


def test_a_count_alone_would_have_reported_execution_as_proven(results) -> None:
    """Why the harness measures two properties and not one.

    Distinctness alone scores execution at two distinct implementations, which reads as
    healthy. The second property — whether the contract can refuse anything — is what separates
    a swappable technology from a plugin list, and removing it would restore exactly the
    over-report that let nine envelopes accumulate.
    """
    axis = _axis(results, "execution")
    assert len(axis.distinct) >= 2 and axis.disposition != PROVEN


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
