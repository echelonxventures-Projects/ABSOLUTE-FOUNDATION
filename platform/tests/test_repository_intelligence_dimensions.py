"""UCOS-EPIC-014 — the eight discovery dimensions driven over a SYNTHETIC substrate.

WHY THIS MODULE EXISTS, STATED AS THE MEASUREMENT THAT PRODUCED IT. Every existing suite
runs the dimensions over THIS repository, which is a repository that mostly satisfies
them: the catalog composes, the graph is acyclic, no module fails to parse, no two modules
are byte-identical, no console script dangles and no capability declares two owners. So
the PASS arm of each dimension was measured and the FAIL and ADVISORY arms — which are the
entire product of a discovery engine — were not. A detector observed only over a substrate
that gives it nothing to detect is indistinguishable from one that detects nothing.

Every substrate below is BUILT rather than scanned. That is the point twice over: it is
the only way to present the engine with a repository that contradicts itself, and it is
what makes these tests a statement about the DIMENSIONS rather than about the state this
repository happens to be in on the day they run.
"""

from __future__ import annotations

from pathlib import Path
from platform.repository_intelligence import discovery
from platform.repository_intelligence.config import RepositoryIntelligenceConfig
from platform.repository_intelligence.contracts import (
    DiscoveryDimension,
    FindingStatus,
    RecommendationAction,
    Severity,
    UnitKind,
)
from platform.repository_intelligence.errors import RecommendationError
from platform.repository_intelligence.graph import build_graph
from platform.repository_intelligence.recommendation import (
    PRIORITY_NONE,
    RepositoryRecommendationEngine,
)
from platform.repository_intelligence.substrate import (
    CATALOG_SOURCE_ABSENT,
    Declarations,
    ModuleFact,
    RepositorySubstrate,
)

import pytest

CATALOG_SOURCE = "test-catalog"


def _config(tmp_path: Path, **overrides) -> RepositoryIntelligenceConfig:
    fields = {
        "repository_root": tmp_path,
        "repository_id": "synthetic",
        "code_roots": ("engine", "platform"),
    }
    fields.update(overrides)
    return RepositoryIntelligenceConfig(**fields)


def _module(
    module: str,
    *,
    capability: str | None = None,
    loc: int = 40,
    content: str | None = None,
    imports: tuple[str, ...] = (),
    import_time: tuple[str, ...] | None = None,
    symbols: tuple[str, ...] = (),
    docline: str = "A capability that describes itself.",
    is_test: bool = False,
    parsed: bool = True,
) -> ModuleFact:
    parts = module.split(".")
    return ModuleFact(
        module=module,
        capability=capability if capability is not None else ".".join(parts[:2]),
        root=parts[0],
        path=module.replace(".", "/") + ".py",
        loc=loc,
        content_sha256=content if content is not None else f"sha-{module}",
        imports=imports,
        import_time_imports=imports if import_time is None else import_time,
        symbols=symbols,
        docline=docline,
        is_test=is_test,
        parsed=parsed,
    )


def _substrate(
    tmp_path: Path,
    modules: tuple[ModuleFact, ...],
    *,
    zones: dict[str, int] | None = None,
    declarations: Declarations | None = None,
    catalog: tuple[dict, ...] = (),
    catalog_source: str = CATALOG_SOURCE,
    config: RepositoryIntelligenceConfig | None = None,
) -> RepositorySubstrate:
    return RepositorySubstrate(
        config=config or _config(tmp_path),
        modules=tuple(sorted(modules, key=lambda m: m.module)),
        zones=zones or {},
        declarations=declarations or Declarations(available=False),
        catalog=catalog,
        catalog_source=catalog_source,
    )


def _codes(result) -> list[str]:
    return sorted(f.code for f in result.findings)


def _finding(result, code: str):
    for item in result.findings:
        if item.code == code:
            return item
    raise AssertionError(f"{code!r} not among {_codes(result)}")


# -- 1. repository ---------------------------------------------------------------------


def test_a_readable_substrate_reports_its_units_and_passes(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.alpha"),
            _module("engine.alpha.contracts"),
            _module("platform.tests.test_alpha", capability="platform.tests", is_test=True),
        ),
        zones={"00-BOOK": 12, "evidence": 3, ".": 1, "engine": 2},
        declarations=Declarations(
            available=True, console_scripts={"ucos-alpha": "engine.alpha:main"}
        ),
    )
    units, result = discovery.discover_repository(substrate)
    kinds = {unit.kind for unit in units}
    assert UnitKind.CODE_CAPABILITY in kinds
    assert UnitKind.ENTRY_POINT in kinds
    assert UnitKind.CONSTITUTIONAL_ZONE in kinds  # 00-BOOK matches the numbered convention
    assert UnitKind.EVIDENCE_STORE in kinds  # 'evidence' does not
    assert {u.name for u in units if u.kind is UnitKind.CONSTITUTIONAL_ZONE} == {"00-BOOK"}
    assert _finding(result, discovery.SUBSTRATE_PRESENT).status is FindingStatus.PASS
    # the declared code roots do not exist under tmp_path, so no CODE_ROOT unit is emitted
    assert UnitKind.CODE_ROOT not in kinds


