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
	@echo "  make rib           regenerate the UCOS-RIB-001 Repository Integration Blueprint (EPIC-001)"
	@echo "  make rib-gate      fail-closed Repository Integration Gate (twelve quality gates)"
	@echo "  make rib-self      UCOS-RIB-001 guards over its own surface"
	@echo "  make uakos-archive read-only integrity guard over the completed UAKOS/USIS phases"
	@echo "  make closure       regenerate UAKOS-CLOSURE-002 repository-closure artifacts"
	@echo "  make closure-gate  fail-closed closure gate (non-zero exit while gaps remain)"
	@echo "  make closure-phase2      regenerate PHASE-002 concept-graph reconciliation (outputs 20-35)"
	@echo "  make closure-phase2-gate fail-closed PHASE-002 gate (non-zero exit while concept gaps remain)"
	@echo "  make closure-phase3      regenerate PHASE-003 implementation planning (outputs 36-48)"
	@echo "  make closure-phase3-gate fail-closed PHASE-003 gate (non-zero exit while repository NOT-CLOSED)"
	@echo "  make corpus        UKAP-001 D-1: discover exports, resolve the newest as canonical input"
	@echo "  make corpus-replay      re-derive corpus currency from corpus.json (no corpus root)"
	@echo "  make corpus-gate   fail-closed corpus-currency gate (non-zero while the corpus is stale)"
	@echo "  make assimilate    regenerate UAKOS-CLOSURE-008 assimilation registers (01-08)"
	@echo "  make assimilate-replay  re-render the registers from assimilation.json (no evidence tree)"
	@echo "  make assimilate-gate    fail-closed completion gate (non-zero while any object is unclassified)"
	@echo "  make roadmap       regenerate the UCOS-MXR-001 master execution roadmap (01-10)"
	@echo "  make roadmap-replay     re-render the roadmap from roadmap.json (recorded HEAD kept)"
	@echo "  make roadmap-gate  fail-closed execution-roadmap gate (deps resolved, order total)"
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
	@echo "  make research      regenerate UCOS-URI-001 research intelligence (assimilation/registry/standards)"
	@echo "  make research-gate fail-closed Research Validation Gate (13 obligations)"
	@echo "  make publication   regenerate UCOS-UPI-001 publications (every registered format)"
	@echo "  make publication-gate fail-closed Publication Validation Gate (14 obligations)"
	@echo "  make publications  research + publication in dependency order"
	@echo "  make uei           regenerate the UEI-000001 evolution-intelligence determinations (Ω∞-001B)"
	@echo "  make uei-gate      fail-closed Evolution Intelligence Gate (Ω∞-001B exit criteria)"
	@echo "  make uei-self      UEI guards over its own surface"
	@echo "  make umk           regenerate the UMK-000001 Universal Meta-Kernel deliverables (PROGRAM-002)"
	@echo "  make umk-gate      fail-closed Universal Meta-Kernel constitutional gate"
	@echo "  make umk-self      UMK-000001 guards over its own surface"
	@echo "  make umk-certify   fail-closed UNCONDITIONAL certification (all 20 matrix dimensions = 100%)"
	@echo "  make uprf          regenerate the UPF-000001 Universal Provider Framework deliverables (PROGRAM-003)"
	@echo "  make uprf-gate     fail-closed Universal Provider Framework constitutional gate"
	@echo "  make uprf-self     UPF-000001 guards over its own surface"
	@echo "  make uprf-certify  fail-closed UNCONDITIONAL certification (all 20 matrix dimensions = 100%)"
	@echo "  make mcos          regenerate the MCOS-000001 Meta-Civilization Platform deliverables (PROGRAM-004)"
	@echo "  make mcos-gate     fail-closed Meta-Civilization Platform constitutional gate"
	@echo "  make mcos-self     MCOS-000001 guards over its own surface (incl. reuse-before-create)"
	@echo "  make mcos-certify  fail-closed UNCONDITIONAL certification (all 20 matrix dimensions = 100%)"
	@echo "  make ucef          regenerate the UCEF-000001 constitutional-evolution registers (CEP-009-AMD-001)"
	@echo "  make ucef-gate     fail-closed Constitutional Evolution Gate (CEP-009 ADDENDUM B exit criteria)"
	@echo "  make ucef-self     UCEF-000001 guards over its own surface (incl. open-world + reuse-before-create)"
	@echo "  make uar           regenerate the UCOS-UAR-001 Universal Analysis Registry"
	@echo "  make uar-gate      fail-closed Universal Analysis Registry gate"
	@echo "  make uar-self      UCOS-UAR-001 guards over its own surface (incl. zero-enumeration)"
	@echo "  make uapf          report the UAPF-000001 declared pipeline catalogue (derived plans)"
	@echo "  make uapf-gate     fail-closed Universal Autonomous Pipeline Framework gate"
	@echo "  make uapf-self     UAPF-000001 guards over its own surface (determinism + taxonomy)"
	@echo "  make uaep          regenerate the UAEP-000001 platform capability binding registers"
	@echo "  make uaep-gate     fail-closed Platform Binding Gate (every named capability resolves)"
	@echo "  make uaep-self     UAEP-000001 guards over its own surface (incl. open-world + reuse-before-create)"
	@echo "  make uaep-replay   prove the committed registers replay from the committed declaration"
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

