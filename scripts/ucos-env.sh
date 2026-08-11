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
# Returns 0 iff every pinned dev tool is present at exactly the pinned version AND
# every executable that tool's own installed-files manifest declares is present in
# the venv script directory and executable.
#
# Metadata alone is NOT sufficient, and the difference is not theoretical. A pinned
# tool can be RECORDED at the correct version while its executable is absent: an
# interrupted or partially completed reinstall leaves the import package, the
# version and the dist-info intact but never writes bin/<tool>. A metadata-only
# check then reports "already present and at expected versions", ucos_install_deps
# is never invoked, and the tool fails at the point of use instead of at the point
# of verification — which is the opposite of a self-healing environment. Measured
# consequence: bin/ruff was absent while `metadata.version("ruff")` returned the
# pinned 0.8.4, so this function reported a healthy toolchain, no repair was
# attempted, and verify.sh Stage 1 failed with FileNotFoundError on every run. That
# in turn failed the fixed-point gate's CK-VERIFY and STAGE-VERIFY, and the
# resulting certifier residue closed G-15 over an otherwise convergent repository.
#
# The executable set is DERIVED from each distribution's own manifest, never listed
# here, so it needs no edit when a pin is added or changed, and it covers wheel data
# scripts that declare no console_scripts entry point. That last case is exactly the
# ruff case: ruff ships its binary as a wheel script with an EMPTY console_scripts
# group, so an entry-points-based check would miss the only executable that mattered.
ucos_deps_ok() {
  local py; py="$(ucos_venv_python)"
  [ -x "$py" ] || return 1
  local expected; expected="$(ucos_expected_deps "$py")"
  [ -n "$expected" ] || return 1
  "$py" - <<PY
import csv
import io
import os
import sys
import sysconfig
from importlib import metadata
from pathlib import Path

expected = """$expected"""
alias = {"pytest_cov": "pytest-cov"}
scripts_dir = Path(sysconfig.get_path("scripts")).resolve()
ok = True

for line in expected.strip().splitlines():
    name, want = line.split()
    pkg = alias.get(name, name.replace("_", "-"))

    # 1. the package is installed, at the pinned version
    try:
        dist = metadata.distribution(pkg)
    except Exception:
        print(f"MISSING {pkg}", file=sys.stderr)
        ok = False
        continue
    if dist.version != want:
        print(f"DRIFT {pkg}: have {dist.version} want {want}", file=sys.stderr)
        ok = False

    # 2. every executable the package itself declares is installed and usable.
    #    RECORD is read DIRECTLY rather than through Distribution.files, because
    #    Distribution.files applies skip_missing_files() and therefore silently
    #    OMITS any recorded file that is absent from disk — it hides precisely the
    #    condition this check exists to detect. Measured: with bin/ruff deleted,
    #    dist.files yielded 10 entries and none of them was the bin entry, while
    #    RECORD line 1 still read "../../../bin/ruff,sha256=...,27802040". A files()
    #    based check is therefore inert by construction.
    record = dist.read_text("RECORD")
    if record is None:
        print(f"NORECORD {pkg}: installed-files manifest absent, executables unverifiable",
              file=sys.stderr)
        ok = False
        continue
    base = Path(dist.locate_file("")).resolve()
    for row in csv.reader(io.StringIO(record)):
        if not row or not row[0]:
            continue
        try:
            located = (base / row[0]).resolve()
        except Exception:
            continue
        if located.parent != scripts_dir:
            continue
        if not located.is_file():
            print(f"NOSCRIPT {pkg}: {located} is declared by the package but absent",
                  file=sys.stderr)
            ok = False
        elif not os.access(located, os.X_OK):
            print(f"NOEXEC {pkg}: {located} is present but not executable", file=sys.stderr)
            ok = False

sys.exit(0 if ok else 1)
PY
}

