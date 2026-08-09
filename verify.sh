#!/usr/bin/env bash
#
# UCOS Ω∞ — Canonical Verification Entry Point.
#
#   ./verify.sh              lint + tests/coverage + governance + meta-constitutional gate
#   ./verify.sh --full       also run the full registration + drift gate (register.sh --guard)
#   ./verify.sh --failfast   stop at the first failing stage
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

FULL=0
FAILFAST=0
for arg in "$@"; do
  case "$arg" in
    --full) FULL=1 ;;
    --failfast) FAILFAST=1 ;;
    -h|--help) sed -n '3,12p' "$0"; exit 0 ;;
    *) ucos_die "unknown option: $arg (see ./verify.sh --help)" ;;
  esac
done

# --- Stage 0: ensure the canonical environment (no activation needed) ------------
ucos_ensure_venv
PY="$(ucos_venv_python)"

STAGES_RUN=()
STAGES_FAIL=()
STAGES_SECS=()
VERIFY_START=$SECONDS
run_stage() {
  local label="$1"; shift
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
generate_prerequisites() {
  "$PY" -m engine.knowledge.cli init                          >/dev/null || return 1
  "$PY" -m engine.determinism.reproduce                       >/dev/null || return 1
  "$PY" 00-MASTER/UAKOS-CLOSURE-002/closure_engine.py         >/dev/null || return 1
  "$PY" 00-MASTER/UAKOS-CLOSURE-002/phase2_engine.py          >/dev/null || return 1
  "$PY" 00-MASTER/UAKOS-CLOSURE-002/phase3_engine.py          >/dev/null || return 1
}
run_stage "prerequisite generation (knowledge · determinism · closure 1-3)" \
  generate_prerequisites

# --- Stage 2: tests + coverage gate — CD-02 (pytest addopts drive --cov ≥ 90%) ---
# Running via the venv interpreter guarantees pytest-cov is present, so the --cov
# arguments in pyproject are always recognized.
run_stage "pytest + coverage gate (--cov-fail-under=90)" "$PY" -m pytest

# --- Stage 3: coverage report (explicit coverage tool invocation) ----------------
# pytest-cov already produced .coverage + coverage.xml above; re-summarize with the
# coverage CLI to prove the coverage tool itself resolves and to surface the total.
run_stage "coverage report" "$PY" -m coverage report

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

# --- Stage 7 (opt-in): full registration transaction + drift gate ----------------
# register.sh regenerates the synchronized registers and fails on drift; it mutates
# generated DATA/REGISTRIES/CONTROL-TOWER/PORTAL, so it is opt-in for local runs.
if [ "$FULL" = "1" ]; then
  run_stage "registration + drift gate (register.sh --guard)" \
    env PYTHON="$PY" bash 00-BOOK/tools/register.sh --guard
fi

summarize_and_exit