# corpus: UKAP-001 / D-1 — CORPUS CURRENCY RESTORATION. Discovers every available ChatGPT
# export (archive form under the corpus roots + in-repository conversation exports),
# identifies the NEWEST by content / git commit order (never by filename or filesystem
# mtime), resolves it as the canonical assimilation input, measures what the committed
# baselines actually consumed, and fails closed when a newer export exists but is ignored.
# Deterministic, stdlib-only; mutates nothing outside 00-MASTER/UKAP-001/. Corpus roots come
# from UKAP_CORPUS_ROOTS, else UAKOS_EVIDENCE_ROOT (the existing evidence-root contract).
.PHONY: corpus corpus-replay corpus-gate
corpus:
	@python3 00-MASTER/UKAP-001/corpus_engine.py

# corpus-replay: re-derive the determination from the committed corpus.json alone — proves
# the currency record is self-contained (no corpus root required). The in-repo export class
# and both consumption measurements are still re-measured live, so a replay is never vacuous.
corpus-replay:
	@python3 00-MASTER/UKAP-001/corpus_engine.py --render

# corpus-gate: fail-closed — non-zero exit while any corpus class is STALE: a newer export
# exists but is ignored, an assimilated conversation is absent from the canonical export, an
# in-repo export was never reconstructed, or assimilated export content has drifted.
corpus-gate:
	@python3 00-MASTER/UKAP-001/corpus_engine.py --render --gate

# assimilate: UAKOS-CLOSURE-008 — constitutional assimilation & repository completion.
# Consumes the FROZEN knowledge-assimilation base + tri-source verification determination
# (read-only, hashed) and drives every verified knowledge object into exactly one of six
# terminal states, homing every approved item with a destination, owner, constitutional
# authority, wave and dependency chain. Deterministic, stdlib-only; mutates nothing outside
# 00-MASTER/UAKOS-CLOSURE-008/. Set UAKOS_EVIDENCE_ROOT to relocate the evidence tree.
#
# CORPUS CURRENCY (UKAP-001 D-1): every assimilation target depends on `corpus-gate`, so no
# assimilation artifact can be produced or certified while the corpus is stale. This is the
# dependency-closure guarantee — currency is verified BEFORE knowledge is assimilated.
.PHONY: assimilate assimilate-replay assimilate-gate
assimilate: corpus-gate
	@python3 00-MASTER/UAKOS-CLOSURE-008/assimilation_engine.py

# assimilate-replay: re-render every register from the in-repo assimilation.json alone —
# proves the repository is self-contained (no external evidence tree required).
assimilate-replay: corpus-gate
	@python3 00-MASTER/UAKOS-CLOSURE-008/assimilation_engine.py --render

# assimilate-gate: fail-closed — non-zero exit while any verified knowledge object is
# unclassified, unhomed, unowned, untraceable, or any semantic mapping fails to resolve.
assimilate-gate: corpus-gate
	@python3 00-MASTER/UAKOS-CLOSURE-008/assimilation_engine.py --render --gate

# roadmap: UCOS-MXR-001 — master execution roadmap (post UAKOS-CLOSURE-008). Compiles the
# CURRENT REPOSITORY STATE (MCP-002/MCP-003 state of record, UCDA-000001 work packages, the RIE
# intelligence artifacts, closure.json, assimilation.json + HEAD band evidence) into a
# deterministic execution program: backlog, dependency graph, waves, critical path, parallel
# groups, validation/certification gates and the readiness determination. No discovery, no
# reconciliation; mutates nothing outside 00-MASTER/UCOS-MXR-001/.
.PHONY: roadmap roadmap-replay roadmap-gate
roadmap:
	@python3 00-MASTER/UCOS-MXR-001/roadmap_engine.py

# roadmap-replay: re-render 01..10 from the committed roadmap.json alone. A committed artifact
# can never contain the sha of the commit that carries it, so the DRIFT check must replay
# (preserving the recorded HEAD) while `roadmap-gate` proves the program is still derivable.
roadmap-replay:
	@python3 00-MASTER/UCOS-MXR-001/roadmap_engine.py --render

# roadmap-gate: fail-closed — non-zero exit unless the roadmap is executable (acyclic graph,
# every dependency resolved, every item located/named-owner/validatable/rollback-able, no READY
# item behind a non-executable prerequisite, total order).
roadmap-gate:
	@python3 00-MASTER/UCOS-MXR-001/roadmap_engine.py --gate

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



