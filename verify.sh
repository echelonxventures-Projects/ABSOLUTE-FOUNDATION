#!/usr/bin/env bash
#
# UCOS Ω∞ — Canonical Verification Entry Point.
#
#   ./verify.sh              lint + tests/coverage + governance + meta-constitutional gate
#                            + universal object governance + autonomous evolution gate
#                            + universal object birth contract  (THE certification default)
#   ./verify.sh --fast       developer feedback: lint + impact-selected tests + eligibility
#   ./verify.sh --change     commit validation: impact-selected tests + every governance gate
#   ./verify.sh --integration merge validation: whole suite + every governance gate
#   ./verify.sh --full       release certification: --integration + registration/drift gate
#   ./verify.sh --failfast   stop at the first failing stage
#
# MODE SEMANTICS. The default invocation is unchanged and remains the certification
# contract: .github/workflows/ec1-ci.yml calls bare `./verify.sh`, so weakening the
# default would weaken CI silently. --fast and --change are DEVELOPER modes: they run
# pytest with --no-cov and therefore do NOT own the 90% coverage floor, which stays
# owned by the default/--integration/--full path. A --fast or --change run is never
# evidence of certification, and neither prints a certification claim.
#
# --change and --fast select tests through engine.verification_impact, which FAILS WIDE:
# any change it cannot bound by import edges (a declaration, registry, schema, config,
# document or unregistered file) escalates to the whole suite with coverage. So a
# selected run is only ever a subset when the subset is provably sufficient.
#
# THE one repository-standard command. A brand-new terminal can run this with NO
# manual `source .../activate` and NO tribal knowledge: it self-heals the canonical
# venv (correct Python series + pinned pytest/pytest-cov/coverage/ruff), then runs
# every gate through the venv interpreter by absolute path. Exits non-zero on any
# failure. This is the permanent remediation for the recurring
# "pytest-cov missing / ruff missing / coverage missing" failure mode.

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=scripts/ucos-env.sh
source "scripts/ucos-env.sh"

MODE="default"
FULL=0
FAILFAST=0
_mode_set=""
_set_mode() {
  if [ -n "$_mode_set" ] && [ "$_mode_set" != "$1" ]; then
    ucos_die "modes are mutually exclusive: --$_mode_set and --$1"
  fi
  _mode_set="$1"
  MODE="$1"
}
for arg in "$@"; do
  case "$arg" in
    --full) _set_mode full; FULL=1 ;;
    --integration) _set_mode integration ;;
    --change) _set_mode change ;;
    --fast) _set_mode fast ;;
    --failfast) FAILFAST=1 ;;
    -h|--help) sed -n '3,26p' "$0"; exit 0 ;;
    *) ucos_die "unknown option: $arg (see ./verify.sh --help)" ;;
  esac
done


# --- Stage 0: ensure the canonical environment (no activation needed) ------------
ucos_ensure_venv
PY="$(ucos_venv_python)"

# Stage labels a --fast run skips: the governance gates. Declared as a pattern so the
# skip lives inside run_stage and the file still contains exactly ONE `run_stage "…"`
# line per declared stage — which is what platform/tests/test_canonical_validation_evidence.py
# reads to derive the verification contract and its digest. A second run_stage literal
# for the same stage would corrupt that contract.
_FAST_SKIP_RE='registry validate|meta-constitutional conformance|universal object governance|autonomous universal evolution|evolution surface replay|universal object birth contract'

