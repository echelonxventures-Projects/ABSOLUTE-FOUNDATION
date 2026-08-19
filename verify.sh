#!/usr/bin/env bash
#
# UCOS Ω∞ — Canonical Verification Entry Point.
#
#   ./verify.sh              DEFAULT = --change (commit validation)
#   ./verify.sh --fast       developer feedback: lint + impact-selected tests
#   ./verify.sh --change     commit validation: impact-selected tests + every governance gate
#   ./verify.sh --integration merge validation: whole suite under the floor + every gate
#   ./verify.sh --full       release certification: --integration + registration observation
#   ./verify.sh --failfast   stop at the first failing stage
#   ./verify.sh --serial     execute every stage sequentially (scheduling only; measures the same)
#   ./verify.sh --explain    print the plan and exit, executing nothing
#
# THE DEFAULT CHANGED, AND SAYING SO IS THE POINT. It was the full certification
# contract; it is now --change. That is not a weakening by stealth, because certification
# did not become weaker — it became EXPLICIT: .github/workflows/ec1-ci.yml invokes
# `./verify.sh --full` by name, and --full runs every stage the old default ran, under the
# same 90% floor, over the same whole suite. What changed is that the command a developer
# types dozens of times a day no longer costs a release certification. A 47-minute default
# is a default people route around, and a gate that is routed around is not a gate.
#
# MODES ARE NOT DECLARED HERE. 00-MASTER/UVI-000001/uvi-declaration.json holds the
# Verification Mode Constitution — what each mode claims, what it explicitly does not
# claim, which stages it admits, whether it may reuse evidence — and the Stage Registry
# that classifies every stage below by phase, plane and dependency. This script parses its
# own flags (a shell must, before it can run anything) and UVI-L-01 measures that the flags
# it accepts and the modes the constitution declares are the same set, in both directions.
#
# WHAT SELECTS THE TESTS. --fast and --change ask engine.verification_intelligence, which
# composes five substrates the repository already publishes — object identity, ownership,
# the dependency graph, the capability catalogue and the relationship graph — and FAILS
# WIDE: any change it cannot bound (a declaration, registry, schema, config, document,
# unregistered file, or a change to the selector itself) escalates to the whole suite WITH
# coverage. A selected run is only ever a subset when the subset is provably sufficient.
# Nothing anywhere names a test file; UVI-L-06 measures that.
#
# WHAT IS NOT NEGOTIABLE. Every gate below still exists, is still owned by the same
# instrument and is still evaluated by the same command. UVI-L-04 holds the pre-existing
# contract as a ratchet: every stage the certification default ran before this rework must
# still be a declared stage AND still admitted by every certification-eligible mode.
# UVI-L-05 refuses any mode that claims more than it measures, and UVI-L-08 measures that
# sharding and concurrency change no obligation — the shards union to exactly the
# selection, and the coverage floor is evaluated once, by the coverage tool, over combined
# data.
#
# THE one repository-standard command. A brand-new terminal can run this with NO
# manual `source .../activate` and NO tribal knowledge: it self-heals the canonical
# venv (correct Python series + pinned pytest/pytest-cov/coverage/ruff), then runs
# every gate through the venv interpreter by absolute path. Exits non-zero on any
# failure.

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=scripts/ucos-env.sh
source "scripts/ucos-env.sh"

MODE="change"
FULL=0
FAILFAST=0
SERIAL=0
EXPLAIN=0
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
    --serial) SERIAL=1 ;;
    --explain) EXPLAIN=1 ;;
    -h|--help) sed -n '3,12p' "$0"; exit 0 ;;
    *) ucos_die "unknown option: $arg (see ./verify.sh --help)" ;;
  esac
done


# --- Stage 0: ensure the canonical environment (no activation needed) ------------
ucos_ensure_venv
PY="$(ucos_venv_python)"

# --- Stage 0b: compute the plan, once, before anything executes -------------------
# The whole decision — which declared stages run, which are answered from evidence,
# which this mode does not admit, what the test selection is and how it is partitioned —
# is taken here and written to a plan file the stages below read. Deciding once up front
# rather than as the run proceeds is what makes a run reproducible and what makes the
# plan digest comparable between two machines.
#
# FAIL SAFE, IN THE ONLY DIRECTION THAT IS SAFE. If planning faults, the plan file is
# empty; uvi_action then answers RUN for every stage and the pytest stage falls back to
# the whole suite under the coverage floor. An intelligence layer that cannot compute a
# plan must never be able to cause LESS verification than there would have been without
# it.
UVI_PLAN="$(mktemp -t ucos-verify-plan)"
UVI_PLAN_OK=1
trap 'rm -f "$UVI_PLAN"' EXIT
if ! "$PY" -m engine.verification_intelligence plan --mode "$MODE" --tsv --out "$UVI_PLAN" 2>/dev/null; then
  ucos_warn "verification intelligence faulted; every stage will run and the whole suite will be verified under the coverage floor"
  : > "$UVI_PLAN"
  UVI_PLAN_OK=0
