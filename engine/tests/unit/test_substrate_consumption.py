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

from engine.substrate import adapter, gate

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
    monkeypatch.setitem(sys.modules, "uakp", None)
    monkeypatch.setitem(sys.modules, "uakp.rules", None)
    monkeypatch.chdir(REPO)
    assert gate.main() == gate.EXIT_FAULT
    assert "FAULT" in capsys.readouterr().err


def test_the_ratchet_is_declared_with_a_reason() -> None:
    ratchet = _declaration()["ratchet"]
    assert isinstance(ratchet["contradictions"], int)
    reason = ratchet["$contradictions"]
    prose = "\n".join(reason) if isinstance(reason, list) else reason
    assert prose.strip(), (
        "a ceiling with no reason is a number somebody chose, and nobody can tell whether "
        "reaching zero is work or redesign"
    )
    assert str(ratchet["contradictions"]) in prose, (
        "the reason does not mention the number it explains, so the two can drift apart "
        "without either looking wrong"
    )


def test_the_gate_holds_at_its_declared_ceiling() -> None:
    from uakp import rules
    from uakp.core.contradiction import detect
    from uakp.core.graph import Graph

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
    authorities = {a.identity: a for a in adapter.authorities(str(REPO))}
    ledger = authorities["UCOS-IDENTITY-LEDGER"]
    for claimed in ledger.governs:
        assert (REPO / claimed).exists(), f"the ledger authority claims {claimed}, which is gone"


# --- the refusal witnesses (UEC-L-14) -----------------------------------------------------
#
# UEC-L-05 measures that a test NAMES this gate. That is necessary and nowhere near
# sufficient: every test above names it and none of them had forged a condition it must
# refuse, so the gate was counted as governed while nobody had shown it could refuse
# anything. A verifier nothing has shown can refuse certifies nothing, and its green tick is
# worse than no tick because it licenses the belief that the property was checked.
#
# Each witness below builds a whole root whose truth is known, points the gate at it, and
# asserts the CLOSED exit code as a literal — the shape UEC-000001 declares under
# refusal_witness.accepted_shapes.


def _forged_root(tmp_path, contradictions: int) -> pathlib.Path:
    """A minimal repository whose only declared truth is a contradiction ceiling.

    No `00-BOOK/DATA/artifacts.json`, no exclusion register and no identity ledger, so every
    artifact the walk finds is owned by nobody. The count is therefore knowable in advance
    and the ceiling can be set above it and below it on purpose.
    """
    declaration = tmp_path / "00-MASTER" / "UCOS-SUB-001" / "sub-declaration.json"
    declaration.parent.mkdir(parents=True)
    declaration.write_text(
        json.dumps(
            {
                "artifact_id": "UCOS-SUB-001",
                "requires": "uakp>=0.0.1",
                "ratchet": {"contradictions": contradictions},
                "discovery": {"ungoverned_directories": [".git", "__pycache__"]},
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_the_gate_refuses_new_debt_above_the_ceiling(tmp_path, monkeypatch, capsys) -> None:
    """The upper side of the ratchet: an artifact no authority claims must fail the gate."""
    monkeypatch.chdir(_forged_root(tmp_path, contradictions=0))
    assert gate.main() == 1, "a ratchet that admits new debt is not a ratchet"
    assert "CLOSED" in capsys.readouterr().err


def test_the_gate_refuses_slack_below_the_ceiling(tmp_path, monkeypatch, capsys) -> None:
    """The lower side, which is the half a one-directional ceiling gets wrong.

    Debt repaid without tightening the ceiling leaves room a future regression can occupy in
    silence, so measuring under the ceiling is refused exactly as measuring over it is.
    """
    monkeypatch.chdir(_forged_root(tmp_path, contradictions=10_000))
    assert gate.main() == 1, "slack under the ceiling is a regression nobody would see"
    assert "slack" in capsys.readouterr().err


def test_an_unusable_declaration_is_a_fault_and_never_a_pass(tmp_path, monkeypatch) -> None:
    """A gate whose own declaration will not parse has measured nothing and must say so."""
    broken = tmp_path / "00-MASTER" / "UCOS-SUB-001" / "sub-declaration.json"
    broken.parent.mkdir(parents=True)
    broken.write_text("{not json", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert gate.main() == 2, "an unreadable declaration must yield no verdict"


def test_an_absent_ungoverned_directory_list_is_a_fault_rather_than_a_default(tmp_path) -> None:
    """The list moved from a frozenset literal into the declaration so that admitting a name
    is a data change (UCKP-ART-17). A default would silently walk `.git` and `.ec1-venv` and
    report thousands of artifacts nothing governs, so its absence raises."""
    declaration = tmp_path / "00-MASTER" / "UCOS-SUB-001" / "sub-declaration.json"
    declaration.parent.mkdir(parents=True)
    declaration.write_text(json.dumps({"discovery": {"ungoverned_directories": []}}), "utf-8")
    with pytest.raises(ValueError, match="empty"):
        adapter.ungoverned_directories(str(tmp_path))


def test_the_ungoverned_directory_list_is_read_from_data_and_not_frozen_in_code() -> None:
    """ISD-L-01 and UCON-L-15 both counted the literal, and both were right: a set whose
    membership can only change by editing a module is a closed enumeration."""
    source = (CONSUMER / "adapter.py").read_text(encoding="utf-8")
    assert "frozenset(\n" not in source, "the closed enumeration is back in the module"
    declared = _declaration()["discovery"]["ungoverned_directories"]
    assert adapter.ungoverned_directories(str(REPO)) == frozenset(declared)


def test_every_semantic_edit_moves_the_declaration_digest() -> None:
    """UEC-L-08 asks whether a certification identity exists; this asks the harder question.

    A digest over a projection — the ratchet alone, or a curated subset — certifies two
    different declarations with one value, which is the defect engine/construct was measured
    carrying. Every field participates here, so no edit can change what the gate enforces
    while leaving its identity where it was.
    """
    declaration = _declaration()
    before = gate.declaration_digest(declaration)
    assert before == gate.declaration_digest(_declaration()), "the digest is not deterministic"
    mutated = dict(declaration)
    mutated["ratchet"] = dict(declaration["ratchet"])
    mutated["ratchet"]["contradictions"] = declaration["ratchet"]["contradictions"] + 1
    assert gate.declaration_digest(mutated) != before, (
        "moving the ceiling left the certification identity unchanged, so one digest "
        "certifies two different declarations"
    )


def test_the_gate_is_reachable_from_two_independent_invocation_planes() -> None:
    """UEC-L-06: two planes mean deleting one leaves a signal. The Makefile target named
    `$(PYTHON)`, which this repository does not define, so `make -n` printed
    `m engine.substrate` and the only plane there was could never have executed."""
    planes = {
        "Makefile": (REPO / "Makefile").read_text(encoding="utf-8"),
        "sub-gate.yml": (REPO / ".github" / "workflows" / "sub-gate.yml").read_text("utf-8"),
    }
    for name, text in planes.items():
        assert "engine.substrate.gate" in text, f"{name} does not invoke the gate by name"
    assert set(_declaration()["gate"]["invoked_from"]), "the declaration records no plane"
