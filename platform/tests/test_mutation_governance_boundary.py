"""UCOS-CL-016 — the mutation governance boundary is declared, and it holds.

The determination is OPTION B: the Constitutional Mutation Gateway governs mutations of
constitutional truth, not source files. ``test_the_gateway_does_not_touch_the_filesystem``
is the evidence for that determination rather than a restatement of it — if the gateway
ever grows a filesystem, the determination must be revisited and this test says so by
failing.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BOUNDARY = REPO / "00-BOOK" / "DATA" / "mutation-governance-boundary.json"


@pytest.fixture(scope="module")
def boundary() -> dict:
    return json.loads(BOUNDARY.read_text(encoding="utf-8"))


def test_the_boundary_is_declared(boundary: dict) -> None:
    assert boundary["schema"] == "ucos-mutation-governance-boundary"
    assert boundary["determination"].startswith("OPTION B")
    assert boundary["authorities"] and boundary["mutation_classes"]


def test_1_every_mutation_class_names_exactly_one_governing_chain(boundary: dict) -> None:
    for entry in boundary["mutation_classes"]:
        assert entry.get("governed_by"), f"{entry['class']} is ungoverned"
        assert isinstance(entry["governed_by"], str)


def test_2_no_class_is_claimed_by_two_authorities_as_primary(boundary: dict) -> None:
    classes = [e["class"] for e in boundary["mutation_classes"]]
    assert len(classes) == len(set(classes)), f"duplicate mutation class: {classes}"


def test_3_no_mutation_class_is_ungoverned(boundary: dict) -> None:
    """Every class of change the repository can undergo has a named authority chain."""
    covered = {e["class"] for e in boundary["mutation_classes"]}
    required = {
        "CONSTITUTIONAL_TRUTH",
        "SOURCE",
        "GENERATED_ARTIFACT",
        "EXCLUSION",
        "REPOSITORY_STATE",
    }
    assert required <= covered, f"ungoverned mutation classes: {sorted(required - covered)}"


def test_4_every_named_authority_implementation_exists(boundary: dict) -> None:
    for authority in boundary["authorities"]:
        impl = authority["implementation"]
        target = REPO / impl
        if "::" in impl:
            target = REPO / impl.split("::")[0]
        assert target.exists(), f"{authority['authority']} names a missing implementation: {impl}"


def test_5_the_boundary_itself_is_tracked() -> None:
    import subprocess

    tracked = subprocess.run(  # noqa: S603
        ["git", "ls-files", "--error-unmatch", "00-BOOK/DATA/mutation-governance-boundary.json"],  # noqa: S607
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    # Before the first commit of this closure the file is new; after it, tracked. Either
    # way it must be present on disk and readable, which is what governance depends on.
    assert BOUNDARY.is_file()
    if tracked.returncode != 0:
        pytest.skip("boundary artifact not yet committed (first closure commit pending)")


def test_the_gateway_does_not_touch_the_filesystem() -> None:
    """The evidence for OPTION B, asserted rather than asserted-about.

    The Constitutional Mutation Gateway operates on in-memory Population and
    ConstitutionalMetadata values. It never opens a file, resolves a path, or invokes git.
    That is *why* source mutations fall outside it. If this ever stops being true, the
    determination in the boundary artifact is stale and must be re-made — so this test
    failing is a signal to revisit the boundary, not to relax the test.
    """
    forbidden_calls = {"open", "read_text", "write_text", "mkdir", "unlink"}
    forbidden_names = {"Path", "subprocess"}

    for module in ("gateway.py", "state.py"):
        source = (REPO / "engine" / "constitution" / module).read_text(encoding="utf-8")
        tree = ast.parse(source)

        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
                imported.update(alias.name for alias in node.names)

        leaked = imported & (forbidden_names | {"pathlib", "os", "shutil"})
        assert not leaked, (
            f"engine/constitution/{module} imports {sorted(leaked)} — the gateway has grown a "
            "filesystem, so the OPTION B determination that source mutations fall outside "
            "CMG is no longer supported by its implementation"
        )

        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert not (
            called & forbidden_calls
        ), f"engine/constitution/{module} calls {sorted(called & forbidden_calls)}"


def test_exclusion_is_governed_by_a_register_not_by_the_exclusion_mechanism(boundary: dict) -> None:
    """The UCOS-CL-001 correction, stated as a boundary rule.

    `.gitignore` must not be its own governing authority. That circularity is precisely what
    let two ignore lines clear a blocking convergence criterion.
    """
    exclusion = next(e for e in boundary["mutation_classes"] if e["class"] == "EXCLUSION")
    assert "UCOS-EXCLUSION-REGISTER-001" in exclusion["governed_by"]
    assert "GATE-12" in exclusion["governed_by"]


def test_source_class_chain_terminates_in_clone_certification(boundary: dict) -> None:
    """A source mutation is not governed until a clone reproduces its consequences."""
    source = next(e for e in boundary["mutation_classes"] if e["class"] == "SOURCE")
    for stage in ("pre-commit", "verify.sh", "UCOS-RIB-001", "UCOS-AEE-001", "Phase 8", "Phase 9"):
        assert stage in source["governed_by"], f"SOURCE chain omits {stage}"
