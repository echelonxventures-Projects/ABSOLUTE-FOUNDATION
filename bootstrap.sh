#!/usr/bin/env bash
#
# UCOS Ω∞ — Fresh-clone Bootstrap.
#
#   ./bootstrap.sh            create/repair the canonical venv + pinned toolchain, then
#                             validate it with the doctor
#   ./bootstrap.sh --verify   also run the full canonical verification afterwards
#
# This is the single documented workflow that turns a fresh `git clone` into a fully
# operational, verifiable checkout — no hidden knowledge, no manual activation:
#
#     git clone <repo> && cd <repo>
#     ./bootstrap.sh            # environment ready
#     ./verify.sh               # reproduce repository verification
#
# It only ever touches the disposable, .gitignored .ec1-venv; source, engine, and
# platform code are never modified.

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=scripts/ucos-env.sh
source "scripts/ucos-env.sh"

DO_VERIFY=0
[ "${1:-}" = "--verify" ] && DO_VERIFY=1

ucos_log "Bootstrapping UCOS canonical environment"
ucos_ensure_venv

ucos_log "Validating environment (doctor)"
./doctor.sh

if [ "$DO_VERIFY" = "1" ]; then
  ucos_log "Running canonical verification"
  exec ./verify.sh
fi

cat >&2 <<EOF

${_UC_G}Environment ready.${_UC_0} Next steps (no venv activation required):

  ./doctor.sh     # re-check environment health
  ./verify.sh     # lint + tests/coverage + governance enforcement
  make verify     # same, via make

EOF
