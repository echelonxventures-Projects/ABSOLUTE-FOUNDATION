"""Mandate conformance — the Absolute Universal Constitutional Architecture diagram.

176 mandates over 14 sections. Each suite below takes one section, locates what the
repository actually holds for it, and declares what it cannot prove.
"""

from __future__ import annotations

from engine.tests.conformance.mandate_corpus import (
    assert_absence_rule_can_find_something,
    assert_homes_exist,
    assert_named_by_nothing,
    assert_partitions,
    section,
)

# --- ARCH-CERTV — the eight certification verdicts ------------------------------
#
# The Quality & Trust Fabric ends in Universal Certification and names its verdict set:
# PASS, REUSE, EXTEND, CREATE, SUPERSEDE, DEPRECATE, BLOCKED, NOT_APPLICABLE, under the
# rule "No mandatory obligation may fail." A verdict set is the one part of a governance
# diagram that must exist as VALUES a running instrument can return -- a verdict nothing
# emits is a verdict nobody can receive.
#
# So this binding asks a narrow, checkable question of each: does some instrument in this
# repository emit this verdict? Two do not, and the reasons differ enough to matter.

#: Verdict -> the module that emits it, and the symbol carrying the value.
VERDICT_EMITTED = {
    "ARCH-CERTV/CV-01": ("engine/certification/closure.py", "PASS"),
    "ARCH-CERTV/CV-02": ("engine/constitution/assimilation.py", "REUSE"),
    "ARCH-CERTV/CV-04": ("engine/constitution/assimilation.py", "CREATE"),
    "ARCH-CERTV/CV-05": ("engine/registry/universal/records.py", "SUPERSEDE"),
    "ARCH-CERTV/CV-06": ("engine/registry/universal/records.py", "DEPRECATE"),
    "ARCH-CERTV/CV-07": ("engine/registry/models.py", "BLOCKED"),
}

#: EXTEND is not a verdict here; it is REUSE carrying targets. `AssimilationVerdict.status`
#: returns exactly CREATE or REUSE, and `reuse_targets` is documented as "the existing
#: subjects the caller should extend instead". The instruction the diagram spells EXTEND is
#: delivered -- under another name and in another field -- so recording it as absent would
#: be false and recording it as emitted would be false too.
VERDICT_EXPRESSED_DIFFERENTLY = {
    "ARCH-CERTV/CV-03": (
        "engine/constitution/assimilation.py",
        "reuse_targets",
        "status returns CREATE or REUSE only; the extend instruction rides on reuse_targets",
    ),
}

#: Emitted by nothing. NOT_APPLICABLE is the verdict that lets an obligation be dismissed
#: without being met, which is exactly why its absence is worth stating: the rule "no
#: mandatory obligation may fail" has no escape hatch here, by omission rather than design.
VERDICT_ABSENT = {
    "ARCH-CERTV/CV-08": "NOT_APPLICABLE",
}


def test_every_certification_verdict_is_emitted_expressed_or_absent() -> None:
    mandates = section("ARCH-CERTV")
    assert len(mandates) == 8, f"the diagram names 8 verdicts, corpus has {len(mandates)}"
    assert_partitions(
        "ARCH-CERTV",
        mandates,
        VERDICT_EMITTED,
        VERDICT_EXPRESSED_DIFFERENTLY,
        VERDICT_ABSENT,
    )


def test_every_emitted_verdict_appears_as_a_value_in_its_module() -> None:
    """The verdict must be a VALUE, not a word in a comment. Each is checked as a quoted
    string literal, which is how a returnable verdict is written in this codebase."""
    from engine.tests.conformance.mandate_corpus import repo_root

    homes = {m: home for m, (home, _symbol) in VERDICT_EMITTED.items()}
    assert_homes_exist("ARCH-CERTV", homes)
    for mandate, (home, symbol) in VERDICT_EMITTED.items():
        text = (repo_root() / home).read_text(encoding="utf-8")
        assert f'"{symbol}"' in text, (
            f"ARCH-CERTV/{mandate}: {home} is declared to emit {symbol!r} and carries no "
            "such value; a verdict nothing emits is a verdict nobody can receive"
        )


def test_the_assimilation_gate_really_returns_only_create_or_reuse() -> None:
    """NON-VACUITY for CV-03. The claim is that EXTEND is not a status this gate can
    return. If it ever becomes one, the row moves to EMITTED and this tiering is wrong."""
    import inspect

    from engine.constitution.assimilation import AssimilationVerdict

    body = inspect.getsource(AssimilationVerdict.status.fget)
    assert '"CREATE"' in body and '"REUSE"' in body
    assert '"EXTEND"' not in body, (
        "the assimilation gate now returns EXTEND as a status; ARCH-CERTV/CV-03 is emitted "
        "rather than expressed differently"
    )
    assert "extend" in (AssimilationVerdict.reuse_targets.fget.__doc__ or "").lower(), (
        "reuse_targets no longer documents itself as what the caller should extend; the "
        "claim that the EXTEND instruction rides on it is no longer supported"
    )


def test_the_absent_verdict_is_emitted_by_nothing() -> None:
    """NON-VACUITY. Searched as a quoted value across every tracked Python file, because
    the question is whether anything can RETURN it, not whether anything mentions it."""
    from engine.tests.conformance.mandate_corpus import repo_root, tracked

    for mandate, verdict in VERDICT_ABSENT.items():
        emitters = [
            path
            for path in tracked()
            if path.endswith(".py")
            and "/tests/" not in path
            and f'"{verdict}"' in (repo_root() / path).read_text(encoding="utf-8", errors="ignore")
        ]
        assert (
            not emitters
        ), f"ARCH-CERTV/{mandate}: {verdict} is declared absent but is emitted by {emitters}"


def test_the_naming_rule_this_suite_relies_on_can_find_something() -> None:
    assert_absence_rule_can_find_something("constitution assimilation")


def test_absence_search_does_not_silently_match_nothing() -> None:
    assert_named_by_nothing("ARCH-CERTV", {"ARCH-CERTV/CV-08": "not applicable verdict"})