def test_a_declared_code_root_that_exists_becomes_a_unit(tmp_path):
    (tmp_path / "engine").mkdir()
    substrate = _substrate(tmp_path, (_module("engine.alpha"),))
    units, _result = discovery.discover_repository(substrate)
    roots = [u for u in units if u.kind is UnitKind.CODE_ROOT]
    assert [u.name for u in roots] == ["engine"]
    assert roots[0].tracked_files == 1


def test_a_substrate_with_no_readable_source_module_fails_closed(tmp_path):
    substrate = _substrate(
        tmp_path, (_module("platform.tests.test_alpha", capability="platform.tests", is_test=True),)
    )
    _units, result = discovery.discover_repository(substrate)
    assert _finding(result, discovery.SUBSTRATE_PRESENT).status is FindingStatus.FAIL


def test_a_module_that_could_not_be_parsed_is_reported(tmp_path):
    substrate = _substrate(
        tmp_path, (_module("engine.alpha"), _module("engine.alpha.broken", parsed=False))
    )
    _units, result = discovery.discover_repository(substrate)
    finding = _finding(result, discovery.MODULE_UNPARSED)
    assert finding.subject == "engine.alpha.broken"
    assert finding.severity is Severity.BLOCKING


def test_the_code_roots_themselves_are_not_capabilities(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine", capability="engine"),
            _module("engine.alpha"),
            _module("platform.tests.test_alpha", capability="platform.tests", is_test=True),
        ),
    )
    assert discovery.implementation_capabilities(substrate) == ("engine.alpha",)


# -- 2. capabilities -------------------------------------------------------------------


def test_an_absent_catalog_fails_rather_than_re_deriving_capability_policy(tmp_path):
    substrate = _substrate(
        tmp_path, (_module("engine.alpha"),), catalog_source=CATALOG_SOURCE_ABSENT
    )
    _records, result = discovery.discover_capabilities(substrate)
    assert _finding(result, discovery.CATALOG_COMPOSED).status is FindingStatus.FAIL


def test_a_capability_absent_from_the_catalog_inherits_its_layer_s_modal_policy(tmp_path):
    catalog = (
        {
            "canonical_name": "engine.beta",
            "category": "engine",
            "authority": "OWNER-A",
            "reuse": "REUSE",
            "replacement_prohibited": True,
            "canonical_location": "engine/beta",
            "implementation_status": "IMPLEMENTED",
        },
        {
            "canonical_name": "engine.gamma",
            "category": "engine",
            "authority": "OWNER-A",
            "reuse": "REUSE",
            "replacement_prohibited": True,
            "canonical_location": "engine/gamma",
            "implementation_status": "IMPLEMENTED",
        },
    )
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"), _module("engine.beta"), _module("engine.gamma")),
        catalog=catalog,
    )
    records, result = discovery.discover_capabilities(substrate)
    omission = _finding(result, discovery.CATALOG_OMISSION)
    assert omission.subject == "engine.alpha"
    assert omission.severity is Severity.ADVISORY
    assert "modal policy of 2 catalogued peers" in omission.details["policy_basis"]
    alpha = next(r for r in records if r.name == "engine.alpha")
    assert alpha.authority == "OWNER-A"
    assert alpha.replacement_prohibited is True
    assert alpha.source == "substrate-scan (catalog omission)"


def test_the_first_capability_in_a_layer_inherits_nothing_and_says_so(tmp_path):
    substrate = _substrate(tmp_path, (_module("engine.alpha"),), catalog=())
    records, _result = discovery.discover_capabilities(substrate)
    alpha = next(r for r in records if r.name == "engine.alpha")
    assert alpha.authority == "UNDETERMINED"
    assert alpha.reuse_directive == ""


def test_a_capability_package_with_no_docstring_is_reported(tmp_path):
    substrate = _substrate(tmp_path, (_module("engine.alpha", docline=""),))
    _records, result = discovery.discover_capabilities(substrate)
    assert _finding(result, discovery.CAPABILITY_UNDOCUMENTED).subject == "engine.alpha"


def test_a_catalog_entry_naming_a_populated_location_is_granularity_not_a_phantom(tmp_path):
    catalog = (
        {
            "canonical_name": "engine.alpha.nested",
            "category": "engine",
            "canonical_location": "engine/alpha/nested",
            "authority": "A",
            "reuse": "R",
        },
    )
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"), _module("engine.alpha.nested.core", capability="engine.alpha")),
        catalog=catalog,
    )
    records, result = discovery.discover_capabilities(substrate)
    finding = _finding(result, discovery.CATALOG_GRANULARITY)
    assert finding.details["claimed_location"] == "engine/alpha/nested"
    assert all(record.present_on_disk for record in records)


