"""Deliverable 4 — classification independent from file extension, and total.

THE HEADLINE TEST is ``test_a_suffixless_executable_is_typed_from_its_bytes``: an artifact with no
extension at all is typed PYTHON, with the suffix classifier never consulted. That is what
"independent from file extension" has to mean if it means anything.

THE SECOND HEADLINE is ``test_content_evidence_beats_a_misleading_suffix``: renaming a file must not
be able to change what it IS while stronger evidence exists.
"""

from __future__ import annotations

import pytest

from engine.omega_infinite import classification as classification_module
from engine.omega_infinite.artifact import (
    CONFIGURATION,
    DATASET,
    DOCUMENT,
    PYTHON,
    UNKNOWN,
    Artifact,
    ArtifactError,
    Location,
)
from engine.omega_infinite.classification import (
    DECLARED_TYPE_KEY,
    RULE_CONTENT_INTERPRETER,
    RULE_CONTENT_STRUCTURE,
    RULE_PROVIDER_DECLARED,
    RULE_SUFFIX,
    RULE_UNCLASSIFIED,
    Classification,
    ClassificationError,
    ClassificationPipeline,
    Classifier,
    InterpreterClassifier,
    ProviderDeclaredClassifier,
    SuffixClassifier,
    TypeVocabulary,
    default_pipeline,
    seed_vocabulary,
    unknown_population,
)


def _artifact(locator: str, **metadata: str) -> Artifact:
    return Artifact(
        identifier=f"probe:{locator}",
        location=Location("probe", locator),
        metadata=metadata,
    )


# ------------------------------------------------------------------------------ the headline pair


def test_a_suffixless_executable_is_typed_from_its_bytes() -> None:
    """DELIVERABLE 4's CENTRAL CLAIM. No extension exists, and the artifact is still PYTHON."""
    pipeline = default_pipeline()
    typed = pipeline.apply(_artifact("bin/ucos-report"), "#!/usr/bin/env python3\nX = 1\n")
    assert typed.artifact_type is PYTHON
    assert typed.classification_rule == RULE_CONTENT_INTERPRETER


def test_content_evidence_beats_a_misleading_suffix() -> None:
    """A ``.md`` file whose bytes are a python script is PYTHON. Renaming cannot change what it is
    while stronger evidence exists — which is what makes classification suffix-INDEPENDENT."""
    typed = default_pipeline().apply(_artifact("docs/thing.md"), "#!/usr/bin/python3.12\nX = 1\n")
    assert typed.artifact_type is PYTHON
    assert typed.classification_rule == RULE_CONTENT_INTERPRETER


# ---------------------------------------------------------------------------------- precedence


def test_a_provider_declaration_outranks_every_inference() -> None:
    """The system of record already knew. Nothing here should second-guess it."""
    typed = default_pipeline().apply(
        _artifact("docs/guide.md", **{DECLARED_TYPE_KEY: "DATASET"}),
        "# Guide\n",
    )
    assert typed.artifact_type is DATASET
    assert typed.classification_rule == RULE_PROVIDER_DECLARED


def test_the_suffix_is_consulted_only_when_the_bytes_said_nothing() -> None:
    typed = default_pipeline().apply(_artifact("config/settings.toml"), "key = 'value'\n")
    assert typed.artifact_type is CONFIGURATION
    assert typed.classification_rule == RULE_SUFFIX


def test_the_declared_pipeline_order_is_the_architecture() -> None:
    """Reversing these four would restore extension-primary classification exactly."""
    assert default_pipeline().identifiers() == (
        "provider-declared",
        "content-interpreter",
        "content-structure",
        "suffix",
    )


# --------------------------------------------------------------------------------- content probes


def test_structured_data_is_recognised_by_shape_not_by_name() -> None:
    typed = default_pipeline().apply(_artifact("evidence/blob"), '{"rows": [1, 2]}')
    assert typed.artifact_type is DATASET
    assert typed.classification_rule == RULE_CONTENT_STRUCTURE


def test_prose_is_recognised_by_a_markup_heading() -> None:
    typed = default_pipeline().apply(_artifact("notes/entry"), "# Heading\n\nbody\n")
    assert typed.artifact_type is DOCUMENT
    assert typed.classification_rule == RULE_CONTENT_STRUCTURE


def test_the_probes_abstain_rather_than_guess() -> None:
    assert classification_module.structured_data_probe("plain text") is None
    assert classification_module.prose_probe("plain text") is None


def test_content_reading_is_bounded() -> None:
    """A bound belongs where it is declared, not with the caller — the MARKER_WINDOW lesson."""
    beyond = "x" * classification_module.CONTENT_WINDOW + "\n#!/usr/bin/env python3\n"
    typed = default_pipeline().apply(_artifact("bin/thing"), beyond)
    assert typed.artifact_type is UNKNOWN


# ---------------------------------------------------------------------------------- totality


def test_an_artifact_nothing_recognises_becomes_a_named_unknown() -> None:
    """TOTAL BY CONSTRUCTION. UNKNOWN with a RULE — a countable finding, never a silence."""
    typed = default_pipeline().apply(_artifact("bin/opaque"), "\x00binary payload\n")
    assert typed.artifact_type is UNKNOWN
    assert typed.classification_rule == RULE_UNCLASSIFIED


def test_classification_never_returns_none_even_with_no_content() -> None:
    answer = default_pipeline().classify(_artifact("thing/with-no-suffix"), None)
    assert answer.artifact_type is UNKNOWN
    assert answer.rule == RULE_UNCLASSIFIED