# uei: UEI-000001 — Universal Evolution Intelligence (UCOS Ω∞ Programme Ω∞-001B).
# Additive only — no existing target, recipe, or dependency above is altered.
#
# The executable expression of the Evolution Intelligence contract. It creates no
# observation, learning, optimization, recommendation, impact-analysis, simulation,
# discovery, planning, execution, measurement or evolution mechanism: every one already
# exists and is certified (platform/observability — EC2-EPIC-013; engine/knowledge — UKDA;
# engine/compiler/optimization.py — EPIC-003; engine/graph/architecture over the certified
# knowledge graph — EPIC-010 over EPIC-002; engine/determinism — EPIC-004;
# engine/runtime/execution — EPIC-005; platform/repository_operations;
# platform/runtime_operations — EC2-EPIC-012; platform/coverage; platform/measurement;
# intelligence/rie). It BINDS them into one contract that every future autonomous
# programme inherits, places each capability under a located governing instrument, and
# verifies from Repository Truth that each binding resolves — then emits the twenty-three
# deliverables, the last of which is the continuation package, into 00-MASTER/UEI-000001/.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; writes nothing outside its own
# operational-memory directory (guarded, fail-closed). Binding a newly proven capability is
# an entry in 00-MASTER/UEI-000001/uei-evolution.json and requires NO change to the engine.
#
# Exit 0 gate OPEN · 1 gate CLOSED (an uncovered, ungoverned or unsatisfied element is
# present) · 2 fail-closed abort (declaration unusable — no verdict may be asserted).
.PHONY: uei uei-gate uei-self
uei:
	@python3 00-MASTER/UEI-000001/uei_engine.py

uei-gate:
	@python3 00-MASTER/UEI-000001/uei_engine.py --gate

# uei-self: the six guards over the programme's own surface — declaration integrity (every
# home/evidence/instrument/programme reference resolves; every deliverable, lifecycle step,
# standing loop, validation, exit criterion and governance obligation is bound), zero-
# enumeration / data-driven proof, forbidden-write scope, self-determinism, the governance
# guard that proves no declared capability is left ungoverned, and the reuse-before-create
# guard that proves no bound home lies inside this programme's own home.
uei-self:
	@python3 00-MASTER/UEI-000001/uei_engine.py --check-declaration
	@python3 00-MASTER/UEI-000001/uei_engine.py --check-no-enumeration
	@python3 00-MASTER/UEI-000001/uei_engine.py --check-write-scope
	@python3 00-MASTER/UEI-000001/uei_engine.py --check-determinism
	@python3 00-MASTER/UEI-000001/uei_engine.py --check-governance
	@python3 00-MASTER/UEI-000001/uei_engine.py --check-reuse-before-create



# research / publication: UCOS-URI-001 Universal Research Intelligence and
# UCOS-UPI-001 Universal Publication Intelligence.
# Additive only — no existing target, recipe, or dependency above is altered.
#
# UCOS-URI-001 assimilates the repository's own canonical knowledge, decision record,
# concept closure and generated corpus measurements into a research corpus of claims,
# findings, contribution areas and standards records — then registers it append-only
# (Knowledge-Once + hash chain), analyses standards conformance, and validates thirteen
# fail-closed obligations. Every record stores a REFERENCE to canonical content; none
# stores a copy (UCKO-PRIN-0001; the anti-pattern UCKO-ANTI-0001).
#
# UCOS-UPI-001 generates every publication format from that corpus: research paper,
# journal article, conference paper (full/short/extended-abstract/poster), white paper,
# technical article, patent draft, standards proposal, technical report, preprint,
# review, thesis/book chapter, RFC-style memo, briefs, datasheet and tutorial — plus any
# format registered afterwards. A format is DATA (a descriptor), not code: adding one is
# an entry in intelligence/UCOS-UPI-001/publication-formats.json (or a runtime
# register_format call) and requires NO engine change. Fourteen fail-closed obligations
# are validated, including an executed proof that the format space is open.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only. Every write lands inside
# intelligence/UCOS-URI-001/ or intelligence/UCOS-UPI-001/ (guarded, fail-closed).
#
# Exit 0 gate OPEN · 1 gate CLOSED (an obligation is unsatisfied or output is
# non-deterministic) · 2 fail-closed abort (required substrate unusable — no verdict
# may be asserted).
.PHONY: research research-gate research-self publication publication-gate publication-self \
        publications research-publication-gate
research:
	@python3 -m intelligence.research build

research-gate:
	@python3 -m intelligence.research gate

# research-self: the subsystem's guards over its own surface — deterministic
# regeneration and the full thirteen-obligation validation report.
research-self:
	@python3 -m intelligence.research verify >/dev/null
	@python3 -m intelligence.research validate >/dev/null
	@echo "UCOS-URI-001: self-guards PASS (determinism + research validation)"

publication:
	@python3 -m intelligence.publication build

publication-gate:
	@python3 -m intelligence.publication gate

# publication-self: deterministic regeneration plus the fourteen-obligation validation
# report (which itself executes the format-openness probe).
publication-self:
	@python3 -m intelligence.publication verify >/dev/null
	@python3 -m intelligence.publication validate >/dev/null
	@echo "UCOS-UPI-001: self-guards PASS (determinism + publication validation)"

# publications: regenerate research intelligence, then every publication format.
publications: research publication

# research-publication-gate: both gates in dependency order (publication consumes the
# research corpus, so a closed research gate closes the publication gate too).
research-publication-gate: research-gate publication-gate



