"""Tests for UKDA canonical-home resolution (:mod:`engine.knowledge.homing`).

The subject of these tests is a *refusal* as much as a capability: the module must
resolve ownership from declarations the repository makes, and must decline to invent one
where no declaration exists (``CEP-002`` 14.2 — *"Ownership SHALL be assigned by governed
determination and SHALL NEVER be implied."*). So the negative cases below are load
bearing, not defensive padding: a change that made an unresolved concept resolve would be
a regression even though it "improves" the numbers.
"""

from __future__ import annotations

import json

import pytest

from engine.knowledge.errors import KnowledgeSourceError, KnowledgeValidationError
from engine.knowledge.homing import (
    REASON_NO_DECLARATION,
    REASON_NO_EVIDENCE,
    REASON_UNSETTLED_CONTEST,
    STANDING_CEILING,
    STANDING_DECLARED,
    STANDING_UNRESOLVED,
    ConceptRecord,
    RegisteredCorpus,
    declared_identity,
    derive_homing,
    families,
    homing_index,
    load_concepts,
    load_registered_corpus,
)

CONSTITUTION = "02-MASTER/THING-001-CONSTITUTION.md"
REALIZATION = "06-IMPLEMENTATION/THING-001-IMPLEMENTATION.md"
REPORT = "12-APPLICATION/APPLICATION-018-MASTER-REGISTRY.md"


def _corpus(*paths: str, categories: dict[str, str] | None = None) -> RegisteredCorpus:
    """A registered corpus containing exactly ``paths``."""
    categories = categories or {}
    return RegisteredCorpus(
        universal_id={p: f"UID-{i:04d}" for i, p in enumerate(paths)},
        category={p: categories.get(p, "GEN") for p in paths},
    )


def _concept(concept_id: str = "THING-001", **kwargs: object) -> ConceptRecord:
    defaults: dict[str, object] = {
        "family": "THING",
        "evidence_files": (),
        "definitional_homes": (),
        "exact_homes": (),
        "zones": ("02-MASTER",),
    }
    defaults.update(kwargs)
    return ConceptRecord(concept_id=concept_id, **defaults)  # type: ignore[arg-type]


def _write(tmp_path, rel: str, text: str) -> None:
    target = tmp_path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------------------
# declared_identity — reading an artifact's statement about itself
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "label",
    ["ARTIFACT ID", "ARTIFACT IDENTIFIER", "ARTIFACT-ID", "artifact id", "**ARTIFACT ID**"],
)
def test_declared_identity_reads_every_label_spelling(label):
    assert declared_identity(f"| Field | Value |\n| {label} | THING-001 |\n") == "THING-001"


def test_declared_identity_strips_emphasis_but_not_the_value():
    assert declared_identity("| ARTIFACT ID | `THING-001` |\n") == "THING-001"


def test_declared_identity_keeps_a_suffixed_identity_distinct():
    """``THING-001-GIG`` declares a *different* identity and must not claim ``THING-001``.

    This is how the repository already separates the Constitutional Implementation
    Orchestration Authority from its Global Implementation Graph Determination.
    """
    assert declared_identity("| ARTIFACT ID | THING-001-GIG |\n") == "THING-001-GIG"


def test_declared_identity_is_absent_when_no_row_is_declared():
    assert declared_identity("# A document with no identity row\n") == ""


def test_declared_identity_ignores_an_identity_row_beyond_the_front_matter():
    """A body mention cannot masquerade as a self-declaration."""
    text = ("x" * 41000) + "\n| ARTIFACT ID | THING-001 |\n"
    assert declared_identity(text) == ""


# --------------------------------------------------------------------------------------
# eligibility — CEP-002 14.1 registration test
# --------------------------------------------------------------------------------------
def test_only_a_registered_artifact_is_eligible():
    corpus = _corpus(CONSTITUTION)
    assert corpus.is_eligible(CONSTITUTION)
    assert not corpus.is_eligible("02-MASTER/UNREGISTERED.md")


