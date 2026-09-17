"""UCOS-CAA-001 — the law side of constitutional authority alignment.

What these tests pin is not "the module runs". It is that the module cannot quietly
become the thing it forbids:

* the roles and rules it declares resolve into articles the root law actually holds,
  so an alignment that cited a non-existent article would fail rather than certify;
* the identity derivation is total, pure and INJECTIVE, which is the whole claim that
  the ledger is a persistence binding of Article 5 rather than a rival to it;
* :func:`verify_binding` really rejects the ways a DATA register could drift away from
  the law it says it derives under — each negative below is a mutation of the real
  binding, because a rejection test written against a hand-made stub proves only that
  the stub is wrong.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from engine.uckp.alignment import (
    ALIGNMENT_BINDING_PATH,
    ALIGNMENT_ID,
    ALIGNMENT_INSTRUMENT,
    ALIGNMENT_RULES,
    AUTHORITY_ROLES,
    AlignmentError,
    alignment_object,
    alignment_objects,
    alignment_urn,
    derivation_is_injective,
    repository_local_urn,
    require_aligned,
    ucko_objects,
    verify_binding,
)
from engine.uckp.constitution import root_law_urn
from engine.uckp.identity import UCKO_URN_PREFIX
from engine.uckp.law import ROOT_LAW

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def binding() -> dict:
    return json.loads((REPO / ALIGNMENT_BINDING_PATH).read_text(encoding="utf-8"))


# --- the declared law ---------------------------------------------------------------


def test_exactly_one_role_may_hold_authority() -> None:
    """Article 1 admits one root. Two supreme roles would be two."""
    supreme = [role for role in AUTHORITY_ROLES if role.may_hold_authority]
    assert [role.role_id for role in supreme] == ["SUPREME"]
    assert supreme[0].cardinality == "EXACTLY_ONE"


def test_every_role_and_rule_cites_an_article_the_law_holds() -> None:
    """A rule enforcing an article nobody declared enforces nothing."""
    articles = set(ROOT_LAW.article_ids())
    for role in AUTHORITY_ROLES:
        assert role.article in articles, role.role_id
    for rule in ALIGNMENT_RULES:
        assert rule.article in articles, rule.rule_id
        assert set(rule.also) <= articles, rule.rule_id


def test_alignment_adds_no_article_or_invariant_to_the_root_law() -> None:
    """Extension is by registration (Article 17), never by amending the law."""
    assert len(ROOT_LAW.articles) == 20
    assert len(ROOT_LAW.invariants) == 17
    assert not {rule.rule_id for rule in ALIGNMENT_RULES} & set(ROOT_LAW.invariant_ids())


def test_rule_ids_are_unique() -> None:
    ids = [rule.rule_id for rule in ALIGNMENT_RULES]
    assert len(ids) == len(set(ids))


# --- identity: one authority, two planes --------------------------------------------


def test_the_derivation_carries_the_identifier_through_verbatim() -> None:
    """Article 5: an identity once minted never changes. Reshaping it is a re-mint."""
    urn = repository_local_urn("UCOS-ENGINE-000496")
    assert urn == f"{UCKO_URN_PREFIX}:ucos-repository:UCOS-ENGINE-000496"
    assert urn.endswith("UCOS-ENGINE-000496")


def test_the_derivation_is_pure() -> None:
    assert repository_local_urn("UCOS-OBS-000001") == repository_local_urn("UCOS-OBS-000001")


@pytest.mark.parametrize(
    "bad", ["", "ENGINE-000496", "UCOS-ENGINE-496", "urn:ucos:ucko:x:y", "UCOS--000001"]
)
def test_the_derivation_refuses_anything_that_is_not_a_repository_identifier(bad) -> None:
    with pytest.raises(AlignmentError):
        repository_local_urn(bad)


def test_injectivity_is_measured_not_assumed() -> None:
    assert derivation_is_injective(["UCOS-ENGINE-000001", "UCOS-CONFIG-000001"]) == ()
    assert derivation_is_injective(["UCOS-ENGINE-000001", "UCOS-ENGINE-000001"]) == ()
    findings = derivation_is_injective(["UCOS-ENGINE-000001", "not-an-id"])
    assert len(findings) == 1
    assert "not-an-id" in findings[0]


def test_the_whole_ledger_derives_without_collision() -> None:
    """The claim is about the population, so it is measured over the population."""
    ledger = json.loads((REPO / "00-BOOK" / "DATA" / "id-ledger.json").read_text("utf-8"))
    identifiers = [
        value
        for name in ("by_path", "by_object", "by_observation")
        for record in ledger[name].values()
        for key in ("universal_id", "observation_id")
        if isinstance(value := record.get(key), str)
    ]
    assert identifiers, "the ledger holds no identity, so nothing was measured"
    assert derivation_is_injective(identifiers) == ()
    assert len({repository_local_urn(i) for i in identifiers}) == len(set(identifiers))


# --- the objects --------------------------------------------------------------------


def test_every_alignment_object_grounds_in_the_root_law() -> None:
    objects = alignment_objects()
    assert objects
    parents = {obj.authority.derives_from for obj in objects}
    assert parents <= {root_law_urn(), alignment_urn()}
    assert alignment_object().authority.derives_from == root_law_urn()


def test_no_alignment_object_claims_to_be_a_root() -> None:
    """A second self-grounding object would be a second ultimate authority."""
    for obj in alignment_objects():
        assert obj.authority.derives_from != obj.ucko_id


def test_every_alignment_object_names_the_instrument_it_derives_from() -> None:
    for obj in alignment_objects():
        assert obj.authority.instrument == ALIGNMENT_INSTRUMENT
        assert obj.provenance


def test_the_provider_hook_is_the_object_set() -> None:
    assert ucko_objects() == alignment_objects()
    assert alignment_urn().endswith(ALIGNMENT_ID)


# --- the join: the binding may not drift from the law -------------------------------


def test_the_shipped_binding_is_aligned(binding) -> None:
    assert verify_binding(binding) == ()
    require_aligned(binding)


@pytest.mark.parametrize("not_a_mapping", [None, [], "binding", 7])
def test_a_binding_that_cannot_be_read_is_a_finding_never_a_pass(not_a_mapping) -> None:
    assert verify_binding(not_a_mapping) == ("the alignment binding is not a mapping",)


def _mutated(binding: dict, mutate) -> tuple[str, ...]:
    document = copy.deepcopy(binding)
    mutate(document)
    return verify_binding(document)


def test_a_binding_that_renames_the_supreme_authority_is_rejected(binding) -> None:
    def rename(doc):
        doc["supreme_authority"]["id"] = "SOMETHING-ELSE"

    assert any("supreme" in f for f in _mutated(binding, rename))


def test_a_binding_that_edits_the_supremacy_clause_is_rejected(binding) -> None:
    def edit(doc):
        doc["supreme_authority"]["supremacy_clause"] = "authority is whatever we agree."

    assert any("supremacy clause has drifted" in f for f in _mutated(binding, edit))


def test_a_binding_that_miscounts_the_law_is_rejected(binding) -> None:
    def miscount(doc):
        doc["supreme_authority"]["articles"] = 21

    assert any("21" in f for f in _mutated(binding, miscount))


def test_a_binding_that_disowns_its_own_superior_is_rejected(binding) -> None:
    def disown(doc):
        doc.pop("constitutional_superior")

    assert any("its own superior" in f for f in _mutated(binding, disown))


def test_a_rule_statement_that_drifts_from_the_law_is_rejected(binding) -> None:
    def drift(doc):
        doc["invariants"][0]["statement"] = "roughly, one authority."

    assert any("drifted" in f for f in _mutated(binding, drift))


def test_a_missing_rule_is_rejected(binding) -> None:
    def drop(doc):
        doc["invariants"] = doc["invariants"][1:]

    assert any("absent from the binding" in f for f in _mutated(binding, drop))


def test_an_invented_rule_is_rejected(binding) -> None:
    def invent(doc):
        doc["invariants"].append(
            {"id": "CAA-INV-99", "name": "N", "statement": "s", "article": "UCKP-ART-01"}
        )

    assert any("CAA-INV-99" in f for f in _mutated(binding, invent))


def test_a_rule_that_is_not_fail_closed_is_rejected(binding) -> None:
    def soften(doc):
        doc["invariants"][0]["fails_closed"] = False

    assert any("fails_closed" in f for f in _mutated(binding, soften))


def test_a_rule_bound_to_the_wrong_article_is_rejected(binding) -> None:
    def rebind(doc):
        doc["invariants"][0]["article"] = "UCKP-ART-20"

    assert any("UCKP-ART-20" in f for f in _mutated(binding, rebind))


def test_a_rule_renamed_in_the_binding_is_rejected(binding) -> None:
    def rename(doc):
        doc["invariants"][0]["name"] = "SOMETHING_ELSE"

    assert any("name differs" in f for f in _mutated(binding, rename))


@pytest.mark.parametrize("field", ["invariants", "authority_roles", "subordinate_instruments"])
def test_a_binding_missing_a_declared_section_is_rejected(binding, field) -> None:
    def drop(doc):
        doc.pop(field)

    assert _mutated(binding, drop)


def test_a_role_promoted_to_hold_authority_is_rejected(binding) -> None:
    def promote(doc):
        doc["authority_roles"]["PROJECTION"]["may_hold_authority"] = True

    assert any("may hold authority" in f for f in _mutated(binding, promote))


def test_a_role_definition_that_drifts_is_rejected(binding) -> None:
    """The binding's prose is a checked projection, not a second wording."""

    def paraphrase(doc):
        doc["authority_roles"]["EVIDENCE"]["definition"] = "roughly, a record of things."

    assert any("definition has drifted" in f for f in _mutated(binding, paraphrase))


