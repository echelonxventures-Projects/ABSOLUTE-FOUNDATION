"""UCOS-UPI-001 Publication Intelligence validation tests.

Proves the three properties the mission demands:
  * everything generated from canonical knowledge — every block resolves to a
    canonical record and carries that record's locator and content hash
  * no duplicated content — a specification cannot hold prose; a reference is never
    repeated inside a document; a reference cited by N publications yields ONE
    citation record
  * unlimited publication formats — a format and a renderer registered at runtime,
    from data alone, generate and validate with no change to any engine

Run: .ec1-venv/bin/python -m pytest intelligence/tests -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from intelligence.kernel.canonical import canonical_json
from intelligence.kernel.config import MemorySink, subsystem_config
from intelligence.kernel.errors import FormatUnknownError, KernelError
from intelligence.publication import GENERATED_BANNER
from intelligence.publication.engine import (
    DOCUMENTS_DIR,
    OUTPUT_DIR,
    PublicationIntelligenceEngine,
)
from intelligence.publication.formats import FormatRegistry
from intelligence.publication.generators import NAMED_DELIVERABLES, PublicationScope
from intelligence.publication.renderers import register_renderer, renderer_ids

REPO = subsystem_config(OUTPUT_DIR).repo_root


def _engine() -> PublicationIntelligenceEngine:
    return PublicationIntelligenceEngine(subsystem_config(OUTPUT_DIR, REPO))


@pytest.fixture(scope="module")
def engine() -> PublicationIntelligenceEngine:
    return _engine()


# -- generation coverage -----------------------------------------------------


def test_every_registered_format_is_generated(engine) -> None:
    publications = engine.publications()
    assert set(publications.format_ids()) == set(engine.formats.format_ids())
    assert len(publications.documents) == len(publications.specs)
    assert len(publications.rendered) == len(publications.specs)


def test_named_deliverables_all_generate(engine) -> None:
    """Every deliverable the mission names resolves to a real, composed document."""
    for name, format_id in sorted(NAMED_DELIVERABLES.items()):
        spec = engine.generator.build(format_id, engine.scope())
        document, body = engine.composer.render(spec)
        assert document.resolved_total() > 0, name
        assert GENERATED_BANNER in body, name
        assert document.title, name


def test_required_sections_are_satisfied(engine) -> None:
    for document in engine.publications().documents:
        descriptor = engine.formats.get(document.format_id)
        for block in document.blocks:
            if block.section_key in descriptor.required and not block.structural:
                assert not block.is_empty, f"{document.format_id}/{block.section_key}"


def test_genres_cover_the_mission_deliverables(engine) -> None:
    genres = engine.formats.genres()
    for genre in ("paper", "journal", "conference", "white-paper", "technical-article",
                  "patent", "standards"):
        assert genre in genres, genre
        assert genres[genre]


# -- generated from canonical knowledge --------------------------------------


def test_every_block_resolves_to_a_canonical_record(engine) -> None:
    for document in engine.publications().documents:
        assert document.unresolved == ()
        for block in document.blocks:
            for resolved in block.resolved:
                assert resolved.text
                assert resolved.source_locator
                assert len(resolved.source_content_sha256) == 64
                assert engine.resolver.exists(resolved.ref)


def test_document_title_comes_from_canonical_knowledge(engine) -> None:
    for document in engine.publications().documents:
        assert document.title_ref.startswith(("cko:", "decision:"))
        assert document.title == engine.resolver.resolve(document.title_ref).text


def test_rendered_documents_declare_they_are_generated(engine) -> None:
    for name, body in engine.publications().rendered.items():
        assert GENERATED_BANNER in body, name


# -- no duplicated content ---------------------------------------------------


def test_specification_carries_no_canonical_prose(engine) -> None:
    for spec in engine.publications().specs:
        serialized = canonical_json(spec.to_dict())
        assert engine.resolver.copied_prose(serialized) == [], spec.format_id


def test_no_reference_repeats_inside_a_document(engine) -> None:
    for spec in engine.publications().specs:
        refs = [ref for section in spec.sections for ref in section.ref_strings]
        assert len(refs) == len(set(refs)), spec.format_id


def test_shared_citation_is_registered_exactly_once(engine) -> None:
    report = engine.registry().shared_citation_report()
    assert report["duplicate_citation_records"] == 0
    assert report["registered_citation_records"] == report["distinct_references"]
    # The whole point: many publications, one record per canonical reference.
    assert report["total_citation_uses"] > report["distinct_references"]
    assert report["reuse_factor"] > 1.0


def test_registry_integrity(engine) -> None:
    integrity = engine.registry().verify()
    assert integrity["chain_intact"] is True
    assert integrity["knowledge_once_holds"] is True
    assert integrity["intact"] is True


# -- unlimited formats -------------------------------------------------------


def test_new_format_registered_from_data_generates_without_code_change(engine) -> None:
    registry = FormatRegistry()
    before = len(registry.format_ids())
    registry.register_format(
        {
            "format_id": "test-newsletter",
            "genre": "newsletter",
            "label": "Engineering Newsletter",
            "sections": ["title-block", "executive-summary", "results", "provenance"],
            "required": ["title-block", "executive-summary", "provenance"],
            "renderer": "markdown",
            "extension": "md",
        }
    )
    assert len(registry.format_ids()) == before + 1
    probe = PublicationIntelligenceEngine(subsystem_config(OUTPUT_DIR, REPO), registry)
    spec = probe.generator.build("test-newsletter", probe.scope())
    document, body = probe.composer.render(spec)
    assert document.resolved_total() > 0
    assert "Engineering Newsletter" in body


def test_new_section_type_registered_from_data(engine) -> None:
    registry = FormatRegistry()
    registry.register_section(
        {
            "key": "test-open-questions",
            "label": "Open Questions",
            "rule": {"source": "claims", "claim_classes": ["negative-result"],
                     "ref": "claim_ref"},
        }
    )
    registry.register_format(
        {
            "format_id": "test-position-paper",
            "genre": "position",
            "label": "Position Paper",
            "sections": ["title-block", "abstract", "test-open-questions", "provenance"],
            "required": ["title-block", "abstract", "provenance"],
        }
    )
    probe = PublicationIntelligenceEngine(subsystem_config(OUTPUT_DIR, REPO), registry)
    spec = probe.generator.build("test-position-paper", probe.scope())
    assert "test-open-questions" in spec.section_keys()
    document, body = probe.composer.render(spec)
    assert "Open Questions" in body


def test_format_declaration_file_extends_the_registry(tmp_path: Path) -> None:
    declaration = {
        "sections": [
            {"key": "test-glossary", "label": "Glossary",
             "rule": {"source": "claims", "ref": "subject_ref", "limit": 5}}
        ],
        "formats": [
            {
                "format_id": "test-field-guide",
                "genre": "guide",
                "label": "Field Guide",
                "sections": ["title-block", "test-glossary", "provenance"],
                "required": ["title-block", "test-glossary", "provenance"],
                "renderer": "plaintext",
                "extension": "txt",
            }
        ],
    }
    path = tmp_path / "publication-formats.json"
    path.write_text(json.dumps(declaration), encoding="utf-8")
    registry = FormatRegistry()
    added = registry.load_file(path)
    assert [d.format_id for d in added] == ["test-field-guide"]
    probe = PublicationIntelligenceEngine(subsystem_config(OUTPUT_DIR, REPO), registry)
    spec = probe.generator.build("test-field-guide", probe.scope())
    _document, body = probe.composer.render(spec)
    assert "GLOSSARY" in body


def test_new_renderer_registered_at_runtime(engine) -> None:
    marker = "TEST-RENDERER-OUTPUT"

    def _render(document, descriptor) -> str:  # noqa: ANN001 - test-local renderer
        return f"{GENERATED_BANNER}\n{marker}\n{descriptor.format_id}\n{document.title}\n"

    register_renderer("test-renderer", _render)
    assert "test-renderer" in renderer_ids()
    registry = FormatRegistry()
    registry.register_format(
        {
            "format_id": "test-custom-syntax",
            "genre": "custom",
            "label": "Custom Syntax Document",
            "sections": ["title-block", "abstract", "provenance"],
            "required": ["title-block", "abstract", "provenance"],
            "renderer": "test-renderer",
            "extension": "custom",
        }
    )
    probe = PublicationIntelligenceEngine(subsystem_config(OUTPUT_DIR, REPO), registry)
    spec = probe.generator.build("test-custom-syntax", probe.scope())
    _document, body = probe.composer.render(spec)
    assert marker in body


def test_openness_probe_is_executed_not_asserted(engine) -> None:
    result = engine.openness_probe()
    assert result["code_changed"] is False
    assert result["generated"] is True
    assert result["rendered"] is True
    assert result["required_sections_satisfied"] is True


def test_unknown_format_is_rejected(engine) -> None:
    with pytest.raises(FormatUnknownError):
        engine.formats.get("no-such-format")


def test_format_referencing_an_undeclared_section_is_rejected() -> None:
    registry = FormatRegistry()
    with pytest.raises(KernelError):
        registry.register_format(
            {
                "format_id": "test-broken",
                "sections": ["title-block", "not-a-declared-section"],
                "required": [],
            }
        )


# -- scopes ------------------------------------------------------------------


def test_publications_can_be_scoped_to_a_research_area(engine) -> None:
    scopes = engine.generator.scopes()
    assert len(scopes) == 1 + len(engine.research.corpus().units)
    area = next(s for s in scopes if s.unit_id)
    spec = engine.generator.build("technical-article", area)
    assert spec.area_label == area.area_label
    assert spec.unit_id == area.unit_id


def test_scope_partitions_the_corpus(engine) -> None:
    corpus = engine.research.corpus()
    whole = PublicationScope.whole_corpus(corpus)
    assert len(whole.claims) == len(corpus.claims)
    per_area = [PublicationScope.for_unit(corpus, u) for u in corpus.units]
    assert sum(len(s.claims) for s in per_area) == len(corpus.claims)


# -- determinism -------------------------------------------------------------


def test_determinism_of_outputs_and_documents(engine) -> None:
    result = engine.verify_determinism()
    assert result["deterministic"] is True
    assert result["output_mismatches"] == []
    assert result["document_mismatches"] == []


def test_rendering_is_byte_identical_across_two_sinks() -> None:
    a, b = MemorySink(), MemorySink()
    _engine().write(a)
    _engine().write(b)
    assert a.store.keys() == b.store.keys()
    for name in a.store:
        assert a.store[name] == b.store[name], f"non-deterministic artifact: {name}"


# -- authority + sealing -----------------------------------------------------


def test_no_duplicate_authority(engine) -> None:
    for payload in engine.outputs().values():
        assert payload["authority"] == "NONE (derived truth)"
        assert payload["programme"] == "UCOS-UPI-001"


def test_outputs_are_sealed(engine) -> None:
    for payload in engine.outputs().values():
        assert json.loads(canonical_json(payload))["content_hash"] == payload["content_hash"]


# -- validation + gate -------------------------------------------------------


def test_validation_certifies_the_publication_set(engine) -> None:
    report = engine.validation()
    assert report.verdict == "CERTIFIED", [c.check_id for c in report.blocking_failures()]
    assert len(report.checks) == 14
    assert report.exit_code == 0


def test_gate_opens_and_reports_a_seal(engine) -> None:
    code, line = engine.gate()
    assert code == 0
    assert "gate=OPEN" in line
    assert "seal=" in line


# -- write scope -------------------------------------------------------------


def test_engine_writes_only_inside_its_own_directory() -> None:
    written = _engine().write()
    for path in written:
        parts = Path(path).parts
        assert "intelligence" in parts
        assert OUTPUT_DIR in parts, f"write escaped {OUTPUT_DIR}: {path}"
    assert any(DOCUMENTS_DIR in Path(p).parts for p in written)
