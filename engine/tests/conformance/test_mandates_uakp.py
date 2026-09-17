"""Mandate conformance — the Universal Autonomous Knowledge Platform foundation.

350 mandates over 18 sections. The document's nine independence clauses (UAKP-IND) and its
two hard-coding principles are bound in `engine/tests/kernel/test_compliance.py`, against
the kernel that can decide a negative by refusing to seed a token. Nothing here restates
them.

WHY THESE FOUR SECTIONS SIT TOGETHER. They were first written into `test_layer_zero.py`,
`test_universe_and_validation.py` and `test_alignment.py` -- the files whose subjects they
touched -- and each of those files states a scope its new contents exceeded. A suite whose
declared scope no longer describes what it asserts is the drift these bindings exist to
catch, so they were moved rather than left where they happened to land.
"""

from __future__ import annotations

import dataclasses
import json

from engine.tests.conformance.mandate_corpus import (
    assert_absence_rule_can_find_something,
    assert_homes_exist,
    assert_named_by_nothing,
    assert_partitions,
    repo_root,
    section,
    tracked,
)
from engine.uckp.facets import REQUIRED_FACETS, Facet
from engine.uckp.ucko import UniversalConstitutionalKnowledgeObject as UCKO

# ================================================================================
# UAKP-OBJ — the thirteen mandated object attributes
# ================================================================================
#
# "Every object SHALL possess" thirteen attributes. Article 6 already answers that question
# with thirty-three facets, so the mandate is not new construction -- it is a claim about
# this law's completeness, and the honest way to settle it is to map all thirteen and let
# the two that do not map say so out loud.
#
# SCOPE. A binding here proves the facet EXISTS and is carried by the UCKO dataclass. It
# does not prove any object has attested it: Article 6 permits a facet to be unattested.

OBJECT_ATTRIBUTE_FACET = {
    "UAKP-OBJ/OJ-01": Facet.IDENTITY,  # Universal Identity attribute
    "UAKP-OBJ/OJ-02": Facet.ONTOLOGY,  # Type attribute -- "What kind of being is it?"
    "UAKP-OBJ/OJ-03": Facet.METADATA,  # Metadata attribute
    "UAKP-OBJ/OJ-04": Facet.LIFECYCLE,  # Lifecycle State attribute
    "UAKP-OBJ/OJ-05": Facet.RELATIONSHIPS,  # Relationships attribute
    "UAKP-OBJ/OJ-06": Facet.AUTHORITY,  # Authority attribute
    "UAKP-OBJ/OJ-07": Facet.PROVENANCE,  # Provenance attribute
    "UAKP-OBJ/OJ-08": Facet.EVIDENCE,  # Evidence attribute
    "UAKP-OBJ/OJ-10": Facet.GOVERNANCE_CONTEXT,  # Governance attribute
    "UAKP-OBJ/OJ-12": Facet.TEMPORAL_HISTORY,  # History attribute
    "UAKP-OBJ/OJ-13": Facet.EVOLUTION_HISTORY,  # Evolution History attribute
}

#: Answered by a deliberate REFUSAL rather than by a facet. A mutable version field would
#: contradict Article 5 (an identity, once minted, never changes) and Article 12 (every
#: transition creates a NEW state referencing its parent). The law answers "which version?"
#: with the state chain, so the absence of a `version` facet is the answer, not a gap.
OBJECT_ATTRIBUTE_BY_REFUSAL = {
    "UAKP-OBJ/OJ-11": (Facet.EVOLUTION_HISTORY, Facet.TEMPORAL_HISTORY),  # Version attribute
}

#: Present, and NOT at the scope the mandate states. "Every object shall possess Confidence";
#: this repository binds confidence to a registered KNOWLEDGE record, a strictly smaller
#: population than every UCKO. Recorded rather than counted satisfied, because a scope
#: difference only a reader notices is a scope difference nothing enforces.
OBJECT_ATTRIBUTE_SCOPED_ELSEWHERE = {
    "UAKP-OBJ/OJ-09": "engine.knowledge.ukip.confidence binds confidence to a knowledge "
    "record, never to a UCKO; the mandate says every object",
}


def test_every_mandated_object_attribute_is_answered_or_declared_out_of_scope() -> None:
    mandates = section("UAKP-OBJ")
    assert len(mandates) == 13, f"the object model states 13 attributes, corpus has {len(mandates)}"
    assert_partitions(
        "UAKP-OBJ",
        mandates,
        OBJECT_ATTRIBUTE_FACET,
        OBJECT_ATTRIBUTE_BY_REFUSAL,
        OBJECT_ATTRIBUTE_SCOPED_ELSEWHERE,
    )


def test_each_mapped_attribute_names_a_required_facet_the_object_carries() -> None:
    fields = {f.name for f in dataclasses.fields(UCKO)}
    for mandate, facet in OBJECT_ATTRIBUTE_FACET.items():
        assert facet in REQUIRED_FACETS, f"{mandate}: {facet} is not a required facet"
        assert facet.attribute in fields, (
            f"{mandate}: facet {facet.value!r} is declared but the UCKO carries no "
            f"{facet.attribute!r} field, so the object cannot answer the question"
        )


def test_the_attribute_mapping_is_injective() -> None:
    """NON-VACUITY. Two attributes answered by one facet means one is unanswered."""
    facets = list(OBJECT_ATTRIBUTE_FACET.values())
    duplicated = sorted({f.value for f in facets if facets.count(f) > 1})
    assert not duplicated, f"facets claimed by more than one mandated attribute: {duplicated}"


def test_version_is_answered_by_refusal_and_the_refusal_is_real() -> None:
    """If a version facet or field ever appears, this mapping became a rationalisation."""
    assert "version" not in {facet.value for facet in Facet}
    fields = {f.name for f in dataclasses.fields(UCKO)}
    assert "version" not in fields, (
        "UAKP-OBJ/OJ-11 is mapped to the state chain on the grounds that no version field "
        "exists; one now does, so the mapping is false"
    )
    for facet in OBJECT_ATTRIBUTE_BY_REFUSAL["UAKP-OBJ/OJ-11"]:
        assert facet.attribute in fields


