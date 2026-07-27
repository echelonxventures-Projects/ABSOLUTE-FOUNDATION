# UCOS Ω∞ — Canonical developer entry points.
#
# Every target delegates to the self-bootstrapping shell entry points so there is a
# single source of truth for environment behavior. None of these require a manually
# activated virtualenv.
#
#   make bootstrap     create/repair the canonical venv + pinned toolchain, validate it
#   make doctor        report + validate the environment (Python/pytest/pytest-cov/coverage/ruff)
#   make verify        THE canonical gate: lint + tests/coverage + governance enforcement
#   make verify-full   verify + full registration/drift gate (register.sh --guard)
#   make repo-ops      complete repository operational verification (EPIC-PLAT-003, T5)
#   make lint          ruff only
#   make test          pytest + coverage gate only
#   make clean-venv    remove the disposable .ec1-venv (recreated on next bootstrap/verify)

.DEFAULT_GOAL := help
.PHONY: help bootstrap doctor verify verify-full lint test format format-check build clean clean-venv hooks repo-ops closure closure-gate closure-phase2 closure-phase2-gate closure-phase3 closure-phase3-gate

VENV := .ec1-venv
PY   := $(VENV)/bin/python

help:
	@echo "UCOS canonical targets:"
	@echo "  make bootstrap     set up + validate the canonical environment (fresh clone)"
	@echo "  make doctor        report + validate tool versions"
	@echo "  make verify        canonical verification (lint + tests/coverage + governance)"
	@echo "  make verify-full   verify + full registration/drift gate"
	@echo "  make repo-ops      complete repository operational verification (EPIC-PLAT-003)"
	@echo "  make closure       regenerate UAKOS-CLOSURE-002 repository-closure artifacts"
	@echo "  make closure-gate  fail-closed closure gate (non-zero exit while gaps remain)"
	@echo "  make closure-phase2      regenerate PHASE-002 concept-graph reconciliation (outputs 20-35)"
	@echo "  make closure-phase2-gate fail-closed PHASE-002 gate (non-zero exit while concept gaps remain)"
	@echo "  make closure-phase3      regenerate PHASE-003 implementation planning (outputs 36-48)"
	@echo "  make closure-phase3-gate fail-closed PHASE-003 gate (non-zero exit while repository NOT-CLOSED)"
	@echo "  make lint          ruff lint only"
	@echo "  make format        ruff format (rewrite engine + platform)"
	@echo "  make format-check  ruff format --check (no writes; CI-style)"
	@echo "  make test          pytest + coverage gate only"
	@echo "  make build         build wheel + sdist via the canonical venv"
	@echo "  make hooks         install the git pre-commit hook (local automation)"
	@echo "  make cmg-gate      fail-closed meta-constitutional gate (CMG-000001)"
	@echo "  make uccep         regenerate the UCCEP-000000 constitutional determinations"
	@echo "  make uccep-gate    fail-closed AGGREGATE constitutional gate (all located gates)"
	@echo "  make uccep-boot    fast read-only aggregate gate (session/pre-commit tier)"
	@echo "  make uccep-full    aggregate gate including the heavy tier (suites + determinism)"
	@echo "  make uccep-self    UCCEP guards over its own surface"
	@echo "  make ucda          regenerate the UCDA-000001 decision-assimilation determinations"
	@echo "  make ucda-gate     fail-closed Implementation Evidence Gate (CEP-002 Art 28)"
	@echo "  make ucda-self     UCDA guards over its own surface"
	@echo "  make uer           regenerate the UER-000001 execution-resilience determinations (Ω∞-001A)"
	@echo "  make uer-gate      fail-closed Execution Resilience Gate (Ω∞-001A exit criteria)"
	@echo "  make uer-self      UER guards over its own surface"
	@echo "  make clean         remove build/test caches (venv preserved)"
	@echo "  make clean-venv    remove the disposable .ec1-venv"

bootstrap:
	@./bootstrap.sh

doctor:
	@./doctor.sh

verify:
	@./verify.sh

verify-full:
	@./verify.sh --full

# repo-ops: EPIC-PLAT-003 (Terminal T5) — one command performs complete repository
# operational verification by orchestrating the canonical engines/scripts. Delegates to
# repo-ops.sh, which self-heals the venv first (no parallel tooling).
repo-ops:
	@./repo-ops.sh