fi

if [ "$EXPLAIN" = "1" ]; then
  "$PY" -m engine.verification_intelligence report --mode "$MODE"
  exit 0
fi

# The plan is looked up by the SAME literal that is passed to run_stage — which is the
# same literal 00-MASTER/UAKOS-CLOSURE-008/validation-record.json digests and that
# .github/workflows/uisd-gate.yml re-derives. One string, one stage, three readers.
# An unrecognised label answers RUN: a stage the plan does not know about must execute,
# never be silently skipped.
uvi_field() {
  [ -s "$UVI_PLAN" ] || { printf '%s' "$2"; return 0; }
  awk -F'\t' -v want="$1" -v col="$3" -v fallback="$2" '
    $4 == want { print $col; found = 1; exit }
    END { if (!found) print fallback }
  ' "$UVI_PLAN"
}
uvi_action() { uvi_field "$1" RUN 1; }
uvi_phase()  { uvi_field "$1" MAIN 2; }
uvi_digest() { uvi_field "$1" - 3; }

# Concurrency is scheduling, never scope. Every stage the registry places in PREFLIGHT or
# MAIN is either READ_ONLY or writes exclusively to gitignored paths, which is what makes
# them safe to overlap; POST and EXTENDED read what MAIN produced and therefore do not.
# Draining is automatic on a phase transition, so the barrier cannot be forgotten when a
# stage is added.
UVI_PARALLEL=1
[ "$SERIAL" = "1" ] && UVI_PARALLEL=0

STAGES_RUN=()
STAGES_FAIL=()
STAGES_SECS=()
_BG_PIDS=()
_BG_LABELS=()
_BG_LOGS=()
_BG_STARTS=()
_BG_DIGESTS=()
_BG_PHASE=""
VERIFY_START=$SECONDS

_record_result() {
  local label="$1" rc="$2" secs="$3" digest="$4"
  STAGES_RUN+=("$label")
  STAGES_SECS+=("$secs")
  if [ "$rc" -ne 0 ]; then
    ucos_err "STAGE FAILED (exit $rc): ${label}"
    STAGES_FAIL+=("$label")
  else
    ucos_ok "STAGE PASSED: ${label}"
  fi
  # The evidence registry is a cache of results, so it records what happened either way:
  # storing only passes would make a failure look like an absent measurement next run.
  if [ "$digest" != "-" ] && [ -n "$digest" ] && [ "$UVI_PLAN_OK" = "1" ]; then
    "$PY" -m engine.verification_intelligence record \
      --stage-label "$label" --digest "$digest" \
      --result "$([ "$rc" -eq 0 ] && echo PASS || echo FAIL)" >/dev/null 2>&1 || true
  fi
}

uvi_drain() {
  [ "${#_BG_PIDS[@]}" -eq 0 ] && { _BG_PHASE=""; return 0; }
  local i rc
  for i in "${!_BG_PIDS[@]}"; do
    set +e
    wait "${_BG_PIDS[$i]}"
    rc=$?
    set -e
    printf '\n%s\n' "----- ${_BG_LABELS[$i]} -----" >&2
    cat "${_BG_LOGS[$i]}" >&2 || true
    local secs
    secs="$(cat "${_BG_LOGS[$i]}.secs" 2>/dev/null || true)"
    [ -n "$secs" ] || secs="$((SECONDS - _BG_STARTS[$i]))"
    rm -f "${_BG_LOGS[$i]}" "${_BG_LOGS[$i]}.secs"
    _record_result "${_BG_LABELS[$i]}" "$rc" "$secs" "${_BG_DIGESTS[$i]}"
  done
  _BG_PIDS=(); _BG_LABELS=(); _BG_LOGS=(); _BG_STARTS=(); _BG_DIGESTS=()
  _BG_PHASE=""
  if [ "$FAILFAST" = "1" ] && [ "${#STAGES_FAIL[@]}" -gt 0 ]; then
    summarize_and_exit
  fi
  return 0
}