def test_confidence_is_scoped_to_knowledge_and_the_scope_limit_is_real() -> None:
    """NON-VACUITY for the one attribute declared out of scope."""
    from engine.knowledge.ukip.confidence import CONFIDENCE_DIMENSION

    assert CONFIDENCE_DIMENSION == "confidence"
    assert "confidence" not in {f.name for f in dataclasses.fields(UCKO)}, (
        "UAKP-OBJ/OJ-09 is declared out of scope because no UCKO carries confidence; "
        "one now does, so it is in scope and must be bound rather than excused"
    )
    assert "confidence" not in {facet.value for facet in Facet}
    for mandate, reason in OBJECT_ATTRIBUTE_SCOPED_ELSEWHERE.items():
        assert len(reason) > 40, f"{mandate}: declared out of scope without a stated reason"


# ================================================================================
# UAKP-UNIV — the twenty-four mandated universes
# ================================================================================
#
# The hierarchy states twenty-four universes and the rule that makes them load-bearing:
# "Engines MAY evolve. Universes SHALL remain constitutionally stable." A universe is
# therefore not a capability under another name -- it is the stable container a capability
# is answerable to, and a repository holding `engine/validation` does NOT thereby hold a
# Validation Universe. Summing the two is what makes a hierarchy read complete while nothing
# carries it.

UNIVERSE_HOMED = {
    "UAKP-UNIV/UV-05": "engine/uckp/universe.py",  # Knowledge Universe
    "UAKP-UNIV/UV-06": "00-BOOK/DATA/evidence-universe.json",  # Evidence Universe
    "UAKP-UNIV/UV-17": "00-BOOK/DATA/observation-universe.json",  # Observation Universe
}

#: Carried only as a row in the ARCH-001 Universal Universe Catalog, which declares its own
#: CONSTITUENT, GOVERNANCE and RATIFICATION authority as NONE. A row is REGISTRATION and
#: never ratification -- real, and weaker than a home.
UNIVERSE_CATALOGUED = {
    "UAKP-UNIV/UV-02": "UNI-035",  # Ontology Universe
    "UAKP-UNIV/UV-03": "UNI-010",  # Identity Universe
    "UAKP-UNIV/UV-08": "UNI-028",  # Memory Universe
    "UAKP-UNIV/UV-09": "UNI-018",  # Governance Universe
    "UAKP-UNIV/UV-11": "UNI-111",  # Reasoning Universe
    "UAKP-UNIV/UV-12": "UNI-112",  # Decision Universe
    "UAKP-UNIV/UV-20": "UNI-092",  # Certification Universe
    "UAKP-UNIV/UV-21": "UNI-052",  # Evolution Universe
    "UAKP-UNIV/UV-22": "UNI-101",  # Integration Universe
}

#: Declared by nothing. Each names the CAPABILITY that exists in its place, because "absent"
#: and "absent, and here is what was mistaken for it" are different findings and only the
#: second can be acted on. An empty string means no capability either.
UNIVERSE_ABSENT_CAPABILITY_ONLY = {
    "UAKP-UNIV/UV-01": "engine/foundation",  # Constitutional Foundation Universe
    "UAKP-UNIV/UV-04": "engine/context",  # Context Universe
    "UAKP-UNIV/UV-07": "platform/universal_truth",  # Truth Universe
    "UAKP-UNIV/UV-10": "",  # Intent Universe -- no capability either
    "UAKP-UNIV/UV-13": "platform/universal_master_plan",  # Planning Universe
    "UAKP-UNIV/UV-14": "00-BOOK/DATA/relationships.json",  # Dependency Universe
    "UAKP-UNIV/UV-15": "engine/knowledge/integration",  # Orchestration Universe
    "UAKP-UNIV/UV-16": "intelligence/realization",  # Realization Universe
    "UAKP-UNIV/UV-18": "engine/validation",  # Validation Universe
    "UAKP-UNIV/UV-19": "00-MASTER/UVI-000001",  # Verification Universe
    "UAKP-UNIV/UV-23": "00-MASTER/UEG-000001",  # Environment Universe
    "UAKP-UNIV/UV-24": "00-MASTER/UCOS-AEE-001",  # Self-Evolution Universe
}

UNIVERSE_CATALOG = "02-MASTER/UCOS-Ω∞-UNIVERSAL-UNIVERSE-CATALOG.md"


def test_every_mandated_universe_is_homed_catalogued_or_declared_absent() -> None:
    mandates = section("UAKP-UNIV")
    assert len(mandates) == 24, f"the hierarchy states 24 universes, corpus has {len(mandates)}"
    assert_partitions(
        "UAKP-UNIV",
        mandates,
        UNIVERSE_HOMED,
        UNIVERSE_CATALOGUED,
        UNIVERSE_ABSENT_CAPABILITY_ONLY,
    )


def test_each_homed_universe_has_a_file_that_names_it() -> None:
    """A home that does not contain the universe's own name is a guess, not a home."""
    assert_homes_exist("UAKP-UNIV", UNIVERSE_HOMED)
    mandates = section("UAKP-UNIV")
    for mandate, home in UNIVERSE_HOMED.items():
        text = (repo_root() / home).read_text(encoding="utf-8", errors="ignore")
        label = mandates[mandate]
        head = label.removesuffix(" Universe")
        assert label in text or (
            "universe" in text.lower() and head.lower() in text.lower()
        ), f"{mandate}: {home} is declared the home of {label!r} but never names it"


def test_each_catalogued_universe_is_a_row_in_the_catalog_under_its_own_name() -> None:
    mandates = section("UAKP-UNIV")
    catalog = (repo_root() / UNIVERSE_CATALOG).read_text(encoding="utf-8")
    for mandate, row in UNIVERSE_CATALOGUED.items():
        expected = f"| {row} | {mandates[mandate]} |"
        assert expected in catalog, (
            f"{mandate}: the catalog carries no row {expected!r}; the registration this "
            "tier rests on is not there"
        )


