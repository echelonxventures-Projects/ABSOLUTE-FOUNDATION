#!/usr/bin/env bash
#
# UCOS Ω∞ — REG-AUTO-001 Atomic Artifact Registration Transaction
#            + UMB-IMP-001 Automatic Registration & Enforcement Realization.
#
# Realizes the governing law "Artifact Creation = Artifact Registration". Running
# this script is the single, idempotent, all-or-nothing operation that brings the
# repository's synchronized state (Artifact Registry, Execution/Control-Tower,
# Digital Twin, Traceability/Knowledge-Graph, Dependencies, Navigation Portal)
# into agreement with the physical artifacts on disk — now bracketed by two
# enforcement gates (UMB-IMP-001) so no unregistered, unclassified, or invalid
# artifact can silently enter the corpus.
#
# The transaction is COMPLETE only if every phase succeeds. If any phase fails,
# the transaction is INCOMPLETE, newly-created artifacts remain UNREGISTERED, and
# any completion claim over them is INVALID (REG-AUTO-001 §7 Atomic Creation Law).
#
# Because ukb.py allocates IDs/pages append-only from an immutable ledger and both
# engines regenerate deterministically, this script is safe to run repeatedly.
#
# Usage:
#   00-BOOK/tools/register.sh                 # run the full registration transaction
#   00-BOOK/tools/register.sh --guard         # transaction + drift gate (CI/pre-commit)
#   00-BOOK/tools/register.sh --strict         # also fail on OTHER/MISC-classified artifacts
#   00-BOOK/tools/register.sh --install-hooks  # install the opt-in git pre-commit gate
#
# --guard additionally fails (exit 3) if, after registration, the generated DATA/
# REGISTRIES/CONTROL-TOWER/PORTAL differ from what is committed — proving an
# artifact was created or changed without its registration being committed.
#
# Standard tooling only: bash + python3 + git.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOK_DIR="$(dirname "$HERE")"
REPO="$(dirname "$BOOK_DIR")"
PY="${PYTHON:-python3}"

GUARD=0
STRICT=0
INSTALL_HOOKS=0
for arg in "$@"; do
  case "$arg" in
    --guard) GUARD=1 ;;
    --strict) STRICT=1 ;;
    --install-hooks) INSTALL_HOOKS=1 ;;
    *) echo "unknown option: $arg" >&2; exit 64 ;;
  esac
done
STRICT_FLAG=""; [ "$STRICT" = "1" ] && STRICT_FLAG="--strict"

cd "$REPO"

# --- Opt-in commit-time gate installer (UMB-IMP-001 gate 2 / REG-AUTO-001 §16.2) --
# Writes a git pre-commit hook that runs `register.sh --guard`. It never modifies
# git config; it only creates a hook file, and only if a git work tree exists.
if [ "$INSTALL_HOOKS" = "1" ]; then
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Not a git work tree — cannot install pre-commit hook." >&2; exit 1
  fi
  HOOKS_DIR="$(git rev-parse --git-path hooks)"
  mkdir -p "$HOOKS_DIR"
  HOOK="$HOOKS_DIR/pre-commit"
  cat > "$HOOK" <<'EOF'
#!/usr/bin/env bash
# UCOS Ω∞ REG-AUTO-001/UMB-IMP-001 commit-time enforcement gate (auto-installed).
# Blocks any commit whose synchronized registers are stale or whose artifacts are
# unregistered/invalid. Remove this file to uninstall.
exec "$(git rev-parse --show-toplevel)/00-BOOK/tools/register.sh" --guard
EOF
  chmod +x "$HOOK"
  echo "Installed commit-time enforcement gate: $HOOK"
  echo "(uninstall by deleting that file; git config was not modified.)"
  exit 0
fi

# --- Re-entrancy guard --------------------------------------------------------
# Registration regenerates .md pages under PORTAL/REGISTRIES; if an authoring hook
# fires on those creates it would re-enter this script. A lock makes any nested
# invocation an immediate no-op, and also prevents concurrent runs from racing the
# append-only ledger. The lock lives under tools/ (outside the scan and the guard
# set) so it never appears as registration drift. Stale locks (>1h) are reclaimed.
LOCK="$HERE/.register.lock"
if [ -f "$LOCK" ]; then
  if [ "$(( $(date +%s) - $(cat "$LOCK" 2>/dev/null || echo 0) ))" -lt 3600 ]; then
    echo "register.sh already running (lock $LOCK) — nested/concurrent call is a no-op."
    exit 0
  fi
fi
date +%s > "$LOCK"
cleanup() { rm -f "$LOCK"; }
trap cleanup EXIT

echo "== REG-AUTO-001 Atomic Artifact Registration Transaction (UMB-IMP-001 gated) =="
echo "   repo: $REPO"

fail() { echo "TRANSACTION INCOMPLETE — $1" >&2; echo "Artifacts remain UNREGISTERED; completion claims INVALID." >&2; exit "${2:-1}"; }