# closure: UAKOS-CLOSURE-002 — regenerate the Vision-to-Repository closure artifacts
# (source inventory, concept inventory, coverage/traceability matrices, gap register,
# closure certificates). Deterministic, stdlib-only; never mutates the frozen corpus.
# CLOSURE_SKIP_CORPUS=1 skips the external corpus scan for a fast repo-only pass.
closure:
	@python3 00-MASTER/UAKOS-CLOSURE-002/closure_engine.py

# closure-gate: fail-closed standing gate — exits non-zero while any constitutional
# gap remains (conversation-only / upload-only / unhomed / duplicate / orphan).
closure-gate:
	@python3 00-MASTER/UAKOS-CLOSURE-002/closure_engine.py --gate

# closure-phase2: UAKOS-CLOSURE-002 · PHASE-002 — regenerate the concept-graph
# reconciliation views (outputs 20-35 + phase2.json) by REUSING the Phase-001 model
# (closure.json) and the canonical typed graph (00-BOOK/DATA/relationships.json).
# Deterministic, stdlib-only; no re-extraction, no fabrication. Depends on `closure`.
closure-phase2: closure
	@python3 00-MASTER/UAKOS-CLOSURE-002/phase2_engine.py

# closure-phase2-gate: fail-closed standing gate for the concept layer — exits non-zero
# while any concept remains unhomed / duplicated / orphaned.
closure-phase2-gate: closure
	@python3 00-MASTER/UAKOS-CLOSURE-002/phase2_engine.py --gate

# closure-phase3: UAKOS-CLOSURE-002 · PHASE-003 — regenerate the canonical implementation
# PLANNING artifacts (outputs 36-48 + phase3.json). Consumes the frozen PHASE-002 baseline
# (closure.json) and produces constitutional plans only — classification, destination, owner,
# dependency DAG, waves, priority, contracts, enrichment execution plan, closure projection.
# Planning only: never modifies Repository Truth, never implements automatically.
closure-phase3: closure-phase2
	@python3 00-MASTER/UAKOS-CLOSURE-002/phase3_engine.py

# closure-phase3-gate: fail-closed — non-zero exit while the repository is NOT-CLOSED
# (planning delivered, authorized execution still pending).
closure-phase3-gate: closure-phase2
	@python3 00-MASTER/UAKOS-CLOSURE-002/phase3_engine.py --gate

# lint/test self-heal the venv first so they never hit "command not found".
lint: bootstrap-quiet
	@$(PY) -m ruff check engine platform

# format/format-check reuse the same pinned ruff as lint (no new tooling).
format: bootstrap-quiet
	@$(PY) -m ruff format engine platform

format-check: bootstrap-quiet
	@$(PY) -m ruff format --check engine platform

test: bootstrap-quiet
	@$(PY) -m pytest

# build mirrors the EC-1 CI "Build (wheel + sdist)" step, run through the canonical
# venv (pinned build==1.2.2, installed on demand so it never pollutes the [dev] set).
build: bootstrap-quiet
	@$(PY) -m pip install --disable-pip-version-check --quiet build==1.2.2 && $(PY) -m build

# hooks: opt-in local automation; reuses scripts/ucos-env.sh + pinned ruff.
hooks:
	@./scripts/install-hooks.sh

.PHONY: bootstrap-quiet
bootstrap-quiet:
	@./bootstrap.sh >/dev/null