def test_a_role_rebound_to_another_article_is_rejected(binding) -> None:
    def rebind(doc):
        doc["authority_roles"]["EVIDENCE"]["article"] = "UCKP-ART-01"

    assert any("EVIDENCE" in f for f in _mutated(binding, rebind))


def test_a_role_with_a_different_cardinality_is_rejected(binding) -> None:
    def widen(doc):
        doc["authority_roles"]["SUPREME"]["cardinality"] = "MANY"

    assert any("cardinality" in f for f in _mutated(binding, widen))


def test_an_invented_role_is_rejected(binding) -> None:
    def invent(doc):
        doc["authority_roles"]["SOVEREIGN"] = {
            "article": "UCKP-ART-01",
            "may_hold_authority": True,
            "cardinality": "MANY",
        }

    assert any("SOVEREIGN" in f for f in _mutated(binding, invent))


def test_an_instrument_claiming_a_supreme_role_is_rejected(binding) -> None:
    def promote(doc):
        doc["subordinate_instruments"][1]["role"] = "SUPREME"

    assert any("Article 1 admits exactly one" in f for f in _mutated(binding, promote))


def test_an_instrument_with_an_unknown_role_is_rejected(binding) -> None:
    def invent(doc):
        doc["subordinate_instruments"][1]["role"] = "PARAMOUNT"

    assert any("PARAMOUNT" in f for f in _mutated(binding, invent))


