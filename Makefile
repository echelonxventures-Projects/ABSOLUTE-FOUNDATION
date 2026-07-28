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