def test_a_catalog_entry_naming_a_location_that_is_absent_becomes_a_phantom_record(tmp_path):
    catalog = (
        {
            "canonical_name": "engine.ghost",
            "category": "engine",
            "canonical_location": "engine/ghost",
            "authority": "A",
            "reuse": "R",
        },
    )
    substrate = _substrate(tmp_path, (_module("engine.alpha"),), catalog=catalog)
    records, result = discovery.discover_capabilities(substrate)
    ghost = next(r for r in records if r.name == "engine.ghost")
    assert ghost.present_on_disk is False
    assert discovery.CATALOG_GRANULARITY not in _codes(result)


def test_a_catalog_entry_outside_the_declared_code_roots_is_ignored(tmp_path):
    catalog = ({"canonical_name": "corpus.thing", "category": "corpus"},)
    substrate = _substrate(tmp_path, (_module("engine.alpha"),), catalog=catalog)
    records, _result = discovery.discover_capabilities(substrate)
    assert [r.name for r in records] == ["engine.alpha"]


# -- 4. dependencies -------------------------------------------------------------------


def test_an_internal_import_that_resolves_to_nothing_is_a_blocking_finding(tmp_path):
    substrate = _substrate(tmp_path, (_module("engine.alpha", imports=("engine.nowhere.at_all",)),))
    _edges, result = discovery.discover_dependencies(substrate)
    finding = _finding(result, discovery.DEPENDENCY_UNRESOLVABLE)
    assert finding.details["imported"] == "engine.nowhere.at_all"
    assert finding.severity is Severity.BLOCKING


def test_an_import_of_a_package_prefix_that_contains_capabilities_resolves(tmp_path):
    substrate = _substrate(tmp_path, (_module("engine.alpha", imports=("engine",)),))
    _edges, result = discovery.discover_dependencies(substrate)
    assert discovery.DEPENDENCY_UNRESOLVABLE not in _codes(result)


def test_a_deferred_import_does_not_create_an_edge_and_cannot_close_a_cycle(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.alpha", imports=("platform.beta",), import_time=()),
            _module("platform.beta", imports=("engine.alpha",)),
        ),
    )
    edges, result = discovery.discover_dependencies(substrate)
    assert [(e.source, e.target) for e in edges] == [("platform.beta", "engine.alpha")]
    assert _finding(result, discovery.DEPENDENCY_ACYCLIC).status is FindingStatus.PASS


def test_a_real_import_cycle_is_refused_by_the_acyclicity_determination(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.alpha", imports=("engine.beta",)),
            _module("engine.beta", imports=("engine.alpha",)),
        ),
    )
    _edges, result = discovery.discover_dependencies(substrate)
    finding = _finding(result, discovery.DEPENDENCY_ACYCLIC)
    assert finding.status is FindingStatus.FAIL
    assert finding.details["cycle_count"] == 1


def test_an_undeclared_third_party_distribution_is_reported(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha", imports=("some_vendor_lib",)),),
        declarations=Declarations(available=True, runtime_dependencies=("other-lib==1.0",)),
    )
    _edges, result = discovery.discover_dependencies(substrate)
    finding = _finding(result, discovery.DEPENDENCY_UNDECLARED)
    assert finding.subject == "some_vendor_lib"
    assert finding.details["importer_count"] == 1


def test_a_declared_distribution_is_not_reported_however_its_name_is_spelled(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha", imports=("some_vendor_lib",)),),
        declarations=Declarations(available=True, dev_dependencies=("Some-Vendor-Lib>=1.0",)),
    )
    _edges, result = discovery.discover_dependencies(substrate)
    assert discovery.DEPENDENCY_UNDECLARED not in _codes(result)


def test_a_first_party_root_outside_the_distributable_roots_is_an_architectural_fact(tmp_path):
    companion = tmp_path / "companion"
    companion.mkdir()
    (companion / "__init__.py").write_text("", encoding="utf-8")
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha", imports=("companion.thing",)),),
        declarations=Declarations(available=True),
    )
    _edges, result = discovery.discover_dependencies(substrate)
    finding = _finding(result, discovery.DEPENDENCY_COMPANION_ROOT)
    assert finding.subject == "companion"
    assert finding.severity is Severity.ADVISORY


def test_a_stdlib_import_is_neither_undeclared_nor_a_companion_root(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha", imports=("json", "os.path", "_private")),),
        declarations=Declarations(available=True),
    )
    _edges, result = discovery.discover_dependencies(substrate)
    assert discovery.DEPENDENCY_UNDECLARED not in _codes(result)
    assert discovery.DEPENDENCY_COMPANION_ROOT not in _codes(result)