def test_operational_memory_is_ineligible_because_it_is_never_registered():
    """``00-MASTER/**`` is Operational Memory (``UCOS-RECON-C1``), excluded by config.

    The exclusion is not re-implemented here — it is inherited by reading the registry,
    so an enumerating programme register simply never appears as a candidate.
    """
    corpus = _corpus(CONSTITUTION)
    assert not corpus.is_eligible("00-MASTER/UAKOS-PHASE-002/04-IMPLEMENTATION-STATUS-REGISTER.md")


def test_a_derived_evidence_path_is_ineligible_even_when_registered():
    corpus = _corpus("02-MASTER/x_evidence/THING-001.md")
    assert not corpus.is_eligible("02-MASTER/x_evidence/THING-001.md")


def test_a_non_markdown_projection_is_ineligible():
    corpus = _corpus("00-BOOK/DATA/artifacts.json")
    assert not corpus.is_eligible("00-BOOK/DATA/artifacts.json")


def test_realization_is_recognised_by_category_or_zone():
    corpus = _corpus(CONSTITUTION, REALIZATION, categories={REALIZATION: "IMP"})
    assert corpus.is_realization(REALIZATION)
    assert not corpus.is_realization(CONSTITUTION)


# --------------------------------------------------------------------------------------
# D1 — the closure engine's definitional-basename measurement, reused
# --------------------------------------------------------------------------------------
def test_a_single_definitional_home_is_the_declared_owner(tmp_path):
    concept = _concept(definitional_homes=(CONSTITUTION,))
    result = derive_homing([concept], _corpus(CONSTITUTION), repo_root=tmp_path)
    (homing,) = result.homings
    assert homing.standing == STANDING_DECLARED
    assert homing.home == CONSTITUTION
    assert homing.rule == "D1-DEFINITIONAL-BASENAME"
    assert result.closed


def test_an_exact_basename_home_outranks_a_prefix_home(tmp_path):
    concept = _concept(
        exact_homes=(CONSTITUTION,),
        definitional_homes=(CONSTITUTION, "02-MASTER/THING-001-SOMETHING-ELSE.md"),
    )
    corpus = _corpus(CONSTITUTION, "02-MASTER/THING-001-SOMETHING-ELSE.md")
    (homing,) = derive_homing([concept], corpus, repo_root=tmp_path).homings
    assert homing.home == CONSTITUTION
    assert not homing.contested


# --------------------------------------------------------------------------------------
# D2 — the artifact declares the concept as its own identity
# --------------------------------------------------------------------------------------
def test_a_declared_artifact_id_resolves_a_concept_with_no_basename_home(tmp_path):
    _write(tmp_path, CONSTITUTION, "| ARTIFACT ID | THING-001 |\n")
    concept = _concept(evidence_files=(CONSTITUTION,))
    (homing,) = derive_homing([concept], _corpus(CONSTITUTION), repo_root=tmp_path).homings
    assert homing.standing == STANDING_DECLARED
    assert homing.home == CONSTITUTION
    assert homing.rule == "D2-DECLARED-ARTIFACT-ID"


def test_a_suffixed_declaration_does_not_claim_the_bare_concept(tmp_path):
    _write(tmp_path, CONSTITUTION, "| ARTIFACT ID | THING-001 |\n")
    _write(tmp_path, "02-MASTER/THING-001-GIG.md", "| ARTIFACT ID | THING-001-GIG |\n")
    concept = _concept(evidence_files=(CONSTITUTION, "02-MASTER/THING-001-GIG.md"))
    corpus = _corpus(CONSTITUTION, "02-MASTER/THING-001-GIG.md")
    (homing,) = derive_homing([concept], corpus, repo_root=tmp_path).homings
    assert homing.home == CONSTITUTION
    assert not homing.contested


# --------------------------------------------------------------------------------------
# contests — CEP-002 14.3 / 14.4
# --------------------------------------------------------------------------------------
def test_a_definitional_claim_outranks_a_realization_claim(tmp_path):
    _write(tmp_path, CONSTITUTION, "| ARTIFACT ID | THING-001 |\n")
    _write(tmp_path, REALIZATION, "| ARTIFACT ID | THING-001 |\n")
    concept = _concept(evidence_files=(CONSTITUTION, REALIZATION))
    corpus = _corpus(CONSTITUTION, REALIZATION, categories={REALIZATION: "IMP"})
    (homing,) = derive_homing([concept], corpus, repo_root=tmp_path).homings
    assert homing.home == CONSTITUTION
    assert homing.superseded == (REALIZATION,)
    assert homing.contested


