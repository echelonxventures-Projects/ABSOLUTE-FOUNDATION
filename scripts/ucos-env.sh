#!/usr/bin/env bash
#
# UCOS Ω∞ — Canonical environment library (shared).
#
# This file is *sourced* by bootstrap.sh, doctor.sh, and verify.sh. It is the single
# source of truth for "what the repository-standard execution environment is" and how
# to make a fresh shell converge to it WITHOUT any manual `source .../activate` step.
#
# Root cause it eliminates (see ENVIRONMENT-SETUP.md §Root-Cause):
#   * "ruff: command not found" / "coverage: command not found"  -> tools were only on
#     PATH inside an activated venv; a fresh shell had none of them.
#   * "pytest: unrecognized arguments: --cov"                     -> pytest ran under an
#     interpreter that lacked pytest-cov (the addopts in pyproject require it).
#   * "verification depends on whether a specific venv was activated" -> everything here
#     invokes the venv interpreter by ABSOLUTE PATH (never relies on PATH/activation).
#
# Design invariants:
#   1. Never depend on PATH. Always call "$(ucos_venv_python) -m <tool>".
#   2. Never require the caller to activate a venv.
#   3. The venv (.ec1-venv) is disposable + .gitignored; it is self-healed to match the
#      canonical Python series and the pinned toolchain in pyproject.toml [dev].
#   4. Standard tooling only: bash + a Python interpreter + git.
#
# Overridable via environment (sane defaults; you should rarely need these):
#   UCOS_PYTHON           explicit interpreter to build the venv from (e.g. python3.12)
#   UCOS_PYTHON_SERIES    canonical "major.minor" the venv must match (default 3.12)
#   UCOS_VENV_DIR         venv location (default <repo>/.ec1-venv)
#   UCOS_ALLOW_RECREATE   1 (default) => auto-recreate a venv whose series drifted
#   UCOS_ALLOW_PYTHON_MISMATCH  1 => tolerate a non-canonical series instead of failing

set -euo pipefail

# --- Canonical constants ---------------------------------------------------------
# The CI toolchain (.github/workflows/*.yml) pins actions/setup-python to 3.12, so
# 3.12 is the authoritative series every local verification must reproduce.
UCOS_PYTHON_SERIES="${UCOS_PYTHON_SERIES:-3.12}"

# --- Repo + venv location --------------------------------------------------------
# This library lives in <repo>/scripts/, so the repo root is one level up.
ucos_repo_root() {
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$here/.." && pwd
}
UCOS_REPO="$(ucos_repo_root)"
UCOS_VENV_DIR="${UCOS_VENV_DIR:-$UCOS_REPO/.ec1-venv}"

# --- Logging (all diagnostics go to stderr so stdout stays clean) ----------------
if [ -t 2 ]; then
  _UC_B=$'\033[1m'; _UC_G=$'\033[32m'; _UC_Y=$'\033[33m'; _UC_R=$'\033[31m'; _UC_0=$'\033[0m'
else
  _UC_B=""; _UC_G=""; _UC_Y=""; _UC_R=""; _UC_0=""
fi
ucos_log()  { printf '%s\n' "${_UC_B}==${_UC_0} $*" >&2; }
ucos_ok()   { printf '%s\n' "${_UC_G}✓${_UC_0} $*" >&2; }
ucos_warn() { printf '%s\n' "${_UC_Y}!${_UC_0} $*" >&2; }
ucos_err()  { printf '%s\n' "${_UC_R}✗${_UC_0} $*" >&2; }
ucos_die()  { ucos_err "$*"; exit 1; }

# --- Interpreter resolution ------------------------------------------------------
# Returns the interpreter used to *build* the venv. Prefers the canonical series so a
# fresh venv matches CI. Honors UCOS_PYTHON if the caller pins one explicitly.
ucos_find_interpreter() {
  local cand series
  local -a candidates=()
  [ -n "${UCOS_PYTHON:-}" ] && candidates+=("$UCOS_PYTHON")
  candidates+=("python${UCOS_PYTHON_SERIES}" "python3" "python")

  for cand in "${candidates[@]}"; do
    command -v "$cand" >/dev/null 2>&1 || continue
    series="$("$cand" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null || true)"
    if [ "$series" = "$UCOS_PYTHON_SERIES" ]; then
      command -v "$cand"; return 0
    fi
  done

  # No canonical interpreter found. Fall back to any python3 unless the caller has
  # asked for strict matching.
  for cand in "${candidates[@]}"; do
    command -v "$cand" >/dev/null 2>&1 || { continue; }
    if [ "${UCOS_ALLOW_PYTHON_MISMATCH:-0}" = "1" ]; then
      ucos_warn "Canonical Python ${UCOS_PYTHON_SERIES} not found; using $(command -v "$cand") ($("$cand" --version 2>&1))." >&2
      command -v "$cand"; return 0
    fi
  done

  ucos_err "No Python ${UCOS_PYTHON_SERIES} interpreter found on PATH."
  ucos_err "Install it (macOS: 'brew install python@${UCOS_PYTHON_SERIES}') or set UCOS_PYTHON=/path/to/python."
  ucos_err "To proceed with a different series anyway: UCOS_ALLOW_PYTHON_MISMATCH=1 ..."
  return 1
}