def test_the_catalog_registers_and_never_ratifies() -> None:
    """NON-VACUITY for the catalogued tier. If the catalog ever claimed authority, these
    nine would be homed rather than registered and the tiers would be wrong."""
    catalog = (repo_root() / UNIVERSE_CATALOG).read_text(encoding="utf-8")
    for field in ("CONSTITUENT AUTHORITY", "GOVERNANCE AUTHORITY", "RATIFICATION AUTHORITY"):
        assert f"| {field} | NONE |" in catalog, (
            f"the catalog no longer declares {field} = NONE; a catalogued universe may now "
            "be a homed one and this binding must be re-decided"
        )


def test_the_absent_universes_are_absent_from_the_catalog_and_name_a_real_capability() -> None:
    """NON-VACUITY for the absent tier -- the tier anything inconvenient would drift into."""
    mandates = section("UAKP-UNIV")
    catalog = (repo_root() / UNIVERSE_CATALOG).read_text(encoding="utf-8")
    known = set(tracked())
    for mandate, capability in UNIVERSE_ABSENT_CAPABILITY_ONLY.items():
        label = mandates[mandate]
        assert (
            f"| {label} |" not in catalog
        ), f"{mandate}: {label!r} is declared absent but the catalog carries a row for it"
        if capability:
            present = capability in known or any(
                path.startswith(capability.rstrip("/") + "/") for path in known
            )
            assert present, (
                f"{mandate}: offered {capability} as the capability standing in for "
                f"{label!r}, and it is not a tracked path"
            )


def test_a_capability_is_never_counted_as_the_universe_it_stands_in_for() -> None:
    """The distinction the whole binding rests on, asserted rather than left in prose."""
    standing_in = {c for c in UNIVERSE_ABSENT_CAPABILITY_ONLY.values() if c}
    assert not (standing_in & set(UNIVERSE_HOMED.values())), (
        "a path offered as a stand-in capability is also claimed as a universe's home; "
        "one of the two claims is false"
    )
    assert sum(1 for c in UNIVERSE_ABSENT_CAPABILITY_ONLY.values() if not c) == 1


# ================================================================================
# UAKP-ENG — the thirty-one mandated engines
# ================================================================================
#
# "Engines are replaceable implementations" and "No engine SHALL contain project-specific
# logic." A replaceable implementation still has to EXIST somewhere. The test of ownership
# is NAMING, not occurrence: a module that mentions "reasoning" is not the Universal
# Reasoning Engine, so a row is admitted only when a module or package is named for the
# engine's function.

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
    # Requirement Discovery
    "UAKP-ENG/EN-14": "00-MASTER/UAKOS-CLOSURE-009/requirement_engine.py",
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

#: Realized, at a scope narrower than the word "Universal" in the mandate. Its own tier:
#: folding it up would let four question-scoped engines read as one universal one, and
#: folding it down would discard working capability.
ENGINE_NARROWER = {
    "UAKP-ENG/EN-16": (
        "00-BOOK/tools/config.py",
        "INTEL_QUESTIONS declares four question-scoped reasoning engines -- change, "
        "impact, dependency and certification -- and no engine that reasons in general",
    ),
}

#: Specified and not built. A different finding from absence: the design decision has been
#: taken and recorded.
ENGINE_SPECIFIED_ONLY = {
    "UAKP-ENG/EN-28": (
        "00-MASTER/UEI-000001/03-UNIVERSAL-LEARNING-SPECIFICATION.md",
        "uei_engine.py implements none of it",
    ),
}

ENGINE_ABSENT = {
    "UAKP-ENG/EN-01": "Knowledge Acquisition",
    "UAKP-ENG/EN-03": "Knowledge Refinement",
    "UAKP-ENG/EN-11": "Duplicate Detection",
    "UAKP-ENG/EN-19": "Execution Specification",
    "UAKP-ENG/EN-20": "Realization Package",
}


def test_every_mandated_engine_is_located_narrowed_specified_or_absent() -> None:
    mandates = section("UAKP-ENG")
    assert len(mandates) == 31, f"the engine model lists 31 engines, corpus has {len(mandates)}"
    assert_partitions(
        "UAKP-ENG",
        mandates,
        ENGINE_HOME,
        ENGINE_NARROWER,
        ENGINE_SPECIFIED_ONLY,
        ENGINE_ABSENT,
    )


def test_every_located_engine_has_a_home_that_exists_and_carries_code() -> None:
    """A located engine whose home is a document is a specification, not an engine."""
    assert_homes_exist("UAKP-ENG", ENGINE_HOME)
    for mandate, home in ENGINE_HOME.items():
        path = repo_root() / home
        if path.is_dir():
            assert any(path.rglob("*.py")), f"{mandate}: {home} is a directory carrying no code"
        else:
            assert (
                path.suffix == ".py"
            ), f"{mandate}: {home} is not code, so it specifies an engine rather than being one"


def test_the_narrowed_and_specified_engines_name_a_real_instrument() -> None:
    for mandate, (home, reason) in {**ENGINE_NARROWER, **ENGINE_SPECIFIED_ONLY}.items():
        assert (repo_root() / home).exists(), f"{mandate}: {home} does not exist"
        assert len(reason) > 30, f"{mandate}: tiered below 'located' without a stated reason"


def test_the_narrowed_reasoning_engine_is_really_narrower() -> None:
    """NON-VACUITY. If a general reasoning engine appears, this row moves up a tier."""
    config = (repo_root() / "00-BOOK" / "tools" / "config.py").read_text(encoding="utf-8")
    assert "INTEL_QUESTIONS" in config
    assert "Reasoning Engine" in config
    assert (
        "Universal Reasoning Engine" not in config
    ), "a Universal Reasoning Engine is now declared; UAKP-ENG/EN-16 is no longer narrower"