def test_an_instrument_deriving_under_nothing_is_rejected(binding) -> None:
    def strip(doc):
        doc["subordinate_instruments"][1]["derives_under"] = []

    assert any("names no article" in f for f in _mutated(binding, strip))


def test_an_instrument_deriving_under_an_invented_article_is_rejected(binding) -> None:
    def invent(doc):
        doc["subordinate_instruments"][1]["derives_under"] = ["UCKP-ART-99"]

    assert any("UCKP-ART-99" in f for f in _mutated(binding, invent))


def test_a_malformed_instrument_entry_is_rejected(binding) -> None:
    def corrupt(doc):
        doc["subordinate_instruments"].append("not a mapping")

    assert any("not a mapping" in f for f in _mutated(binding, corrupt))


# --- the relationship model the binding maps into -----------------------------------


def test_every_mapped_relationship_kind_lands_in_the_real_model(binding) -> None:
    """The stdlib-only gate checks kinds against this map; this checks the map."""
    kinds = binding["relationship_graph_resolution"]["relationship_kind_bindings"]
    assert kinds
    assert verify_binding(binding) == ()


def test_a_relationship_class_the_model_does_not_hold_is_rejected(binding) -> None:
    def invent(doc):
        doc["relationship_graph_resolution"]["relationship_kind_bindings"]["owned_by"][
            "uckp_class"
        ] = "sovereignty"

    assert any("sovereignty" in f for f in _mutated(binding, invent))


