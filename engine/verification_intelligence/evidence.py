"""UVI-000001 Part 05 — the Verification Evidence Registry.

A CACHE, and the docstring says so first because everything else follows from it. An
entry records that one declared stage was executed over one exactly-identified input
and passed. It is not a record of truth, it is not evidence of certification, and
deleting the whole store changes no verdict — it only makes the next run pay again.

The key is computed, never asserted. For a stage declaring ``reuse_inputs``, the digest
is taken over the ``content_hash`` values that ``00-MASTER/UCOS-UGA-001/01-EXECUTABLE-
OBJECT-REGISTRY.json`` already publishes for every object under those prefixes, plus the
stage's own identity and the engine version. So the question "has this exact stage
already passed over this exact input" is answered from hashes the repository already
owns rather than from a second measurement of the tree.

Two refusals are structural rather than configurable:

* **A certification-eligible mode never reaches a reuse decision.** ``integration`` and
  ``full`` declare ``evidence_reuse: false``, and :func:`decide` refuses before it looks
  at the store. A certification that reuses a result certifies a cache.
* **An unhashed input is never a hit.** If any object under a declared prefix carries no
  content hash, or the prefix matches no object at all, the digest is refused and the
  stage runs. A cache key that silently covers nothing is a permanent false hit.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from typing import Any

from engine.verification_intelligence.constitution import repo_root
from engine.verification_intelligence.model import Mode, StageSpec
from engine.verification_intelligence.registry import Substrates

#: Bumping this invalidates every stored entry. It is part of every key, so a change to
#: how a stage is executed can never be answered by a result produced under the old way.
EVIDENCE_VERSION = "1.0"

SCHEMA = "ucos-verification-evidence"


@dataclass(frozen=True, slots=True)
class EvidenceEntry:
    """One recorded stage result."""

    stage_id: str
    input_digest: str
    result: str
    engine_version: str

    @property
    def passed(self) -> bool:
        return self.result == "PASS"


def store_home(root: str | None = None, home: str = ".ucos-verification-evidence/") -> str:
    return os.path.join(root or repo_root(), home)


def input_digest(
    stage: StageSpec, substrates: Substrates, *, extra: tuple[str, ...] = ()
) -> str | None:
    """The content digest of everything ``stage`` reads, or None when it cannot be taken.

    Returns None — never a placeholder — when the stage declares no reuse inputs, when a
    declared prefix matches no registered object, or when a matched object carries no
    content hash. Each of those is a key that would cover less than the stage reads, and
    a key that covers less than the stage reads is a false hit waiting to happen.
    """
    if not stage.reusable or not stage.reuse_inputs:
        return None
    digest = hashlib.sha256()
    digest.update(f"{EVIDENCE_VERSION}\n{stage.stage_id}\n{stage.label}\n".encode())
    for item in extra:
        digest.update(f"extra:{item}\n".encode())
    for prefix in sorted(stage.reuse_inputs):
        matched = sorted(
            path
            for path in substrates.objects
            if path == prefix.rstrip("/")
            or path.startswith(prefix.rstrip("/") + "/")
            or path == prefix
        )
        if not matched:
            return None
        digest.update(f"prefix:{prefix}\n".encode())
        for path in matched:
            content_hash = substrates.objects[path].get("content_hash")
            if not content_hash:
                return None
            digest.update(f"{path}:{content_hash}\n".encode())
    return digest.hexdigest()


def _entry_path(home: str, stage_id: str, digest: str) -> str:
    return os.path.join(home, stage_id, f"{digest}.json")


def lookup(home: str, stage_id: str, digest: str) -> EvidenceEntry | None:
    """The recorded entry for this exact stage and input, if one exists and is usable."""
    target = _entry_path(home, stage_id, digest)
    try:
        with open(target, encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if document.get("schema") != SCHEMA:
        return None
    if document.get("engine_version") != EVIDENCE_VERSION:
        return None
    if document.get("input_digest") != digest or document.get("stage_id") != stage_id:
        return None
    return EvidenceEntry(
        stage_id=stage_id,
        input_digest=digest,
        result=str(document.get("result") or ""),
        engine_version=EVIDENCE_VERSION,
    )


def record(home: str, stage_id: str, digest: str, result: str) -> None:
    """Store a stage result, atomically.

    A half-written entry read by the next run would be a corrupt cache reporting a hit,
    so the write is a rename over a completed temporary file. Failure to write is
    swallowed on purpose: a cache that cannot be written must not fail a verification.
    """
    directory = os.path.join(home, stage_id)
    document: dict[str, Any] = {
        "schema": SCHEMA,
        "engine_version": EVIDENCE_VERSION,
        "stage_id": stage_id,
        "input_digest": digest,
        "result": result,
    }
    try:
        os.makedirs(directory, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(  # noqa: SIM115 - renamed below, not closed early
            "w", encoding="utf-8", dir=directory, delete=False, suffix=".tmp"
        )
        with handle:
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(handle.name, _entry_path(home, stage_id, digest))
    except OSError:
        return


def decide(
    mode: Mode, stage: StageSpec, substrates: Substrates, *, home: str
) -> tuple[bool, str, str | None]:
    """Decide whether ``stage`` may be answered from evidence.

    Returns ``(reuse, reason, digest)``. The reason is carried into the plan either way,
    so a run always states why a stage was executed as well as why one was not.
    """
    if not mode.evidence_reuse:
        return False, f"{mode.mode_id} is a certification-eligible mode; it never reuses", None
    if not stage.reusable:
        return False, "the stage is declared non-reusable", None
    digest = input_digest(stage, substrates)
    if digest is None:
        return False, "no input digest could be taken over the declared inputs", None
    entry = lookup(home, stage.stage_id, digest)
    if entry is None:
        return False, "no evidence exists for this input", digest
    if not entry.passed:
        return False, "the recorded result for this input is not PASS", digest
    return True, f"identical input already passed (digest {digest[:12]})", digest