def test_a_superseded_claim_is_recorded_never_discarded(tmp_path):
    _write(tmp_path, CONSTITUTION, "| ARTIFACT ID | THING-001 |\n")
    _write(tmp_path, REALIZATION, "| ARTIFACT ID | THING-001 |\n")
    concept = _concept(evidence_files=(CONSTITUTION, REALIZATION))
    corpus = _corpus(CONSTITUTION, REALIZATION, categories={REALIZATION: "IMP"})
    result = derive_homing([concept], corpus, repo_root=tmp_path)
    (contest,) = result.contested
    assert REALIZATION in contest.to_dict()["superseded_claims"]


def test_a_contest_among_peers_is_left_unsettled_rather_than_broken_arbitrarily(tmp_path):
    """Two definitional peers must not be separated by a tiebreaker of our own devising."""
    peer = "02-MASTER/THING-001-OTHER-AUTHORITY.md"
    concept = _concept(definitional_homes=(CONSTITUTION, peer))
    result = derive_homing([concept], _corpus(CONSTITUTION, peer), repo_root=tmp_path)
    (homing,) = result.homings
    assert homing.standing == STANDING_UNRESOLVED
    assert homing.reason == REASON_UNSETTLED_CONTEST
    assert set(homing.superseded) == {CONSTITUTION, peer}
    assert not result.closed


def test_an_unsettled_basename_contest_still_defers_to_a_decisive_declaration(tmp_path):
    """A weaker-but-decisive declaration settles what the stronger-but-ambiguous one cannot.

    This is the ``UCOS-COMP-000000`` shape: four artifacts carry the identity in their
    basename, but exactly one declares that identity as its own.
    """
    gig = "02-MASTER/THING-001-GIG.md"
    isr = "02-MASTER/THING-001-ISR.md"
    _write(tmp_path, CONSTITUTION, "| ARTIFACT ID | THING-001 |\n")
    _write(tmp_path, gig, "| ARTIFACT ID | THING-001-GIG |\n")
    _write(tmp_path, isr, "| ARTIFACT ID | THING-001-ISR |\n")
    concept = _concept(
        definitional_homes=(CONSTITUTION, gig, isr),
        evidence_files=(CONSTITUTION, gig, isr),
    )
    (homing,) = derive_homing(
        [concept], _corpus(CONSTITUTION, gig, isr), repo_root=tmp_path
    ).homings
    assert homing.standing == STANDING_DECLARED
    assert homing.home == CONSTITUTION
    assert homing.rule == "D2-DECLARED-ARTIFACT-ID"


# --------------------------------------------------------------------------------------
# the refusal to infer — the substance of the module
# --------------------------------------------------------------------------------------
def test_a_report_that_merely_tabulates_the_concept_is_not_its_owner(tmp_path):
    """The rejected heuristic. A definition-table row is *evidence*, never ownership.

    Measured across the corpus, table/heading/citation matching assigns readiness
    matrices and other units' completion reports as owners. Resolving this concept would
    be implied ownership, which ``CEP-002`` 14.2 forbids.
    """
    _write(tmp_path, REPORT, "| Concept | Status |\n|---|---|\n| THING-001 | READY |\n")
    concept = _concept(evidence_files=(REPORT,))
    (homing,) = derive_homing([concept], _corpus(REPORT), repo_root=tmp_path).homings
    assert homing.standing == STANDING_UNRESOLVED
    assert homing.reason == REASON_NO_DECLARATION


def test_a_heading_mention_is_not_ownership(tmp_path):
    _write(tmp_path, REPORT, "## THING-001 — status summary\n")
    concept = _concept(evidence_files=(REPORT,))
    (homing,) = derive_homing([concept], _corpus(REPORT), repo_root=tmp_path).homings
    assert homing.standing == STANDING_UNRESOLVED