def test_the_absent_engines_are_absent_under_their_own_name() -> None:
    """NON-VACUITY, by the same rule that admits a home: the PATH carries every word of the
    function. Matching on the last word alone once claimed
    `commercial_intelligence/packages.py` as Realization Package."""
    assert_named_by_nothing("UAKP-ENG", ENGINE_ABSENT)


# ================================================================================
# UAKP-REG — the twenty-five mandated registries
# ================================================================================
#
# Three obligations are attached: discoverable, versioned and GOVERNED. The third decides
# this binding, because the repository holds two populations that both call themselves
# registers. 00-BOOK and engine code carry governed registries; 00-MASTER is a
# registration-EXCLUDED zone whose registers declare AUTHORITY = NONE. Counting the second
# as the first is the measurement that would report this mandate satisfied.

REGISTRY_GOVERNED = {
    "UAKP-REG/RG-02": "engine/uckp/registry.py",  # Knowledge Registry
    "UAKP-REG/RG-03": "00-BOOK/DATA/id-ledger.json",  # Identity Registry
    "UAKP-REG/RG-04": "engine/context/registry.py",  # Context Registry
    "UAKP-REG/RG-05": "00-BOOK/DATA/evidence-universe.json",  # Evidence Registry
    "UAKP-REG/RG-11": "00-BOOK/DATA/relationships.json",  # Dependency Registry
    "UAKP-REG/RG-12": "00-BOOK/DATA/generated-artifact-registry.json",  # Artifact Registry
    "UAKP-REG/RG-13": "00-BOOK/DATA/relationships.json",  # Relationship Registry
    # Execution Registry
    "UAKP-REG/RG-16": "00-BOOK/CONTROL-TOWER/UCOS-MASTER-EXECUTION-STATUS-REGISTRY.md",
    "UAKP-REG/RG-18": "engine/verification_intelligence/registry.py",  # Verification Registry
    "UAKP-REG/RG-19": "00-BOOK/DATA/certification.json",  # Certification Registry
    "UAKP-REG/RG-20": "00-BOOK/DATA/constitutional-authority-alignment.json",  # Governance
    "UAKP-REG/RG-22": "00-BOOK/DATA/change-ledger.json",  # Evolution Registry
}

REGISTRY_PROGRAMME_ONLY = {
    "UAKP-REG/RG-06": "00-MASTER/UCCEP-000000/02-REPOSITORY-TRUTH-REGISTER.md",  # Truth
    "UAKP-REG/RG-07": "00-MASTER/UAKOS-CLOSURE-009/02-REPOSITORY-REQUIREMENT-REGISTER.md",
    "UAKP-REG/RG-08": "00-MASTER/UAKOS-CLOSURE-008/10-REPOSITORY-DECISION-REGISTER.md",
    "UAKP-REG/RG-09": "00-MASTER/UAKOS-PHASE-004/05-VALIDATION-PLANNING-REGISTER.md",  # Planning
    "UAKP-REG/RG-10": "00-MASTER/UAEP-000001/01-CAPABILITY-BINDING-REGISTER.md",  # Capability
    "UAKP-REG/RG-14": "00-MASTER/UAKOS-PHASE-002/02-REPOSITORY-IMPLEMENTATION-REGISTER.md",
    "UAKP-REG/RG-15": "00-MASTER/UAKOS-PHASE-003R/01-REALIZATION-TYPE-REGISTER.md",  # Realization
    "UAKP-REG/RG-17": "00-MASTER/UAKOS-CLOSURE-003/05-VALIDATION-REGISTER.md",  # Validation
    "UAKP-REG/RG-23": "00-MASTER/UEG-000001/ueg-declaration.json",  # Environment
    # Adapter Registry
    "UAKP-REG/RG-24": "00-MASTER/UCL-000001/06-METADATA-PROVIDER-AND-ADAPTER-REGISTER.md",
}

#: Ontology is carried by a module, not a register: it holds the classification the mandate
#: wants a registry FOR. Separate, because calling a module a registry blurs the very
#: distinction the other tiers keep.
REGISTRY_AS_MODULE = {
    "UAKP-REG/RG-01": "engine/context/ontology.py",  # Ontology Registry
}

#: Tracked and real, with an `authority` field that is execution-scoped rather than
#: constitutional. Neither governed nor absent, and both labels would be a false report.
REGISTRY_BAND_SCOPED = {
    # Integration Registry
    "UAKP-REG/RG-25": (
        "infrastructure/_evidence/EC3-B13-U10/integration-registry.json",
        "ENGINEERING-EXECUTION-ONLY",
    ),
}

REGISTRY_ABSENT = {
    "UAKP-REG/RG-21": "memory registry",
}

EXCLUDED_ZONE = "00-MASTER/"


def test_every_mandated_registry_is_governed_programme_module_band_or_absent() -> None:
    mandates = section("UAKP-REG")
    assert len(mandates) == 25, f"the model lists 25 registries, corpus has {len(mandates)}"
    assert_partitions(
        "UAKP-REG",
        mandates,
        REGISTRY_GOVERNED,
        REGISTRY_PROGRAMME_ONLY,
        REGISTRY_AS_MODULE,
        REGISTRY_BAND_SCOPED,
        REGISTRY_ABSENT,
    )


def test_every_governed_registry_is_outside_the_registration_excluded_zone() -> None:
    """The property that makes the governed tier mean anything."""
    homes = {**REGISTRY_GOVERNED, **REGISTRY_AS_MODULE}
    for mandate, home in homes.items():
        assert not home.startswith(EXCLUDED_ZONE), (
            f"{mandate}: {home} sits in the registration-excluded zone and cannot be a "
            "governed registry"
        )
    assert_homes_exist("UAKP-REG", homes)


def test_every_programme_register_is_inside_the_excluded_zone_and_exists() -> None:
    for mandate, home in REGISTRY_PROGRAMME_ONLY.items():
        assert home.startswith(EXCLUDED_ZONE), (
            f"{mandate}: {home} is outside {EXCLUDED_ZONE} but is tiered programme-only; "
            "if it is governed it belongs a tier up"
        )
    assert_homes_exist("UAKP-REG", REGISTRY_PROGRAMME_ONLY)