# --- Install / repair the pinned toolchain --------------------------------------
# Two passes, because the ordinary install cannot repair a missing executable.
# pip treats a requirement as SATISFIED when the version metadata is present, so a
# distribution whose bin/<tool> has been lost is left untouched by `pip install -e
# '.[dev]'` — measured: with bin/ruff deleted, the editable install completed quietly
# and bin/ruff was still absent, so ucos_deps_ok failed a second time and
# ucos_ensure_venv aborted. The repair pass therefore force-reinstalls the pinned dev
# tools at their pinned versions, and runs ONLY when the first pass left the toolchain
# unhealthy, so the common case pays nothing for it. --no-deps keeps the blast radius
# to the declared pins and cannot perturb the resolved dependency set.
ucos_install_deps() {
  local py; py="$(ucos_venv_python)"
  ucos_log "Installing pinned toolchain into ${UCOS_VENV_DIR} (pip install -e '.[dev]')"
  "$py" -m pip install --disable-pip-version-check --quiet --upgrade pip >&2
  ( cd "$UCOS_REPO" && "$py" -m pip install --disable-pip-version-check --quiet -e ".[dev]" >&2 )

  if ucos_deps_ok 2>/dev/null; then
    return 0
  fi

  ucos_warn "toolchain still incomplete after install (a pinned executable is missing or unusable); forcing reinstall of the pinned dev tools"
  local specs=()
  local name want
  while read -r name want; do
    [ -n "${name:-}" ] || continue
    [ -n "${want:-}" ] || continue
    specs+=("$(printf '%s' "$name" | tr '_' '-')==${want}")
  done < <(ucos_expected_deps "$py")
  if [ "${#specs[@]}" -gt 0 ]; then
    ucos_log "Forcing reinstall: ${specs[*]}"
    "$py" -m pip install --disable-pip-version-check --quiet \
      --force-reinstall --no-deps "${specs[@]}" >&2
  fi
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


# --- Canonical ruff quality gate (SINGLE SOURCE OF TRUTH) ------------------------
# The lint + format-check gate that every fast verification path must run identically:
#   * verify.sh   Stage 1 (the canonical gate)
#   * the pre-commit hook installed by scripts/install-hooks.sh
# Defining it here — the file both already source — guarantees the two paths can never
# drift (the RC-1 gate-reconciliation invariant: "verify.sh passes => pre-commit passes").
# Runs the pinned ruff via the venv interpreter by ABSOLUTE PATH (no activation, no PATH
# dependency). ruff format --check is a NON-mutating check (it never rewrites files); use
# `make format` to apply formatting.
ucos_ruff_gate() {
  # UCOS-GOV-LINT-BOUNDARY: lint scope is the git-tracked file set, not the filesystem.
  #
  # WHY: ruff receives directory arguments and walks all .py files it finds — including
  # untracked files (macOS Finder " 2" copies, ephemeral editors, generated transients).
  # An untracked file with a lint error blocks every legitimate commit regardless of
  # whether that file will ever be committed. The pre-commit hook exists to validate
  # *the intended mutation* (staged + tracked content), not arbitrary filesystem state.
  #
  # HOW: git ls-files returns only tracked paths. We filter to Python files under the
  # governed source roots (engine/ platform/) and pass them explicitly.  This preserves
  # the RC-1 invariant ("verify.sh passes ⇒ pre-commit passes") because verify.sh also
  # calls this function — both paths now operate on the identical tracked boundary.
  #
  # GOVERNANCE VISIBILITY: untracked files are NOT hidden from governance. RIB GATE-12
  # (dirty_entries_outside_generated) and VAL-02 still surface them as working-tree
  # contamination — they are classified, not silently ignored.
  #
  # IMPLEMENTATION NOTE: if no tracked Python files exist in engine/ or platform/ the
  # gate becomes a no-op and exits 0, which is correct (nothing to lint).
  local py; py="$(ucos_venv_python)"
  local repo; repo="$(git rev-parse --show-toplevel)"

  # Build the tracked file list scoped to the governed source roots.
  local tracked_py
  tracked_py=$(git -C "$repo" ls-files -- 'engine/*.py' 'engine/**/*.py' \
                                          'platform/*.py' 'platform/**/*.py' 2>/dev/null \
               | sed "s|^|$repo/|")

  if [[ -z "$tracked_py" ]]; then
    ucos_ok "ruff gate: no tracked Python files in engine/ or platform/ — skipping"
    return 0
  fi

  # Pass the explicit file list. xargs handles argument-length limits.
  # ruff check: lint violations exit 1; ruff format --check: format drift exits 1.
  echo "$tracked_py" | xargs "$py" -m ruff check
  echo "$tracked_py" | xargs "$py" -m ruff format --check
}