STAGES_RUN=()
STAGES_FAIL=()
STAGES_SECS=()
VERIFY_START=$SECONDS
run_stage() {
  local label="$1"; shift
  if [ "$MODE" = "fast" ] && printf '%s' "$label" | grep -qE "$_FAST_SKIP_RE"; then
    ucos_log "SKIP (--fast, no governance claim): ${label}"
    return 0
  fi
  ucos_log "STAGE: ${label}"
  STAGES_RUN+=("$label")
  local _start=$SECONDS
  set +e
  ( cd "$UCOS_REPO" && "$@" )
  local rc=$?
  set -e
  STAGES_SECS+=("$((SECONDS - _start))")
  if [ "$rc" -ne 0 ]; then
    ucos_err "STAGE FAILED (exit $rc): ${label}"
    STAGES_FAIL+=("$label")
    [ "$FAILFAST" = "1" ] && summarize_and_exit
  else
    ucos_ok "STAGE PASSED: ${label}"
  fi
  # Always succeed: a non-failfast failure is recorded in STAGES_FAIL and reported
  # by the final summary. Without this, run_stage would inherit the non-zero status
  # of the short-circuited `[ FAILFAST = 1 ] && …` test and `set -e` would abort the
  # run before the remaining stages and the summary — the exact opposite of the
  # documented "run all stages, then summarize" contract.
  return 0
}

summarize_and_exit() {
  printf '\n%s\n' "================ VERIFICATION SUMMARY ================" >&2
  local i s dur
  for i in "${!STAGES_RUN[@]}"; do
    s="${STAGES_RUN[$i]}"
    dur="${STAGES_SECS[$i]:-0}"
    if printf '%s\n' "${STAGES_FAIL[@]:-}" | grep -qxF "$s"; then
      printf '  %sFAIL%s  %-44s %3ss\n' "$_UC_R" "$_UC_0" "$s" "$dur" >&2
    else
      printf '  %sPASS%s  %-44s %3ss\n' "$_UC_G" "$_UC_0" "$s" "$dur" >&2
    fi
  done
  printf '  %-52s %3ss\n' "TOTAL (wall clock)" "$((SECONDS - VERIFY_START))" >&2
  printf '%s\n' "=====================================================" >&2
  if [ "$MODE" = "fast" ] || [ "$MODE" = "change" ]; then
    printf '  %s\n' "MODE: --${MODE} (developer mode: --no-cov, coverage floor NOT evaluated)" >&2
    printf '  %s\n' "This run is NOT evidence of certification. Run ./verify.sh for that." >&2
  fi
  if [ "${#STAGES_FAIL[@]}" -gt 0 ]; then
    ucos_err "VERIFICATION FAILED (${#STAGES_FAIL[@]} stage(s))."
    exit 1
  fi
  ucos_ok "VERIFICATION PASSED — all gates green (reproduced without manual venv activation)."
  exit 0
}

# --- Stage 1: ruff quality gate (lint + format-check) — CD-01 / CD-04 ------------
# Invokes the SINGLE-SOURCE-OF-TRUTH gate (ucos_ruff_gate in scripts/ucos-env.sh) so
# this canonical path runs the IDENTICAL ruff gate as the pre-commit hook — closing the
# drift that let verify.sh pass while pre-commit's `ruff format --check` failed.
run_stage "ruff lint + format-check (engine + platform)" ucos_ruff_gate

# --- Stage 1b: prerequisite generation (P0-FINAL-CONVERGENCE-001) ----------------
# The tests below READ generated artifacts that `.gitignore` excludes on the stated
# grounds that they are "regenerated each run": /knowledge/, determinism-evidence/ and
# the UAKOS-CLOSURE-002 engine outputs. Nothing re-ran them. Generation appeared in NO
# stage of this script and in no part of register.sh, so the ignore authority asserted a
# regeneration that no entry point performed. Locally that was invisible because the
# artifacts persist from earlier manual runs; on a clean checkout they simply do not
# exist, and 51 tests that pass here failed in CI — measured on a fresh clone of HEAD:
# 50 failed + 3 errors, reduced to 2 by running exactly these five producers.
#
# This stage MUST precede the pytest stage: a prerequisite generated after the gate that
# consumes it is not a prerequisite. Every write lands on an ignored path, so the stage
# cannot dirty the working tree and cannot be seen as drift by the Registration Gate.
# The producers live in scripts/generate-prerequisites.sh so this path and the stdlib-only
# constitutional gate workflows share ONE definition rather than two that can drift apart.
run_stage "prerequisite generation (knowledge · determinism · closure 1-3)" \
  env PYTHON="$PY" bash scripts/generate-prerequisites.sh