def test_a_concept_with_no_evidence_at_all_is_distinguished_from_one_merely_undeclared():
    """The residue must be triageable, so the two deficits carry different reasons."""
    nothing = _concept("THING-002", evidence_files=(), zones=())
    result = derive_homing([nothing], _corpus(CONSTITUTION))
    (homing,) = result.homings
    assert homing.reason == REASON_NO_EVIDENCE


def test_an_unreadable_candidate_is_not_treated_as_a_declaration(tmp_path):
    """A missing file must fail closed, never resolve. Guards the octal-quoting defect."""
    concept = _concept(evidence_files=(CONSTITUTION,))
    (homing,) = derive_homing([concept], _corpus(CONSTITUTION), repo_root=tmp_path).homings
    assert homing.standing == STANDING_UNRESOLVED


# --------------------------------------------------------------------------------------
# determination aggregate
# --------------------------------------------------------------------------------------
def test_the_determination_reports_its_standing_ceiling(tmp_path):
    """Tier T1 is VACANT, so ``CMG-L-12`` caps the standing at PROVISIONAL."""
    result = derive_homing([_concept(definitional_homes=(CONSTITUTION,))], _corpus(CONSTITUTION))
    assert result.standing_ceiling == STANDING_CEILING
    assert result.to_dict()["standing_ceiling"] == STANDING_CEILING


def test_counts_rules_and_reasons_are_reported_together(tmp_path):
    _write(tmp_path, CONSTITUTION, "| ARTIFACT ID | THING-001 |\n")
    resolved = _concept(evidence_files=(CONSTITUTION,))
    unresolved = _concept("THING-009", evidence_files=(REPORT,))
    _write(tmp_path, REPORT, "| THING-009 | READY |\n")
    result = derive_homing(
        [resolved, unresolved], _corpus(CONSTITUTION, REPORT), repo_root=tmp_path
    )
    assert result.counts() == {
        "concepts": 2,
        "declared": 1,
        "unresolved": 1,
        "contested": 0,
    }
    assert result.by_rule()["D2-DECLARED-ARTIFACT-ID"] == 1
    assert result.unresolved_by_reason()[REASON_NO_DECLARATION] == ["THING-009"]
    assert not result.closed


def test_homing_index_exposes_only_resolved_concepts(tmp_path):
    resolved = _concept(definitional_homes=(CONSTITUTION,))
    unresolved = _concept("THING-009")
    result = derive_homing([resolved, unresolved], _corpus(CONSTITUTION), repo_root=tmp_path)
    assert homing_index(result) == {"THING-001": CONSTITUTION}


def test_families_counts_descend_by_size_then_name():
    a = _concept("A-001", family="ALPHA", definitional_homes=(CONSTITUTION,))
    b = _concept("B-001", family="BETA", definitional_homes=(CONSTITUTION,))
    c = _concept("B-002", family="BETA", definitional_homes=(CONSTITUTION,))
    result = derive_homing([a, b, c], _corpus(CONSTITUTION))
    assert list(families(result.homings)) == ["BETA", "ALPHA"]


def test_output_is_ordered_by_concept_id_so_replay_is_byte_identical(tmp_path):
    concepts = [_concept(cid) for cid in ("THING-003", "THING-001", "THING-002")]
    result = derive_homing(concepts, _corpus(CONSTITUTION), repo_root=tmp_path)
    assert [h.concept_id for h in result.homings] == ["THING-001", "THING-002", "THING-003"]


# --------------------------------------------------------------------------------------
# loaders — fail loudly, never silently empty
# --------------------------------------------------------------------------------------
def test_load_concepts_reads_measured_closure(tmp_path):
    path = tmp_path / "closure.json"
    path.write_text(
        json.dumps(
            {"concepts": [{"id": "THING-001", "family": "THING", "def_homes": [CONSTITUTION]}]}
        ),
        encoding="utf-8",
    )
    (record,) = load_concepts(path)
    assert record.concept_id == "THING-001"
    assert record.definitional_homes == (CONSTITUTION,)


def test_load_concepts_rejects_a_duplicate_concept(tmp_path):
    path = tmp_path / "closure.json"
    path.write_text(json.dumps({"concepts": [{"id": "X-1"}, {"id": "X-1"}]}), encoding="utf-8")
    with pytest.raises(KnowledgeValidationError):
        load_concepts(path)