def test_the_excluded_zone_really_is_excluded_from_registration() -> None:
    """NON-VACUITY. The split rests on 00-MASTER/ being registration-excluded. If that
    exclusion is lifted, ten registries change tier and this binding is wrong."""
    config = (repo_root() / "00-BOOK" / "tools" / "config.py").read_text(encoding="utf-8")
    assert "EXCLUDE_DIR_PREFIXES" in config
    assert f'"{EXCLUDED_ZONE}"' in config, (
        f"{EXCLUDED_ZONE} is no longer listed in EXCLUDE_DIR_PREFIXES; the governed / "
        "programme split this binding makes is no longer the right one"
    )


def test_the_band_scoped_registry_declares_an_execution_only_authority() -> None:
    """NON-VACUITY. The tier's whole claim is the `authority` field."""
    for mandate, (home, authority) in REGISTRY_BAND_SCOPED.items():
        path = repo_root() / home
        assert path.exists(), f"{mandate}: {home} does not exist"
        declared = json.loads(path.read_text(encoding="utf-8")).get("authority")
        assert declared == authority, (
            f"{mandate}: {home} declares authority {declared!r}, not {authority!r}; "
            "its tier was decided by that field and must be re-decided"
        )


def test_the_absent_registry_is_named_by_no_tracked_register_at_all() -> None:
    """NON-VACUITY over BOTH populations, searched in the TRACKED set: an untracked worktree
    copy is not Repository Truth, and an earlier draft of this test offered one as evidence
    of presence."""
    for mandate, label in REGISTRY_ABSENT.items():
        words = [w.lower() for w in label.split()]
        found = [
            path
            for path in tracked()
            if all(word in path.rsplit("/", 1)[-1].lower() for word in words)
        ]
        assert not found, f"{mandate}: {label} is declared absent but a register exists: {found}"


def test_the_naming_rules_these_bindings_rely_on_can_find_something() -> None:
    assert_absence_rule_can_find_something("knowledge ukip classification")


# ================================================================================
# UAKP-ENV — the twenty-six governed knowledge environments
# ================================================================================
#
# "ANY GOVERNED KNOWLEDGE ENVIRONMENT" heads a list of twenty-six -- Monorepo, Polyrepo,
# Wiki, Data Lake, Digital Twin, Future Unknown Environment -- and the document states the
# rule that governs them two paragraphs later: "The platform SHALL never directly depend
# upon a specific repository or storage. Every environment SHALL expose constitutional
# adapters."
#
# So an environment is not a construct. Building a `Monorepo` class would be precisely the
# repository-specific assumption UAKP-IND/ID-04 forbids, and building `Database` or `Cloud
# Environment` would seed a category the kernel refuses by name -- `database` and `cloud` are
# both PROHIBITED_TOKENS. A requirements sweep reads all twenty-six as missing and concludes
# they must be built, which is backwards for the same reason it was backwards for the target
# domains: the implementation of an environment is its ADMISSION.
#
# This matters beyond the section. `Monorepo` and `Polyrepo` are two of the seventeen
# concepts CAEM-001 disposition CREATE -- the only disposition that authorises new
# construction. They are not gaps. They are admissions, and building them would breach the
# document that mandates them.

ENVIRONMENT_PREFIX = "Env-"


def _environment_key(label: str) -> str:
    words = label.replace("-", " ").split()
    return ENVIRONMENT_PREFIX + "".join(word.capitalize() for word in words)


def test_every_governed_environment_is_admissible_with_the_kernel_unchanged() -> None:
    from engine.kernel.compliance import kernel_source_fingerprint
    from engine.kernel.kernel import MetaKernel

    labels = list(section("UAKP-ENV").values())
    assert len(labels) == 26, f"the document lists 26 environments, corpus has {len(labels)}"

    before_source = kernel_source_fingerprint()
    kernel = MetaKernel()
    before_count = len(kernel.metatypes())

    for label in labels:
        kernel.register_metatype(
            _environment_key(label), name=label, description=f"governed environment: {label}"
        )

    assert kernel_source_fingerprint() == before_source, (
        "admitting the environments changed the kernel's own source, so the platform now "
        "depends on specific repositories and storage -- what the adapter rule forbids"
    )
    registered = {obj.natural_key for obj in kernel.metatypes()}
    refused = sorted(
        _environment_key(label) for label in labels if _environment_key(label) not in registered
    )
    assert not refused, f"environments the kernel would not admit: {refused}"
    assert len(kernel.metatypes()) == before_count + len(labels)


def test_no_environment_is_seeded_into_the_kernel() -> None:
    """NON-VACUITY. Admission proves nothing if the environment was hard-coded all along."""
    from engine.kernel.seed import FOUNDING_METATYPES

    labels = {label.lower() for label in section("UAKP-ENV").values()}
    founding = {key.lower() for key, _name, _description in FOUNDING_METATYPES}
    leaked = sorted(labels & founding)
    assert not leaked, f"environments seeded as founding meta-types: {leaked}"


def test_the_storage_shaped_environments_are_names_the_kernel_refuses_to_seed() -> None:
    """The sharper half. Two environments name categories PROHIBITED_TOKENS exists to keep
    out of the kernel, and they are still admissible as registered data. That pair is the
    whole distinction between admitting an environment and assuming one."""
    from engine.kernel.compliance import PROHIBITED_TOKENS

    labels = {label.lower() for label in section("UAKP-ENV").values()}
    assert "database" in labels and "cloud environment" in labels
    assert "database" in PROHIBITED_TOKENS, (
        "`database` is no longer a prohibited token, so nothing stops a storage assumption "
        "being seeded and UAKP-IND/ID-07 is unbound"
    )
    assert (
        "cloud" in PROHIBITED_TOKENS
    ), "`cloud` is no longer a prohibited token, so UAKP-IND/ID-08 is unbound"


