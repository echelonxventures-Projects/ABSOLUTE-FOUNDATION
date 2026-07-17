#!/usr/bin/env bash
#
# UCOS Ω∞ — Canonical Verification Entry Point.
#
#   ./verify.sh              lint + tests/coverage + governance enforcement (read-only gate)
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
run_stage() {
  local label="$1"; shift
  ucos_log "STAGE: ${label}"
  STAGES_RUN+=("$label")
  set +e
  ( cd "$UCOS_REPO" && "$@" )
  local rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    ucos_err "STAGE FAILED (exit $rc): ${label}"
    STAGES_FAIL+=("$label")
    [ "$FAILFAST" = "1" ] && summarize_and_exit
  else
    ucos_ok "STAGE PASSED: ${label}"
  fi
}

summarize_and_exit() {
  printf '\n%s\n' "================ VERIFICATION SUMMARY ================" >&2
  local s
  for s in "${STAGES_RUN[@]}"; do
    if printf '%s\n' "${STAGES_FAIL[@]:-}" | grep -qxF "$s"; then
      printf '  %sFAIL%s  %s\n' "$_UC_R" "$_UC_0" "$s" >&2
    else
      printf '  %sPASS%s  %s\n' "$_UC_G" "$_UC_0" "$s" >&2
    fi
  done
  printf '%s\n' "=====================================================" >&2
  if [ "${#STAGES_FAIL[@]}" -gt 0 ]; then
    ucos_err "VERIFICATION FAILED (${#STAGES_FAIL[@]} stage(s))."
    exit 1
  fi
  ucos_ok "VERIFICATION PASSED — all gates green (reproduced without manual venv activation)."
  exit 0
}

# --- Stage 1: lint (ruff) — CD-01 / CD-04 ----------------------------------------
run_stage "ruff lint (engine + platform)" "$PY" -m ruff check engine platform

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

# --- Stage 5 (opt-in): full registration transaction + drift gate ----------------
# register.sh regenerates the synchronized registers and fails on drift; it mutates
# generated DATA/REGISTRIES/CONTROL-TOWER/PORTAL, so it is opt-in for local runs.
if [ "$FULL" = "1" ]; then
  run_stage "registration + drift gate (register.sh --guard)" \
    env PYTHON="$PY" bash 00-BOOK/tools/register.sh --guard
fi

summarize_and_exit