# rib: UCOS-RIB-001 — Repository Integration Blueprint (EPIC-001 / WP-001).
# Additive only — no existing target, recipe, or dependency above is altered.
#
# The executable expression of EPIC-001. It creates no capability catalogue, no dependency
# graph, no registry, no execution queue, no priority register and no certification
# authority: every one already exists and is already owned (intelligence/UCOS-RIE-* — the
# Repository Intelligence Engine; 00-BOOK/tools/ukb.py — registration; 00-BOOK/DATA — the
# typed graph and the twin certification; 00-MASTER/URRC-000001 — the reality matrices;
# 00-MASTER/UAKOS-CLOSURE-002 — concept closure and the planning layer; 00-MASTER/UEI-000001
# and UER-000001 — the evolution and resilience capability bindings). It DISCOVERS the unit
# universe from Repository Truth with zero enumeration, MEASURES every unit, BINDS each of
# the sixteen chartered matrices to the owner that already holds it — emitting the pointer
# and no rows — or DERIVES it where no owner holds it machine-readably, computes exactly one
# disposition per unit through an ordered, total, data-declared rule set, and emits the
# fourteen mandatory outputs into 00-MASTER/UCOS-RIB-001/.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; writes nothing outside its own operational
# memory directory (guarded, fail-closed). Adding a discovery source, measure, plane,
# disposition, rule, matrix, gap class, duplicate class, gate or output is an entry in
# 00-MASTER/UCOS-RIB-001/rib-blueprint.json and requires NO change to the engine.
#
# Exit 0 every blocking gate passed · 1 a blocking gate failed · 2 fail-closed abort
# (the declaration or a required substrate is unusable, so no verdict may be asserted).
.PHONY: rib rib-gate rib-self
rib:
	@python3 00-MASTER/UCOS-RIB-001/rib_engine.py

rib-gate:
	@python3 00-MASTER/UCOS-RIB-001/rib_engine.py --gate

# rib-self: the eight guards over the programme's own surface — declaration integrity
# (every reference resolves; every obligation names a computed metric; the rule set is
# ordered, reachable and total), zero-enumeration (the blueprint is DATA and the engine
# names none of its subject matter), forbidden-write scope, self-determinism, substrate
# usability, no-fabrication (every row traces to a source, a measure or a counted probe),
# reuse-before-create (no bound owner lies inside this programme's own home), and totality
# (every unit carries exactly one disposition from the closed set).
rib-self:
	@python3 00-MASTER/UCOS-RIB-001/rib_engine.py --check-declaration
	@python3 00-MASTER/UCOS-RIB-001/rib_engine.py --check-no-enumeration
	@python3 00-MASTER/UCOS-RIB-001/rib_engine.py --check-write-scope
	@python3 00-MASTER/UCOS-RIB-001/rib_engine.py --check-determinism
	@python3 00-MASTER/UCOS-RIB-001/rib_engine.py --check-substrate
	@python3 00-MASTER/UCOS-RIB-001/rib_engine.py --check-no-fabrication
	@python3 00-MASTER/UCOS-RIB-001/rib_engine.py --check-reuse-before-create
	@python3 00-MASTER/UCOS-RIB-001/rib_engine.py --check-totality



# uakos-archive: the completed, superseded UAKOS/USIS operational-memory phases.
# Additive only — no existing target, recipe, or dependency above is altered.
#
# Four operational-memory programme phases are terminal historical determinations: their
# missions completed, their responsibility is held by their successor programmes, and they
# are retained read-only as constitutional evidence. They run no live regeneration, so no
# regeneration target names them — this guard is the declared entry point that reaches
# them. It re-executes nothing (their one-shot engines are wall-clock-stamped and would
# dirty the tree), mutates nothing, and only proves each archived phase directory and its
# completion determination is still present.
#
# Exit 0 all four archived phases present · non-zero one is missing.
.PHONY: uakos-archive
uakos-archive:
	@ok=1 ; \
	for d in \
		00-MASTER/UAKOS-PHASE-001A-R1 \
		00-MASTER/UAKOS-PHASE-001B \
		00-MASTER/UAKOS-PHASE-003R \
		00-MASTER/UCOS-USIS-WAVE0 ; do \
		if [ ! -d "$$d" ]; then echo "MISSING archived phase: $$d" ; ok=0 ; fi ; \
	done ; \
	[ "$$ok" -eq 1 ] && echo "UAKOS/USIS archived operational-memory phases present (4)"



# umk: UMK-000001 — Universal Meta-Kernel Foundation (PROGRAM-002, WAVE-2).
# Additive only — no existing target, recipe, or dependency above is altered.
#
# The Universal Meta-Kernel itself lives under engine/kernel/: the smallest possible
# open, self-describing meta-type system. Everything the platform can ever represent is a
# MetaObject classified by a registered MetaType; the reflective root MetaType is
# classified by itself. Concept-categories are registered DATA, never enum members, so a
# previously unknown category (a civilization, language family, value-exchange system,
# taxation/audit/temporal/governance/scientific model, provider category, capability
# domain or execution model) is admitted by registration only — the kernel is never
# redesigned (Engineering Rule 7).
#
# This target runs the executable expression of PROGRAM-002 in
# 00-MASTER/UMK-000001/umk_engine.py, which BINDS every universal abstraction declared in
# umk-kernel.json to its home in engine/kernel/, runs the kernel's own executed
# constitutional proof (engine/kernel/compliance.py), and emits the seven deliverables +
# validation/certification evidence into 00-MASTER/UMK-000001/. It legislates nothing and
# freezes no architecture.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; writes nothing outside its own
# operational-memory directory (guarded, fail-closed). The kernel is also runnable
# directly via the `ucos-kernel` console script (prove / certify / describe / evidence).
#
# Exit 0 constitutionally compliant · 1 a quality gate failed · 2 fail-closed abort
# (declaration or substrate unusable — no verdict may be asserted).
.PHONY: umk umk-gate umk-self umk-certify
umk:
	@python3 00-MASTER/UMK-000001/umk_engine.py