def test_a_relation_term_the_model_does_not_hold_is_rejected(binding) -> None:
    def invent(doc):
        doc["relationship_graph_resolution"]["relationship_kind_bindings"]["owned_by"][
            "uckp_relation"
        ] = "belongs-to"

    assert any("belongs-to" in f for f in _mutated(binding, invent))


def test_a_kind_bound_to_an_article_the_law_lacks_is_rejected(binding) -> None:
    def invent(doc):
        doc["relationship_graph_resolution"]["relationship_kind_bindings"]["owned_by"][
            "article"
        ] = "UCKP-ART-77"

    assert any("UCKP-ART-77" in f for f in _mutated(binding, invent))


def test_a_malformed_kind_binding_is_rejected(binding) -> None:
    def corrupt(doc):
        doc["relationship_graph_resolution"]["relationship_kind_bindings"]["owned_by"] = 7

    assert any("carries no binding" in f for f in _mutated(binding, corrupt))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda doc: doc.pop("relationship_graph_resolution"),
        lambda doc: doc["relationship_graph_resolution"].pop("relationship_kind_bindings"),
    ],
)
def test_a_binding_without_a_relationship_model_is_rejected(binding, mutate) -> None:
    assert _mutated(binding, mutate)


# --- the derivation contract the stdlib-only gate reads -----------------------------


@pytest.mark.parametrize("field", ["urn_prefix", "namespace", "id_shape", "function"])
def test_a_derivation_field_that_drifts_is_rejected(binding, field) -> None:
    def drift(doc):
        doc["identity_authority_resolution"]["derivation"][field] = "drifted"

    assert any(field in f for f in _mutated(binding, drift))


@pytest.mark.parametrize("field", ["shape", "example"])
def test_a_derivation_illustration_that_drifts_is_rejected(binding, field) -> None:
    def drift(doc):
        doc["identity_authority_resolution"]["derivation"][field] = "drifted"

    assert _mutated(binding, drift)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda doc: doc.pop("identity_authority_resolution"),
        lambda doc: doc["identity_authority_resolution"].pop("derivation"),
        lambda doc: doc.pop("supreme_authority"),
    ],
)
def test_a_binding_without_an_identity_resolution_is_rejected(binding, mutate) -> None:
    assert _mutated(binding, mutate)


def test_require_aligned_raises_on_a_drifted_binding(binding) -> None:
    document = copy.deepcopy(binding)
    document["supreme_authority"]["id"] = "SOMETHING-ELSE"
    with pytest.raises(AlignmentError):
        require_aligned(document)


def test_an_orthogonal_instrument_must_declare_a_scope_and_it_must_be_bounded(binding) -> None:
    """ORTHOGONAL IS THE ROLE THAT SAYS "I GOVERN SOMETHING ELSE", AND IT HAS TO SAY WHAT.

    An instrument claiming a supreme role is refused by Article 1, and an unknown role is
    refused by the vocabulary — both tested. The ORTHOGONAL branch beneath them had neither
    arm run, and it is the one that stops the role from becoming a way to claim supremacy
    without the word: an instrument that governs "everything in UCOS" orthogonally is a second
    supreme authority with a different label, and one that declares no scope at all is the
    same claim left unwritten.
    """

    def unscoped(doc):
        doc["subordinate_instruments"][1]["role"] = "ORTHOGONAL"
        doc["subordinate_instruments"][1].pop("owns", None)

    assert any("declares no explicit scope" in f for f in _mutated(binding, unscoped))

    def blank_scope(doc):
        doc["subordinate_instruments"][1]["role"] = "ORTHOGONAL"
        doc["subordinate_instruments"][1]["owns"] = "   "

    assert any("declares no explicit scope" in f for f in _mutated(binding, blank_scope))

    def unrestricted(doc):
        doc["subordinate_instruments"][1]["role"] = "ORTHOGONAL"
        doc["subordinate_instruments"][1]["owns"] = "Unrestricted authority over the corpus"

    assert any("unrestricted scope" in f for f in _mutated(binding, unrestricted))

    def bounded(doc):
        doc["subordinate_instruments"][1]["role"] = "ORTHOGONAL"
        doc["subordinate_instruments"][1]["owns"] = "the temporal coordinate model"

    assert not any("ORTHOGONAL" in f for f in _mutated(binding, bounded))