def test_the_unknown_population_is_reportable() -> None:
    """The number Phase 2 is measured against has to be computable in Phase 1."""
    typed = default_pipeline().apply_all(
        (_artifact("a.py"), _artifact("b/opaque"), _artifact("c.md"))
    )
    assert unknown_population(typed) == (typed[1],)


def test_apply_all_injects_the_reader_so_a_remote_provider_may_decline_to_fetch() -> None:
    """A pipeline that read content itself could not run against a space whose bytes cost a network
    call each, so WHO reads — and whether reading happens at all — is the caller's decision."""
    reads: list[str] = []

    def read(artifact: Artifact) -> str:
        reads.append(artifact.location.locator)
        return "#!/usr/bin/env python3\n"

    typed = default_pipeline().apply_all((_artifact("bin/one"), _artifact("bin/two")), read)
    assert reads == ["bin/one", "bin/two"]
    assert {a.artifact_type for a in typed} == {PYTHON}

    # and with no reader, nothing is read and the suffix still decides
    untouched = default_pipeline().apply_all((_artifact("docs/x.md"),))
    assert untouched[0].artifact_type is DOCUMENT


# -------------------------------------------------------------------------------- the vocabulary


def test_the_seed_vocabulary_is_deliberately_minimal() -> None:
    """A hundred-entry table would be the 'giant rule table' the directive forbids."""
    seeded = seed_vocabulary()
    assert len(seeded.suffixes) <= 12
    assert len(seeded.interpreters) <= 4


def test_the_longest_matching_suffix_wins() -> None:
    vocabulary = TypeVocabulary(suffixes={".gz": DATASET, ".tar.gz": CONFIGURATION})
    assert vocabulary.for_suffix("bundle.tar.gz") is CONFIGURATION
    assert vocabulary.for_suffix("bundle.gz") is DATASET
    assert vocabulary.for_suffix("bundle.zip") is None


def test_suffix_matching_is_case_insensitive() -> None:
    assert seed_vocabulary().for_suffix("READ.MD") is DOCUMENT


def test_an_interpreter_matches_despite_a_version_suffix() -> None:
    vocabulary = seed_vocabulary()
    assert vocabulary.for_interpreter("/usr/bin/python3.12") is PYTHON
    assert vocabulary.for_interpreter("python") is PYTHON
    assert vocabulary.for_interpreter("/bin/sh") is None


def test_the_vocabulary_extends_without_editing_the_module() -> None:
    """Adding a language is a registration. NO hard-coded language list exists to edit."""
    rust = classification_module.ArtifactType("RUST", "Rust source.")
    extended = seed_vocabulary().with_suffix(".rs", rust).with_interpreter("cargo", rust)
    assert extended.for_suffix("src/main.rs") is rust
    assert extended.for_interpreter("cargo") is rust
    # the seed is untouched — the vocabulary is immutable
    assert seed_vocabulary().for_suffix("src/main.rs") is None


def test_a_caller_may_replace_the_vocabulary_wholesale() -> None:
    only_rust = TypeVocabulary(suffixes={".rs": classification_module.ArtifactType("RUST", "")})
    pipeline = default_pipeline(only_rust)
    assert pipeline.apply(_artifact("a.py")).artifact_type is UNKNOWN
    assert pipeline.apply(_artifact("a.rs")).artifact_type.name == "RUST"


# --------------------------------------------------------------------------- individual classifiers


def test_a_classification_must_name_its_rule() -> None:
    with pytest.raises(ClassificationError, match="must name the rule"):
        Classification(PYTHON, "  ")


def test_each_classifier_abstains_when_it_has_no_evidence() -> None:
    """ABSTAINING IS A FIRST-CLASS ANSWER. A classifier that guessed would prevent every weaker
    classifier from ever being consulted."""
    plain = _artifact("thing/no-suffix")
    assert ProviderDeclaredClassifier(lambda n: PYTHON).classify(plain, None) is None
    assert InterpreterClassifier(seed_vocabulary()).classify(plain, "no shebang") is None
    assert InterpreterClassifier(seed_vocabulary()).classify(plain, None) is None
    assert InterpreterClassifier(seed_vocabulary()).classify(plain, "#!/bin/sh\n") is None
    assert SuffixClassifier(seed_vocabulary()).classify(plain, None) is None


def test_a_provider_declared_type_the_registry_does_not_know_is_a_fault() -> None:
    """A provider inventing types by spelling is how a vocabulary stops being one."""
    pipeline = default_pipeline()
    with pytest.raises(ArtifactError, match="not a declared artifact type"):
        pipeline.classify(_artifact("a", **{DECLARED_TYPE_KEY: "NOT_A_REAL_TYPE"}))


def test_the_classifier_protocol_is_satisfied_by_the_concrete_classifiers() -> None:
    for classifier in default_pipeline().classifiers:
        assert isinstance(classifier, Classifier)


def test_a_third_party_classifier_needs_no_dependency_on_this_module() -> None:
    """The Protocol is structural, so a caller may inject a classifier of its own."""

    class Always:
        def identifier(self) -> str:
            return "always-dataset"

        def classify(self, artifact: Artifact, content: str | None) -> Classification:
            del artifact, content
            return Classification(DATASET, "CUSTOM-01")

    pipeline = ClassificationPipeline((Always(),))
    typed = pipeline.apply(_artifact("anything.py"))
    assert typed.artifact_type is DATASET
    assert typed.classification_rule == "CUSTOM-01"
