"""UCOS-NUC-001 — the one-command surface of the Nucleus Ownership Authority.

Every subcommand emits canonical JSON on stdout and nothing else, so its output is
evidence: byte-identical across machines and runs, and directly diffable. Exit code 0 means
the constitutional condition held; 1 means it did not. The CLI writes no file — a
determination is materialised by the authority that owns the truth it would enter.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Any

from engine.context.location import build_frame_registry
from engine.context.location import to_document as location_document
from engine.context.location_assurance import (
    certify_location,
    replay_location,
    validate_location,
)
from engine.nucleus import catalog, certification, context, law, lifecycle, lineage, ownership
from engine.nucleus.errors import NucleusError
from engine.nucleus.evolution import EvolutionLedger, state_must_grow
from engine.nucleus.registry import build_seed_registry
from engine.registry.universal.dictionary import dictionary_for


def _emit(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def _cmd_law(_args: argparse.Namespace) -> int:
    document = law.to_document()
    document["digest"] = law.digest()
    _emit(document)
    return 0


def _cmd_catalog(_args: argparse.Namespace) -> int:
    _emit(catalog.to_document())
    return 0


def _cmd_registry(_args: argparse.Namespace) -> int:
    registry = build_seed_registry()
    document = registry.to_document()
    document["digest"] = registry.digest()
    _emit(document)
    return 0


def _cmd_gate(_args: argparse.Namespace) -> int:
    report = ownership.enforce(build_seed_registry())
    payload = report.to_dict()
    payload["digest"] = report.digest()
    _emit(payload)
    return 0 if report.passed else 1


def _cmd_compose(args: argparse.Namespace) -> int:
    registry = build_seed_registry()
    if args.composition:
        _emit(registry.compose(args.composition))
        return 0
    _emit(
        {
            "schema": "ucos-composition-index",
            "compositions": [registry.compose(c.key) for c in registry.compositions()],
            "count": len(registry.compositions()),
        }
    )
    return 0


def _cmd_order(_args: argparse.Namespace) -> int:
    registry = build_seed_registry()
    _emit(
        {
            "schema": "ucos-composition-order",
            "order": [{"wave": w, "subject": k} for w, k in registry.composition_order()],
            "cycles": list(registry.selection_cycles()),
        }
    )
    return 0


def _cmd_lifecycle(args: argparse.Namespace) -> int:
    if args.subject:
        execution = lifecycle.execute(args.subject)
        payload = execution.to_dict()
        payload["digest"] = execution.digest()
        payload["replay"] = lifecycle.replay(args.subject)
        _emit(payload)
        return 0 if execution.complete else 1
    document = lifecycle.to_document()
    document["digest"] = lifecycle.digest()
    _emit(document)
    return 0


def _cmd_lineage(_args: argparse.Namespace) -> int:
    registry = build_seed_registry()
    ledger = lineage.ledger_for(registry)
    payload = ledger.to_document()
    payload["digest"] = ledger.digest()
    payload["unrecorded"] = list(ledger.unrecorded(s.universal_id for s in registry.subjects()))
    _emit(payload)
    return 0 if ledger.is_intact() and not payload["unrecorded"] else 1


def _cmd_dictionary(args: argparse.Namespace) -> int:
    registry = build_seed_registry()
    dictionary = (
        context.dictionary_with_context(registry) if args.with_context else dictionary_for(registry)
    )
    payload = dictionary.to_document()
    payload["verification"] = dictionary.verify()
    payload["digest"] = dictionary.digest()
    _emit(payload)
    return 0 if dictionary.is_verified else 1


def _cmd_validate(args: argparse.Namespace) -> int:
    registry = build_seed_registry()
    report = certification.validate(registry, frame_key=args.frame or None)
    payload = report.to_dict()
    payload["digest"] = report.digest()
    _emit(payload)
    return 0 if report.passed else 1


def _cmd_certify(args: argparse.Namespace) -> int:
    registry = build_seed_registry()
    try:
        certificate = certification.certify(registry, frame_key=args.frame or None)
    except NucleusError as exc:
        _emit(exc.to_dict())
        return 1
    payload = certificate.to_dict()
    payload["digest"] = certificate.digest()
    _emit(payload)
    return 0


def _cmd_evolve(args: argparse.Namespace) -> int:
    registry = build_seed_registry()
    ledger = lineage.ledger_for(registry)
    evolution = EvolutionLedger(lineage=ledger, validator=state_must_grow)
    resolution = build_frame_registry().resolve(args.frame) if args.frame else None
    subjects = registry.nuclei() if not args.subject else (registry.subject(args.subject),)
    for index, subject in enumerate(subjects, start=1):
        if resolution is None:
            evolution.evolve(
                subject_id=subject.universal_id,
                subject_key=subject.key,
                change="stage-0-baseline",
                authority=law.LAW_ID,
                state={"capability": index},
            )
        else:
            context.evolve_in_context(
                evolution,
                resolution,
                subject_id=subject.universal_id,
                subject_key=subject.key,
                change="stage-0-baseline",
                authority=law.LAW_ID,
                state={"capability": index},
            )
    payload = evolution.to_document()
    payload["digest"] = evolution.digest()
    _emit(payload)
    return 0 if not evolution.unevidenced() else 1


def _cmd_context(args: argparse.Namespace) -> int:
    frames = build_frame_registry()
    if args.frame:
        resolution = frames.resolve(args.frame)
        payload = resolution.to_dict()
        payload["digest"] = resolution.digest()
        _emit(payload)
        return 0 if resolution.complete else 1
    _emit(location_document(frames))
    return 0


def _cmd_rebase(args: argparse.Namespace) -> int:
    frames = build_frame_registry()
    report = frames.rebase(args.subject, frame_keys=args.frames)
    _emit(report)
    return 0 if report["differing_count"] else 1


def _cmd_context_validate(_args: argparse.Namespace) -> int:
    report = validate_location()
    payload = report.to_dict()
    payload["digest"] = report.content_hash
    _emit(payload)
    return 0 if report.is_valid else 1


def _cmd_context_certify(_args: argparse.Namespace) -> int:
    certificate = certify_location()
    _emit(certificate.to_dict())
    return 0 if certificate.certified else 1


def _cmd_replay(args: argparse.Namespace) -> int:
    """The whole system's fixed point: context, lifecycle and certification together.

    Three independent replays, one verdict. A drift in any of them is a constitutional
    failure, because a system that cannot reproduce its own state cannot be certified to
    be in one.
    """
    registry = build_seed_registry()
    frames = build_frame_registry()
    frame_key = args.frame or None
    resolution = frames.resolve(frame_key) if frame_key else None
    stage_function = context.context_stage_function(resolution) if resolution else None

    subjects = [n.universal_id for n in registry.nuclei()]
    lifecycle_runs = [
        lifecycle.replay(subject)
        if stage_function is None
        else lifecycle.replay(subject, stage_function=stage_function)
        for subject in subjects
    ]
    location = replay_location(frames)
    first = certification.certify(registry, frame_key=frame_key)
    second = certification.certify(registry, frame_key=frame_key)

    drifted_lifecycles = [
        subject
        for subject, run in zip(subjects, lifecycle_runs, strict=True)
        if not run["fixed_point"]
    ]
    payload = {
        "schema": "ucos-constitutional-replay",
        "version": "1.0.0",
        "frame": frame_key or "",
        "lifecycle": {
            "subjects": len(subjects),
            "drifted": drifted_lifecycles,
            "fixed_point": not drifted_lifecycles,
        },
        "location": location,
        "certification": {
            "first": first.digest(),
            "second": second.digest(),
            "fixed_point": first.digest() == second.digest(),
        },
    }
    payload["fixed_point"] = (
        payload["lifecycle"]["fixed_point"]
        and location["fixed_point"]
        and payload["certification"]["fixed_point"]
    )
    _emit(payload)
    return 0 if payload["fixed_point"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ucos-nucleus",
        description=(
            "The Nucleus Ownership Authority: capabilities belong to Nuclei; layers and "
            "compositions own nothing. Commerce is a Composition."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("law", help="the nucleus ownership law").set_defaults(func=_cmd_law)
    sub.add_parser("catalog", help="the declared structural catalogue").set_defaults(
        func=_cmd_catalog
    )
    sub.add_parser("registry", help="the registered structural population").set_defaults(
        func=_cmd_registry
    )
    sub.add_parser("gate", help="run FG-18-NUCLEUS-OWNS-CAPABILITY").set_defaults(func=_cmd_gate)
    sub.add_parser("order", help="the derived composition order").set_defaults(func=_cmd_order)
    sub.add_parser("lineage", help="the structural lineage ledger").set_defaults(func=_cmd_lineage)

    dictionary = sub.add_parser("dictionary", help="the universal identifier dictionary")
    dictionary.add_argument(
        "--with-context",
        action="store_true",
        help="also enumerate every reference frame and resolved axis identifier",
    )
    dictionary.set_defaults(func=_cmd_dictionary)

    validate = sub.add_parser("validate", help="constitutional validation")
    validate.add_argument(
        "--frame", default="", help="bind the population to this reference frame and measure it"
    )
    validate.set_defaults(func=_cmd_validate)

    certify = sub.add_parser("certify", help="constitutional certification")
    certify.add_argument(
        "--frame", default="", help="certify the population in this reference frame"
    )
    certify.set_defaults(func=_cmd_certify)

    compose = sub.add_parser("compose", help="realise a composition from registered nuclei")
    compose.add_argument("--composition", default="", help="composition key (default: all)")
    compose.set_defaults(func=_cmd_compose)

    run = sub.add_parser("lifecycle", help="the constitutional lifecycle, or run it")
    run.add_argument("--subject", default="", help="subject to run the lifecycle over")
    run.set_defaults(func=_cmd_lifecycle)

    evolve = sub.add_parser("evolve", help="record a governed evolution")
    evolve.add_argument("--subject", default="", help="subject key (default: every nucleus)")
    evolve.add_argument("--frame", default="", help="evolve within this reference frame")
    evolve.set_defaults(func=_cmd_evolve)

    resolve = sub.add_parser("context", help="location-derived context resolution")
    resolve.add_argument("--frame", default="", help="reference frame key (default: all)")
    resolve.set_defaults(func=_cmd_context)

    rebase = sub.add_parser("rebase", help="re-resolve one subject across several frames")
    rebase.add_argument("--subject", required=True)
    rebase.add_argument("--frames", nargs="+", required=True)
    rebase.set_defaults(func=_cmd_rebase)

    sub.add_parser("context-validate", help="validate the location architecture").set_defaults(
        func=_cmd_context_validate
    )
    sub.add_parser("context-certify", help="certify the location architecture").set_defaults(
        func=_cmd_context_certify
    )

    replay = sub.add_parser("replay", help="prove the whole system is a deterministic fixed point")
    replay.add_argument("--frame", default="", help="replay within this reference frame")
    replay.set_defaults(func=_cmd_replay)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except NucleusError as exc:
        _emit(exc.to_dict())
        return 1


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