def test_the_two_environments_dispositioned_create_are_admissions_not_gaps() -> None:
    """Monorepo and Polyrepo are dispositioned CREATE by CAEM-001 -- new construction. The
    document that mandates them forbids exactly that, so the disposition is answered by
    admission and this test records which two it answers."""
    labels = {label.lower() for label in section("UAKP-ENV").values()}
    assert {"monorepo", "polyrepo"} <= labels

    from engine.kernel.compliance import kernel_source_fingerprint
    from engine.kernel.kernel import MetaKernel

    kernel = MetaKernel()
    before = kernel_source_fingerprint()
    for label in ("Monorepo", "Polyrepo"):
        kernel.register_metatype(_environment_key(label), name=label, description="admitted")
    assert kernel_source_fingerprint() == before
    registered = {obj.natural_key for obj in kernel.metatypes()}
    assert {_environment_key("Monorepo"), _environment_key("Polyrepo")} <= registered


def test_admission_is_open_beyond_the_twenty_six_that_were_listed() -> None:
    """EV2-26 is `Future Unknown Environment`, which is not an environment but the claim
    that the list can grow. Proven the way the object classes prove it: by admitting one the
    document never named."""
    from engine.kernel.compliance import kernel_source_fingerprint
    from engine.kernel.kernel import MetaKernel

    labels = list(section("UAKP-ENV").values())
    assert "Future Unknown Environment" in labels

    kernel = MetaKernel()
    for label in labels:
        kernel.register_metatype(_environment_key(label), name=label, description="admitted")

    before = kernel_source_fingerprint()
    unlisted = "Env-SubstrateNoDocumentHasNamedYet"
    kernel.register_metatype(unlisted, name="unlisted", description="admitted by registration")
    assert unlisted in {obj.natural_key for obj in kernel.metatypes()}, (
        "the kernel admits the twenty-six the document lists and refuses one it does not; "
        "that is a closed environment set, which the adapter rule forbids"
    )
    assert kernel_source_fingerprint() == before


# ================================================================================
# UAKP-PO — the twenty-four steps of the Primary Objective
# ================================================================================
#
# "Given ANY governed knowledge environment, the platform SHALL automatically:" and then
# twenty-four verbs, ending "Repeat continuously". Nothing new is mandated here -- the
# engine model two sections later names the machinery, and the objective names the OUTCOME
# each piece of machinery is for.
#
# That makes this binding a join rather than a fresh inventory, and it is written as one:
# every row resolves through `ENGINE_HOME`, `ENGINE_ABSENT` or `ENGINE_SPECIFIED_ONLY`
# above, so a step cannot be reported delivered while the engine that would deliver it is
# reported missing. Re-locating the same instruments here would be a second authoring of
# one finding, void under UCKP-ART-03, and would let the two drift apart silently.

#: Objective step -> the mandated engine that delivers it.
OBJECTIVE_ENGINE = {
    "UAKP-PO/PO-01": "UAKP-ENG/EN-07",  # Discover the environment
    "UAKP-PO/PO-03": "UAKP-ENG/EN-06",  # Discover structure
    "UAKP-PO/PO-06": "UAKP-ENG/EN-15",  # Discover dependencies
    "UAKP-PO/PO-07": "UAKP-ENG/EN-10",  # Discover canonical ownership
    "UAKP-PO/PO-08": "UAKP-ENG/EN-08",  # Discover evidence
    "UAKP-PO/PO-09": "UAKP-ENG/EN-09",  # Discover truth
    "UAKP-PO/PO-10": "UAKP-ENG/EN-13",  # Discover gaps
    "UAKP-PO/PO-11": "UAKP-ENG/EN-12",  # Discover conflicts
    "UAKP-PO/PO-13": "UAKP-ENG/EN-14",  # Generate requirements
    "UAKP-PO/PO-14": "UAKP-ENG/EN-18",  # Generate planning
    "UAKP-PO/PO-17": "UAKP-ENG/EN-21",  # Orchestrate realization
    "UAKP-PO/PO-18": "UAKP-ENG/EN-24",  # Validate
    "UAKP-PO/PO-19": "UAKP-ENG/EN-25",  # Verify
    "UAKP-PO/PO-20": "UAKP-ENG/EN-26",  # Certify
    "UAKP-PO/PO-21": "UAKP-ENG/EN-02",  # Update canonical knowledge
    "UAKP-PO/PO-23": "UAKP-ENG/EN-31",  # Improve itself
}

#: Objective step -> an instrument that is not one of the mandated engines. Three steps the
#: engine model does not name and the repository performs anyway.
OBJECTIVE_INSTRUMENT = {
    "UAKP-PO/PO-04": "engine/uckp/alignment.py",  # Discover governance
    "UAKP-PO/PO-05": "engine/uckp/graph.py",  # Discover relationships
    "UAKP-PO/PO-24": "00-MASTER/UCOS-RFP-001/rfp_engine.py",  # Repeat continuously
}

#: Steps nothing performs. Four of the five are the engine model's own gaps read back as
#: outcomes, which is what makes those gaps legible: "Knowledge Acquisition Engine is
#: absent" and "the platform cannot discover knowledge" are the same finding, and only the
#: second states what is lost.
OBJECTIVE_UNDELIVERED = {
    "UAKP-PO/PO-02": "UAKP-ENG/EN-01",  # Discover knowledge
    "UAKP-PO/PO-12": "",  # Discover opportunities -- no engine is even mandated for it
    "UAKP-PO/PO-15": "UAKP-ENG/EN-20",  # Generate realization packages
    "UAKP-PO/PO-16": "UAKP-ENG/EN-19",  # Generate execution specifications
    "UAKP-PO/PO-22": "UAKP-ENG/EN-28",  # Learn
}