umk-gate:
	@python3 00-MASTER/UMK-000001/umk_engine.py --gate

# umk-certify: fail-closed UNCONDITIONAL certification — exits non-zero unless every one
# of the twenty Universal Certification Matrix dimensions reports exactly 100%. The two
# coverage dimensions are read from coverage.xml, so run `make test` (or `make verify`)
# first so the measured statement/branch coverage is present.
umk-certify: test
	@python3 00-MASTER/UMK-000001/umk_engine.py --certify

# umk-self: the programme's guards over its own surface — declaration integrity (every
# abstraction resolves to a real home, every seeded meta-type exists, every architectural-
# proof category is proven), forbidden-write scope (every output lands inside
# 00-MASTER/UMK-000001/), and self-determinism (deliverables are byte-identical across runs).
umk-self:
	@python3 00-MASTER/UMK-000001/umk_engine.py --check-declaration
	@python3 00-MASTER/UMK-000001/umk_engine.py --check-write-scope
	@python3 00-MASTER/UMK-000001/umk_engine.py --check-determinism



# uprf: UPF-000001 — Universal Provider Framework (PROGRAM-003, WAVE-2).
# Additive only — no existing target, recipe, or dependency above is altered.
#
# The framework itself lives under engine/provider/: the constitutional realization layer
# over the immutable PROGRAM-002 kernel. A provider category is a registered kernel
# meta-type (open set); a provider is a kernel MetaObject classified by its category.
# Concrete providers are future registrations, never framework modifications. It imports
# and modifies neither the kernel nor the distinct platform/universal_provider (EC-2).
#
# This target runs the executable expression of PROGRAM-003 in
# 00-MASTER/UPF-000001/upf_engine.py, which BINDS every provider responsibility declared in
# upf-provider.json to its home under engine/provider/ (or a reused kernel primitive), runs
# the framework's own executed constitutional proof (engine/provider/compliance.py), and
# emits the nine deliverables + validation/certification evidence into 00-MASTER/UPF-000001/.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; writes nothing outside its own
# operational-memory directory (guarded, fail-closed). The framework is also runnable
# directly via the `ucos-uprf` console script (prove / certify / describe / evidence).
#
# Exit 0 compliant/certified · 1 a gate/dimension below 100% · 2 fail-closed abort.
.PHONY: uprf uprf-gate uprf-self uprf-certify
uprf:
	@python3 00-MASTER/UPF-000001/upf_engine.py

uprf-gate:
	@python3 00-MASTER/UPF-000001/upf_engine.py --gate

# uprf-self: declaration integrity (every responsibility resolves, every category is
# proven), forbidden-write scope (outputs land inside 00-MASTER/UPF-000001/), self-determinism.
uprf-self:
	@python3 00-MASTER/UPF-000001/upf_engine.py --check-declaration
	@python3 00-MASTER/UPF-000001/upf_engine.py --check-write-scope
	@python3 00-MASTER/UPF-000001/upf_engine.py --check-determinism

# uprf-certify: fail-closed UNCONDITIONAL certification — non-zero unless every one of the
# twenty Universal Certification Matrix dimensions reports exactly 100%. Coverage dimensions
# are read from coverage.xml, so `make test` runs first.
uprf-certify: test
	@python3 00-MASTER/UPF-000001/upf_engine.py --certify


# ---------------------------------------------------------------------------
# UCOS-RFP-001 — REPOSITORY FIXED-POINT CLOSURE (G-15).
#
# The permanent answer to the class of defect that produced CK-REG-DRIFT. It adds no
# validator, engine, registry or capability: it BINDS the producers the repository
# already owns into one declared pipeline and asserts a single property over them —
# executing that pipeline over the committed HEAD must leave the repository
# byte-identical, for each declared convergence pass. Every producer, cycle class,
# artifact class and closure criterion is an entry in
# 00-MASTER/UCOS-RFP-001/rfp-declaration.json; this Makefile and the engine never need
# to change to admit a new one, and nothing is enumerated in either.
#
# The gate is what makes closure conditional on REALITY rather than on assertion:
# certification says the state is lawful, the fixed point says the state is real.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; writes nothing outside
# 00-MASTER/UCOS-RFP-001/ (guarded, fail-closed). The gate itself PERSISTS NOTHING —
# its verdict is the exit code, because an artifact recording "the repository is a
# fixed point" would falsify that sentence by being written (RFP-3).
#
# Exit 0 fixed point (gate OPEN) · 1 not a fixed point (gate CLOSED) · 2 fail-closed abort.
.PHONY: rfp rfp-gate rfp-detect rfp-self
rfp:
	@python3 00-MASTER/UCOS-RFP-001/rfp_engine.py

# rfp-gate: G-15. Fail-closed. Requires a clean committed tree to begin (a fixed point
# is a property of a COMMITTED state), then runs the full declared pipeline three times.
rfp-gate:
	@python3 00-MASTER/UCOS-RFP-001/rfp_engine.py --gate