def test_an_intra_capability_import_creates_no_edge(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.alpha", imports=("engine.alpha.contracts",)),
            _module("engine.alpha.contracts"),
        ),
    )
    edges, _result = discovery.discover_dependencies(substrate)
    assert edges == ()


# -- 3. reuse --------------------------------------------------------------------------


def test_a_capability_nothing_imports_and_nothing_publishes_is_unproven(tmp_path):
    substrate = _substrate(tmp_path, (_module("engine.alpha"),))
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    assessments, result = discovery.discover_reuse(substrate, records, edges)
    assert [a.proof.value for a in assessments] == ["unproven"]
    assert discovery.REUSE_UNPROVEN in _codes(result)
    assert discovery.REUSE_DIRECTIVE_MISSING in _codes(result)


def test_a_console_script_is_reuse_evidence_when_nothing_imports_the_capability(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"),),
        declarations=Declarations(
            available=True, console_scripts={"ucos-alpha": "engine.alpha.cli:main"}
        ),
        catalog=(
            {
                "canonical_name": "engine.alpha",
                "category": "engine",
                "reuse": "REUSE",
                "authority": "A",
                "canonical_location": "engine/alpha",
            },
        ),
    )
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    assessments, result = discovery.discover_reuse(substrate, records, edges)
    assert [a.proof.value for a in assessments] == ["entry_point"]
    assert assessments[0].published_entry_points == ("ucos-alpha",)
    assert discovery.REUSE_UNPROVEN not in _codes(result)
    assert discovery.REUSE_DIRECTIVE_MISSING not in _codes(result)


def test_an_importer_proves_reuse(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"), _module("platform.beta", imports=("engine.alpha",))),
        catalog=(
            {
                "canonical_name": "engine.alpha",
                "category": "engine",
                "reuse": "REUSE",
                "authority": "A",
                "canonical_location": "engine/alpha",
            },
            {
                "canonical_name": "platform.beta",
                "category": "platform",
                "reuse": "REUSE",
                "authority": "A",
                "canonical_location": "platform/beta",
            },
        ),
    )
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    assessments, _result = discovery.discover_reuse(substrate, records, edges)
    proven = {a.capability: a.proof.value for a in assessments}
    assert proven["engine.alpha"] == "proven"


def test_a_phantom_capability_is_not_assessed_for_reuse(tmp_path):
    catalog = (
        {
            "canonical_name": "engine.ghost",
            "category": "engine",
            "canonical_location": "engine/ghost",
            "reuse": "R",
            "authority": "A",
        },
    )
    substrate = _substrate(tmp_path, (_module("engine.alpha"),), catalog=catalog)
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    assessments, _result = discovery.discover_reuse(substrate, records, edges)
    assert "engine.ghost" not in {a.capability for a in assessments}


# -- 5. gaps ---------------------------------------------------------------------------


def test_an_unregistered_untested_capability_reports_every_gap_it_has(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"), _module("engine.alpha.cli", capability="engine.alpha")),
        declarations=Declarations(available=True),
    )
    records, _ = discovery.discover_capabilities(substrate)
    result = discovery.discover_gaps(substrate, records)
    assert discovery.GAP_UNREGISTERED_COVERAGE in _codes(result)
    assert discovery.GAP_UNREGISTERED_COV_OPTION in _codes(result)
    assert discovery.GAP_UNTESTED in _codes(result)
    assert discovery.GAP_UNPUBLISHED_CLI in _codes(result)
    assert all(f.severity is Severity.ADVISORY for f in result.findings)


def test_a_fully_registered_tested_and_published_capability_reports_no_gap(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.alpha"),
            _module("engine.alpha.cli", capability="engine.alpha"),
            _module(
                "platform.tests.test_alpha",
                capability="platform.tests",
                is_test=True,
                imports=("engine.alpha",),
            ),
        ),
        declarations=Declarations(
            available=True,
            coverage_sources=("engine/alpha",),
            pytest_cov_packages=("engine.alpha",),
            console_scripts={"ucos-alpha": "engine.alpha.cli:main"},
        ),
    )
    records, _ = discovery.discover_capabilities(substrate)
    result = discovery.discover_gaps(substrate, records)
    assert discovery.GAP_UNREGISTERED_COVERAGE not in _codes(result)
    assert discovery.GAP_UNTESTED not in _codes(result)
    assert discovery.GAP_UNPUBLISHED_CLI not in _codes(result)


def test_a_convention_a_layer_has_established_is_expected_of_its_peers(tmp_path):
    modules = (
        _module("engine.alpha"),
        _module("engine.alpha.errors", capability="engine.alpha"),
        _module("engine.beta"),
        _module("engine.beta.errors", capability="engine.beta"),
        _module("engine.gamma"),
    )
    substrate = _substrate(tmp_path, modules)
    records, _ = discovery.discover_capabilities(substrate)
    result = discovery.discover_gaps(substrate, records)
    missing = [f for f in result.findings if f.code == discovery.GAP_MISSING_CONVENTION_MODULE]
    assert [f.subject for f in missing] == ["engine.gamma.errors"]
    assert missing[0].details["peers"] == 3


