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
from dataclasses import replace
from pathlib import Path

import pytest

from intelligence.kernel.canonical import canonical_json
from intelligence.kernel.config import MemorySink, subsystem_config
from intelligence.kernel.errors import FormatUnknownError, KernelError
from intelligence.publication import GENERATED_BANNER
from intelligence.publication.__main__ import main as cli_main
from intelligence.publication.engine import (
    DOCUMENTS_DIR,
    OUTPUT_DIR,
    PublicationIntelligenceEngine,
)
from intelligence.publication.formats import FormatRegistry
from intelligence.publication.generators import NAMED_DELIVERABLES, PublicationScope
from intelligence.publication.renderers import (
    get_renderer,
    register_renderer,
    render_markdown,
    renderer_ids,
)

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
    for genre in (
        "paper",
        "journal",
        "conference",
        "white-paper",
        "technical-article",
        "patent",
        "standards",
    ):
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
            "rule": {"source": "claims", "claim_classes": ["negative-result"], "ref": "claim_ref"},
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
            {
                "key": "test-glossary",
                "label": "Glossary",
                "rule": {"source": "claims", "ref": "subject_ref", "limit": 5},
            }
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


# --------------------------------------------------------------------------- the CLI
#
# ``python -m intelligence.publication`` was 73 statements measured at 0.0%. The engine below it
# had 349 lines of tests and the surface an operator actually types had none, so every exit code
# in the module docstring was a claim about untested code. Each test here calls ``main`` with the
# argv an operator would type and asserts the LITERAL exit code, because a gate's exit code is
# its whole interface to the shell and an attribute reference proves nothing about its value.


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = cli_main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_the_cli_prints_the_open_format_catalog(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "formats")
    assert code == 0
    catalog = json.loads(out)
    assert catalog, "an empty catalog would mean the format space is closed, not open"


def test_the_cli_renders_a_named_deliverable(capsys: pytest.CaptureFixture[str]) -> None:
    """One render through the CLI; the other names are checked against the registry below,
    because building the engine once per deliverable buys the same assurance six times."""
    code, out, _ = _run(capsys, "generate", sorted(NAMED_DELIVERABLES)[0])
    assert code == 0
    assert out.strip(), "the deliverable rendered an empty document"
    assert out.endswith("\n"), "a rendered document must end in a newline"


def test_every_named_deliverable_resolves_to_a_registered_format() -> None:
    registry = FormatRegistry()
    for name, format_id in sorted(NAMED_DELIVERABLES.items()):
        assert registry.has(format_id), f"{name} names {format_id}, which no format declares"


def test_the_cli_accepts_a_format_id_as_well_as_a_deliverable_name(
    capsys: pytest.CaptureFixture[str],
) -> None:
    format_id = NAMED_DELIVERABLES[sorted(NAMED_DELIVERABLES)[0]]
    code, out, _ = _run(capsys, "generate", format_id)
    assert code == 0 and out.strip()


def test_the_cli_emits_the_set_registry_snapshot_and_validation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for command in ("set", "registry", "snapshot"):
        code, out, _ = _run(capsys, command)
        assert code == 0, command
        assert json.loads(out), f"{command} emitted an empty document"
    code, out, _ = _run(capsys, "validate")
    report = json.loads(out)
    assert (code == 0) is (report["gate"] == "OPEN"), (
        "the CLI must return the report's own verdict; deciding it separately would let the "
        "shell and the document disagree about the same run"
    )
    assert code in (0, 1)


def test_the_cli_gate_agrees_with_the_engine_gate(capsys: pytest.CaptureFixture[str]) -> None:
    expected, line = _engine().gate()
    code, out, _ = _run(capsys, "gate")
    assert code == expected
    assert code in (0, 1), "the gate is two-valued unless it aborts, and an abort is exit 2"
    assert out.strip() == line.strip()