# rfp-detect: the same measurement, reported without asserting a verdict — for use while
# repairing a producer. Never fails, so it can never be mistaken for the gate.
rfp-detect:
	@python3 00-MASTER/UCOS-RFP-001/rfp_engine.py --detect

# rfp-self: declaration integrity, zero-enumeration proof (the engine names no producer,
# zone or cycle class), forbidden-write scope, self-determinism, and self-compliance —
# the programme that abolishes commit self-reference and working-tree self-observation
# proving it commits neither in its own emitted bytes.
rfp-self:
	@python3 00-MASTER/UCOS-RFP-001/rfp_engine.py --check-declaration
	@python3 00-MASTER/UCOS-RFP-001/rfp_engine.py --check-no-enumeration
	@python3 00-MASTER/UCOS-RFP-001/rfp_engine.py --check-write-scope
	@python3 00-MASTER/UCOS-RFP-001/rfp_engine.py --check-determinism
	@python3 00-MASTER/UCOS-RFP-001/rfp_engine.py --check-self-compliance



# ---------------------------------------------------------------------------
# mcos: MCOS-000001 — Universal Meta-Civilization Platform (PROGRAM-004, WAVE-2).
# Additive only — no existing target, recipe, or dependency above is altered.
#
# The layer that GENERATES constitutional operating systems lives under engine/civilization/:
# the third realization layer over the immutable PROGRAM-002 kernel, sibling to the PROGRAM-003
# provider framework. Three components over ONE kernel — an open dimension space (the Universal
# Dimension Model), a planner that derives execution from declarations rather than a pipeline
# (Dynamic Capability Composition), and an ordered chain of registered strata through which a
# constitutional operating system comes into being (the Constitutional Generation Model).
#
# Seven of the ten mandated constructs already had a canonical owner and were NOT
# re-implemented: the Universal Meta Kernel (engine/kernel, UMK-000001), the Universal Registry
# Architecture (the kernel registry — a second registry is prohibited), Universal Capability
# Discovery (engine/discovery), the Open-World Expansion certifications, Unlimited
# Constitutional Evolution (CEP-009, UEI-000001), the Universal Engineering Platform
# (PLATFORM-005/010, named not authored), and the MCOS name itself (resolved onto MCS-000, with
# authority NONE). Reuse is MEASURED by mcos-self, not asserted.
#
# This target runs the executable expression of PROGRAM-004 in
# 00-MASTER/MCOS-000001/mcos_engine.py, which BINDS every responsibility declared in
# mcos-civilization.json to its home under engine/civilization/ (or a REUSED owner elsewhere),
# runs the layer's own executed constitutional proof (engine/civilization/compliance.py), and
# emits the nine deliverables + validation/certification evidence into 00-MASTER/MCOS-000001/.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; writes nothing outside its own
# operational-memory directory (guarded, fail-closed). Admitting a dimension, capability,
# composition strategy, generation stratum or constitutional operating system is a REGISTRATION
# and requires NO change to the layer, to the engine, or to the kernel. The platform is also
# runnable directly via the `ucos-mcos` console script (describe / prove / certify / evidence).
#
# Exit 0 compliant/certified · 1 a gate/dimension below 100% · 2 fail-closed abort.
.PHONY: mcos mcos-gate mcos-self mcos-certify
mcos:
	@python3 00-MASTER/MCOS-000001/mcos_engine.py

mcos-gate:
	@python3 00-MASTER/MCOS-000001/mcos_engine.py --gate

# mcos-self: declaration integrity (every substrate, mechanism, gate, proof category, generated
# operating system and stratum resolves), reuse-before-create (a responsibility claiming REUSED
# must be homed OUTSIDE this layer, and one claiming NEW must be homed inside — the guard that
# stops a re-implementation wearing a reuse label), forbidden-write scope, and self-determinism.
mcos-self:
	@python3 00-MASTER/MCOS-000001/mcos_engine.py --check-declaration
	@python3 00-MASTER/MCOS-000001/mcos_engine.py --check-reuse-before-create
	@python3 00-MASTER/MCOS-000001/mcos_engine.py --check-write-scope
	@python3 00-MASTER/MCOS-000001/mcos_engine.py --check-determinism

# mcos-certify: fail-closed UNCONDITIONAL certification — non-zero unless every one of the
# twenty Universal Certification Matrix dimensions reports exactly 100%. Coverage dimensions are
# read from coverage.xml, so `make test` runs first.
mcos-certify: test
	@python3 00-MASTER/MCOS-000001/mcos_engine.py --certify




