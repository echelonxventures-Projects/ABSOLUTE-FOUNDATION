#!/usr/bin/env bash
#
# UCOS Ω∞ — Repository Operations Automation (EPIC-PLAT-003, Terminal T5).
#
#   ./repo-ops.sh                 complete repository operational verification
#   ./repo-ops.sh --resume        resume, skipping stages already passed (checkpoint)
#   ./repo-ops.sh --json          also emit the machine-readable report on stdout
#
# THE one command that performs complete repository operational verification using the
# existing canonical engines. Like ./verify.sh, a brand-new terminal can run this with
# NO manual `source .../activate`: it self-heals the canonical venv (correct Python
# series + pinned toolchain), then drives the configuration-driven pipeline through the
# venv interpreter by absolute path.
#
# The pipeline is declared in $UCOS_REPO_OPS_CONFIG (default: repo-operations.json).
# Every stage delegates to existing infrastructure — verify.sh / doctor.sh, the EC-1
# Acceptance / Validation / Certification engines, the frozen-corpus guard, and the
# canonical coverage report. No parallel tooling is created.

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=scripts/ucos-env.sh
source "scripts/ucos-env.sh"

CONFIG="${UCOS_REPO_OPS_CONFIG:-$UCOS_REPO/repo-operations.json}"
CHECKPOINT="${UCOS_REPO_OPS_CHECKPOINT:-$UCOS_REPO/.runtime/repository-operations-checkpoint.json}"

# --- Stage 0: ensure the canonical environment (no activation needed) ------------
ucos_ensure_venv
PY="$(ucos_venv_python)"

ucos_log "Repository operations: $CONFIG"
exec "$PY" -m platform.repository_operations.cli \
  --config "$CONFIG" \
  --repo-root "$UCOS_REPO" \
  --checkpoint "$CHECKPOINT" \
  "$@"
