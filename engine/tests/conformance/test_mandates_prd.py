"""Mandate conformance — the Product Requirements Document (Constitutional Foundation v1.0).

188 mandates over 18 sections. The PRD's negative principles and success criteria are bound
separately, in `engine/tests/kernel/test_compliance.py`, against the instrument that can
actually decide a negative: a running kernel whose source fingerprint is measured. Nothing
here re-states those; a second binding of the same claim is the duplication ART-03 voids.
"""

from __future__ import annotations

from engine.tests.conformance.mandate_corpus import (
    assert_absence_rule_can_find_something,
    assert_homes_exist,
    assert_partitions,
    section,
)

# --- PRD-ADM — the Universal Admission Framework --------------------------------
#
# Section 7 states nine things every new construct must support, and closes with the
# sentence that makes them testable rather than aspirational: "No manual platform redesign."
#
# Two different claims live in that section and this suite keeps them apart. The nine steps
# are CAPABILITIES -- each needs a located instrument. The closing sentence is a property of
# the platform as a whole, and it is already proven where it can be proven: the kernel
# admission tests measure a source fingerprint across an admission and require it unchanged.
# Restating that here would add a second authority for one claim without adding evidence.

#: Admission step -> the instrument that carries it.
ADMISSION_STEP_HOME = {
    "PRD-ADM/ADM-01": "engine/universal_discovery",  # Discovery
    "PRD-ADM/ADM-02": "engine/registry",  # Registration
    "PRD-ADM/ADM-03": "engine/knowledge/ukip/classification.py",  # Classification
    "PRD-ADM/ADM-04": "engine/validation",  # Validation
    "PRD-ADM/ADM-05": "engine/governance",  # Governance
    "PRD-ADM/ADM-06": "engine/uicm/observation.py",  # Observation
    "PRD-ADM/ADM-07": "engine/constitution/evolution.py",  # Evolution
    "PRD-ADM/ADM-08": "engine/certification",  # Certification
    "PRD-ADM/ADM-09": "intelligence/publication",  # Publication
}


def test_every_admission_step_has_a_located_instrument() -> None:
    mandates = section("PRD-ADM")
    assert len(mandates) == 9, f"section 7 states 9 admission steps, corpus has {len(mandates)}"
    assert_partitions("PRD-ADM", mandates, ADMISSION_STEP_HOME)
    assert_homes_exist("PRD-ADM", ADMISSION_STEP_HOME)


def test_every_admission_instrument_is_importable_code_not_a_specification() -> None:
    """An admission step whose home is prose is a described capability, not one a construct
    can pass through. Each home is required to carry Python that imports."""
    import importlib

    from engine.tests.conformance.mandate_corpus import repo_root

    for mandate, home in ADMISSION_STEP_HOME.items():
        path = repo_root() / home
        if path.is_dir():
            assert any(path.rglob("*.py")), f"{mandate}: {home} carries no code"
            module = home.replace("/", ".")
        else:
            assert path.suffix == ".py", f"{mandate}: {home} is not code"
            module = home[: -len(".py")].replace("/", ".")
        importlib.import_module(module)


def test_the_nine_steps_are_nine_distinct_instruments() -> None:
    """NON-VACUITY. Nine mandated capabilities all pointing at one module would mean eight
    of them are unlocated and the mapping is hiding it."""
    homes = list(ADMISSION_STEP_HOME.values())
    duplicated = sorted({h for h in homes if homes.count(h) > 1})
    assert not duplicated, f"one instrument claimed for several admission steps: {duplicated}"


def test_no_manual_platform_redesign_is_bound_elsewhere_and_not_restated_here() -> None:
    """The closing sentence of section 7 is a whole-platform property. It is decided by the
    kernel admission proof, which measures a source fingerprint across an admission -- the
    only instrument here that can decide it. This test asserts that binding still exists so
    the claim cannot go missing by being nobody's."""
    from engine.kernel.compliance import architectural_proof

    proof = architectural_proof()
    assert proof["kernel_unchanged"] is True, (
        "categories are represented but the kernel source changed, so 'no manual platform "
        "redesign' is false and every admission step above admits into a moving target"
    )


def test_the_naming_rule_this_suite_relies_on_can_find_something() -> None:
    assert_absence_rule_can_find_something("knowledge ukip classification")