run_stage() {
  local label="$1"; shift
  local action phase digest
  action="$(uvi_action "$label")"
  phase="$(uvi_phase "$label")"
  digest="$(uvi_digest "$label")"

  case "$action" in
    SKIP)
      ucos_log "SKIP (--${MODE} does not admit this stage, and claims nothing from it): ${label}"
      return 0
      ;;
    REUSE)
      ucos_log "REUSE (identical input already passed): ${label}"
      STAGES_RUN+=("$label")
      STAGES_SECS+=("0")
      return 0
      ;;
  esac

  # A phase transition drains whatever is still running. POST reads what MAIN produced,
  # and MAIN reads what PREFLIGHT generated, so overlapping across a boundary would be
  # reading a half-written input.
  if [ -n "$_BG_PHASE" ] && [ "$_BG_PHASE" != "$phase" ]; then
    uvi_drain
  fi

  ucos_log "STAGE: ${label}"
  local _start=$SECONDS

  if [ "$UVI_PARALLEL" = "1" ] && { [ "$phase" = "PREFLIGHT" ] || [ "$phase" = "MAIN" ]; }; then
    # The subshell records its OWN elapsed time. Measuring from launch to reap instead
    # would report the time until the barrier got to it, not the time it took: every
    # read-only gate finishes in seconds and is reaped after the pytest stage, so the
    # first version of this summary reported eleven gates at 441s each. A summary that
    # misattributes 440 seconds to a gate that took one is worse than no summary.
    local log; log="$(mktemp -t ucos-verify-stage)"
    ( cd "$UCOS_REPO"; _s=$SECONDS; "$@"; _rc=$?; printf '%s' "$((SECONDS - _s))" > "${log}.secs"; exit "$_rc" ) > "$log" 2>&1 &
    _BG_PIDS+=("$!")
    _BG_LABELS+=("$label")
    _BG_LOGS+=("$log")
    _BG_STARTS+=("$_start")
    _BG_DIGESTS+=("$digest")
    _BG_PHASE="$phase"
    return 0
  fi

  set +e
  ( cd "$UCOS_REPO" && "$@" )
  local rc=$?
  set -e
  _record_result "$label" "$rc" "$((SECONDS - _start))" "$digest"
  # Always succeed: a non-failfast failure is recorded in STAGES_FAIL and reported by the
  # final summary. Without this, run_stage would inherit the non-zero status of the
  # short-circuited failfast test and `set -e` would abort the run before the remaining
  # stages and the summary — the opposite of the documented contract.
  if [ "$FAILFAST" = "1" ] && [ "$rc" -ne 0 ]; then
    summarize_and_exit
  fi
  return 0
}

