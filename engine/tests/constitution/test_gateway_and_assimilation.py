"""UCOS-CMG/RTAG — every stage of the mutation pipeline is driven into its refusal.

The pipeline's value is entirely in what it stops, so a test suite that only shows a
lawful mutation applying would prove nothing. Each of the seven stages is failed here in
isolation, and the refusal is asserted to name *that* stage — a mutation refused at
``proposal`` when it should have been refused at ``registration`` would mean the pipeline
is not actually checking what it claims to.
"""

from __future__ import annotations

import pytest

from engine.constitution import assimilation, catalog, gateway, metadata
from engine.constitution.errors import DuplicateTruth, MutationRefused
from engine.constitution.metadata import Population
from engine.tests.constitution.conftest import declare, population


def _mutation(*records: metadata.ConstitutionalMetadata, **kwargs: str) -> gateway.Mutation:
    return gateway.Mutation(
        records=records,
        authority=kwargs.get("authority", "ext:UCOS-AUTHORITY-TEST"),
        reason=kwargs.get("reason", "test"),
    )


# --------------------------------------------------------------------------- assimilation


def test_creation_is_permitted_only_where_nothing_canonical_exists(lawful: Population) -> None:
    verdict = assimilation.require_creatable(
        assimilation.Proposal(subject="fresh", owner="ext:o", outputs=("fresh-thing",)), lawful
    )
    assert verdict.creatable
    assert verdict.status == "CREATE"
    assert set(verdict.gap()) == {s.name for s in assimilation.SEARCHES}


@pytest.mark.parametrize(
    ("proposal", "search"),
    [
        (assimilation.Proposal(subject="root"), "artifact"),
        (assimilation.Proposal(subject="new", outputs=("root-output",)), "capability"),
    ],
)
def test_each_canonical_search_refuses_creation(
    lawful: Population, proposal: assimilation.Proposal, search: str
) -> None:
    verdict = assimilation.assimilate(proposal, lawful)
    assert not verdict.creatable
    assert search in {i.search for i in verdict.incumbents}
    assert "root" in verdict.reuse_targets
    with pytest.raises(DuplicateTruth) as excinfo:
        assimilation.require_creatable(proposal, lawful)
    assert excinfo.value.detail["clause"] == "CEL-08"


def test_the_owner_search_refuses_duplication_but_not_growth() -> None:
    """A nucleus owning many capabilities is expected; owning one twice is not."""
    pop = population(declare("held", canonical_owner=("ext:owner",), outputs=("thing",)))
    growth = assimilation.Proposal(subject="new", owner="ext:owner", outputs=("other-thing",))
    duplicate = assimilation.Proposal(subject="new", owner="ext:owner", outputs=("thing",))
    assert assimilation.assimilate(growth, pop).creatable
    assert not assimilation.assimilate(duplicate, pop).creatable


def test_duplicate_capabilities_are_measurable_across_a_population() -> None:
    pop = population(
        declare("a", outputs=("shared",)),
        declare("b", outputs=("shared",)),
    )
    assert assimilation.duplicate_capabilities(pop) == {"shared": ("a", "b")}


def test_a_proposal_can_be_read_out_of_a_declaration() -> None:
    record = declare("x", outputs=("out",), inputs=("in",))
    proposal = assimilation.proposal_for(record)
    assert proposal.subject == "x"
    assert proposal.outputs == ("out",)


# --------------------------------------------------------------------------- gateway


def test_the_pipeline_order_is_derived_from_the_declared_chain() -> None:
    assert gateway.pipeline_order() == (
        "proposal",
        "evidence",
        "validation",
        "verification",
        "certification",
        "registration",
        "truth_update",
    )


def test_a_lawful_mutation_applies_and_yields_a_committed_seal(lawful: Population) -> None:
    grown, record = gateway.apply(lawful, _mutation(declare("newcomer", dependencies=("root",))))
    assert record.applied
    assert record.status == "APPLIED"
    assert record.chain_is_intact()
    assert len(record.outcomes) == len(gateway.PIPELINE)
    assert record.seal is not None and record.seal.committed
    assert record.replay is not None and record.replay.fixed_point
    assert "newcomer" in grown
    assert "newcomer" not in lawful  # the base population is untouched


def test_an_amendment_supersedes_rather_than_duplicating(lawful: Population) -> None:
    """The artifact search must not make correcting a subject impossible."""
    amended = declare("leaf", dependencies=("root",), constraints=("amended",))
    grown, record = gateway.apply(lawful, _mutation(amended))
    assert record.applied
    assert grown.get("leaf").entries("constraints") == ("amended",)
    assert len(grown) == len(lawful)


def _unmintable() -> metadata.ConstitutionalMetadata:
    """A record that is completely declared but carries an identifier nobody could mint."""
    good = declare("registered")
    return metadata.ConstitutionalMetadata(
        subject="registered", universal_id="not-an-id", facets=good.facets
    )