def test_every_objective_step_is_delivered_by_an_engine_an_instrument_or_nothing() -> None:
    mandates = section("UAKP-PO")
    assert len(mandates) == 24, f"the objective states 24 steps, corpus has {len(mandates)}"
    assert_partitions(
        "UAKP-PO",
        mandates,
        OBJECTIVE_ENGINE,
        OBJECTIVE_INSTRUMENT,
        OBJECTIVE_UNDELIVERED,
    )


def test_every_engine_backed_step_resolves_to_an_engine_this_suite_located() -> None:
    """The join. A step delivered by an engine that is not in ENGINE_HOME would be a claim
    this suite has already contradicted twenty lines above."""
    for mandate, engine in OBJECTIVE_ENGINE.items():
        assert engine in ENGINE_HOME, (
            f"{mandate}: {engine} is not a located engine; the step cannot be delivered by "
            "machinery this suite reports missing"
        )


def test_no_engine_delivers_two_objective_steps() -> None:
    """NON-VACUITY. Twenty-four steps and thirty-one engines, so a one-to-one join is
    available; two steps on one engine would mean one of them is unaccounted for."""
    claimed = list(OBJECTIVE_ENGINE.values())
    duplicated = sorted({e for e in claimed if claimed.count(e) > 1})
    assert not duplicated, f"engines claimed by more than one objective step: {duplicated}"


def test_every_instrument_backed_step_is_tracked_and_is_not_a_mandated_engine() -> None:
    """The tier boundary. An instrument that IS a mandated engine belongs in the join."""
    assert_homes_exist("UAKP-PO", OBJECTIVE_INSTRUMENT)
    located = set(ENGINE_HOME.values())
    for mandate, home in OBJECTIVE_INSTRUMENT.items():
        assert home not in located, (
            f"{mandate}: {home} is a located mandated engine and is understated as a "
            "loose instrument"
        )


def test_every_undelivered_step_names_an_engine_this_suite_reports_missing() -> None:
    """NON-VACUITY, and the half that makes the gaps legible.

    Four of the five point at an engine, and each is required to be in the absent or
    specified-only tier -- so a step cannot be written off while its engine is reported
    working. The fifth points at nothing because the engine model mandates no engine for
    `Discover opportunities` at all, which is a gap in the mandate rather than in the code.
    """
    unbuilt = set(ENGINE_ABSENT) | set(ENGINE_SPECIFIED_ONLY)
    for mandate, engine in OBJECTIVE_UNDELIVERED.items():
        if not engine:
            continue
        assert engine in unbuilt, (
            f"{mandate}: {engine} is no longer reported missing, so this step is delivered "
            "and must move out of the undelivered tier"
        )
    assert sum(1 for engine in OBJECTIVE_UNDELIVERED.values() if not engine) == 1


def test_discover_opportunities_is_mandated_by_no_engine_at_all() -> None:
    """NON-VACUITY for the one step with no engine behind it. If the engine model ever names
    one, this row stops being a hole in the mandate and becomes a hole in the code."""
    engines = {label.lower() for label in section("UAKP-ENG").values()}
    assert not any(
        "opportunit" in label for label in engines
    ), "an opportunity engine is now mandated; UAKP-PO/PO-12 must point at it"
    steps = section("UAKP-PO")
    assert steps["UAKP-PO/PO-12"] == "Discover opportunities"


# ================================================================================
# UAKP-PRIN — the thirty-two architectural principles
# ================================================================================
#
# Thirty-two principles, mostly of the form "X before Y" or "Everything X". Seven of them
# assert an ABSENCE and are bound in `engine/tests/kernel/test_compliance.py`, against the
# kernel that can decide a negative; the twenty-five below are the rest.
#
# THE TIERS ARE THE POINT, AND THEY COME FROM THIS REPOSITORY'S OWN DIAGNOSIS. adr/0021
# stated a principle and disclosed in its own Consequences that nothing enforced it, and
# adr/0041 named the shape: "a rule that is right, with a measurement that does not reach
# where it applies." A principle enforced by a GATE is refused when violated. A principle
# STATED by an article is law with no measurement. Reporting both as satisfied reproduces
# exactly the defect the repository has already caught itself in twice.

#: Principle -> a quality gate that refuses its violation.
PRINCIPLE_GATE = {
    "UAKP-PRIN/PN-24": "no-closed-registries",  # Everything discoverable
    "UAKP-PRIN/PN-27": "unknown-future-compatibility",  # Everything extensible
    "UAKP-PRIN/PN-31": "no-finite-enumeration",  # Infinite extensibility
    "UAKP-PRIN/PN-02": "no-domain-provider-technology-earth-civilization-coupling",  # Concepts
    "UAKP-PRIN/PN-06": "no-implementation-leakage",  # Truth before implementation
}

#: Principle -> the article of the root law that states it. Law without a gate.
PRINCIPLE_ARTICLE = {
    "UAKP-PRIN/PN-01": "UCKP-ART-02",  # Constitution before implementation
    "UAKP-PRIN/PN-04": "UCKP-ART-11",  # Objects before documents
    "UAKP-PRIN/PN-05": "UCKP-ART-07",  # Graphs before hierarchies
    "UAKP-PRIN/PN-13": "UCKP-ART-18",  # Reuse before duplication
    "UAKP-PRIN/PN-14": "UCKP-ART-09",  # Replaceability before coupling
    "UAKP-PRIN/PN-15": "UCKP-ART-14",  # Evolution before stagnation
    "UAKP-PRIN/PN-17": "UCKP-ART-03",  # Knowledge once reuse everywhere
    "UAKP-PRIN/PN-25": "UCKP-ART-16",  # Everything governable
    "UAKP-PRIN/PN-28": "UCKP-ART-04",  # Everything replaceable
    "UAKP-PRIN/PN-29": "UCKP-ART-14",  # Everything evolvable
}

