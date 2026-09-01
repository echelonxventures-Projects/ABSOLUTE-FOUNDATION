"""The join, the Ω-3 relocation proof, the gate and the scope plugin — over the real repository.

WHY THESE TESTS USE THE REAL TREE. Every phase above is unit-tested against synthetic repositories,
which is the right way to test a rule. But the CLAIM Ω makes is about this repository: that its
governance is total, that no verdict reads a directory name, and that the coverage denominator the
suite actually runs under is derived. A synthetic fixture cannot witness any of those.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.universal_discovery import gate, ratchet, relocation, surface
from engine.universal_discovery.model import (
    DISPOSITIONS,
    RATCHET_KINDS,
    SURFACE_DISPOSITIONS,
    OmegaError,
    Population,
)


@pytest.fixture(scope="module")
def omega() -> surface.OmegaSurface:
    """Built once. The join parses 2,177 files; per-test building would dominate the suite."""
    return surface.build(".")


# ------------------------------------------------------------------------------------- the join


def test_one_population_produces_every_verdict(omega: surface.OmegaSurface) -> None:
    """The defect the join exists to close: four populations that no code ever compared."""
    assert len(omega.artifacts) == len(omega.population.paths)
    assert {a.path for a in omega.artifacts} == set(omega.population.paths)


def test_the_totals_partition_rather_than_overlap(omega: surface.OmegaSurface) -> None:
    by_disposition = omega.totals["by_disposition"]
    assert sum(e["files"] for e in by_disposition.values()) == len(omega.artifacts)  # type: ignore[union-attr]
    assert set(by_disposition) == set(DISPOSITIONS)  # type: ignore[arg-type]


def test_the_surface_denominator_excludes_bytes_owned_elsewhere(
    omega: surface.OmegaSurface,
) -> None:
    """GENERATED and ARCHIVED are outside the ratio because a producer or a freeze owns them."""
    surface_files = [a for a in omega.artifacts if a.disposition in SURFACE_DISPOSITIONS]
    assert len(surface_files) == omega.totals["executable_surface_files"]
    assert omega.totals["executable_surface_statements"] == sum(a.statements for a in surface_files)


def test_the_measured_share_is_reported_and_is_a_real_fraction(
    omega: surface.OmegaSurface,
) -> None:
    share = omega.totals["measured_surface_percent"]
    assert isinstance(share, float)
    assert 0.0 < share <= 100.0
    assert (
        omega.totals["measured_surface_statements"] <= omega.totals["executable_surface_statements"]
    )


def test_structural_measures_never_consult_a_coverage_report(
    omega: surface.OmegaSurface,
) -> None:
    """UCI-L-06 once moved 10→9 on the mere presence of ``coverage.xml``. A structural measure that
    changes because an artifact it does not measure happened to exist measures nothing."""
    statements, callables, imports = surface._structure(
        "import json\n\n\nclass A:\n    def m(self):\n        return json\n"
    )
    assert (statements, callables, imports) == (4, 2, 1)
    assert surface._structure("def broken(:\n") == (0, 0, 0)


def test_the_digest_is_a_function_of_findings_and_not_of_inputs(
    omega: surface.OmegaSurface,
) -> None:
    """``source_heads`` is an input, so a comment change must not move the evidence digest."""
    document = omega.as_document()
    assert "source_heads" not in document
    assert "imported_by" not in document
    assert len(omega.digest()) == 64


def test_the_evidence_document_declares_its_own_determinism(
    omega: surface.OmegaSurface,
) -> None:
    document = omega.as_document()
    assert document["schema"] == surface.SCHEMA
    assert "No wall clock" in str(document["determinism"])
    assert document["discovered"]["measurable_packages"]  # type: ignore[index]
    json.dumps(document)  # must be serialisable, since it is written as evidence


def test_a_stale_declaration_is_refused_in_both_directions() -> None:
    """A declared exemption whose subject is gone, or that is also measured, is a REFUSAL."""
    base = {
        "paths": ("alpha/core/x.py",),
        "roots": ("alpha",),
        "importable_roots": ("alpha",),
        "test_roots": (),
        "measurable_packages": ("alpha.core",),
    }
    with pytest.raises(OmegaError, match="exemption is stale"):
        surface._assert_declarations_live(
            Population(**base, declared_exemptions={"alpha.gone": "reason"})  # type: ignore[arg-type]
        )
    with pytest.raises(OmegaError, match="other direction"):
        surface._assert_declarations_live(
            Population(**base, declared_exemptions={"alpha.core": "reason"})  # type: ignore[arg-type]
        )
    with pytest.raises(OmegaError, match="git does not track"):
        surface._assert_declarations_live(
            Population(**base, declared_transient={"alpha/absent.py": "reason"})  # type: ignore[arg-type]
        )


def test_an_empty_population_cannot_be_constructed() -> None:
    with pytest.raises(OmegaError, match="empty"):
        Population(
            paths=(), roots=("a",), importable_roots=(), test_roots=(), measurable_packages=("a",)
        )
    with pytest.raises(OmegaError, match="no root was derived"):
        Population(
            paths=("a.py",),
            roots=(),
            importable_roots=(),
            test_roots=(),
            measurable_packages=("a",),
        )


# ------------------------------------------------------------------ Ω-3: the relocation proof


def test_relocating_the_largest_root_changes_no_governance_verdict(
    omega: surface.OmegaSurface,
) -> None:
    """Ω-3's SUCCESS CRITERION over the real tree: ``engine/x.py`` → ``galaxy/x.py``, alike.

    Not a claim in a docstring — the experiment runs here and on every gate invocation.
    """
    drift = relocation.relocation_invariance(omega)
    assert not drift, f"relocation changed a governance verdict for {len(drift)}: {drift[:5]}"


def test_the_experiment_relocates_the_hardest_root(omega: surface.OmegaSurface) -> None:
    """Testing the smallest root would be the cheap version of the proof."""
    largest = relocation._largest_root(omega.artifacts)
    counts: dict[str, int] = {}
    for artifact in omega.artifacts:
        if artifact.root:
            counts[artifact.root] = counts.get(artifact.root, 0) + 1
    assert counts[largest] == max(
        count for root, count in counts.items() if root and root[0].isalpha()
    )


def test_the_destination_root_does_not_exist(omega: surface.OmegaSurface) -> None:
    """Otherwise the experiment could pass by colliding with a real tree."""
    assert relocation.DESTINATION not in omega.population.roots
    assert not Path(relocation.DESTINATION).exists()


def test_a_relocated_exemption_follows_its_package() -> None:
    """``engine.uicm`` becoming ``galaxy.uicm`` is the edit the move implies, not a smoothing."""
    assert relocation._relocate_exemptions({"engine.uicm": "why"}, "engine") == {
        "galaxy.uicm": "why"
    }
    assert relocation._relocate_exemptions({"other.pkg": "why"}, "engine") == {"other.pkg": "why"}


def test_relocation_maps_only_the_named_root() -> None:
    assert relocation._relocate("engine/a.py", "engine", "galaxy") == "galaxy/a.py"
    assert relocation._relocate("engineering/a.py", "engine", "galaxy") == "engineering/a.py"
    assert relocation._relocate("platform/a.py", "engine", "galaxy") == "platform/a.py"


# ------------------------------------------------------------------------------------- Ω-4 wiring


def test_every_ratcheted_metric_declares_a_known_kind_and_a_subject(
    omega: surface.OmegaSurface,
) -> None:
    assert omega.observations
    for observation in omega.observations:
        assert observation.kind in RATCHET_KINDS
        assert observation.subject.strip(), f"{observation.metric} states no subject"


def test_the_metric_set_covers_every_exemption_rule(omega: surface.OmegaSurface) -> None:
    """Each exemption class's size must be ratcheted, or one of them can grow unremarked."""
    metrics = {name for name, *_rest in surface.metrics(omega.artifacts, _FakeGraph())}
    assert {"unexplained_exemptions", "unnameable_exemptions", "declared_exemptions"} <= metrics