def test_a_layer_with_one_capability_establishes_no_convention(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"), _module("engine.alpha.errors", capability="engine.alpha")),
    )
    records, _ = discovery.discover_capabilities(substrate)
    result = discovery.discover_gaps(substrate, records)
    assert discovery.GAP_MISSING_CONVENTION_MODULE not in _codes(result)


# -- 6. conflicts ----------------------------------------------------------------------


def test_a_lower_layer_depending_on_a_higher_one_is_a_layer_violation(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha", imports=("platform.beta",)), _module("platform.beta")),
    )
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    result = discovery.discover_conflicts(substrate, records, edges)
    finding = _finding(result, discovery.CONFLICT_LAYER_VIOLATION)
    assert finding.subject == "engine.alpha -> platform.beta"
    assert finding.severity is Severity.BLOCKING


def test_a_cycle_is_reported_once_more_in_the_conflict_dimension_s_own_terms(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.alpha", imports=("engine.beta",)),
            _module("engine.beta", imports=("engine.alpha",)),
        ),
    )
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    result = discovery.discover_conflicts(substrate, records, edges)
    assert _finding(result, discovery.CONFLICT_IMPORT_CYCLE).details["cycle"]


def test_registration_in_one_coverage_gate_and_not_the_other_is_a_contradiction(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"),),
        declarations=Declarations(available=True, coverage_sources=("engine/alpha",)),
    )
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    result = discovery.discover_conflicts(substrate, records, edges)
    finding = _finding(result, discovery.CONFLICT_REGISTRATION_INCONSISTENT)
    assert finding.details == {"in_coverage_source": True, "in_pytest_cov": False}


def test_a_console_script_naming_a_module_that_does_not_exist_is_refused(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"),),
        declarations=Declarations(
            available=True, console_scripts={"ucos-ghost": "engine.ghost.cli:main"}
        ),
    )
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    result = discovery.discover_conflicts(substrate, records, edges)
    assert _finding(result, discovery.CONFLICT_ENTRY_POINT_UNRESOLVABLE).subject == "ucos-ghost"


def test_two_console_scripts_resolving_to_one_entry_point_are_reported(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"),),
        declarations=Declarations(
            available=True,
            console_scripts={"ucos-alpha": "engine.alpha:main", "alpha": "engine.alpha:main"},
        ),
    )
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    result = discovery.discover_conflicts(substrate, records, edges)
    finding = _finding(result, discovery.CONFLICT_ENTRY_POINT_ALIASED)
    assert finding.details["scripts"] == ["alpha", "ucos-alpha"]


def test_a_catalogued_capability_that_is_not_on_disk_is_a_phantom(tmp_path):
    catalog = (
        {
            "canonical_name": "engine.ghost",
            "category": "engine",
            "canonical_location": "engine/ghost",
            "authority": "A",
            "reuse": "R",
        },
    )
    substrate = _substrate(tmp_path, (_module("engine.alpha"),), catalog=catalog)
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    result = discovery.discover_conflicts(substrate, records, edges)
    assert _finding(result, discovery.CATALOG_PHANTOM).subject == "engine.ghost"


@pytest.mark.parametrize(
    ("includes", "reported"),
    [(("engine*",), False), (("engine",), False), (("platform*",), True)],
)
def test_a_code_root_no_package_include_matches_is_not_distributed(tmp_path, includes, reported):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"),),
        config=_config(tmp_path, code_roots=("engine",)),
        declarations=Declarations(available=True, packaged_includes=includes),
    )
    records, _ = discovery.discover_capabilities(substrate)
    edges, _ = discovery.discover_dependencies(substrate)
    result = discovery.discover_conflicts(substrate, records, edges)
    assert (discovery.CONFLICT_NOT_PACKAGED in _codes(result)) is reported


# -- 7. duplicates ---------------------------------------------------------------------


def test_two_byte_identical_modules_are_a_blocking_duplicate(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.alpha", content="same", loc=40),
            _module("platform.beta", content="same", loc=40),
        ),
    )
    result = discovery.detect_duplicates(substrate)
    finding = _finding(result, discovery.DUPLICATE_MODULE_CONTENT)
    assert finding.severity is Severity.BLOCKING
    assert finding.details["paths"] == ["engine/alpha.py", "platform/beta.py"]


def test_two_byte_identical_but_trivial_modules_are_convention_not_duplication(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.alpha", content="same", loc=1),
            _module("platform.beta", content="same", loc=1),
        ),
    )
    result = discovery.detect_duplicates(substrate)
    assert _finding(result, discovery.DUPLICATE_TRIVIAL_CONTENT).severity is Severity.ADVISORY
    assert discovery.DUPLICATE_MODULE_CONTENT not in _codes(result)