# ---------------------------------------------------------------------------
# ucef: UCEF-000001 — Universal Constitutional Evolution Framework (CEP-009-AMD-001).
# Additive only — no existing target, recipe, or dependency above is altered.
#
# This block adds NO new validator, engine, authority or capability. It runs the executable
# expression of the constitutional-evolution contract declared in
# 00-MASTER/UCEF-000001/ucef-framework.json, whose NORMATIVE home is
# 00-CEP/CEP-009-...-AMENDMENT-EVOLUTION-CONSTITUTION.md ADDENDUM B. Every law, lifecycle
# stage, acceptance property, expansion axis, construct class and governance obligation in
# that DATA file BINDS to an authority that already exists and is already located — the
# meta-governance admission procedure and construct taxonomy (00-CMG/CMG-000001 Art XIII,
# XIV, XV, XL, XLI, LXXVI, LXXVII), governance change control (00-CEP/CEP-002 Art 20/21/28),
# validation (00-CEP/CEP-004 + verify.sh), certification (00-CEP/CEP-005), traceability
# (00-CEP/CEP-008), registration (REG-AUTO-001 + 00-BOOK/tools/register.sh), the
# implementation contract (00-MASTER/UCIC-001) and the evolution registry
# (00-CEP/CEP-009 Art XVI + 00-MASTER/EVOLUTION-001).
#
# Admitting a further construct class, expansion axis, lifecycle stage, acceptance property,
# governance obligation or validation dimension is an entry in that DATA file and requires NO
# change to the engine, to this Makefile, or to the workflow. A self-guard proves it: the
# engine names none of them.
#
# Exit semantics of the gate:
#   0  every law is anchored, every stage is bound to a located owner outside the programme,
#      every acceptance property is discharged by a located mechanism, the construct register
#      is declared OPEN, no expansion axis declares a finite bound, the stage graph is acyclic
#      and closed, and every mandatory dimension and exit criterion is satisfied (gate OPEN)
#   1  a binding, dimension or exit criterion is unsatisfied (gate CLOSED)
#   2  fail-closed abort — the declaration is unusable, so no verdict may be asserted
.PHONY: ucef ucef-gate ucef-self
ucef:
	@python3 00-MASTER/UCEF-000001/ucef_engine.py

ucef-gate:
	@python3 00-MASTER/UCEF-000001/ucef_engine.py --gate

# ucef-self: the six guards over the programme's own surface — declaration integrity (every
# law basis, stage owner, acceptance mechanism, axis basis, construct admission route and
# governance instrument resolves against Repository Truth), zero-enumeration (the framework is
# DATA: the engine special-cases no declared member), write-scope (no write ever lands outside
# 00-MASTER/UCEF-000001/, and never in a frozen or certified zone), determinism (assessment and
# rendering are byte-identical across runs, no wall-clock is emitted), reuse-before-create (no
# bound authority lies inside this programme's own home, so nothing owned elsewhere is
# re-authored here), and open-world (no finite ceiling is declared anywhere — the construct
# register is open and non-exhaustive and every expansion axis is unbounded).
ucef-self:
	@python3 00-MASTER/UCEF-000001/ucef_engine.py --check-declaration
	@python3 00-MASTER/UCEF-000001/ucef_engine.py --check-no-enumeration
	@python3 00-MASTER/UCEF-000001/ucef_engine.py --check-write-scope
	@python3 00-MASTER/UCEF-000001/ucef_engine.py --check-determinism
	@python3 00-MASTER/UCEF-000001/ucef_engine.py --check-reuse-before-create
	@python3 00-MASTER/UCEF-000001/ucef_engine.py --check-open-world



# ---------------------------------------------------------------------------
# uar: UCOS-UAR-001 — Universal Analysis Registry.
#
# WHY THIS BLOCK EXISTS. The engine was already complete, already deterministic and already
# self-guarded, but no declared entry point named it — so the Repository Integration Blueprint
# measured it as a DEAD ENGINE (`GAP-DEAD-ENGINE`, `VER-11`) and, because `RCH-ENTRYPOINT` is one
# of its seven pre-declared reachability dimensions, simultaneously as an ORPHAN unit (`VER-09`,
# `GATE-11`). One cause, two findings, both blocking `GATE-03`.
#
# UCOS-RIB-001/WP-003 §008 names the discharge exactly: "name the programme engine from a declared
# entry point, or disposition the engine", and assigns the act to the `Makefile` / CI entry points
# — this file. Disposition was rejected on measurement, not preference: all five of the engine's
# own checks exit 0 (26 declared analyses, every home resolving), so the engine is live code that
# was merely unreachable, and retiring working, self-guarded code to satisfy a reachability metric
# would destroy capability to make a number look better.
#
# Additive only — no existing target, recipe or dependency above is altered. This introduces NO
# authority, NO registry and NO new mechanism: it exposes an EXISTING engine through the EXISTING
# entry-point convention every other programme here already uses.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; writes nothing outside
# 00-MASTER/UCOS-UAR-001/. Adding an analysis is an entry in uar-analyses.json and requires no
# change to the engine or to this Makefile.
#
# Exit 0 gate OPEN · 1 gate CLOSED · 2 fail-closed abort.
.PHONY: uar uar-gate uar-self
uar:
	@python3 00-MASTER/UCOS-UAR-001/uar_engine.py

uar-gate:
	@python3 00-MASTER/UCOS-UAR-001/uar_engine.py --gate

# uar-self: declaration integrity (every declared analysis has a unique id and a resolving home),
# zero-enumeration proof (no declared analysis id appears as a literal in the engine source, so
# the registry cannot be faked by hardcoding), write scope, and self-determinism.
uar-self:
	@python3 00-MASTER/UCOS-UAR-001/uar_engine.py --check-declaration
	@python3 00-MASTER/UCOS-UAR-001/uar_engine.py --check-no-enumeration
	@python3 00-MASTER/UCOS-UAR-001/uar_engine.py --check-write-scope
	@python3 00-MASTER/UCOS-UAR-001/uar_engine.py --check-determinism