class _FakeGraph:
    unresolved_dynamic: dict[str, int] = {}


def test_the_density_and_entropy_metrics_carry_their_ratio(
    omega: surface.OmegaSurface,
) -> None:
    """A ratio without its numerator and denominator is a number nobody can check."""
    for observation in omega.observations:
        if observation.kind in ratchet.RATIO_KINDS:
            assert observation.ratio is not None
            numerator, denominator = observation.ratio
            assert denominator > 0
            assert observation.value == pytest.approx(numerator / denominator, abs=1e-6)


# ------------------------------------------------------------------------------------- the gate


def test_the_gate_passes_over_the_real_repository() -> None:
    verdict = gate.evaluate(".")
    assert verdict.passed, "\n".join(verdict.findings)
    assert verdict.exit_code == 0


def test_the_gate_reports_every_phase_and_names_its_notes() -> None:
    verdict = gate.evaluate(".")
    rendered = gate.render(verdict)
    for phase in (
        "Ω-1 DISCOVERY",
        "Ω-2 AUTHORITY",
        "Ω-3 EXECUTION GRAPH",
        "Ω-5 DISPOSITION",
        "Ω-4 RATCHETS",
    ):
        assert phase in rendered, f"{phase} is missing from the gate report"
    assert len(verdict.notes) >= 4