def test_a_role_declaration_that_is_not_a_mapping_is_rejected(binding) -> None:
    """A ROLE IS A DECLARATION WITH FIELDS, AND A ROLE THAT IS NOT ONE IS ABSENT.

    A role missing from the binding entirely is refused, and a role whose fields have drifted
    is refused field by field — both tested. The arm between them was not: a key present under
    the role's name whose value is a string, a list or a number. Reading its fields would raise
    from inside a verifier whose contract is to RETURN findings, so it is reported as the
    absence it is.
    """

    def corrupt(doc):
        role_id = next(iter(doc["authority_roles"]))
        doc["authority_roles"][role_id] = "not a mapping"

    findings = _mutated(binding, corrupt)

    assert any("declared in the law and absent from the binding" in f for f in findings)


def test_two_identifiers_deriving_one_urn_is_a_collision(binding) -> None:
    """INJECTIVITY IS MEASURED, NOT ASSUMED — and the collision arm had no case.

    The whole committed ledger derives without collision, which is the property the measure
    exists to check and therefore not evidence that it CAN report one. Two identifiers mapping
    to one repository-local URN means one of the two objects is unaddressable through the
    derivation: every reference resolves to the other, and nothing in the ledger says so.
    """
    assert derivation_is_injective(["UCOS-A-000001", "UCOS-B-000002"]) == ()

    # Two DISTINCT identifiers that derive one URN: the derivation trims, so a trailing
    # space makes a different identifier addressing the same object.
    findings = derivation_is_injective(["UCOS-A-000001", "UCOS-A-000001 "])

    assert any("both derive" in finding for finding in findings)


def test_every_alignment_object_renders_the_declaration_behind_it() -> None:
    """A ROLE AND A RULE ARE DATA, AND THEIR RENDERS ARE HOW THEY LEAVE THE PROCESS.

    Both are compared field by field against the binding, so their own projections had no
    caller — and they are what writes the law side of the comparison out. A rule carries the
    article it enforces plus the further articles it also serves, which is the difference
    between "this rule exists" and "this rule enforces an article that already exists".
    """
    role = AUTHORITY_ROLES[0]
    rule = ALIGNMENT_RULES[0]

    assert role.to_dict() == {
        "role_id": role.role_id,
        "definition": role.definition,
        "article": role.article,
        "may_hold_authority": role.may_hold_authority,
        "cardinality": role.cardinality,
    }
    assert rule.to_dict() == {
        "rule_id": rule.rule_id,
        "name": rule.name,
        "statement": rule.statement,
        "article": rule.article,
        "also": list(rule.also),
    }


# --- the thirty-one mandated engines, located against Repository Truth ----------
#
# UAKP's engine model lists thirty-one engines and states the rule that makes locating them
# an alignment question rather than an inventory: "Engines are replaceable implementations"
# and "No engine SHALL contain project-specific logic." A replaceable implementation still
# has to EXIST somewhere, and the question of which instrument holds a mandated capability
# is the same question UCOS-CAA-001 answers for authorities.
#
# THE TEST OF OWNERSHIP IS NAMING, NOT OCCURRENCE. A module that mentions "reasoning" is not
# the Universal Reasoning Engine. So a row below is admitted only when a module or package is
# named for the engine's function, and the five that nothing names are listed as absent
# rather than matched to the nearest file that happens to contain the word.