# clean removes regenerable build/test caches only; the venv is preserved (use
# clean-venv for that). No source, generated register, or corpus path is touched.
clean:
	@rm -rf .pytest_cache .ruff_cache .mypy_cache build dist ./*.egg-info .coverage coverage.xml \
		&& echo "removed build/test caches (venv preserved — run 'make clean-venv' to reset it)"

clean-venv:
	@rm -rf $(VENV) && echo "removed $(VENV) (run 'make bootstrap' to recreate)"


# cmg-gate: fail-closed meta-constitutional gate (CMG-000001 Article L, LXVI.7).
# Additive only — no existing target, recipe, or dependency above is altered.
# Exit 0 zero findings · 1 findings · 2 fail-closed abort.
.PHONY: cmg-gate
cmg-gate:
	@./00-CMG/tools/cmg-gate.sh


# uccep: UCCEP-000000 — Universal Continuous Constitutional Evolution Programme.
# Additive only — no existing target, recipe, or dependency above is altered.
#
# The AGGREGATE constitutional gate. It executes the gates that already exist and are
# already owned (cmg-gate, ukb enforce/validate, the closure engines, repository health,
# graph invariants, intelligence determinism, verify.sh, the determinism double-build),
# then emits the fifteen programme determinations + the assimilation/findings register
# into 00-MASTER/UCCEP-000000/. AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; writes
# nothing outside its own operational-memory directory (guarded, fail-closed).
#
# Adding a programme, gate, check, invariant or finding is an entry in
# 00-MASTER/UCCEP-000000/uccep-bindings.json and requires NO change to any engine.
#
# Exit 0 every executed blocking check passed · 1 a blocking check failed ·
# 2 fail-closed abort (declaration unusable — no verdict may be asserted).
.PHONY: uccep uccep-gate uccep-boot uccep-full uccep-self
uccep:
	@python3 00-MASTER/UCCEP-000000/uccep_engine.py --tier standard

uccep-gate:
	@python3 00-MASTER/UCCEP-000000/uccep_engine.py --tier standard --gate

uccep-boot:
	@python3 00-MASTER/UCCEP-000000/uccep_engine.py --tier boot --gate

uccep-full: bootstrap-quiet
	@python3 00-MASTER/UCCEP-000000/uccep_engine.py --tier full --gate

# uccep-self: the programme's guards over its own surface — declaration integrity,
# zero-enumeration / data-driven proof, forbidden-write scope, self-determinism.
uccep-self:
	@python3 00-MASTER/UCCEP-000000/uccep_engine.py --check-declaration
	@python3 00-MASTER/UCCEP-000000/uccep_engine.py --check-no-enumeration
	@python3 00-MASTER/UCCEP-000000/uccep_engine.py --check-write-scope
	@python3 00-MASTER/UCCEP-000000/uccep_engine.py --check-determinism


# ucda: UCDA-000001 — Constitutional Decision Assimilation.
# Additive only — no existing target, recipe, or dependency above is altered.
#
# The executable expression of the Implementation Evidence Gate legislated by
# 00-CEP/CEP-002 Article 28 (CEP-002-AMD-002). It asserts that no constitutionally
# agreed decision remains only in conversation history: every decision declared in
# 00-MASTER/UCDA-000001/ucda-decisions.json must name the LOCATED register it was
# recorded in, occupy exactly one stage of the mandatory lifecycle, and carry exactly
# one disposition from the closed set, with the evidence that disposition requires
# resolving against the repository.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; writes nothing outside its own
# operational-memory directory (guarded, fail-closed). Adding a decision, a work
# package, a stage or a disposition is an entry in the declaration and requires NO
# change to the engine.
#
# The gate is also bound into the aggregate gate as G-14 / CK-DECISION-EVIDENCE, so
# `make uccep-gate` and the CI aggregate gate execute it too.
#
# Exit 0 gate OPEN · 1 gate CLOSED (a decision is undispositioned) ·
# 2 fail-closed abort (declaration unusable — no verdict may be asserted).
.PHONY: ucda ucda-gate ucda-self
ucda:
	@python3 00-MASTER/UCDA-000001/ucda_engine.py

ucda-gate:
	@python3 00-MASTER/UCDA-000001/ucda_engine.py --gate

# ucda-self: the programme's guards over its own surface — declaration integrity
# (lifecycle ordering/reachability/terminality, closed disposition set, per-disposition
# evidence obligations), zero-enumeration / data-driven proof, forbidden-write scope,
# self-determinism.
ucda-self:
	@python3 00-MASTER/UCDA-000001/ucda_engine.py --check-declaration
	@python3 00-MASTER/UCDA-000001/ucda_engine.py --check-no-enumeration
	@python3 00-MASTER/UCDA-000001/ucda_engine.py --check-write-scope
	@python3 00-MASTER/UCDA-000001/ucda_engine.py --check-determinism



# uer: UER-000001 — Universal Execution Resilience (UCOS Ω∞ Programme Ω∞-001A).
# Additive only — no existing target, recipe, or dependency above is altered.
#
# The executable expression of the Execution Resilience contract. It creates no
# checkpoint, journal, recovery, atomic-write, resume, ledger, continuation, replay,
# repository-safety or health engine: every one already exists and is certified
# (engine/runtime/execution — EPIC-RTE-002; platform/repository_operations;
# 00-BOOK/tools/governance_telemetry.py; the master recovery/execution instruments).
# It BINDS them into one contract that every future autonomous programme inherits, and
# verifies from Repository Truth that each binding resolves, then emits the fourteen
# constitutional deliverables — the last of which is the continuation package — into
# 00-MASTER/UER-000001/.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; writes nothing outside its own
# operational-memory directory (guarded, fail-closed). Binding a newly proven gap is an
# entry in 00-MASTER/UER-000001/uer-resilience.json and requires NO change to the engine.
#
# Exit 0 gate OPEN · 1 gate CLOSED (a capability/validation/exit criterion is unsatisfied)
# · 2 fail-closed abort (declaration unusable — no verdict may be asserted).
.PHONY: uer uer-gate uer-self
uer:
	@python3 00-MASTER/UER-000001/uer_engine.py

uer-gate:
	@python3 00-MASTER/UER-000001/uer_engine.py --gate

# uer-self: the programme's guards over its own surface — declaration integrity
# (every home/evidence/programme reference resolves; every pipeline step, validation and
# exit criterion is bound to a declared capability/validation), zero-enumeration /
# data-driven proof, forbidden-write scope, self-determinism.
uer-self:
	@python3 00-MASTER/UER-000001/uer_engine.py --check-declaration
	@python3 00-MASTER/UER-000001/uer_engine.py --check-no-enumeration
	@python3 00-MASTER/UER-000001/uer_engine.py --check-write-scope
	@python3 00-MASTER/UER-000001/uer_engine.py --check-determinism



# urrc: URRC-000001 — Repository Reality & Constitutional Completion.
# Additive only — no existing target, recipe, or dependency above is altered.
#
# The executable expression of the programme charter. It creates no catalogue, no
# registry, no roadmap, no graph, no sequence and no authority: where a canonical owner
# already exists it is bound by pointer and never restated; where none exists the fact is
# derived from declared machine-readable substrate; where honest derivation is impossible
# the absence is declared with a counted probe and the evidence class that would be
# required. Every write lands inside 00-MASTER/URRC-000001/ (guarded, fail-closed).
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only. Adding a deliverable, matrix, gate,
# substrate, derivation or binding mode is an edit to
# 00-MASTER/URRC-000001/urrc-bindings.json and requires NO change to the engine.
#
# Exit 0 every blocking gate passed · 1 a blocking gate failed · 2 fail-closed abort
# (the declaration or a required substrate is unusable, so no verdict may be asserted).
.PHONY: urrc urrc-gate urrc-self
urrc:
	@python3 00-MASTER/URRC-000001/urrc_engine.py

urrc-gate:
	@python3 00-MASTER/URRC-000001/urrc_engine.py --gate

# urrc-self: the eight guards over the programme's own surface — declaration integrity,
# zero-enumeration (data-driven proof), forbidden-write scope, self-determinism, substrate
# usability, no-fabrication, reuse-before-create (the zero-duplication invariant), and the
# law-namespace guard that proves no emitted byte reintroduces the ratified law token.
urrc-self:
	@python3 00-MASTER/URRC-000001/urrc_engine.py --check-declaration
	@python3 00-MASTER/URRC-000001/urrc_engine.py --check-no-enumeration
	@python3 00-MASTER/URRC-000001/urrc_engine.py --check-write-scope
	@python3 00-MASTER/URRC-000001/urrc_engine.py --check-determinism
	@python3 00-MASTER/URRC-000001/urrc_engine.py --check-substrate
	@python3 00-MASTER/URRC-000001/urrc_engine.py --check-no-fabrication
	@python3 00-MASTER/URRC-000001/urrc_engine.py --check-reuse-before-create
	@python3 00-MASTER/URRC-000001/urrc_engine.py --check-law-namespace