def test_the_gate_refuses_when_a_ratchet_regresses(tmp_path: Path) -> None:
    """NON-VACUITY for the gate itself: it must be able to close, not merely to open.

    The sealed state is reloaded with every bound driven to zero, which is a regression on every
    metric at once. A gate that still passed would be decoration.
    """
    state = ratchet.load(surface.RATCHET_STATE)
    assert state.best, "the sealed state is empty, so this test would prove nothing"
    document = {
        "schema": ratchet.SCHEMA,
        "version": ratchet.VERSION,
        "best": dict.fromkeys(state.best, 0.0),
        "kinds": state.kinds,
        "holds": {},
        "justifications": [],
        "floors": [],
    }
    scratch = tmp_path / "state.json"
    ratchet.write(str(scratch), document)
    tightened = ratchet.load(str(scratch))
    refused = [
        tightened.observe(name, kind, value, subject)
        for name, kind, value, subject, _ratio in surface.metrics(omega_artifacts(), _FakeGraph())
        if value > 0
    ]
    assert refused, "no metric was above zero, so the tightened state proves nothing"
    assert ratchet.refusals(refused), "every bound was driven to zero and the gate still passed"


def omega_artifacts() -> tuple:
    return surface.build(".").artifacts


def test_sealing_writes_exactly_two_paths_inside_the_programme_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The one writing path. Both targets resolve inside ``00-MASTER/UCOS-OMEGA-001/``."""
    verdict = gate.evaluate(".")
    written = []

    def capture(path: str, document: object) -> None:
        written.append(path)

    monkeypatch.setattr(ratchet, "write", capture)
    monkeypatch.setattr(gate.ratchet, "write", capture)
    target = tmp_path / gate.EVIDENCE
    target.parent.mkdir(parents=True, exist_ok=True)
    paths = gate.seal(str(tmp_path), verdict)
    assert paths == (gate.EVIDENCE, surface.RATCHET_STATE)
    for path in paths:
        assert path.startswith("00-MASTER/UCOS-OMEGA-001/"), path
    assert target.is_file()


# ------------------------------------------------------------------------------- the CLI surface


def test_the_cli_reports_and_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    from engine.universal_discovery import __main__ as cli

    assert cli.main([]) == 0
    assert "UNIVERSAL DISCOVERY GATE" in capsys.readouterr().out


def test_the_cli_emits_the_surface_document(capsys: pytest.CaptureFixture[str]) -> None:
    from engine.universal_discovery import __main__ as cli

    assert cli.main(["--json"]) == 0
    document = json.loads(capsys.readouterr().out)
    assert document["schema"] == surface.SCHEMA


def test_the_cli_prints_the_derived_scope(capsys: pytest.CaptureFixture[str]) -> None:
    from engine.universal_discovery import __main__ as cli

    assert cli.main(["--scope"]) == 0
    document = json.loads(capsys.readouterr().out)
    assert document["measurable_packages"] and document["test_roots"]


def test_a_discovery_fault_exits_two_rather_than_reporting_a_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from engine.universal_discovery import __main__ as cli

    assert cli.main(["--root", str(tmp_path)]) == 2
    assert "FAULT" in capsys.readouterr().err


# ----------------------------------------------------------------------------- the scope plugin


def test_the_plugin_derives_the_same_scope_the_gate_measures(
    omega: surface.OmegaSurface,
) -> None:
    """One derivation. If these two ever disagree, the suite is measuring a different world."""
    from engine.universal_discovery import pytest_scope

    packages, test_roots = pytest_scope.derive()
    assert tuple(packages) == omega.population.measurable_packages
    assert tuple(test_roots) == omega.population.test_roots


def test_the_plugin_locates_the_repository_from_its_own_position() -> None:
    from engine.universal_discovery import pytest_scope

    assert (Path(pytest_scope._repository_root()) / "pyproject.toml").is_file()


def test_the_running_suite_is_measured_against_the_derived_denominator(
    request: pytest.FixtureRequest, omega: surface.OmegaSurface
) -> None:
    """THE CLAIM THAT MATTERS, witnessed from inside the run it is about.

    Every other test here measures the derivation. This one asks pytest-cov what denominator IT was
    handed, which is the only way to know that the suite reporting a coverage percentage is
    reporting it over the derived set rather than over something else.

    Skipped when the plugin is not loaded, which happens for a deliberately narrow invocation such
    as ``-o addopts="" --cov=one.package``. That is an explicit request, and the plugin honours it
    rather than overriding it — so asserting equality here would fail a run that is behaving
    correctly.
    """
    if not request.config.pluginmanager.hasplugin("engine.universal_discovery.pytest_scope"):
        pytest.skip("the scope plugin is not loaded in this invocation, so nothing is witnessable")
    source = getattr(request.config.option, "cov_source", None)
    if not source:
        pytest.skip("this run was invoked with --no-cov, so there is no denominator to witness")
    assert set(source) == set(
        omega.population.measurable_packages
    ), "the denominator pytest-cov received is not the one discovery derived"


def test_the_hook_injects_the_derived_scope_and_the_derived_collection_set() -> None:
    """The hook body, exercised directly. It cannot be covered from inside a run it precedes.

    ``pytest_load_initial_conftests`` executes before coverage starts, so the lines that do the
    injection are invisible to any measurement of the run they configure. Driving the hook with a
    stand-in ``early_config`` is the only way to measure it, and it also pins the two behaviours a
    reader would otherwise have to infer: an explicit ``--cov=`` wins, and named paths suppress the
    injected collection set.
    """
    from engine.universal_discovery import pytest_scope

    class _Namespace:
        def __init__(self, **kwargs: object) -> None:
            self.__dict__.update(kwargs)

    class _EarlyConfig:
        def __init__(self, namespace: _Namespace) -> None:
            self.known_args_namespace = namespace

    def drive(namespace: _Namespace, args: list[str]) -> list[str]:
        wrapper = pytest_scope.pytest_load_initial_conftests(_EarlyConfig(namespace), None, args)
        next(wrapper)  # everything before the yield is the injection
        with pytest.raises(StopIteration):
            next(wrapper)
        return args

    packages, test_roots = pytest_scope.derive()

    # 1. No explicit scope and no named path: both sets are injected.
    namespace = _Namespace(cov_source=[], file_or_dir=[])
    args = drive(namespace, ["-ra"])
    assert namespace.cov_source == packages
    assert args[1:] == test_roots

    # 2. An explicit --cov= wins. A developer measuring one package must not silently be given 79.
    explicit = _Namespace(cov_source=["engine.foundation"], file_or_dir=[])
    drive(explicit, [])
    assert explicit.cov_source == ["engine.foundation"]

    # 3. A named path suppresses the injected collection set, but the denominator is still derived.
    targeted = _Namespace(cov_source=[], file_or_dir=["engine/tests/unit"])
    args = drive(targeted, [])
    assert args == []
    assert targeted.cov_source == packages


def test_the_injection_can_be_disabled_for_bisecting_discovery_itself(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The escape hatch exists, is read from the environment so it cannot become the default, and
    is reported in the header when it is in force."""
    from engine.universal_discovery import pytest_scope

    class _Namespace:
        cov_source: list[str] = []
        file_or_dir: list[str] = []

    class _EarlyConfig:
        known_args_namespace = _Namespace()

    monkeypatch.setenv(pytest_scope.DISABLE, "1")
    args: list[str] = []
    wrapper = pytest_scope.pytest_load_initial_conftests(_EarlyConfig(), None, args)
    next(wrapper)
    with pytest.raises(StopIteration):
        next(wrapper)
    assert args == [] and _Namespace.cov_source == []
    assert "DISABLED" in pytest_scope.pytest_report_header(None)


def test_the_plugin_reports_the_denominator_in_the_run_header(
    request: pytest.FixtureRequest,
) -> None:
    from engine.universal_discovery import pytest_scope

    header = pytest_scope.pytest_report_header(request.config)
    assert "UCOS-OMEGA-001" in header