#: Engine -> the module or package that carries it. One path may carry two engines when the
#: instrument itself names both, which UCL-000001 does for extraction and elevation.
ENGINE_HOME = {
    "UAKP-ENG/EN-02": "engine/knowledge/ukip/assimilation.py",  # Knowledge Assimilation
    "UAKP-ENG/EN-04": "engine/knowledge/ukip/classification.py",  # Knowledge Classification
    "UAKP-ENG/EN-05": "engine/context/resolution.py",  # Context Resolution
    "UAKP-ENG/EN-06": "engine/universal_discovery",  # Repository Discovery
    "UAKP-ENG/EN-07": "engine/execution_environment/discovery.py",  # Environment Discovery
    "UAKP-ENG/EN-08": "engine/knowledge/ukip/evidence.py",  # Evidence Discovery
    "UAKP-ENG/EN-09": "platform/universal_truth",  # Truth Discovery
    "UAKP-ENG/EN-10": "engine/constitution/authority.py",  # Canonical Authority
    "UAKP-ENG/EN-12": "engine/omega_infinite/contradiction.py",  # Conflict Detection
    "UAKP-ENG/EN-13": "engine/uicm/gap.py",  # Gap Discovery
    "UAKP-ENG/EN-14": "00-MASTER/UAKOS-CLOSURE-009/requirement_engine.py",  # Requirement Discovery
    "UAKP-ENG/EN-15": "engine/knowledge/integration/dependency.py",  # Dependency Discovery
    "UAKP-ENG/EN-17": "00-MASTER/UAKOS-CLOSURE-008/decision_engine.py",  # Decision
    "UAKP-ENG/EN-18": "intelligence/realization/planning.py",  # Planning
    "UAKP-ENG/EN-21": "engine/runtime/orchestration.py",  # Orchestration
    "UAKP-ENG/EN-22": "intelligence/realization",  # Realization
    "UAKP-ENG/EN-23": "engine/uicm/observation.py",  # Observation
    "UAKP-ENG/EN-24": "engine/validation",  # Validation
    "UAKP-ENG/EN-25": "engine/uaue/verification.py",  # Verification
    "UAKP-ENG/EN-26": "engine/certification",  # Certification
    "UAKP-ENG/EN-27": "00-MASTER/UCL-000001/ucl_engine.py",  # Knowledge Extraction
    "UAKP-ENG/EN-29": "00-MASTER/UCL-000001/ucl_engine.py",  # Capability Elevation
    "UAKP-ENG/EN-30": "engine/constitution/evolution.py",  # Evolution
    "UAKP-ENG/EN-31": "00-MASTER/UCOS-AEE-001/aee_engine.py",  # Self-Evolution
}

#: Realized, but at a scope narrower than the word "Universal" in the mandate. Recorded as
#: its own tier because folding it into ENGINE_HOME would let four question-scoped engines
#: read as one universal one, and folding it into ABSENT would discard working capability.
ENGINE_NARROWER = {
    "UAKP-ENG/EN-16": (
        "00-BOOK/tools/config.py",
        "INTEL_QUESTIONS declares four question-scoped reasoning engines -- change, "
        "impact, dependency and certification -- and no engine that reasons in general",
    ),
}

#: Specified and not built. The specification is real and the implementation is not, which
#: is a different finding from absence: the design decision has been taken and recorded.
ENGINE_SPECIFIED_ONLY = {
    "UAKP-ENG/EN-28": (
        "00-MASTER/UEI-000001/03-UNIVERSAL-LEARNING-SPECIFICATION.md",
        "uei_engine.py implements none of it",
    ),
}

#: Nothing in the repository is named for these. Listed so the engine model's completeness
#: claim fails loudly rather than by silence.
ENGINE_ABSENT = {
    "UAKP-ENG/EN-01": "Knowledge Acquisition",
    "UAKP-ENG/EN-03": "Knowledge Refinement",
    "UAKP-ENG/EN-11": "Duplicate Detection",
    "UAKP-ENG/EN-19": "Execution Specification",
    "UAKP-ENG/EN-20": "Realization Package",
}


def _engine_mandates() -> dict[str, str]:
    repo = Path(__file__).resolve().parents[3]
    corpus = json.loads(
        (repo / "00-MASTER" / "CAEM-001" / "06-MANDATE-CORPUS.json").read_text(encoding="utf-8")
    )
    return {a["atom_id"]: a["label"] for a in corpus["atoms"] if a["section"] == "UAKP-ENG"}