def test_one_capability_name_in_two_roots_is_reported_and_assessed(tmp_path):
    shared = ("Alpha", "Beta", "Gamma", "Delta")
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.thing", symbols=shared),
            _module("platform.thing", symbols=shared),
        ),
    )
    result = discovery.detect_duplicates(substrate)
    finding = _finding(result, discovery.DUPLICATE_CAPABILITY_NAME)
    assert finding.subject == "thing"
    assert finding.details["assessment"].startswith("SUSPECT")
    assert finding.details["surface_jaccard"] == 1.0


def test_a_layered_pair_with_distinct_surfaces_is_assessed_as_intentional(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.thing", symbols=("Alpha", "Beta")),
            _module("platform.thing", symbols=("Gamma", "Delta")),
        ),
    )
    finding = _finding(discovery.detect_duplicates(substrate), discovery.DUPLICATE_CAPABILITY_NAME)
    assert finding.details["assessment"].startswith("INTENTIONAL")
    assert finding.details["surface_jaccard"] == 0.0


def test_two_differently_named_capabilities_sharing_a_surface_are_duplication_candidates(tmp_path):
    shared = ("Alpha", "Beta", "Gamma", "Delta")
    substrate = _substrate(
        tmp_path,
        (_module("engine.left", symbols=shared), _module("engine.right", symbols=shared)),
    )
    result = discovery.detect_duplicates(substrate)
    finding = _finding(result, discovery.DUPLICATE_SYMBOL_SURFACE)
    assert finding.details["shared_count"] == 4
    assert finding.details["surface_jaccard"] == 1.0


def test_a_shared_surface_below_the_declared_thresholds_is_not_reported(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.left", symbols=("Alpha", "Beta", "Only")),
            _module("engine.right", symbols=("Alpha", "Beta", "Other")),
        ),
    )
    assert discovery.DUPLICATE_SYMBOL_SURFACE not in _codes(discovery.detect_duplicates(substrate))


def test_a_capability_with_no_public_surface_is_not_compared(tmp_path):
    substrate = _substrate(
        tmp_path, (_module("engine.left", symbols=()), _module("engine.right", symbols=()))
    )
    assert discovery.detect_duplicates(substrate).findings == ()


# -- 8. ownership ----------------------------------------------------------------------


def test_a_declared_terminal_is_the_strongest_ownership_evidence(tmp_path):
    substrate = _substrate(
        tmp_path, (_module("engine.alpha", docline="EPIC-DOC-003 (Terminal T4) — the portal."),)
    )
    units, _ = discovery.discover_repository(substrate)
    records, _ = discovery.discover_capabilities(substrate)
    ownership, result = discovery.discover_ownership(substrate, units, records)
    assert ownership[0].owner == "Terminal T4"
    assert ownership[0].confidence == "high"
    assert result.findings == ()


def test_two_declared_terminals_make_ownership_contested_rather_than_resolved(tmp_path):
    substrate = _substrate(
        tmp_path,
        (
            _module("engine.alpha", docline="Terminal T4 — the portal."),
            _module("engine.alpha.core", capability="engine.alpha", docline="Terminal T5 — core."),
        ),
    )
    units, _ = discovery.discover_repository(substrate)
    records, _ = discovery.discover_capabilities(substrate)
    ownership, result = discovery.discover_ownership(substrate, units, records)
    assert ownership[0].confidence == "contested"
    assert _finding(result, discovery.OWNERSHIP_CONTESTED).details["candidates"] == [
        "Terminal T4",
        "Terminal T5",
    ]


def test_a_programme_identifier_owns_a_capability_that_declares_no_terminal(tmp_path):
    substrate = _substrate(
        tmp_path, (_module("engine.alpha", docline="UCOS-EPIC-014 — commercial intelligence."),)
    )
    units, _ = discovery.discover_repository(substrate)
    records, _ = discovery.discover_capabilities(substrate)
    ownership, _result = discovery.discover_ownership(substrate, units, records)
    assert ownership[0].owner == "EPIC-014"
    assert ownership[0].confidence == "medium"


def test_the_layer_authority_owns_a_capability_that_declares_nothing(tmp_path):
    catalog = (
        {
            "canonical_name": "engine.alpha",
            "category": "engine",
            "authority": "OWNER-A",
            "reuse": "R",
            "canonical_location": "engine/alpha",
        },
    )
    substrate = _substrate(
        tmp_path, (_module("engine.alpha", docline="A module."),), catalog=catalog
    )
    units, _ = discovery.discover_repository(substrate)
    records, _ = discovery.discover_capabilities(substrate)
    ownership, result = discovery.discover_ownership(substrate, units, records)
    assert ownership[0].owner == "OWNER-A"
    assert ownership[0].confidence == "low"
    assert result.findings == ()