@pytest.mark.parametrize(
    ("record_factory", "stage"),
    [
        (lambda: metadata.ConstitutionalMetadata.declare("bare", universal_id=""), "proposal"),
        (lambda: declare("dup", outputs=("root-output",)), "evidence"),
        (lambda: declare("dangling", dependencies=("ghost",)), "validation"),
        (lambda: declare("selfie", certifications=("selfie",)), "validation"),
        (_unmintable, "verification"),
    ],
)
def test_each_stage_refuses_what_it_owns(lawful: Population, record_factory, stage: str) -> None:
    record = gateway.propose(lawful, _mutation(record_factory()))
    assert not record.applied
    assert record.refused_at == stage
    with pytest.raises(MutationRefused) as excinfo:
        gateway.apply(lawful, _mutation(record_factory()))
    assert excinfo.value.detail["refused_at"] == stage
    assert excinfo.value.detail["clause"] == "CEL-04"


def test_the_pipeline_stops_at_the_first_refusal(lawful: Population) -> None:
    """A stage after a failed one would be judging a state that will never exist."""
    record = gateway.propose(lawful, _mutation(declare("dangling", dependencies=("ghost",))))
    assert [o.name for o in record.outcomes] == ["proposal", "evidence", "validation"]
    assert record.chain_is_intact()


def test_the_registration_stage_is_a_second_defence(lawful: Population) -> None:
    """Reachable only directly — and that is the point.

    ``verification`` proves identity as one of its nine obligations, so a malformed
    identifier never survives to ``registration`` through the pipeline. That does not make
    the stage redundant: it is the same second-defence discipline as
    :mod:`engine.nucleus.ownership`, which measures a population that arrived by some path
    the constructor never saw. A stage whose refusal branch has never executed is a stage
    nobody has checked, so it is forced here.
    """
    stage = next(s for s in gateway.PIPELINE if s.name == "registration")
    base = lawful

    unmintable = _unmintable()
    satisfied, detail = stage.run(
        gateway.Context(
            base=base,
            candidate=base.with_records([unmintable]),
            mutation=_mutation(unmintable),
        )
    )
    assert not satisfied
    assert "identity authority could mint" in detail

    unregistered = declare("unregistered")
    stripped = metadata.ConstitutionalMetadata(
        subject="unregistered",
        universal_id=unregistered.universal_id,
        facets={**dict(unregistered.facets), "registrations": ()},
    )
    satisfied, detail = stage.run(
        gateway.Context(
            base=base,
            candidate=base.with_records([stripped]),
            mutation=_mutation(stripped),
        )
    )
    assert not satisfied
    assert "names no registry" in detail


def test_a_mutation_with_no_authority_is_refused(lawful: Population) -> None:
    record = gateway.propose(lawful, gateway.Mutation(records=(declare("x"),), authority=""))
    assert record.refused_at == "proposal"
    assert "authority" in record.outcomes[0].detail


def test_an_empty_mutation_is_refused(lawful: Population) -> None:
    record = gateway.propose(lawful, gateway.Mutation(records=(), authority="ext:a"))
    assert record.refused_at == "proposal"


def test_a_refused_mutation_leaves_repository_truth_untouched(lawful: Population) -> None:
    before = lawful.digest()
    record = gateway.propose(lawful, _mutation(declare("selfie", certifications=("selfie",))))
    assert not record.applied
    assert record.population.digest() == before
    assert record.population is lawful


def test_the_journal_is_tamper_evident(lawful: Population) -> None:
    record = gateway.propose(lawful, _mutation(declare("newcomer")))
    assert record.chain_is_intact()
    forged = gateway.MutationRecord(
        gateway_id=record.gateway_id,
        mutation=record.mutation,
        outcomes=(
            gateway.StageOutcome(
                name=record.outcomes[0].name,
                satisfied=record.outcomes[0].satisfied,
                statement=record.outcomes[0].statement,
                detail="edited after the fact",
                prev_hash=record.outcomes[0].prev_hash,
                entry_hash=record.outcomes[0].entry_hash,
            ),
        ),
        order=record.order,
        applied=record.applied,
        population=record.population,
    )
    assert not forged.chain_is_intact()


def test_the_gateway_is_the_only_producer_of_a_clean_seal_over_a_new_state() -> None:
    """A hand-assembled population has no seal, so it can do none of the guarded acts."""
    from engine.constitution import state

    base = catalog.build_population()
    smuggled = base.with_records([declare("smuggled")])
    seal = state.commit(base)
    with pytest.raises(Exception) as excinfo:
        state.guard(seal, smuggled, act="register")
    assert "moved since it was sealed" in str(excinfo.value)