ucos_venv_python() { printf '%s\n' "$UCOS_VENV_DIR/bin/python"; }

ucos_venv_present() { [ -x "$UCOS_VENV_DIR/bin/python" ]; }

ucos_venv_series() {
  ucos_venv_present || return 1
  "$UCOS_VENV_DIR/bin/python" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null
}

# --- Expected pinned toolchain (single source of truth = pyproject.toml [dev]) ---
# Emits "name version" lines. Uses tomllib (stdlib >=3.11).
ucos_expected_deps() {
  local py="$1"
  "$py" - "$UCOS_REPO/pyproject.toml" <<'PY'
import sys, re
try:
    import tomllib
    with open(sys.argv[1], "rb") as f:
        data = tomllib.load(f)
    deps = data.get("project", {}).get("optional-dependencies", {}).get("dev", [])
except Exception:
    deps = []
for spec in deps:
    m = re.match(r"^\s*([A-Za-z0-9_.\-]+)\s*==\s*([^\s;]+)", spec)
    if m:
        print(m.group(1).replace("-", "_").lower(), m.group(2))
PY
}

# --- Dependency verification -----------------------------------------------------
# Returns 0 iff every pinned dev tool is importable at exactly the pinned version.
ucos_deps_ok() {
  local py; py="$(ucos_venv_python)"
  [ -x "$py" ] || return 1
  local expected; expected="$(ucos_expected_deps "$py")"
  [ -n "$expected" ] || return 1
  "$py" - <<PY
import sys
from importlib import metadata
expected = """$expected"""
dist = {"pytest_cov": "pytest-cov"}
ok = True
for line in expected.strip().splitlines():
    name, want = line.split()
    pkg = dist.get(name, name.replace("_", "-"))
    try:
        have = metadata.version(pkg)
    except Exception:
        print(f"MISSING {pkg}", file=sys.stderr); ok = False; continue
    if have != want:
        print(f"DRIFT {pkg}: have {have} want {want}", file=sys.stderr); ok = False
sys.exit(0 if ok else 1)
PY
}

# --- Install / repair the pinned toolchain --------------------------------------
ucos_install_deps() {
  local py; py="$(ucos_venv_python)"
  ucos_log "Installing pinned toolchain into ${UCOS_VENV_DIR} (pip install -e '.[dev]')"
  "$py" -m pip install --disable-pip-version-check --quiet --upgrade pip >&2
  ( cd "$UCOS_REPO" && "$py" -m pip install --disable-pip-version-check --quiet -e ".[dev]" >&2 )
}

# --- Ensure the venv exists, matches the canonical series, and has the toolchain -
# This is the heart of the remediation: after this returns, "$(ucos_venv_python) -m
# pytest|ruff|coverage" is guaranteed to work with the pinned versions, regardless of
# whether any venv was activated in the shell.
ucos_ensure_venv() {
  local desired="$UCOS_PYTHON_SERIES"

  if ucos_venv_present; then
    local cur; cur="$(ucos_venv_series || echo '?')"
    if [ "$cur" != "$desired" ]; then
      if [ "${UCOS_ALLOW_RECREATE:-1}" = "1" ] && [ "${UCOS_ALLOW_PYTHON_MISMATCH:-0}" != "1" ]; then
        ucos_warn "venv Python ${cur} != canonical ${desired}; recreating (.ec1-venv is disposable/.gitignored)."
        rm -rf "$UCOS_VENV_DIR"
      else
        ucos_warn "venv Python ${cur} != canonical ${desired}; continuing without recreate (UCOS_ALLOW_RECREATE=0 or mismatch tolerated)."
      fi
    fi
  fi

  if ! ucos_venv_present; then
    local interp; interp="$(ucos_find_interpreter)" || return 1
    ucos_log "Creating venv at ${UCOS_VENV_DIR} from ${interp} ($("$interp" --version 2>&1))"
    "$interp" -m venv "$UCOS_VENV_DIR"
  fi

  if ucos_deps_ok; then
    ucos_ok "Pinned toolchain already present and at expected versions."
  else
    ucos_install_deps
    ucos_deps_ok || ucos_die "Toolchain still not at pinned versions after install; see errors above."
    ucos_ok "Pinned toolchain installed."
  fi
}
