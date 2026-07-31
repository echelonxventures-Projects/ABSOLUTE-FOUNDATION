"""UCKP Layer Zero — the Universal Evolution Model (Article 14).

Evolution observes, learns, reasons, simulates, analyses impact and dependencies,
resolves authority, implements, validates, verifies, replays, certifies, transitions
and assimilates — and then begins again. Article 14 adds three constraints that shape
the whole module: it appends, it never rewrites, and it never terminates.

"Never terminates" is easy to write and easy to violate, so it is encoded rather than
promised. :func:`next_stage` wraps from the last stage back to the first, so there is no
stage from which nothing follows, and :meth:`EvolutionLedger.is_terminated` is a method
that always returns ``False`` because there is no state it could return ``True`` from.
An evolution model with a terminal stage would eventually stop, and a constitution that
stops evolving becomes a description of the past.

"Never rewrites" is enforced by :meth:`EvolutionLedger.append`, which admits only the
stage the cycle says comes next. A caller cannot skip validation to reach certification,
because skipping is exactly how an unproven claim acquires a certificate.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

from engine.uckp.canonical import content_hash
from engine.uckp.errors import EvolutionError


class EvolutionStage(str, Enum):
    """The fifteen stages of the perpetual constitutional cycle."""

    OBSERVE = "observe"
    LEARN = "learn"
    REASON = "reason"
    SIMULATE = "simulate"
    IMPACT_ANALYSIS = "impact-analysis"
    DEPENDENCY_ANALYSIS = "dependency-analysis"
    AUTHORITY_RESOLUTION = "authority-resolution"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    VERIFICATION = "verification"
    REPLAY = "replay"
    CERTIFICATION = "certification"
    STATE_TRANSITION = "state-transition"
    KNOWLEDGE_ASSIMILATION = "knowledge-assimilation"
    CONTINUATION = "continuation"

    @classmethod
    def coerce(cls, value: object) -> EvolutionStage:
        if isinstance(value, cls):
            return value
        text = str(value).strip().lower()
        for member in cls:
            if member.value == text:
                return member
        raise EvolutionError("unknown evolution stage", stage=str(value))


#: The cycle, in order. Derived from the enum so the two can never disagree.
EVOLUTION_CYCLE: tuple[EvolutionStage, ...] = tuple(EvolutionStage)

#: How many stages one full cycle contains.
CYCLE_LENGTH = len(EVOLUTION_CYCLE)


def next_stage(stage: EvolutionStage | str) -> EvolutionStage:
    """The stage that follows ``stage``, wrapping forever (Article 14)."""
    current = EvolutionStage.coerce(stage)
    index = EVOLUTION_CYCLE.index(current)
    return EVOLUTION_CYCLE[(index + 1) % CYCLE_LENGTH]


def is_terminal(stage: EvolutionStage | str) -> bool:
    """Always false. No stage of a perpetual cycle is terminal."""
    EvolutionStage.coerce(stage)
    return False


@dataclass(frozen=True, slots=True)
class EvolutionRecord:
    """One appended step of the perpetual cycle."""

    cycle: int
    stage: EvolutionStage
    subject: str
    outcome: str
    digest: str
    findings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "cycle": self.cycle,
            "stage": self.stage.value,
            "subject": self.subject,
            "outcome": self.outcome,
            "digest": self.digest,
            "findings": list(self.findings),
        }

    @classmethod
    def from_dict(cls, data: object) -> EvolutionRecord:
        record = data if isinstance(data, dict) else {}
        return cls(
            cycle=int(record.get("cycle", 0)),
            stage=EvolutionStage.coerce(record.get("stage")),
            subject=str(record.get("subject", "")),
            outcome=str(record.get("outcome", "")),
            digest=str(record.get("digest", "")),
            findings=tuple(str(item) for item in record.get("findings") or ()),
        )


class EvolutionLedger:
    """The append-only record of constitutional evolution."""

    __slots__ = ("_records",)

    def __init__(self, records: Iterable[EvolutionRecord] = ()) -> None:
        self._records: list[EvolutionRecord] = []
        for record in records:
            self.append(record)

    def append(self, record: EvolutionRecord) -> EvolutionRecord:
        """Append the next lawful stage. Skipping and rewriting are both refused."""
        if not self._records:
            if record.stage is not EVOLUTION_CYCLE[0] or record.cycle != 0:
                raise EvolutionError(
                    "evolution must begin at the first stage of cycle zero",
                    stage=record.stage.value,
                    cycle=record.cycle,
                )
            self._records.append(record)
            return record
        previous = self._records[-1]
        expected_stage = next_stage(previous.stage)
        wrapped = expected_stage is EVOLUTION_CYCLE[0]
        expected_cycle = previous.cycle + 1 if wrapped else previous.cycle
        if record.stage is not expected_stage:
            raise EvolutionError(
                "evolution stages may not be skipped or reordered",
                expected=expected_stage.value,
                declared=record.stage.value,
            )
        if record.cycle != expected_cycle:
            raise EvolutionError(
                "evolution cycle must advance exactly once per full cycle",
                expected=expected_cycle,
                declared=record.cycle,
            )
        self._records.append(record)
        return record

    def extend(self, records: Iterable[EvolutionRecord]) -> tuple[EvolutionRecord, ...]:
        return tuple(self.append(record) for record in records)

    def records(self) -> tuple[EvolutionRecord, ...]:
        return tuple(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def current_stage(self) -> EvolutionStage | None:
        return self._records[-1].stage if self._records else None

    def expected_stage(self) -> EvolutionStage:
        """The stage the ledger will accept next. Always defined (Article 14)."""
        if not self._records:
            return EVOLUTION_CYCLE[0]
        return next_stage(self._records[-1].stage)

    def cycles(self) -> int:
        return (self._records[-1].cycle + 1) if self._records else 0

    def completed_cycles(self) -> int:
        """Cycles that reached the final stage — the ones with a state transition."""
        return sum(1 for record in self._records if record.stage is EVOLUTION_CYCLE[-1])

    def is_terminated(self) -> bool:
        """Always false. There is no ledger state from which nothing may follow."""
        return False

    def stage_records(self, stage: EvolutionStage | str) -> tuple[EvolutionRecord, ...]:
        resolved = EvolutionStage.coerce(stage)
        return tuple(record for record in self._records if record.stage is resolved)

    def findings(self) -> tuple[str, ...]:
        return tuple(finding for record in self._records for finding in record.findings)

    def to_document(self) -> dict[str, object]:
        return {
            "schema": "ucos-uckp-evolution-ledger",
            "version": "1.0.0",
            "counts": {
                "records": len(self._records),
                "cycles": self.cycles(),
                "completed_cycles": self.completed_cycles(),
                "findings": len(self.findings()),
            },
            "cycle_definition": [stage.value for stage in EVOLUTION_CYCLE],
            "expected_stage": self.expected_stage().value,
            "terminated": self.is_terminated(),
            "records": [record.to_dict() for record in self._records],
        }

    def fingerprint(self) -> str:
        return content_hash([record.to_dict() for record in self._records])


__all__ = [
    "CYCLE_LENGTH",
    "EVOLUTION_CYCLE",
    "EvolutionLedger",
    "EvolutionRecord",
    "EvolutionStage",
    "is_terminal",
    "next_stage",
]