# --- Stage 2: tests + coverage gate — CD-02 (pytest addopts drive --cov ≥ 90%) ---
# Running via the venv interpreter guarantees pytest-cov is present, so the --cov
# arguments in pyproject are always recognized.
#
# MODE-AWARE. The default, --integration and --full paths run the whole suite under the
# 90% floor and are the only certification-eligible paths. --fast and --change ask
# engine.verification_impact what the change actually reaches, and run only that, with
# --no-cov so they cannot become a second owner of the floor. The impact engine fails
# wide: exit 2 means it could not bound the change, and this stage then runs the whole
# suite WITH coverage rather than proceeding on a subset it cannot justify.
# The argv is chosen by mode; the STAGE LABEL is not. There is exactly one
# `run_stage "pytest + coverage gate (--cov-fail-under=90)"` line in this file, because
# platform/tests/test_canonical_validation_evidence.py derives the verification contract
# and its sha256 digest from these literals — a per-mode label would make the contract
# depend on how the run was invoked, which is precisely what a contract must not do.
PYTEST_ARGV=(-m pytest)
if [ "$MODE" = "fast" ] || [ "$MODE" = "change" ]; then
  ucos_log "impact: asking engine.verification_impact what this change reaches"
  set +e
  _impact_out="$("$PY" -m engine.verification_impact --quiet --print-tests 2>/dev/null)"
  _impact_rc=$?
  set -e
  _selected="$(printf '%s\n' "$_impact_out" | tr -d '\r' | sed '/^$/d')"
  if [ "$_impact_rc" -ne 0 ] || [ -z "$_selected" ]; then
    # Fail wide. Escalation keeps the FULL argv, so an unbounded change is verified
    # under the coverage floor exactly as the default path would verify it.
    ucos_log "impact: scope ESCALATED — running the whole suite WITH coverage"
    "$PY" -m engine.verification_impact || true
  else
    _count="$(printf '%s\n' "$_selected" | wc -l | tr -d ' ')"
    ucos_log "impact: ${_count} test file(s) selected (--no-cov; floor not evaluated in this mode)"
    # shellcheck disable=SC2206
    PYTEST_ARGV=(-m pytest -o addopts= --no-cov -q ${_selected})
  fi
fi
run_stage "pytest + coverage gate (--cov-fail-under=90)" "$PY" "${PYTEST_ARGV[@]}"


# --- Stage 3: coverage report (explicit coverage tool invocation) ----------------
# pytest-cov already produced .coverage + coverage.xml above; re-summarize with the
# coverage CLI to prove the coverage tool itself resolves and to surface the total.
# Skipped in --fast/--change: those modes ran --no-cov, so there is no coverage data to
# summarise and printing a stale total would be worse than printing none.
if [ "$MODE" != "fast" ] && [ "$MODE" != "change" ]; then
  run_stage "coverage report" "$PY" -m coverage report
fi

# --- Stage 4: governance enforcement (UMB-IMP-001 pre-registration gate) ---------
# Read-only eligibility/validity/classification gate (same gate CI runs first).
run_stage "governance enforce --pre" "$PY" 00-BOOK/tools/ukb.py enforce --pre

# --- Stage 5: registry structural validation (schema + referential integrity) -----
# Validates emitted DATA against JSON schemas and checks structural invariants.
# This gate was wired in by CRAP-001/CAEM-001 S-2 to close the silent-failure gap
# that let 539 schema violations pass undetected through all prior gates.
run_stage "registry validate (schema + integrity)" "$PY" 00-BOOK/tools/ukb.py validate