# ---------------------------------------------------------------------------
# uapf: UAPF-000001 — the Universal Autonomous Pipeline Framework.
#
# WHY THIS BLOCK EXISTS. The framework is the constitutional execution foundation for every
# autonomous activity (Evolution Pipeline, Build Pipeline, and every future pipeline category),
# and its two canonical pipelines are DECLARED as data in
# platform/universal_pipeline/catalog/uapf-pipelines.json rather than written as code. Neither
# the framework nor the catalogue may be reachable only from a test: the Repository Integration
# Blueprint measures a capability that no declared entry point names as a DEAD ENGINE
# (`GAP-DEAD-ENGINE`, `VER-11`) and, because `RCH-ENTRYPOINT` is one of its reachability
# dimensions, simultaneously as an ORPHAN unit (`VER-09`). This block plus the `ucos-uapf`
# console script in pyproject.toml are the discharge, using the same entry-point convention
# every other programme here already uses.
#
# Additive only — no existing target, recipe or dependency above is altered. This introduces NO
# authority, NO registry and NO new mechanism: it exposes an EXISTING framework through the
# EXISTING entry-point convention.
#
# AUTHORITY = NONE (DERIVED TRUTH). Stdlib only; READ-ONLY — it opens the declared catalogue and
# writes nothing anywhere, not the certified corpus (DP-03), not the registries, not a cache.
# Adding a pipeline, a stage, a gate, a policy or a whole new pipeline CATEGORY is an entry in
# the catalogue and requires no change to the framework or to this Makefile.
#
# Exit 0 gate OPEN · 1 gate CLOSED · 2 fail-closed abort.
.PHONY: uapf uapf-gate uapf-self
uapf:
	@python3 -m platform.universal_pipeline.cli

uapf-gate:
	@python3 -m platform.universal_pipeline.cli --gate

# uapf-self: the framework's guards over its own surface — that the derived registry is
# byte-identical across two independent discovery passes of the same declarations
# (--check-determinism), and that the open vocabularies it governs are enumerable
# (--taxonomy: pipeline types, event categories, stage handlers, object kinds, readiness
# predicates). Both are read-only.
uapf-self:
	@python3 -m platform.universal_pipeline.cli --check-determinism
	@python3 -m platform.universal_pipeline.cli --taxonomy >/dev/null
	@python3 -m platform.universal_pipeline.cli --gate


# ---------------------------------------------------------------------------------------
# uaep: UAEP-000001 — the platform capability binding register.
#
# The platform agreement names sixteen capabilities. Fifteen already had a canonical home
# before this programme existed and one had none, so this programme binds each name to the
# home that already realises it and then proves the binding still resolves. It creates no
# engine, no registry, no catalogue, no identity, no graph and no pipeline: every binding is
# a pointer, and `uaep-self` refuses any binding that points inside this programme's own home.
#
# The declaration 00-MASTER/UAEP-000001/uaep-platform.json is the single source: capabilities,
# homes, symbols, vocabularies, pipeline categories and validation dimensions are all DATA,
# so adding one is an edit to that file and never to the engine (proven by --check-no-enumeration).
#
# A declared validation dimension the engine does not measure FAILS CLOSED rather than being
# reported satisfied — absence of evidence is never evidence.
.PHONY: uaep uaep-gate uaep-self uaep-replay
uaep:
	@python3 00-MASTER/UAEP-000001/uaep_engine.py --render

uaep-gate:
	@python3 00-MASTER/UAEP-000001/uaep_engine.py --gate

# uaep-self: the six guards over the programme's own surface — declaration integrity (no
# duplicate id, no empty mandatory field), zero-enumeration (no capability id or name appears
# in the engine source, including its docstring), write-scope (every rendered target resolves
# inside 00-MASTER/UAEP-000001/), determinism (two renders are byte-identical; no wall-clock
# is emitted), reuse-before-create (no capability is bound to an artifact this programme owns),
# and open-world (every declared vocabulary names a registrar that exists in its declared home,
# so the type, handler, event and object-kind spaces stay open).
uaep-self:
	@python3 00-MASTER/UAEP-000001/uaep_engine.py --check-declaration
	@python3 00-MASTER/UAEP-000001/uaep_engine.py --check-no-enumeration
	@python3 00-MASTER/UAEP-000001/uaep_engine.py --check-write-scope
	@python3 00-MASTER/UAEP-000001/uaep_engine.py --check-determinism
	@python3 00-MASTER/UAEP-000001/uaep_engine.py --check-reuse-before-create
	@python3 00-MASTER/UAEP-000001/uaep_engine.py --check-open-world

# uaep-replay: prove the committed registers are the deterministic product of the committed
# declaration. Re-render, then require a clean diff over this programme's home.
uaep-replay:
	@python3 00-MASTER/UAEP-000001/uaep_engine.py --render --quiet
	@git diff --exit-code -- 00-MASTER/UAEP-000001 \
	  || { echo "UAEP-000001 REPLAY DRIFT — committed registers are not the product of the declaration" >&2; exit 1; }
	@echo "UAEP-000001 replay: no drift"