def test_a_capability_nothing_owns_is_reported_as_unowned(tmp_path):
    substrate = _substrate(tmp_path, (_module("engine.alpha", docline="A module."),))
    units, _ = discovery.discover_repository(substrate)
    records, _ = discovery.discover_capabilities(substrate)
    ownership, result = discovery.discover_ownership(substrate, units, records)
    assert ownership[0].confidence == "none"
    assert _finding(result, discovery.OWNERSHIP_UNOWNED).subject == "engine.alpha"


def test_a_module_with_no_docline_contributes_no_owner_token(tmp_path):
    assert discovery._declared_owners(
        _substrate(tmp_path, (_module("engine.alpha", docline=""),)), "engine.alpha"
    ) == ((), ())


# -- orchestration ---------------------------------------------------------------------


def test_discover_all_runs_every_dimension_and_the_outcome_is_addressable(tmp_path):
    substrate = _substrate(
        tmp_path,
        (_module("engine.alpha"), _module("platform.beta", imports=("engine.alpha",))),
    )
    outcome = discovery.discover_all(substrate)
    assert len(outcome.results) == 8
    assert {r.dimension for r in outcome.results} == set(DiscoveryDimension)
    for dimension in DiscoveryDimension:
        assert outcome.result_for(dimension).dimension is dimension
    summary = discovery.dimension_summary(outcome)
    assert set(summary) == {d.value for d in DiscoveryDimension}
    assert all("verdict" in row for row in summary.values())


def test_asking_the_outcome_for_a_dimension_it_does_not_carry_yields_an_empty_result():
    outcome = discovery.DiscoveryOutcome(
        units=(), capabilities=(), reuse=(), edges=(), ownership=(), results=()
    )
    empty = outcome.result_for(DiscoveryDimension.GAP)
    assert empty.dimension is DiscoveryDimension.GAP
    assert empty.findings == ()


# --------------------------------------------------------------------------------------
# recommendation — the advice the engine gives about a substrate that contradicts itself
#
# WHY THIS SECTION EXISTS. The recommendation engine is the product of every dimension
# above: it turns findings into a ranked, evidence-cited work list, and it is the guard
# that answers "should I build this?" before a capability is duplicated. Over THIS
# repository it produces one shape of advice, so the branches that only fire on a
# contradictory substrate — the cycle-breaking repair target, the aggregate remedy, the
# NO_ACTION verdict over a clean repository — were unexecuted, and so was every arm of
# `advise` below REUSE.
# --------------------------------------------------------------------------------------


def _advisor(tmp_path: Path, modules: tuple[ModuleFact, ...], **kwargs):
    substrate = _substrate(tmp_path, modules, **kwargs)
    outcome = discovery.discover_all(substrate)
    return (
        substrate,
        outcome,
        RepositoryRecommendationEngine(
            substrate, outcome, build_graph(outcome.units, outcome.edges)
        ),
    )


def test_a_repository_with_nothing_to_report_is_advised_to_do_nothing(tmp_path):
    """The NO_ACTION arm. An engine that could only ever produce work would have no way to
    say that the repository is consistent, and 'no findings' would read as 'not run'."""
    from platform.repository_intelligence.contracts import RecommendationAction

    substrate = _substrate(tmp_path, (_module("engine.alpha"),))
    empty = discovery.DiscoveryOutcome(
        units=(), capabilities=(), reuse=(), edges=(), ownership=(), results=()
    )
    engine = RepositoryRecommendationEngine(substrate, empty, build_graph(empty.units, empty.edges))
    (only,) = engine.recommend()
    assert only.action is RecommendationAction.NO_ACTION
    assert only.priority == PRIORITY_NONE
    assert engine.summary((only,))["total"] == 1
    assert engine.summary(())["next_action"] is None


def test_the_engine_refuses_anything_that_is_not_a_discovery_outcome(tmp_path):
    from platform.repository_intelligence.errors import RecommendationError

    substrate = _substrate(tmp_path, (_module("engine.alpha"),))
    outcome = discovery.discover_all(substrate)
    graph = build_graph(outcome.units, outcome.edges)
    with pytest.raises(RecommendationError):
        RepositoryRecommendationEngine(substrate, {"not": "an outcome"}, graph)


def test_a_cycle_is_repaired_by_naming_the_heaviest_edge_to_invert(tmp_path):
    """The cheapest single inversion, derived from edge weight, rather than 'break the
    cycle' — advice that names no edge is advice nobody can act on."""
    modules = (
        _module("engine.alpha", imports=("engine.beta",)),
        _module("engine.alpha.two", capability="engine.alpha", imports=("engine.beta",)),
        _module("engine.beta", imports=("engine.alpha",)),
    )
    _substrate_, _outcome, engine = _advisor(tmp_path, modules)
    targets = [r.target for r in engine.recommend() if r.target]
    assert any("engine.alpha -> engine.beta (2 module(s))" in t for t in targets)
    assert any("cyclic component(s)" in t for t in targets)


