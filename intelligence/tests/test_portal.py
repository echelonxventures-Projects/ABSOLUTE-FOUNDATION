"""EPIC-DOC-003 (Terminal T4) — Repository Intelligence Portal tests.

Proves the mission's constitutional requirements for the portal:
  * everything generated — no page is hand-authored (every page carries the banner)
  * everything linked   — every page carries a nav bar linking every sibling page
  * everything traceable — every page cites its evidence fingerprint + derivation
  * everything searchable — a working deterministic inverted index exists
  * 100% deterministic  — identical repository state ⇒ byte-identical pages
  * reuse, not rebuild  — the T3 acceptance engine is reused verbatim over a subject
                          assimilated from the RIE model (nothing re-derived)

Run: .ec1-venv/bin/python -m pytest intelligence/tests -q
"""

from __future__ import annotations

import pytest

from intelligence.portal import (
    ACCEPTANCE_PORTAL,
    CAPABILITY_PORTAL,
    CERTIFICATION_PORTAL,
    COVERAGE_PORTAL,
    DEPENDENCY_PORTAL,
    DRIFT_PORTAL,
    EVIDENCE_PORTAL,
    EXECUTION_PORTAL,
    FREEZE_PORTAL,
    FRONTIER_PORTAL,
    HEALTH_PORTAL,
    PAGES,
    PORTAL_INDEX,
    READINESS_PORTAL,
    SEARCH_PORTAL,
    VALIDATION_PORTAL,
    WORKSTREAMS_PORTAL,
    RepositoryIntelligencePortal,
    build_acceptance_facts,
)
from intelligence.rie.config import RepoConfig
from intelligence.rie.engine import RepositoryIntelligenceEngine

REPO = RepoConfig.create().repo_root

_ALL_PAGES = {
    PORTAL_INDEX,
    HEALTH_PORTAL,
    READINESS_PORTAL,
    EXECUTION_PORTAL,
    ACCEPTANCE_PORTAL,
    VALIDATION_PORTAL,
    CERTIFICATION_PORTAL,
    FRONTIER_PORTAL,
    WORKSTREAMS_PORTAL,
    DRIFT_PORTAL,
    COVERAGE_PORTAL,
    FREEZE_PORTAL,
    CAPABILITY_PORTAL,
    DEPENDENCY_PORTAL,
    SEARCH_PORTAL,
    EVIDENCE_PORTAL,
}


def _portal() -> RepositoryIntelligencePortal:
    return RepositoryIntelligencePortal(RepositoryIntelligenceEngine(RepoConfig.create(REPO)))


@pytest.fixture(scope="module")
def portal() -> RepositoryIntelligencePortal:
    return _portal()


@pytest.fixture(scope="module")
def rendered(portal: RepositoryIntelligencePortal) -> dict[str, str]:
    return portal.render_all()


# -- structure ----------------------------------------------------------------


def test_render_all_keys(rendered: dict[str, str]) -> None:
    assert set(rendered) == _ALL_PAGES
    # 15 objective/supporting pages plus the navigable home.
    assert len(PAGES) == 15
    assert len(rendered) == 16


def test_page_titles_are_unique() -> None:
    titles = [title for _, title, _ in PAGES]
    assert len(titles) == len(set(titles))


def test_every_page_is_generated_navigable_and_traceable(rendered: dict[str, str]) -> None:
    for filename, content in rendered.items():
        # generated banner (never hand-authored) + the epic marker.
        assert "GENERATED REPOSITORY INTELLIGENCE PORTAL" in content
        assert "EPIC-DOC-003" in content
        # every page carries a navigation bar linking every sibling page.
        assert "**Intelligence:**" in content
        for other, title, _ in PAGES:
            if other == filename:
                assert f"**{title}**" in content
            else:
                assert f"[{title}]({other})" in content
        # non-home pages link home; home links out to every page.
        if filename != PORTAL_INDEX:
            assert f"[Home]({PORTAL_INDEX})" in content
        else:
            assert "**Home**" in content
        # traceable: every page carries the evidence fingerprint + non-authority.
        assert "Evidence:" in content
        assert "content-hash" in content
        assert "NONE (derived truth)" in content
        # linked to the sibling constitutional knowledge portal (EPIC-DOC-002).
        assert "Constitutional Knowledge Portal" in content


def test_index_lists_every_page(portal: RepositoryIntelligencePortal) -> None:
    index = portal.index()
    for filename, title, purpose in PAGES:
        assert f"[{title}]({filename})" in index
        assert purpose in index
    assert "Repository posture" in index


# -- objective coverage (the eleven mission objectives) -----------------------