# --- Gate 0 — Pre-registration enforcement (UMB-IMP-001) --------------------------
# Blocks the transaction if any NEWLY-created (unregistered) in-scope artifact is
# invalid or unclassified — so it cannot silently enter the corpus.
echo "-- Phase 0/10: ukb enforce --pre (pre-registration eligibility/validity/classification gate)"
"$PY" "$HERE/ukb.py" enforce --pre $STRICT_FLAG || fail "pre-registration enforcement gate failed" 4

# --- Phase 1 — Foundation registration (Artifact Registry + Execution Registry +
#               Control Tower baseline + Traceability/Knowledge Graph + Deps) -----
echo "-- Phase 1/10: ukb build (registry, pages, graph, control-tower baseline)"
"$PY" "$HERE/ukb.py" build            || fail "ukb build failed" 1

# --- Phase 2 — State synchronization (UMB-IMP-004): discover connectors, detect
#               change since cursor, execute, verify, audit, recover. `--due`
#               respects each connector's cadence so the transaction is cheap in
#               steady state and idempotent (no new signals => no audit growth). -
echo "-- Phase 2/10: ukbx sync --due (live connectors + auto synchronization)"
"$PY" "$HERE/ukbx.py" sync --due      || fail "state synchronization failed" 1

# --- Phase 3 — Digital Twin synchronization + Control Tower dimension refresh -----
echo "-- Phase 3/10: ukbx twin (digital twin + automated control-tower dimensions)"
"$PY" "$HERE/ukbx.py" twin            || fail "ukbx twin failed" 1

# --- Phase 4 — Navigation portal regeneration (no dead ends) ----------------------
echo "-- Phase 4/10: ukbx portal (navigation portal)"
"$PY" "$HERE/ukbx.py" portal          || fail "ukbx portal failed" 1

# --- Phase 5 — Foundation validation (append-only, no dup ids/pages, ref integrity)
echo "-- Phase 5/10: ukb validate (structural + schema invariants)"
"$PY" "$HERE/ukb.py" validate         || fail "ukb validate failed" 2

# --- Phase 6 — Twin validation (signals, provenance, secret-free) -----------------
echo "-- Phase 6/10: ukbx validate (signal ledger integrity)"
"$PY" "$HERE/ukbx.py" validate        || fail "ukbx validate failed" 2

# --- Phase 7 — Digital-Twin Certification (UKB-014 hard checks) --------------------
echo "-- Phase 7/10: ukbx twin --check (digital-twin certification)"
"$PY" "$HERE/ukbx.py" twin --check    || fail "digital-twin certification failed" 2

# --- Phase 8 — Digital-Twin Certification Runtime (UMB-IMP-006): 9 integrity
#               domains (identity/registry/traceability/knowledge-graph/change/
#               version/lineage/synchronization/twin-intelligence) over the REAL
#               state; generates evidence + append-only audit trail + report; a
#               failed domain names the exact defect and fails the transaction. --
echo "-- Phase 8/10: ukbx certify (digital-twin certification runtime — 9 integrity domains)"
"$PY" "$HERE/ukbx.py" certify         || fail "digital-twin certification runtime failed" 2

# --- Gate 9 — Post-registration enforcement (UMB-IMP-001) -------------------------
# Asserts registration completeness (every eligible file is now registered) and
# validity; records the outcome in the append-only enforcement audit log.
echo "-- Phase 9/10: ukb enforce (post-registration completeness/parity gate + audit)"
"$PY" "$HERE/ukb.py" enforce $STRICT_FLAG || fail "post-registration enforcement gate failed" 4

echo "-- Phase 10/10: transaction sealed"
echo "TRANSACTION COMPLETE — every artifact on disk is registered, classified, validated, and synchronized."

# Release the re-entrancy lock before the (optional) drift gate so it can never be
# seen as an untracked file by any tree inspection.
rm -f "$LOCK"; trap - EXIT

# --- Optional drift gate (CI / pre-commit) ----------------------------------------
if [ "$GUARD" = "1" ]; then
  echo "-- Guard: checking committed synchronized state for drift"
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "   (not a git work tree; skipping drift gate)"; exit 0
  fi
  DIRTY="$(git status --porcelain -- \
      00-BOOK/DATA 00-BOOK/REGISTRIES 00-BOOK/CONTROL-TOWER 00-BOOK/PORTAL 2>/dev/null || true)"
  if [ -n "$DIRTY" ]; then
    echo "REGISTRATION DRIFT DETECTED — synchronized state was not committed:" >&2
    echo "$DIRTY" >&2
    echo "An artifact was created or modified without committing its registration." >&2
    echo "Stage the regenerated DATA/REGISTRIES/CONTROL-TOWER/PORTAL and recommit." >&2
    exit 3
  fi
  echo "Guard PASSED — repository, registry, control tower, twin, and portal are in sync."
fi