def test_the_cli_verify_proves_deterministic_regeneration(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = _run(capsys, "verify")
    assert code == 0
    assert json.loads(out)["deterministic"] is True


def test_the_cli_build_reports_what_it_wrote(capsys: pytest.CaptureFixture[str]) -> None:
    """Regeneration is idempotent by construction — ``verify`` above proves it — so this run
    rewrites byte-identical files rather than mutating the tree."""
    code, out, _ = _run(capsys, "build")
    assert code == 0
    assert "UPI: regenerated" in out
    assert out.count("  - ") >= 1, "a build that names no artifact reports nothing"


def test_a_broken_formats_file_is_a_fail_closed_abort_and_not_a_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A KernelError is exit 2: the run reached no verdict, which is not the same as CLOSED."""
    declaration = tmp_path / "formats.json"
    declaration.write_text('["not-an-object"]', encoding="utf-8")
    code, _out, err = _run(capsys, "--formats-file", str(declaration), "formats")
    assert code == 2
    assert "FAIL-CLOSED ABORT" in err


def test_an_extra_format_registered_from_a_file_reaches_the_catalog(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    declaration = tmp_path / "formats.json"
    declaration.write_text(json.dumps({"sections": [], "formats": []}), encoding="utf-8")
    code, out, _ = _run(capsys, "--formats-file", str(declaration), "formats")
    assert code == 0 and json.loads(out)


def test_an_unknown_format_is_refused_rather_than_substituted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``FormatUnknownError`` is a ``KernelError``, so the CLI converts it into exit 2 — a run
    that reached no verdict — rather than letting it look like a closed gate."""
    code, _out, err = _run(capsys, "generate", "no-such-format")
    assert code == 2
    assert "FAIL-CLOSED ABORT" in err
    assert "no-such-format" in err, "a refusal that does not name its subject cannot be acted on"


def test_a_subcommand_is_required() -> None:
    with pytest.raises(SystemExit) as raised:
        cli_main([])
    assert raised.value.code == 2


# -- the renderers over a document with nothing to render -------------------------------
#
# WHY THIS SECTION EXISTS. Every renderer is exercised over THIS repository's publications,
# which have citations, resolved blocks and no unresolved references. The branches that
# only fire when a document is EMPTY or INCOMPLETE were therefore unexecuted in all five
# syntaxes: the "no citations" note, the unresolved-reference list, the empty-block skip,
# and the `return []` a structural renderer gives for a section it does not own. Those are
# the branches a publication takes on the day a reference stops resolving, which is exactly
# when the output has to stay readable and honest.


def _empty_document(**overrides):
    from intelligence.publication.model import ComposedBlock, ComposedDocument

    fields = {
        "publication_id": "PUB-EMPTY",
        "format_id": "fmt",
        "genre": "genre",
        "format_label": "Format",
        "area_label": "Area",
        "title": "An Empty Publication",
        "title_ref": "cko:UCOS-X#title",
        "blocks": (
            ComposedBlock("title-block", "Title", 0, True, ()),
            ComposedBlock("references", "References", 1, True, ()),
            ComposedBlock("provenance", "Provenance", 2, True, ()),
            ComposedBlock("body", "Body", 3, False, ()),
            ComposedBlock("nobody-owns-this", "Foreign", 4, True, ()),
        ),
        "citations": (),
        "renderer": "markdown",
        "extension": "md",
        "citation_style": "numeric",
        "unresolved": ({"ref": "cko:GONE#statement", "reason": "not found"},),
    }
    fields.update(overrides)
    return ComposedDocument(**fields)


def _descriptor(engine):
    return engine.formats.get(engine.formats.format_ids()[0])


@pytest.mark.parametrize("renderer_id", ["markdown", "latex", "html", "plaintext", "json"])
def test_every_renderer_survives_a_document_with_nothing_resolved(engine, renderer_id) -> None:
    body = get_renderer(renderer_id)(_empty_document(), _descriptor(engine))
    assert isinstance(body, str)
    assert body.strip()


def test_the_markdown_renderer_says_there_are_no_citations_rather_than_printing_a_header(
    engine,
) -> None:
    body = render_markdown(_empty_document(), _descriptor(engine))
    assert "_no citations_" in body
    assert "| # | Canonical reference |" not in body


def test_the_markdown_renderer_lists_every_unresolved_reference_by_name(engine) -> None:
    """An unresolved reference is a fact about the publication, and hiding it would make an
    incomplete document indistinguishable from a complete one."""
    body = render_markdown(_empty_document(), _descriptor(engine))
    assert "### Unresolved references" in body
    assert "cko:GONE#statement" in body
    assert "not found" in body


def test_a_structural_section_no_renderer_owns_contributes_nothing(engine) -> None:
    from intelligence.publication.renderers import render_html, render_latex, render_markdown

    document = _empty_document()
    descriptor = _descriptor(engine)
    for body in (
        render_markdown(document, descriptor),
        render_latex(document, descriptor),
        render_html(document, descriptor),
    ):
        assert "Foreign" not in body


def test_a_descriptor_that_carries_notes_renders_them_in_every_syntax(engine) -> None:
    from intelligence.publication.renderers import render_html, render_latex

    descriptor = _descriptor(engine)
    noted = replace(descriptor, notes="A note the format declares about itself.")
    assert "A note the format declares" in render_latex(_empty_document(), noted)
    assert "A note the format declares" in render_html(_empty_document(), noted)


def test_a_renderer_must_have_an_id_and_be_callable() -> None:
    from intelligence.publication.renderers import register_renderer

    with pytest.raises(KernelError):
        register_renderer("", lambda document, descriptor: "")
    with pytest.raises(KernelError):
        register_renderer("not-callable", "this is not a renderer")


def test_an_unregistered_renderer_is_refused_and_names_what_is_registered() -> None:
    with pytest.raises(KernelError) as excinfo:
        get_renderer("no-such-renderer")
    assert excinfo.value.context["registered"] == renderer_ids()


# -- the named deliverables, called by the names the mission gives them -----------------
#
# WHY THIS SECTION EXISTS. `NAMED_DELIVERABLES` is exercised through the generic
# `build(format_id, ...)` path, which is the right thing to test — but it leaves the seven
# explicitly-named methods, the genre selector and the deliverable descriptor lookup as
# published API nothing calls. An API published and never invoked is an API whose next
# rename breaks a caller nobody warned.


def test_every_named_deliverable_method_builds_the_format_it_names(engine) -> None:
    from intelligence.publication.generators import (
        NAMED_DELIVERABLES,
        descriptor_for_deliverable,
    )

    generator = engine.generator
    by_method = {
        "paper": generator.generate_paper,
        "journal": generator.generate_journal_article,
        "conference-paper": generator.generate_conference_paper,
        "white-paper": generator.generate_white_paper,
        "technical-article": generator.generate_technical_article,
        "patent-draft": generator.generate_patent_draft,
        "standards-proposal": generator.generate_standards_proposal,
    }
    assert set(by_method) == set(NAMED_DELIVERABLES)
    for name, build in sorted(by_method.items()):
        spec = build(engine.scope())
        assert spec.format_id == NAMED_DELIVERABLES[name]
        assert descriptor_for_deliverable(name, engine.formats).format_id == spec.format_id


def test_a_deliverable_may_also_be_addressed_by_its_format_id(engine) -> None:
    from intelligence.publication.generators import descriptor_for_deliverable

    assert descriptor_for_deliverable("research-paper", engine.formats).format_id == (
        "research-paper"
    )


def test_building_by_genre_builds_exactly_that_genre(engine) -> None:
    genre = engine.formats.get("research-paper").genre
    specs = engine.generator.build_by_genre(genre, engine.scope())
    expected = {f.format_id for f in engine.formats.by_genre(genre)}
    assert {s.format_id for s in specs} == expected
    assert expected


def test_a_title_falls_back_through_every_claim_before_reporting_none(engine) -> None:
    """The preferred claim classes are an ORDER, not a requirement: a corpus that declares
    none of them still gets a title from whatever claim it does have, and a corpus with no
    resolvable claim at all reports the absence rather than inventing one."""
    generator = engine.generator
    scope = engine.scope()
    assert generator._title_ref(scope)

    preferred = ("foundational-claim", "determination", "specification-claim")
    others = tuple(c for c in scope.claims if c.claim_class not in preferred)
    if others:
        assert generator._title_ref(replace(scope, claims=others))

    assert generator._title_ref(replace(scope, claims=())) == ""