def test_every_mandated_engine_is_located_narrowed_specified_or_absent() -> None:
    """TOTALITY. Thirty-one, partitioned four ways, each engine in exactly one tier."""
    mandates = _engine_mandates()
    assert len(mandates) == 31, f"the engine model lists 31 engines, corpus has {len(mandates)}"

    tiers = (ENGINE_HOME, ENGINE_NARROWER, ENGINE_SPECIFIED_ONLY, ENGINE_ABSENT)
    accounted = set().union(*(set(t) for t in tiers))
    assert set(mandates) == accounted, (
        f"engines in no tier: {sorted(set(mandates) - accounted)}; "
        f"tiered identifiers that are not engine mandates: {sorted(accounted - set(mandates))}"
    )
    assert (
        sum(len(t) for t in tiers) == len(accounted) == 31
    ), "an engine appears in more than one tier, so it is being claimed both present and absent"


def test_every_located_engine_has_a_home_that_exists_and_carries_code() -> None:
    """A located engine whose home is a document is a specification, not an engine."""
    repo = Path(__file__).resolve().parents[3]
    for mandate, home in ENGINE_HOME.items():
        path = repo / home
        assert path.exists(), f"{mandate}: declared home {home} does not exist"
        if path.is_dir():
            assert any(path.rglob("*.py")), f"{mandate}: {home} is a directory carrying no code"
        else:
            assert (
                path.suffix == ".py"
            ), f"{mandate}: {home} is not code, so it specifies an engine rather than being one"


def test_the_narrowed_and_specified_engines_name_a_real_instrument() -> None:
    repo = Path(__file__).resolve().parents[3]
    for mandate, (home, reason) in {**ENGINE_NARROWER, **ENGINE_SPECIFIED_ONLY}.items():
        assert (repo / home).exists(), f"{mandate}: {home} does not exist"
        assert len(reason) > 30, f"{mandate}: tiered below 'located' without a stated reason"


def test_the_narrowed_reasoning_engine_is_really_narrower() -> None:
    """NON-VACUITY. The claim is that reasoning is bound to specific questions. If a general
    reasoning engine ever appears, this row is wrong and must move up a tier."""
    repo = Path(__file__).resolve().parents[3]
    config = (repo / "00-BOOK" / "tools" / "config.py").read_text(encoding="utf-8")
    assert "INTEL_QUESTIONS" in config
    assert "Reasoning Engine" in config
    assert (
        "Universal Reasoning Engine" not in config
    ), "a Universal Reasoning Engine is now declared; UAKP-ENG/EN-16 is no longer narrower"


def test_the_absent_engines_are_absent_under_their_own_name() -> None:
    """NON-VACUITY for the tier anything inconvenient would drift into.

    The check is the same one used to admit a located engine: is a module or package NAMED
    for this function? Naming means the PATH carries every word of the function, not just
    the last one -- `platform/commercial_intelligence/packages.py` is named for commercial
    packages and matching it to "Realization Package" on the word `package` alone would be
    the occurrence-is-ownership error this whole tiering exists to avoid. Searching file
    CONTENT instead would match every document that discusses an engine and make absence
    unprovable in the other direction.
    """
    repo = Path(__file__).resolve().parents[3]
    roots = [repo / "engine", repo / "platform", repo / "intelligence", repo / "service"]
    for mandate, function in ENGINE_ABSENT.items():
        words = [w.lower() for w in function.split()]
        found = [
            str(p.relative_to(repo))
            for root in roots
            if root.exists()
            for p in root.rglob("*.py")
            if "test" not in p.parts
            and "tests" not in p.parts
            and all(w in str(p.relative_to(repo)).lower() for w in words)
        ]
        assert (
            not found
        ), f"{mandate}: {function} is declared absent but a module is named for it: {found}"


def test_the_naming_rule_that_proves_absence_can_find_something() -> None:
    """The absence rule is only evidence if it is capable of a positive. Run it against a
    located engine and require a hit, so a rule that silently matches nothing cannot pass
    every absence claim by construction."""
    repo = Path(__file__).resolve().parents[3]
    hits = [
        str(p.relative_to(repo))
        for p in (repo / "engine").rglob("*.py")
        if "tests" not in p.parts
        and all(w in str(p.relative_to(repo)).lower() for w in ("knowledge", "classification"))
    ]
    assert hits, "the path-naming rule matches nothing at all, so every absence claim is vacuous"