# --- Stage 6: meta-constitutional conformance gate (CMG-000001 Article L) ---------
# The meta layer is permitted EXACTLY ONE automated realization, and Article LXVI.7
# requires it be "invoked through the corpus's existing verification entry point" —
# this stage IS that invocation. It adds no second pipeline, scheduler, or daemon
# (LXVI.7) and no second criteria set (L.2): the criteria are CMG-INV-01..12 and
# nothing else, evaluated by the validator Article L.3 names as its realization.
#
# Before this stage existed, meta-constitutional conformance was measurable but only
# on demand, so a corpus could drift into parallel authority, orphan governance, a
# dangling superior or an illegal lifecycle record and stay green through every gate.
# XLIX.7 is explicit that an unchecked obligation is of UNKNOWN compliance and SHALL
# NOT be presumed satisfied; binding the gate here converts the twelve invariants from
# on-demand measurement into continuous enforcement.
#
# Read-only and fail-closed (L.4): the validator writes nothing and reports a finding
# rather than a pass on any unparseable, missing or ambiguous input. It is deterministic
# and hermetic (L.5), so it cannot flake a verification run.
run_stage "meta-constitutional conformance (CMG-INV-01..12)" bash 00-CMG/tools/cmg-gate.sh

# --- Stage 6b: universal object governance gate (UCOS-UGA-001 UGA-INV-01..10) -----
# The gates above enforce the DOCUMENT corpus. config.INCLUDE_EXTENSIONS is
# (.md, .txt, .docx, .json), so the registration boundary never saw a thing that
# EXECUTES: at the time this stage was added, 4510 version-controlled objects —
# every engine, every test, every workflow, and all 29 producers named by the
# generated-artifact registry — carried no universal identity, no owner and no
# lifecycle. The corpus governed 1233 artifacts by naming producers that were
# themselves anonymous.
#
# This stage closes that leg. It asserts the ten universal invariants over the
# WHOLE version-controlled boundary, so a new engine, test or config file can no
# longer enter the repository unidentified, unowned, unregistered or unaudited.
#
# Read-only and fail-closed: `gate` mints nothing and writes nothing (`run` does
# that), and it reports a violation rather than a pass on any input it cannot
# measure. Deterministic and hermetic — no clock, no network — so it cannot flake.
#
# All ten invariants block. UGA-INV-06 (bootstrap path for every generated input)
# was briefly carried as a non-blocking DECLARED-OPEN condition while `realization/`
# had a declared producer but no bootstrap invocation. That gap is now discharged:
# the producer was made deterministic — its manifest sealed a per-run `action`, so it
# had no fixed point — and added to scripts/generate-prerequisites.sh. The registry's
# `bootstrap_gaps` is empty and the exemption is gone with the condition it covered.
run_stage "universal object governance (UGA-INV-01..10)" \
  "$PY" 00-MASTER/UCOS-UGA-001/uga_engine.py gate

# --- Stage 6c: autonomous universal evolution gate (UAUE-000001) ------------------
# The evolution declaration binds three of its eleven positions — Execute, Validate and
# Verify — to `./verify.sh` as their gate, and its Evolve position to `make uaue-gate`.
# Until this stage existed, that binding was a claim about a pipeline that had never heard
# of UAUE: the gate was fail-closed, deterministic and green, and it was only ever invoked
# by hand. AUE-VER-04 (governance integrity) requires that every gate a position names be
# wired into the repository's verification, and an obligation nothing evaluates is of
# UNKNOWN compliance rather than satisfied. This stage is that wiring.
#
# Every obligation is fail-closed, and the stage name deliberately carries no count: the set
# grows as more of the declaration becomes measurable, and a number in a label is a stale claim
# waiting to happen — this stage is named in the canonical validation record, so a count here
# would make every new obligation a documentation edit in three files. What the obligations are is
# the gate's own report: the declaration rehydrates; every position resolves to an owner that
# exists and binds the symbols it is read through; every canonical Article-14 stage is claimed by
# exactly one position; every dependency resolves and runs forward; conducting the same candidates
# twice produces byte-identical runs; the declared UNKNOWN subject traverses the whole loop to a
# settled, certified run requiring no new registry, authority, engine or schema; every declared
# mandatory invariant is measured against its expectation; every declared register renders bytes
# that reproduce on another process and another machine; every declared exit criterion of every
# implementation phase is measured; and — the obligation this stage is the other half of — this
# pipeline is measured to actually invoke the gate fail-closed, so deleting the stage below closes
# the gate instead of silently unbinding four positions.
#
# Read-only and hermetic. `--gate` conducts and measures; it renders nothing, mutates
# nothing outside memory, and reaches no clock and no network, so it cannot dirty the tree
# and cannot flake. Exit 1 means an obligation was refused; exit 2 means no verdict could
# be reached, which is deliberately not the same answer.
run_stage "autonomous universal evolution (UAUE gate, every declared obligation)" \
  "$PY" -m engine.uaue.gate --gate --quiet

