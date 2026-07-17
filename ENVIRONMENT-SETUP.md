# UCOS Ω∞ — Environment Setup

Canonical, reproducible setup for the UCOS EC-1 engine + platform verification
environment. This document plus the three entry-point scripts (`bootstrap.sh`,
`doctor.sh`, `verify.sh`) are the **complete** setup knowledge — there is no hidden
tribal knowledge and **no manual `source .../activate` step**.

---

## TL;DR (fresh clone → verified)

```bash
git clone <repo> && cd <repo>
./bootstrap.sh      # create/repair canonical venv + pinned toolchain, then validate
./verify.sh         # lint + tests/coverage + governance enforcement (exits non-zero on failure)
```

`make bootstrap` / `make doctor` / `make verify` are equivalent.

---

## Canonical execution environment

| Component    | Canonical requirement | Source of truth |
|--------------|----------------------|-----------------|
| Python       | **3.12** (`major.minor`) | `.github/workflows/*.yml` (`actions/setup-python` → 3.12); `pyproject.toml requires-python >=3.12` |
| pytest       | **8.3.4**            | `pyproject.toml [project.optional-dependencies].dev` |
| pytest-cov   | **6.0.0**            | same |
| coverage     | **7.15.2**           | same (pinned explicitly for reproducibility) |
| ruff         | **0.8.4**            | same |
| virtualenv   | `.ec1-venv/` (repo-local, `.gitignore`d, disposable) | `scripts/ucos-env.sh` |
| governance   | `00-BOOK/tools/ukb.py enforce --pre` (read-only gate); `register.sh --guard` (full) | `.github/workflows/ucos-registration-gate.yml` |

**Runtime code is stdlib-only** (constitutional TP-04/TP-05); the pinned packages
above are *verification tooling only*, installed into `.ec1-venv` via
`pip install -e ".[dev]"`.

The same environment produced the **EPIC-007 / 008 / 009 / 010** verifications: the
pinned `.[dev]` toolchain run against an in-repo `.ec1-venv`, driven by the `pytest`
`addopts` (`--cov=…`, `--cov-fail-under=90`) in `pyproject.toml`, plus `ruff check`
and the governance enforcement gate. The only drift observed was the venv's
**Python interpreter** (a local `.ec1-venv` had been built with Python 3.14 while CI
pins 3.12); `bootstrap.sh`/`doctor.sh` now detect and auto-heal that drift.

---

## Root-cause analysis (why a fresh shell failed verification)

The recurring failures — `pytest: error: unrecognized arguments: --cov…`,
`ruff: command not found`, `coverage: command not found`, "verification only works if
a specific venv was activated" — all share **one** root cause:

> Verification depended on **PATH state established by `source .ec1-venv/bin/activate`**.
> Nothing in the repo guaranteed that state, so results depended on whether a human
> remembered to activate the right venv.

Two concrete failure modes fall out of that:

1. **`ruff` / `coverage` "command not found"** — those executables only exist on
   `PATH` *inside* an activated `.ec1-venv`. A brand-new terminal has neither.
2. **`pytest: unrecognized arguments: --cov`** — a *global* `pytest` (e.g.
   `/opt/homebrew/bin/pytest`) is on `PATH` but has **no `pytest-cov`**, so the
   `--cov` options that `pyproject.toml` injects via `addopts` are unrecognized. This
   was reproduced directly:

   ```
   $ /opt/homebrew/bin/pytest --co -q
   pytest: error: unrecognized arguments: --cov=engine.foundation … --cov-fail-under=90
   ```

Contributing factors (all now addressed):

| Factor | Before | After |
|--------|--------|-------|
| Missing bootstrap | none | `bootstrap.sh` |
| Missing activation | manual `source …/activate` | eliminated — tools invoked via `$(venv)/bin/python -m …` by absolute path |
| Missing env validation | none | `doctor.sh` |
| Missing canonical command | none | `verify.sh` / `make verify` |
| pyproject dependency gap | `coverage` unpinned (transitive) | `coverage==7.15.2` pinned in `[dev]` |
| venv Python drift | `.ec1-venv` built with 3.14 vs CI 3.12 | auto-detected + auto-recreated to 3.12 |
| PATH drift / global pytest shadowing | possible | irrelevant — PATH is never trusted |

---

## How the remediation works

`scripts/ucos-env.sh` is the single source of truth, sourced by all three entry
points. Its invariants:

1. **Never trust PATH.** Every tool runs as `"$(ucos_venv_python)" -m <tool>`
   (absolute path into `.ec1-venv`).
2. **Never require activation.** No script emits or expects `source …/activate`.
3. **Self-heal the venv.** If `.ec1-venv` is missing, or its Python `major.minor`
   differs from the canonical series, it is (re)created from `python3.12`. The venv
   is disposable and `.gitignore`d, so recreation is safe.
4. **Self-heal the toolchain.** If any pinned tool is missing or version-drifted,
   `pip install -e ".[dev]"` is re-run. Verified against `pyproject.toml [dev]`.

### Overrides (rarely needed)

| Variable | Default | Purpose |
|----------|---------|---------|
| `UCOS_PYTHON` | _(auto)_ | explicit interpreter to build the venv from |
| `UCOS_PYTHON_SERIES` | `3.12` | canonical `major.minor` the venv must match |
| `UCOS_VENV_DIR` | `<repo>/.ec1-venv` | venv location |
| `UCOS_ALLOW_RECREATE` | `1` | auto-recreate a drifted venv |
| `UCOS_ALLOW_PYTHON_MISMATCH` | `0` | tolerate a non-canonical series instead of failing |

---

## Prerequisites

- **bash**, **git**, and **Python 3.12** available on the machine.
  - macOS: `brew install python@3.12`
  - The interpreter only needs to be discoverable as `python3.12` on `PATH`, or
    passed via `UCOS_PYTHON=/path/to/python3.12`.

Nothing else is required; the pinned verification toolchain is installed
automatically into `.ec1-venv`.

See **VERIFICATION-RUNBOOK.md** for the day-to-day verification workflow and
troubleshooting.