#: Principle -> an instrument that performs it without stating it as law.
PRINCIPLE_INSTRUMENT = {
    "UAKP-PRIN/PN-07": "00-BOOK/DATA/evidence-universe.json",  # Evidence before truth
    "UAKP-PRIN/PN-08": "engine/constitution/gateway.py",  # Governance before automation
    "UAKP-PRIN/PN-09": "engine/universal_discovery",  # Discovery before configuration
    "UAKP-PRIN/PN-16": "engine/constitution/gateway.py",  # Autonomy under governance
    "UAKP-PRIN/PN-26": "engine/knowledge/integration/composition.py",  # Everything composable
    "UAKP-PRIN/PN-30": "engine/infinite_scope",  # Infinite scalability
}

#: Stated by no article, refused by no gate, performed by no instrument. Four orderings the
#: repository asserts nowhere: the priority of universes over engines, of capabilities over
#: projects, of composition over specialization, and of configuration over customization --
#: which is one of the seventeen concepts dispositioned CREATE and stays one.
PRINCIPLE_UNENFORCED = {
    "UAKP-PRIN/PN-03": "universes before engines",
    "UAKP-PRIN/PN-10": "composition before specialization",
    "UAKP-PRIN/PN-11": "configuration before customization",
    "UAKP-PRIN/PN-12": "capabilities before projects",
}


def test_every_architectural_principle_is_gated_stated_performed_or_unenforced() -> None:
    mandates = section("UAKP-PRIN")
    assert len(mandates) == 32, f"the document lists 32 principles, corpus has {len(mandates)}"

    negative = {
        "UAKP-PRIN/PN-18",
        "UAKP-PRIN/PN-19",
        "UAKP-PRIN/PN-20",
        "UAKP-PRIN/PN-21",
        "UAKP-PRIN/PN-22",
        "UAKP-PRIN/PN-23",
        "UAKP-PRIN/PN-32",
    }
    assert negative <= set(mandates)
    positive = {k: v for k, v in mandates.items() if k not in negative}
    assert len(positive) == 25

    assert_partitions(
        "UAKP-PRIN",
        positive,
        PRINCIPLE_GATE,
        PRINCIPLE_ARTICLE,
        PRINCIPLE_INSTRUMENT,
        PRINCIPLE_UNENFORCED,
    )


def test_the_negative_principles_are_bound_elsewhere_and_not_restated_here() -> None:
    """Seven principles assert an absence. Corpus search cannot decide a negative and this
    suite does not try; the kernel suite binds them to a token it refuses to seed or a gate
    that passes. Asserted so the claim cannot go missing by being nobody's."""
    from engine.tests.kernel.test_compliance import (
        BOUND_TO_GATE,
        BOUND_TO_PROHIBITED_TOKEN,
        UNCOVERED,
    )

    accounted = set(BOUND_TO_PROHIBITED_TOKEN) | set(BOUND_TO_GATE) | set(UNCOVERED)
    for mandate in ("UAKP-PRIN/PN-20", "UAKP-PRIN/PN-22", "UAKP-PRIN/PN-32"):
        assert mandate in accounted, f"{mandate} is no longer accounted for by the kernel suite"


def test_every_gated_principle_names_a_gate_that_exists_and_passes() -> None:
    from engine.kernel.compliance import quality_gates

    gates = {gate["id"]: gate for gate in quality_gates()["gates"]}
    for mandate, gate_id in PRINCIPLE_GATE.items():
        assert gate_id in gates, f"{mandate}: no gate named {gate_id!r}"
        assert gates[gate_id]["passed"] is True, f"{mandate}: gate {gate_id!r} fails"


def test_every_stated_principle_names_an_article_that_exists() -> None:
    from engine.uckp.law import ROOT_LAW

    articles = {article.article_id for article in ROOT_LAW.articles}
    for mandate, article_id in PRINCIPLE_ARTICLE.items():
        assert article_id in articles, f"{mandate}: {article_id} is not an article of the root law"


def test_a_stated_principle_is_never_also_a_gated_one() -> None:
    """The tier boundary, and the whole diagnosis. A principle with a gate is enforced; one
    with only an article is the adr/0021 shape -- right, and unmeasured. Listing a principle
    in both tiers would hide which of the two it actually is."""
    assert not (set(PRINCIPLE_GATE) & set(PRINCIPLE_ARTICLE))
    assert not (set(PRINCIPLE_GATE) & set(PRINCIPLE_INSTRUMENT))
    assert len(PRINCIPLE_ARTICLE) > len(PRINCIPLE_GATE), (
        "more principles are gated than merely stated, which would be a better repository "
        "than this measurement found; re-check the tiers before believing it"
    )


def test_every_performing_instrument_is_tracked() -> None:
    assert_homes_exist("UAKP-PRIN", PRINCIPLE_INSTRUMENT)


def test_the_unenforced_principles_are_named_by_no_gate_and_no_article() -> None:
    """NON-VACUITY. Each unenforced principle is searched against both populations by its
    distinctive noun, so a gate or article that does cover one cannot be missed."""
    from engine.kernel.compliance import quality_gates
    from engine.uckp.law import ROOT_LAW

    gate_ids = " ".join(gate["id"] for gate in quality_gates()["gates"]).lower()
    law_text = " ".join(f"{a.title} {a.clause}" for a in ROOT_LAW.articles).lower()
    for mandate, principle in PRINCIPLE_UNENFORCED.items():
        noun = principle.split()[0]
        assert noun not in gate_ids, f"{mandate}: a gate now names {noun!r}"
        pair = principle.replace(" before ", " ")
        assert pair not in law_text, f"{mandate}: the law now states {principle!r}"


def test_configuration_before_customization_stays_a_genuine_gap() -> None:
    """One of the seventeen CREATE concepts. Unlike Monorepo and Polyrepo, nothing in the
    mandate forbids building it -- the repository simply has no notion of customization to
    order configuration against, which is why it is unenforced rather than admitted."""
    assert "UAKP-PRIN/PN-11" in PRINCIPLE_UNENFORCED
    assert not [p for p in tracked() if "customization" in p.lower()], (
        "a customization instrument now exists; PN-11 can be ordered against it and is no "
        "longer a gap"
    )