# --- Stage 6d: evolution surface replay (UAUE-000001 derived truth) ---------------
# The nineteen files in 00-MASTER/UAUE-000001/ — the append-only history projection and
# the eighteen declared registers — are DERIVED TRUTH: the deterministic product of the
# declaration and the measured tree. This stage regenerates them in memory and compares
# the committed bytes, so a hand edit is a failure here rather than a fact anywhere.
#
# Byte comparison, not parsed comparison: a projection that only matches after
# normalisation is a projection whose canonical form nobody is holding to. The remedy for
# a drift report is never to edit the file — it is `make uaue-render`, which reproduces it
# from the declaration.
run_stage "evolution surface replay (history + 18 registers)" \
  "$PY" -m engine.uaue.gate --replay --quiet

# --- Stage 6e: universal object birth contract (UOBC-000001) ----------------------
# Identity before existence. Six identity mechanisms existed before UOBC-000001 and all
# six identify things that ALREADY EXIST — they scan the tree and name what they find,
# which makes identity a measurement of location that changes when the location does.
# This gate measures the one thing none of them measures: that every object in the birth
# ledger was identified before it was instantiated, and that no identity was replaced.
#
# The eight laws are each computed, never asserted: UOBC-L-01 identity precedes existence
# (measured against the declaration's own identity_exists flags), L-02 derived never
# counted (the ledger must not hold `category_seq`, the declared mint marker, or it would
# be a second identity authority under CAA-INV-04's own test), L-03 identity immutability
# (every recorded id is RE-DERIVED from its namespace and local name — a tampered id
# fails without needing a history), L-04 no anonymous object, L-05 no temporary identity,
# L-06 no post-creation registration, L-07 evolution under one identity, L-08 append-only
# history.
#
# Read-only and hermetic: it loads the declaration and the ledger, computes, writes
# nothing, and reads no clock and no network, so it cannot dirty the tree and cannot
# flake. Exit 1 means a law was measured and refused; exit 2 means no verdict could be
# reached, which is deliberately a different answer.
run_stage "universal object birth contract (UOBC-000001, identity before existence)" \
  "$PY" -m engine.object_birth.gate --gate --quiet

# --- Stage 7 (opt-in): full registration transaction + drift gate ----------------
# READ-ONLY. Calls register.sh --observe, the verification plane: it answers "is
# registration state valid?" by reading, and allocates nothing.
#
# It used to call --guard, which runs the full transaction — Phase 1 is `ukb build
# --mint` — and only THEN checked for drift, so it CAUSED the drift it reported. A
# --guard run over a corpus with 140 unregistered artifacts minted all 140 permanent
# identities and emitted ~140 PORTAL pages from inside ./verify.sh --full.
# CORPUS_REGISTRATION is now declared in mutation-governance-boundary.json as governed
# by REG-AUTO-001 and explicitly NOT by verify.sh. Migration is an explicit transaction.
if [ "$FULL" = "1" ]; then
  run_stage "registration observation (register.sh --observe, read-only)" \
    env PYTHON="$PY" bash 00-BOOK/tools/register.sh --observe
fi

summarize_and_exit