def test_load_concepts_rejects_an_empty_concept_id(tmp_path):
    path = tmp_path / "closure.json"
    path.write_text(json.dumps({"concepts": [{"id": "  "}]}), encoding="utf-8")
    with pytest.raises(KnowledgeValidationError):
        load_concepts(path)


def test_load_concepts_requires_the_concepts_array(tmp_path):
    path = tmp_path / "closure.json"
    path.write_text(json.dumps({"nope": []}), encoding="utf-8")
    with pytest.raises(KnowledgeSourceError):
        load_concepts(path)


def test_load_concepts_rejects_a_missing_file(tmp_path):
    with pytest.raises(KnowledgeSourceError):
        load_concepts(tmp_path / "absent.json")


def test_load_concepts_rejects_malformed_json(tmp_path):
    path = tmp_path / "closure.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(KnowledgeSourceError):
        load_concepts(path)


def test_load_concepts_rejects_a_non_object_root(tmp_path):
    path = tmp_path / "closure.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(KnowledgeSourceError):
        load_concepts(path)


def test_load_concepts_rejects_a_non_object_record(tmp_path):
    path = tmp_path / "closure.json"
    path.write_text(json.dumps({"concepts": ["nope"]}), encoding="utf-8")
    with pytest.raises(KnowledgeValidationError):
        load_concepts(path)


def test_load_registered_corpus_reads_paths_and_categories(tmp_path):
    path = tmp_path / "artifacts.json"
    path.write_text(
        json.dumps(
            {
                "artifacts": [
                    {"path": CONSTITUTION, "universal_id": "UID-1", "category": "GOV"},
                    {"path": REALIZATION, "universal_id": "UID-2", "category": "IMP"},
                    {"path": "", "universal_id": "UID-3"},
                ]
            }
        ),
        encoding="utf-8",
    )
    corpus = load_registered_corpus(path)
    assert corpus.is_eligible(CONSTITUTION)
    assert corpus.is_realization(REALIZATION)
    assert "" not in corpus.universal_id


def test_load_registered_corpus_refuses_an_empty_registry(tmp_path):
    """An empty registry would make every concept unresolvable for the wrong reason."""
    path = tmp_path / "artifacts.json"
    path.write_text(json.dumps({"artifacts": []}), encoding="utf-8")
    with pytest.raises(KnowledgeSourceError):
        load_registered_corpus(path)


def test_load_registered_corpus_requires_the_artifacts_array(tmp_path):
    path = tmp_path / "artifacts.json"
    path.write_text(json.dumps({"nope": []}), encoding="utf-8")
    with pytest.raises(KnowledgeSourceError):
        load_registered_corpus(path)


def test_load_registered_corpus_rejects_a_non_object_artifact(tmp_path):
    path = tmp_path / "artifacts.json"
    path.write_text(json.dumps({"artifacts": ["nope"]}), encoding="utf-8")
    with pytest.raises(KnowledgeValidationError):
        load_registered_corpus(path)


# --------------------------------------------------------------------------------------
# the live repository — the measurement this module exists to make
# --------------------------------------------------------------------------------------
def test_the_repository_resolves_and_the_residue_is_reported():
    """Against real Repository Truth: some ownership is declared, much is not.

    Asserts the *shape* of the finding rather than a frozen count, so the test tracks the
    repository instead of pinning it: ownership must be resolved for a non-trivial set,
    the residue must be non-empty (RG-B01 is open), and every residue entry must carry a
    reason so it can be triaged.
    """
    concepts = load_concepts()
    corpus = load_registered_corpus()
    result = derive_homing(concepts, corpus)
    assert result.counts()["concepts"] == len(concepts)
    assert result.declared, "no concept resolved — the declaration rules regressed"
    assert result.unresolved, "residue empty — RG-B01 would be closed; update the register"
    assert all(h.reason for h in result.unresolved)
    assert all(h.home and h.rule for h in result.declared)
    assert not result.closed


def test_the_repository_measurement_is_deterministic():
    concepts = load_concepts()
    corpus = load_registered_corpus()
    first = derive_homing(concepts, corpus).to_dict()
    second = derive_homing(concepts, corpus).to_dict()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