def test_pages_project_every_mission_objective(rendered: dict[str, str]) -> None:
    # Repository Health
    assert "Overall" in rendered[HEALTH_PORTAL]
    assert "Knowledge-graph edges" in rendered[HEALTH_PORTAL]
    # Repository Readiness (T3 + AEOS)
    assert "freeze readiness" in rendered[READINESS_PORTAL].lower()
    assert "AEOS foundation readiness" in rendered[READINESS_PORTAL]
    # Execution Status
    assert "Per-dimension execution status" in rendered[EXECUTION_PORTAL]
    assert "Digital-twin projection" in rendered[EXECUTION_PORTAL]
    # Acceptance Status
    assert "Gate findings" in rendered[ACCEPTANCE_PORTAL]
    assert "UCOS-ACCEPT-EPIC-DOC-003" in rendered[ACCEPTANCE_PORTAL]
    # Validation Status
    assert "Unit validation" in rendered[VALIDATION_PORTAL]
    # Certification Status
    assert "Digital-twin verdict" in rendered[CERTIFICATION_PORTAL]
    # Implementation Frontier
    assert "Next executable capability" in rendered[FRONTIER_PORTAL]
    assert "Critical path" in rendered[FRONTIER_PORTAL]
    # Active Workstreams
    assert "Single active frontier" in rendered[WORKSTREAMS_PORTAL]
    # Repository Drift
    assert "Duplicate findings" in rendered[DRIFT_PORTAL]
    assert "Stale evidence" in rendered[DRIFT_PORTAL]
    # Coverage
    assert "Line coverage" in rendered[COVERAGE_PORTAL]
    assert "Per-root census" in rendered[COVERAGE_PORTAL]
    # Architecture Freeze Readiness
    assert "Freeze verdict" in rendered[FREEZE_PORTAL]
    assert "Known spine gaps" in rendered[FREEZE_PORTAL]


def test_supporting_pages_project_their_source(rendered: dict[str, str]) -> None:
    assert "reuse policy" in rendered[CAPABILITY_PORTAL]
    assert "```mermaid" in rendered[DEPENDENCY_PORTAL]
    assert "Layered architecture" in rendered[DEPENDENCY_PORTAL]
    assert "Inverted index" in rendered[SEARCH_PORTAL]
    assert "Evidence files" in rendered[EVIDENCE_PORTAL]


# -- reuse of the T3 acceptance engine (not rebuilt) --------------------------


def test_acceptance_is_reused_verbatim(portal: RepositoryIntelligencePortal) -> None:
    decision = portal.decision
    readiness = portal.acceptance_readiness
    # The decision is the genuine T3 fail-closed decision over 20 built-in gates.
    assert decision.counts()["total"] == 20
    assert decision.record.verify_integrity() is True
    # Readiness is derived from the same decision (single source of the verdict).
    assert readiness.gates_total == decision.counts()["total"]
    assert readiness.accepted == decision.accepted
    # The freeze verdict is fail-closed: ready iff accepted.
    assert (readiness.verdict == "READY") == decision.accepted


def test_acceptance_facts_are_derived_and_deterministic() -> None:
    engine = RepositoryIntelligenceEngine(RepoConfig.create(REPO))
    outputs = engine.outputs()
    model = {**outputs["UCOS-RIE-MODEL.json"], "_drift": outputs["UCOS-RIE-SNAPSHOT.json"]["drift"]}
    a = build_acceptance_facts(model, "REPO")
    b = build_acceptance_facts(model, "REPO")
    assert a == b
    # Derived, not hand-listed: units come from the discovered capabilities.
    assert a["repository_id"] == "REPO"
    assert a["epic_id"] == "EPIC-DOC-003"
    assert len(a["units"]) > 0
    # Freeze blockers surface the AEOS spine gaps (derived from the model).
    assert any("not implemented" in b for b in a["freeze_blockers"])


# -- searchable ---------------------------------------------------------------


def test_search_index_maps_terms_back_to_documents(portal: RepositoryIntelligencePortal) -> None:
    search = portal.search()
    assert "Inverted index" in search
    # A capability id is a document; a gate id is a document; both are indexed.
    assert "gate:" in search
    # An engine capability term resolves in the index.
    assert "engine" in search


# -- determinism --------------------------------------------------------------


def test_render_is_pure(portal: RepositoryIntelligencePortal) -> None:
    assert portal.render_all() == portal.render_all()


def test_two_portals_render_byte_identical() -> None:
    first = _portal().render_all()
    second = _portal().render_all()
    assert first.keys() == second.keys()
    for filename in first:
        assert first[filename] == second[filename], f"non-deterministic page: {filename}"


def test_write_all_is_deterministic(tmp_path) -> None:
    portal = _portal()
    a = portal.write_all(tmp_path / "a")
    portal.write_all(tmp_path / "b")
    assert len(a) == 16
    for filename in _ALL_PAGES:
        assert (tmp_path / "a" / filename).read_text() == (tmp_path / "b" / filename).read_text()