summarize_and_exit() {
  uvi_drain
  printf '\n%s\n' "================ VERIFICATION SUMMARY ================" >&2
  local i s dur
  for i in "${!STAGES_RUN[@]}"; do
    s="${STAGES_RUN[$i]}"
    dur="${STAGES_SECS[$i]:-0}"
    if printf '%s\n' "${STAGES_FAIL[@]:-}" | grep -qxF "$s"; then
      printf '  %sFAIL%s  %-58s %4ss\n' "$_UC_R" "$_UC_0" "$s" "$dur" >&2
    else
      printf '  %sPASS%s  %-58s %4ss\n' "$_UC_G" "$_UC_0" "$s" "$dur" >&2
    fi
  done
  printf '  %-66s %4ss\n' "TOTAL (wall clock)" "$((SECONDS - VERIFY_START))" >&2
  printf '%s\n' "=====================================================" >&2
  printf '  %s\n' "MODE: --${MODE}$([ "$UVI_PARALLEL" = "1" ] && echo " (stages overlapped where the registry declares them independent)")" >&2
  if [ "$MODE" = "fast" ] || [ "$MODE" = "change" ]; then
    printf '  %s\n' "This run is a DEVELOPER mode. Unless its selection escalated it did not evaluate" >&2
    printf '  %s\n' "the coverage floor, and it is not evidence of certification: run ./verify.sh --full." >&2
  fi
  if [ "${#STAGES_FAIL[@]}" -gt 0 ]; then
    ucos_err "VERIFICATION FAILED (${#STAGES_FAIL[@]} stage(s))."
    exit 1
  fi
  ucos_ok "VERIFICATION PASSED — every stage this mode admits is green."
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
# THE ARGV IS NOT CHOSEN HERE ANY MORE, AND THAT IS THE POINT. It used to be assembled
# by this block: a mode test, a call to the impact engine, a shell word-split of its
# stdout into a pytest command line. Selection, escalation, coverage policy and process
# topology were four decisions taken in bash, one of them by splitting a string on
# whitespace. They are now one decision, taken once, in Stage 0b, by an engine that is
# itself tested and measured under the coverage floor — and `run-tests` executes exactly
# the plan `--explain` printed, which is what makes the plan honest rather than a
# description of something else.
#
# What that engine does with this stage, per the constitution: --integration and --full
# run the whole suite under the floor and are the only certification-eligible paths;
# --fast and --change run the selection with --no-cov so they cannot become a second
# owner of the floor; and any selection that ESCALATES runs the whole suite WITH the
# floor, exactly as the certification path would have run it. Under every mode the
# selection is partitioned into shards that run concurrently, and under the floor their
# coverage data is combined so the floor is evaluated once, over the union, by the
# coverage tool itself.
#
# The STAGE LABEL is not mode-dependent and must not become so. There is exactly one
# `run_stage "pytest + coverage gate (--cov-fail-under=90)"` line in this file, because
# platform/tests/test_canonical_validation_evidence.py derives the verification contract
# and its sha256 digest from these literals — a per-mode label would make the contract
# depend on how the run was invoked, which is precisely what a contract must not do.
PYTEST_ARGV=(-m engine.verification_intelligence run-tests --mode "$MODE")
if [ "$UVI_PLAN_OK" != "1" ]; then
  # No plan was produced, so there is no selection to trust. Run everything, under the
  # floor, exactly as the certification path would.
  PYTEST_ARGV=(-m pytest)
fi
run_stage "pytest + coverage gate (--cov-fail-under=90)" "$PY" "${PYTEST_ARGV[@]}"


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

# --- Stage 6f: universal infinite scope and direction (UISD-000001) ---------------
# Whether the architecture is still capable of growing. The unboundedness property was
# certified in prose on 2026-07-23 — 16 axes in 03-CONSTITUTIONAL-UNBOUNDEDNESS-
# CERTIFICATION.md, 23 finite-assumption axes in 04-HIDDEN-FINITE-ASSUMPTION-
# CERTIFICATION.md — but that second document records in its own §4 that no exhaustive
# proof of absence was performed and confines the residual risk to the realization
# layers. A property asserted in a dated document decays; this stage computes it.
#
# What it does NOT assert, because the assertion would be false and the stage would get
# deleted rather than fixed: that no enumeration is closed anywhere. engine/uckp/facets.py
# closes 33 facets deliberately so that every vocabulary inside them stays open — closure
# of the QUESTION set is what keeps the ANSWER sets infinite. The refused condition is
# UNDISCLOSED closure: an enumeration closed while nothing states what closes it or how a
# member is admitted. Ten enumerations are disclosed; one is disclosed as unintentional
# and carries gap ISD-G-01, which is the honest answer rather than a silent pass.
#
# The ten laws are each computed, never asserted: ISD-L-01 scope capacity, L-02 direction
# capacity (the edge schema's type must be pattern-bound, never enum-bound), L-03 the
# principle inherits its own lifecycle and holds a birth record, L-04 the lifecycle stage
# graph declares itself open AND its executable projection has not drifted, L-05 the
# evolution cycle has no terminal stage and wraps, L-06 a relationship vocabulary admits a
# new term IN MEMORY without mutating the original — openness performed, not claimed —
# L-07 no active permanence declaration (a ratchet over 15 classified sites), L-08 every
# baseline surface parses its coordinate or discloses the owner it is deferred to, L-09 no
# runtime pin and no version ceiling, L-10 the capability model declares itself non-final.
#
# OBSERVE MODE. It reads the declaration, reads declared files, imports located modules
# in-process, computes, and writes nothing — including to gitignored paths. No clock, no
# network, no subprocess, so it cannot dirty the tree and cannot flake. Exit 1 means a law
# was measured and refused; exit 2 means no verdict could be reached.
run_stage "universal infinite scope and direction (UISD-000001, unbounded and self-applied)" \
  "$PY" -m engine.infinite_scope.gate --quiet

# --- Stage 6g: constitutional primitive alignment (UCPA-000001) -------------------
# The root ontology was correct and unenforced. BEING, EXISTENCE, RELATIONSHIP and
# TRANSFORMATION were adjudicated and RATIFIED (UCOS-RAT-001 RAT-01/02/03, recorded at
# 01-WORKING/SUPERSESSION-REGISTER.md SUP-01/02/07), and then lived only as markdown:
# ONT-02, ONT-03 and ONT-04 appeared in no .py and no .json file anywhere in the tree. No
# gate measured them, so the canonical register's own reduction obligation was asserted
# and never computed, and an edit reinstating the superseded 5-primitive chain — or
# re-promoting BEING to an addressable layer — would have passed ./verify.sh --full.
#
# Separately, the 33-facet model (engine/uckp/facets.py) and the root primitives were
# co-resident and unreconciled: no artifact related a facet to a primitive. This stage
# carries that mapping and measures it, which is what Phase 1 Scope A asked for.
#
# It legislates NOTHING. Every primitive it names must first be found in the register that
# owns it, and the facet side is IMPORTED rather than restated, so the mapping cannot
# silently drift from the model it maps — it can only fail. A thirty-fourth facet admitted
# without a reduction closes this gate, which is correct: facets.py states that a new facet
# is a constitutional amendment, and an amendment must not pass unnoticed.
#
# The eight laws are computed, never asserted: UCPA-L-01 every bound primitive is an
# element the canonical register already declares, by id AND by element name, L-02 standing
# is read out of the ratification record rather than assumed, L-03 the facet reduction is
# total and single-valued over the live enumeration in both directions, L-04 nothing
# reduces to the axiom — RAT-01 made executable, L-05 every classified projection resolves
# and every superseded one is named by a superseding instrument that names it back, L-06
# exactly one authority and it is the one 00-MASTER/URRC-000001 already binds, L-07 the
# primitive set admits a future member — openness performed in memory, never persisted —
# L-08 the programme reduces to a primitive it declares rather than exempting itself.
#
# OBSERVE MODE. It reads the declaration, reads declared files, imports the facet model
# in-process, computes, and writes nothing — including to gitignored paths. No clock, no
# network, no subprocess, so it cannot dirty the tree and cannot flake. Exit 1 means a law
# was measured and refused; exit 2 means no verdict could be reached.
run_stage "constitutional primitive alignment (UCPA-000001, root ontology measured and reduced)" \
  "$PY" -m engine.root_ontology.gate --quiet

# --- Stage 6h: universal verification intelligence (UVI-000001) -------------------
# The stage that measures the thing deciding what the other stages do. Every gate above
# answers "is the repository compliant"; this one answers "is the verification that just
# ran the verification it claimed to be". Before it existed, the selector could have
# narrowed a run, a mode could have claimed a floor it never evaluated, a shard plan could
# have dropped a test object, and every one of those would have shown up as a faster green
# run — the most dangerous possible failure mode for a verification selector, because its
# symptom is indistinguishable from success.
#
# The ten laws are computed, never asserted: UVI-L-01 the flags this script accepts and the
# modes the constitution declares are the same set in both directions, L-02 the bare
# invocation resolves to the one declared default, L-03 the stage labels below and the
# stage registry agree exactly and in order, L-04 the ratchet — every gate the certification
# default ran before this rework is still declared AND still admitted by every
# certification-eligible mode, L-05 no mode claims more than it measures (certification
# requires the whole suite, the floor, and no evidence reuse), L-06 selection is derived
# rather than authored, measured over the engine's evaluated string constants so that a
# docstring may discuss a test file and a code path may not name one, L-07 fail wide,
# performed rather than described — three synthetic unbounded changes are put through the
# selector and each must widen, L-08 topology neutrality, performed — the suite is
# partitioned at six worker counts and every partition must be exactly the suite, L-09 no
# certification-eligible mode can reach a reuse decision at all, L-10 planning twice over
# one state produces identical bytes and no plan carries a clock or a machine path.
#
# OBSERVE MODE. It reads the declaration, this script and its own sources, plans in memory,
# and writes nothing — including to gitignored paths. No clock, no network, no subprocess,
# so it cannot dirty the tree and cannot flake. Exit 1 means a law was measured and refused;
# exit 2 means no verdict could be reached, which is deliberately a different answer.
run_stage "universal verification intelligence (UVI-000001, selection derived and assurance preserved)" \
  "$PY" -m engine.verification_intelligence.gate --gate --quiet

# --- Stage 7 (POST): coverage report (explicit coverage tool invocation) ---------
# The pytest stage already produced .coverage + coverage.xml; re-summarize with the
# coverage CLI to prove the coverage tool itself resolves and to surface the total.
#
# The registry classifies this stage POST and declares it depends on the pytest stage,
# which is what moved it here from immediately after that stage: POST means "reads what
# MAIN produced", and a stage that reads MAIN's output cannot overlap MAIN. Placing it
# after the last MAIN stage is what lets every gate above it run concurrently — the
# ordering is derived from the declared dependency, not from taste.
#
# The plan skips it under --fast and --change, which run --no-cov: there is no coverage
# data to summarise, and printing a stale total would be worse than printing none. A
# developer run whose selection ESCALATED is the exception — it ran under the floor, so
# the plan turns this stage back on.
run_stage "coverage report" "$PY" -m coverage report

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
