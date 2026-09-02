"""UCOS as a consumer of the UAKP substrate, and the direction of that dependency.

The constitution requires a universal platform that UCOS CONSUMES, and requires it not to be
developed as part of UCOS. The substrate is now extracted; these hold the binding back to it
to the property that makes the extraction worth anything — that the substrate never learns
about UCOS.
"""

from __future__ import annotations

import ast
import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]
DECLARATION = REPO / "00-MASTER" / "UCOS-SUB-001" / "sub-declaration.json"
CONSUMER = REPO / "engine" / "substrate"

uakp = pytest.importorskip("uakp", reason="the substrate is not installed in this environment")


def _declaration() -> dict:
    return json.loads(DECLARATION.read_text(encoding="utf-8"))


def test_the_substrate_never_learns_about_ucos() -> None:
    """The one property the extraction exists to create.

    An adapter placed in the substrate would undo it in a single commit, so this is asserted
    over the substrate's own installed source rather than trusted.
    """
    root = pathlib.Path(uakp.__file__).resolve().parent
    forbidden = ("00-BOOK", "00-MASTER", "00-CMG", "99-FREEZE", "UCOS")
    for module in sorted(root.rglob("*.py")):
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for token in forbidden:
                    assert token not in node.value, (
                        f"{module.name} names {token!r}. The substrate has learned about its "
                        f"consumer, which is the extraction undone."
                    )


def test_every_ucos_specific_fact_lives_on_the_consumer_side() -> None:
    """The mirror: the adapter is where UCOS knowledge is allowed to be."""
    source = (CONSUMER / "adapter.py").read_text(encoding="utf-8")
    assert "00-BOOK" in source, (
        "the consumer-side adapter names no UCOS register, so either it reads nothing or the "
        "knowledge moved somewhere worse"
    )


def test_consumption_is_not_a_runtime_dependency() -> None:
    """pyproject declares dependencies = [] on constitutional grounds, ISD-L-09 refuses a
    pinned runtime dependency, and test_infinite_scope asserts the list is empty. Consumption
    happens in the governance plane; the runtime core is untouched."""
    manifest = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert "dependencies = []" in manifest
    assert "uakp" not in manifest.split("[project.optional-dependencies]")[0]


def test_an_absent_substrate_is_a_fault_and_never_a_pass(monkeypatch, capsys) -> None:
    """A gate that reported OPEN because it could not import its subject would be the exact
    false green this apparatus exists to refuse.

    The substrate IS installed here, so its absence is forged rather than arranged: blocking
    the import is the only way to reach the branch that matters, and a branch nothing reaches
    is a branch nobody has shown can fire.
    """
    from engine.substrate import gate

    monkeypatch.setitem(sys.modules, "uakp", None)
    monkeypatch.setitem(sys.modules, "uakp.rules", None)
    monkeypatch.chdir(REPO)
    assert gate.main() == gate.EXIT_FAULT
    assert "FAULT" in capsys.readouterr().err


def test_the_ratchet_is_declared_with_a_reason() -> None:
    ratchet = _declaration()["ratchet"]
    assert isinstance(ratchet["contradictions"], int)
    assert ratchet["$contradictions"].strip(), (
        "a ceiling with no reason is a number somebody chose, and nobody can tell whether "
        "reaching zero is work or redesign"
    )


def test_the_gate_holds_at_its_declared_ceiling() -> None:
    from uakp import rules
    from uakp.core.contradiction import detect
    from uakp.core.graph import Graph

    from engine.substrate import adapter

    graph = Graph.of(
        artifacts=adapter.artifacts(str(REPO)), authorities=adapter.authorities(str(REPO))
    )
    measured = len(list(detect(graph, rules.SHIPPED)))
    assert measured == _declaration()["ratchet"]["contradictions"], (
        f"measured {measured}; the ratchet refuses in both directions, so this is either new "
        f"debt or debt repaid without tightening the ceiling"
    )


def test_an_append_only_ledger_records_identity_and_does_not_claim_presence() -> None:
    """UCKP-ART-05 makes an identity permanent, so a retired path keeps its ledger entry
    forever. Treating history as a present claim reported thirteen contradictions that were
    all genuinely absent paths and none of them defects — one was the deliberate retirement
    of ledger_authority.py, which is the system working."""
    from engine.substrate import adapter

    authorities = {a.identity: a for a in adapter.authorities(str(REPO))}
    ledger = authorities["UCOS-IDENTITY-LEDGER"]
    for claimed in ledger.governs:
        assert (REPO / claimed).exists(), f"the ledger authority claims {claimed}, which is gone"