def test_a_repair_target_falls_back_to_the_detail_the_finding_carries(tmp_path):
    modules = (
        _module("engine.alpha"),
        _module("engine.alpha.cli", capability="engine.alpha"),
    )
    _substrate_, _outcome, engine = _advisor(
        tmp_path,
        modules,
        declarations=Declarations(
            available=True, console_scripts={"ucos-ghost": "engine.ghost.cli:main"}
        ),
    )
    targets = {r.target for r in engine.recommend()}
    assert "engine.ghost.cli:main" in targets


def test_advisory_findings_that_share_a_code_share_one_recommendation(tmp_path):
    modules = (_module("engine.alpha"), _module("engine.beta"), _module("engine.gamma"))
    _substrate_, outcome, engine = _advisor(
        tmp_path, modules, declarations=Declarations(available=True)
    )
    untested = [
        f for result in outcome.results for f in result.findings if f.code == discovery.GAP_UNTESTED
    ]
    assert len(untested) == 3
    aggregated = [r for r in engine.recommend() if r.subject == discovery.GAP_UNTESTED]
    assert len(aggregated) == 1
    assert aggregated[0].rationale.startswith("3 subject(s):")
    assert aggregated[0].target == "3 subjects"
    assert len(aggregated[0].evidence) == 3


def test_proposing_a_capability_that_already_exists_is_answered_with_reuse(tmp_path):
    catalog = (
        {
            "canonical_name": "engine.alpha",
            "category": "engine",
            "reuse": "REUSE",
            "authority": "A",
            "canonical_location": "engine/alpha",
            "replacement_prohibited": True,
        },
    )
    _substrate_, _outcome, engine = _advisor(tmp_path, (_module("engine.alpha"),), catalog=catalog)
    advice = engine.advise("engine.alpha")
    assert advice.action is RecommendationAction.REUSE
    assert "replacement is prohibited" in advice.rationale
    assert advice.target == "engine/alpha"


def test_proposing_a_name_that_exists_in_another_layer_is_answered_with_extend(tmp_path):
    _substrate_, _outcome, engine = _advisor(tmp_path, (_module("engine.alpha"),))
    advice = engine.advise("platform.alpha")
    assert advice.action is RecommendationAction.EXTEND
    assert "engine.alpha" in advice.rationale


def test_a_proposal_whose_vocabulary_an_existing_capability_covers_is_answered_with_compose(
    tmp_path,
):
    module = _module(
        "engine.gapfinder",
        docline="Discover gaps, conflicts and duplicates across the repository.",
        symbols=("discover_gaps", "discover_conflicts", "detect_duplicates"),
    )
    _substrate_, _outcome, engine = _advisor(tmp_path, (module,))
    candidates = engine.reuse_candidates(
        "engine.finder", "discover gaps conflicts and duplicates across the repository"
    )
    assert candidates
    assert candidates[0].capability == "engine.gapfinder"
    assert 0.0 < candidates[0].score <= 1.0
    assert set(candidates[0].to_dict()) == {
        "capability",
        "score",
        "matched_tokens",
        "reuse_directive",
        "replacement_prohibited",
        "location",
    }
    advice = engine.advise(
        "engine.finder", "discover gaps conflicts and duplicates across the repository"
    )
    assert advice.action is RecommendationAction.COMPOSE
    assert advice.target == "engine.gapfinder"


def test_a_proposal_nothing_covers_is_answered_with_create(tmp_path):
    _substrate_, _outcome, engine = _advisor(tmp_path, (_module("engine.alpha", docline="A."),))
    advice = engine.advise("engine.quantum", "orbital mechanics telemetry")
    assert advice.action is RecommendationAction.CREATE


def test_a_proposal_with_no_usable_tokens_yields_no_reuse_candidate(tmp_path):
    _substrate_, _outcome, engine = _advisor(tmp_path, (_module("engine.alpha"),))
    assert engine.reuse_candidates("...", "") == ()


def test_advising_on_an_empty_proposal_is_refused_rather_than_permitted(tmp_path):
    """A permissive CREATE over an empty proposal is exactly the answer that lets a
    duplicate capability through."""
    _substrate_, _outcome, engine = _advisor(tmp_path, (_module("engine.alpha"),))
    for empty in ("", "   "):
        with pytest.raises(RecommendationError):
            engine.advise(empty)


def test_a_capability_with_no_derivable_vocabulary_is_not_a_candidate(tmp_path):
    _substrate_, _outcome, engine = _advisor(
        tmp_path, (_module("engine.a", capability="engine.a", docline="", symbols=()),)
    )
    assert engine.reuse_candidates("engine.other", "a description with words") == ()
