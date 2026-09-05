"""UZX-000001 — the programme's own enforcement, and the cases that license it.

adr/0021 stated a principle, disclosed that nothing enforced it, and kept none for fourteen days.
The Zero-X programme reproduced that structure one level up: twelve residue classes governed by a
plan document with no gate. These tests are what makes the difference between a programme that is
well-tended and one that enforces its own discipline.
"""

from __future__ import annotations

import pytest

import engine.omega_infinite.direct_callers  # noqa: F401 - the caller loads what the register names

# Imported through the PACKAGE, not the module. Ω-4 counted engine/zero_class/__init__.py as an
# unreachable artifact when this reached past it — code no import, plane or entry point touches —
# which is the same refusal engine/conformance drew when its tests bypassed its own package. A
# package nothing imports is a package nothing proves.
from engine.zero_class import (
    ZeroClassError,
    measure,
    stage_of,
    unenforced,
)
from engine.zero_class.measure import (
    DETECTED,
    RATCHETED,
    UNENFORCED_CEILING,
    load_register,
)


@pytest.fixture(scope="module")
def results():
    return measure()


def test_the_register_declares_at_least_one_class(results) -> None:
    assert results


def test_no_class_is_governed_without_enforcement(results) -> None:
    """ZX-SELF: the register measures itself by the rule it applies to everything else.

    A register that exempted itself would repeat adr/0021 exactly, one level up — a rule that is
    right, with a measurement that does not reach the instrument stating it.
    """
    assert len(unenforced()) <= UNENFORCED_CEILING, (
        "a class is declared with a detector that cannot be resolved, run, or shown to fail in "
        f"both directions: {unenforced()}"
    )


def test_every_detected_class_proves_both_directions(results) -> None:
    """Stage 2 is not 'a detector exists'. It is 'a detector demonstrably fails correctly'."""
    for result in results:
        if result.stage >= DETECTED:
            assert result.catches, f"{result.class_id} cannot demonstrate it catches a violation"
            assert result.spares, f"{result.class_id} cannot demonstrate it spares a benign case"


def test_every_ratcheted_class_does_not_exceed_its_ceiling(results) -> None:
    for result in results:
        if result.stage >= RATCHETED:
            assert result.measured is not None and result.ceiling is not None
            assert result.measured <= result.ceiling, result.class_id


def test_a_detector_that_cannot_spare_is_refused() -> None:
    """THE FAILING CASE THIS INSTRUMENT RESTS ON.

    Without it, "no class is unenforced" could mean the rule holds or that nothing can fail it.
    A predicate that flags everything catches every violation and is still useless: false
    positives make a floor unreachable, because the last entries resist every migration and the
    only way to close the count is to declare modules that never had a defect. That is not
    hypothetical — the first bypass detector did exactly this, counting a declaration naming a
    tool as an invocation of it.
    """
    entry = {
        "class_id": "ZX-FAKE",
        "name": "a detector that flags everything",
        "definition": "constructed for this test",
        "detector": "engine.zero_class.measure.unenforced",
        "predicate": _flags_everything,
        "must_catch": ["x = 1\n"],
        "must_not_catch": ["y = 2\n"],
        "remedy": "PROPOSED",
    }
    result = stage_of(entry)
    assert result.catches is True
    assert result.spares is False, "a predicate that flags everything must fail the spare case"
    assert result.stage < DETECTED, "it must not reach DETECTED on catching alone"
    assert any("false positive" in reason for reason in result.reasons)


def test_a_class_with_no_detector_stays_declared() -> None:
    result = stage_of({"class_id": "ZX-NONE", "name": "undetected", "definition": "x"})
    assert result.stage < DETECTED
    assert any("no detector" in reason for reason in result.reasons)


def test_a_declared_but_undetected_class_says_why() -> None:
    """A class honestly at stage 1 is a different thing from one nobody thought of."""
    register = load_register()
    pending = register.get("declared_not_detected") or []
    assert pending, "the register claims full coverage; that claim needs evidence"
    for entry in pending:
        assert len(entry.get("why", "")) > 60, entry.get("class_id")


def test_the_register_never_declares_a_stage() -> None:
    """The register names classes and detectors. Stages are computed, never read."""
    register = load_register()
    for entry in register["classes"]:
        assert (
            "stage" not in entry
        ), f"{entry['class_id']} declares a stage it should be measured for"


def test_an_unloaded_detector_is_a_fault_not_a_pass() -> None:
    with pytest.raises(ZeroClassError, match="not loaded|no attribute"):
        stage_of(
            {
                "class_id": "ZX-GHOST",
                "name": "ghost",
                "definition": "x",
                "detector": "no.such.module.detector",
                "predicate": "no.such.module.predicate",
                "must_catch": ["a = 1\n"],
                "must_not_catch": ["b = 2\n"],
            }
        )


def _flags_everything(_path) -> bool:
    """A predicate with no discrimination, for the failing case above."""
    return True
