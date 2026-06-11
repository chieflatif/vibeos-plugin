# VibeOS — Harness Product Dossier

> **Purpose of this document.** A comprehensive, source-grounded inventory of what the VibeOS harness *is* and *does* — its architecture, feature domains, mechanisms, and the engineering philosophy behind them. It is written as a finished product capabilities reference and is intended as the single source of truth handed to the case-study / showcase team. Counts and component names are derived from the harness's own generated inventory, not estimated.

---

## 1. What VibeOS Is

VibeOS is a **governed development operating layer for AI-assisted software engineering** — a Claude Code plugin that turns a general coding assistant into an autonomous, self-governing build engine. You describe what you want to build; VibeOS runs discovery, generates a phased plan, then builds it autonomously — writing tests first, implementing against them, and enforcing a layered wall of automated quality audits that hold the line at **zero technical debt**.

It is not a wrapper around a model and not a prompt library. It is a **harness**: a deterministic governance substrate that sits underneath the model and constrains, verifies, and orchestrates everything the model does. The model provides intelligence and acceleration; the harness provides the guarantees.

**The one-line positioning:** *Build enterprise-grade, compliance-targeted software with AI agents — at zero technical debt — by making the harness, not the model, responsible for correctness, truthful status, and architectural fidelity.*

---

## 2. The Core Thesis (Harness Engineering)

VibeOS is built on a single non-negotiable architectural principle:

> **Every blocking control lives on the deterministic floor. Model-native features are acceleration, never the only guard.**

A model can be brilliant and still drift, hallucinate a "done," skip a test, or quietly degrade a primary path into a fallback. So VibeOS never trusts the model to police itself. Correctness, security, scope, and truthful status are enforced by **deterministic scripts, hooks, and gates** that run regardless of which model (or model version) is driving. The model accelerates; the floor guarantees.

This produces the harness's defining behaviors:
- **Tests are written from the spec, before implementation exists** — by an agent that never sees the implementation code.
- **Implementation agents physically cannot modify test files** — enforced by a pre-tool-use hook, not by instruction.
- **Audit agents are read-only and isolated** — they cannot edit, cannot spawn other agents, and run in throwaway worktrees.
- **A work order is only "complete" when the real execution path is verified** — not when unit tests pass, not when a mock works.
- **Status artifacts must be truthful** — the harness has dedicated machinery to detect and reject misleading "done" claims and plan/index drift.

### The Five Principles (with a hard precedence order)

| Principle | Meaning |
|---|---|
| **Security** | Compliance is a constraint from day one — secret scanning, auth boundaries, tenant isolation, PII handling, OWASP alignment are built in, not bolted on. |
| **Fidelity** | What gets built is what was anchored. The document pyramid is the single source of truth; scope discipline, drift auditors, and ratcheting baselines keep execution on the map. |
| **Provability** | Every claim is backed by evidence — evidence bundles, audit trails, a generated inventory, and a claim ledger that distinguishes "proven" from "asserted." |
| **Eloquence** | Code and communication are clear and intentional; file-size limits and clarity reminders fight sprawl and confusion. |
| **Efficiency** | The reward state of honoring the other four — not a license to shortcut them. |

**Conflict rule:** when principles collide, precedence is strict — **Security > Fidelity > Provability > Eloquence > Efficiency.** It is never acceptable to save tokens by skipping an audit, and never acceptable to ship elegant code that drifted from the anchor.

---

## 3. The Five-Layer Architecture

VibeOS separates a runtime-independent **deterministic enforcement floor** from a model-driven **cognition ceiling**, with a hard line between them.

1. **Deterministic Enforcement Floor (runtime-independent).** The gate runner + quality manifest, secret scanning, finding-level baselines and ratcheting, the findings lifecycle, lane-readiness core, work-order contract generators and lints, the framework-manifest/delta engine, the autonomy control plane, and Git hooks. Every *blocking* control lives here.
2. **Orchestration Layer.** The build loop that sequences specialized agents through the work-order lifecycle, with checkpointing, convergence control, and error recovery.
3. **Agent Fleet.** Specialized, single-purpose subagents (implementers, testers, and an independent auditor panel) dispatched only from the main thread.
4. **Decision Engine.** Deterministic decision trees that translate project intake into architecture rules, gate selection, phase plans, and compliance mappings.
5. **Cognition Ceiling (model-driven).** Natural-language understanding, code generation, audit reasoning, product-drift judgment, and conversational routing — accelerated by the model, but always answerable to the floor.

---

## 4. The Lifecycle

VibeOS runs a project through a complete, governed lifecycle, each stage backed by a dedicated skill and its enforcement:

**Discover → Plan → Build → Audit → Checkpoint → Upgrade**, with **Comp** as a competition-grade fast path.

- **Discover** — turn a rough idea into validated product, anchor, and governance documents (or analyze an existing codebase).
- **Plan** — run intake, apply the decision engine, and emit a complete phased plan of ordered work orders.
- **Build** — autonomously execute work orders end-to-end with TDD, the agent pipeline, quality gates, and the audit cycle.
- **Audit** — dispatch the full independent auditor panel for multi-perspective review with consensus logic.
- **Checkpoint** — phase-boundary review that establishes quality baselines and enforces ratcheting (finding count can never increase between phases).
- **Upgrade** — apply a newer framework version to an existing project, reconcile config, and re-run the decision engine and gates as a discovery sweep.

---

## 5. Feature Domains

### 5.1 Discovery & Planning Intelligence
- **Decision engine** — 10 deterministic decision trees (architecture rules, gate selection, hook selection, phase selection, development-plan generation, technical recommendation, product shaping, AI-integration patterns, observability patterns, compliance mapping). Intake answers deterministically produce the architecture constraints, the gate suite, and the phase plan — the plan is *derived*, not improvised.
- **Document pyramid** — a single-source-of-truth chain (thesis → product anchor → PRD → technical spec → dependencies → architecture → plan). Execution is governed by the map; the anchor is the reference every drift check evaluates against.
- **Governed work orders** — every unit of work has a spec file with scope, acceptance criteria, dependencies, audit checkpoints, and evidence. A work-order index and development plan track all of them.

### 5.2 Autonomous Build Engine
- **Test-Driven by construction** — a tester agent writes tests from the spec *before* any implementation exists; implementation agents then make them pass. The tester never reads implementation code, so tests encode intent, not the code's shape.
- **Specialized agent pipeline per work order** — investigator → tester → prompt-engineer (when prompt artifacts change) → backend/frontend implementer → quality gates → audit cycle → doc-writer → completion.
- **Checkpoint & resume** — progress is journaled after each agent. If a run is interrupted (context reset, crash, manual pause), the build resumes from the exact step it left off.
- **Truthful completion discipline** — a work order can only be marked `Complete` when intended behavior is implemented, the *real* execution path is verified, tests pass, gates pass, status is truthful, and the repo is left clean and resumable. A full vocabulary of honest partial states (`Implemented Locally`, `Awaiting Real-Path Verification`, `Dev-Mode Complete`, `Awaiting Gate Cleanup`, `Awaiting Evidence`, `Awaiting Checkpoint`) prevents false "done."
- **Error recovery** — agent timeouts and malformed output trigger bounded retries with simplified prompts, then escalate with options, consequences, and a recommendation.

### 5.3 The Agent Fleet (32 specialized agents)
A roster of single-purpose subagents, dispatched only from the main thread (subagents cannot spawn subagents):

- **Builders:** investigator, tester, backend, frontend, prompt-engineer, doc-writer, integration-captain, contract-validator.
- **Planning:** plan-auditor.
- **Independent auditor panel:** security, architecture, correctness, test-quality, evidence, product-drift, flow, system-invariant, dependency-intelligence, delivery-infrastructure, and red-team auditors.
- **Two execution modes per auditor:** *isolated* (a fresh throwaway git worktree for maximum independence) and *same-tree* (12 in-worktree variants for fast, session-scoped review without isolation overhead). A third visibility mode routes review to an external Codex CLI.
- **Hard guarantees:** audit agents are read-only (`Write`, `Edit`, `Agent` disallowed) and isolated; implementation agents cannot touch test files.

### 5.4 The Quality Gate System (Deterministic Floor)
A declarative gate manifest catalogs every check with a tier, blocking flag, lifecycle phase, and environment. The gate runner executes the right gates at the right lifecycle moment. Gates are bound to lifecycle phases:

- **pre_commit (10 gates):** secret scanning, security-pattern scanning, stub/placeholder detection, file-size limits, code quality (lint), tests-required, tests-pass, code-complexity/god-object detection, dependency version + audit checks.
- **wo_entry (2):** work-order validation, infrastructure-manifest validation.
- **wo_exit (11):** architecture enforcement, development-plan alignment, scope discipline, cross-boundary contracts, work-order status integrity, evidence-bundle and audit-completeness checks, test integrity, logging patterns, model versions, documentation completeness.
- **comp_gauntlet (12):** competition-grade checks — AI failure modes, flow integrity, system invariants, dependency intelligence, delivery infrastructure, dev-mode fallback detection, observability, auth boundaries, API contracts, production readiness.
- **full_audit (17):** the deep sweep — testing anti-patterns, AI integration, auth, communication contract, data integrity, dev environment, env completeness, infrastructure connectivity, observability, OWASP alignment, PII handling, production readiness, resilience patterns, tenant isolation, worktree freshness, and more.
- **session_start / session_end:** session validation and long-run-autonomy validation.

Gates use a **tiered model** — tier 0/1 are blocking (security and code-quality/architecture), tier 2/3 are advisory (compliance/dependencies and documentation/communication) — configurable per project by the decision engine based on deployment context.

### 5.5 The Layered Audit System
- **Two layers.** Layer 1 is the deterministic gate floor (above). Layer 2 is the independent auditor panel — model-driven reasoning that finds what scripts can't: logic errors, missing error paths, incomplete implementations, hidden product drift.
- **Consensus + severity logic.** Findings are aggregated, deduplicated, and filtered by severity; critical/high findings trigger an automated fix cycle, medium/low are logged.
- **Convergence control.** The fix loop is bounded by a convergence controller (state-hash diffing, iteration ceilings, finding-count deltas) that decides CONVERGED / CONTINUE / STUCK / MAX-ITER — so the system fixes findings without looping forever, and escalates with options when it genuinely stalls.
- **Every fix is re-audited.** Findings are adversarially verified before being accepted as real, and re-checked after each fix.

### 5.6 Anti-Drift & Fidelity Engine
The harness's answer to the single biggest failure mode of vibe-coded projects — drift across hundreds of files:
- **Finding-level baselines & ratcheting.** Each finding is fingerprinted (category:file:pattern:severity). New findings are flagged individually; the finding count can **never increase between phases**. Fixed findings are ratcheted out of the baseline.
- **Product-drift & flow auditors.** Dedicated agents check that the work still serves the original product anchor and that the primary user journey survives every change.
- **Scope discipline guards.** Per-work-order write scopes; parallel worktrees are blocked from writing outside their assigned territory.
- **Status integrity.** Machinery detects and rejects plan/index status drift and misleading "done" claims — keeping the project's own status truthful.

### 5.7 Hook-Based Enforcement (12 hooks)
Event-driven controls that fire automatically, documented in a synchronized hook manifest:
- **SessionStart** — prerequisite validation and rich recovery context (branch, recent work, next work order, drift summary, resume point).
- **UserPromptSubmit** — governance guard (blocks attempts to bypass gates/audits/hooks) and the intent router.
- **PreToolUse** — secret scanning, frozen-file protection, test-file protection (TDD enforcement), test-diff auditing (anti-weakening), worktree scope/bash guards, proof protection, file-size budget.
- **Stop** — response-quality inspection (blocks on concrete stub/placeholder/swallowed-error markers) and significance-triggered complementary audit.
- **Lifecycle hooks** for post-tool verification, subagent-return validation, durable state flush on session end / pre-compact, worktree setup/teardown, and agent-team governance.

### 5.8 Voice-Led Intent Routing (Conversational by Design)
Users never need to type slash commands. A UserPromptSubmit hook analyzes natural language, classifies intent and lifecycle state, and injects a routing hint with a confidence level. High-confidence intents invoke the right skill immediately; medium-confidence confirm in one sentence; low-confidence ask a brief clarifier. The system is a conversation, not a CLI — slash commands remain as power-user shortcuts.

### 5.9 Multi-Runtime Orchestration
- **Runtime capability detection.** The harness probes the local environment and builds a capability matrix — which runtimes are present, their versions, and which capabilities (subagents, worktrees, agent teams, dynamic workflows, headless operation, hooks) are available — each with an evidence string — then **recomputes its orchestration strategy** to match.
- **Claude + Codex.** VibeOS orchestrates Claude Code natively and can dispatch a complementary, independent audit to an external Codex CLI — a genuinely separate second opinion. The harness stays *limitation-aware*: it never claims Codex has Claude-equivalent hook parity, and keeps deterministic Git hooks as the cross-runtime enforcement fallback.
- **Model policy by capability tier.** Model selection uses capability tiers verified at runtime, never hardcoded model IDs — so the harness doesn't go stale as models evolve, and silent model downgrades are blocked.

### 5.10 The Comp Gauntlet (Competition-Grade MVPs)
A dedicated fast path for building competition-grade enterprise MVPs and design-partner prototypes, validated by a 12-gate gauntlet that goes beyond ordinary quality: AI failure-mode handling, flow integrity, system invariants, dependency intelligence, delivery infrastructure, dev-mode-fallback detection, observability, auth boundaries, API contracts, and production readiness — backed by a battle harness (blueprint, dossier, red-team, scorecard).

### 5.11 Long-Run Autonomy (24–48 Hour Runs)
- **Resumable by design.** Heartbeat evidence, checkpoints, an audit cadence, stale-run detection, evidence-backed recovery resolution, and an explicit terminal state.
- **Full autonomous mode.** A session override that suppresses routine check-ins and keeps building until a real blocker, an explicit risk decision, a plan boundary, or completion — pausing only when governance genuinely requires a human decision.
- **Bounded loops.** No unbounded loops anywhere; every loop declares ceilings (turns, cost) and a goal-verified stop condition. Limit-aware self-rescheduling supports overnight headless runs.

### 5.12 Machine-Readable Work-Order Contracts
Each work order carries a machine-readable contract: class (which sets auditor-panel size and evidence depth), write-scope globs, required auditors, model policy, budget posture, optional loop goal/ceilings, and no-touch boundaries. Generators emit worktree scopes and agent allow/deny material from a single work-order file, and lints cross-validate the contract against the prose — structurally eliminating whole classes of drift. The work-order index becomes a *generated* view, so hand-edits that would reintroduce drift are detected and rejected.

### 5.13 Lane-Readiness Automation (Parallel Worktrees)
Parallel work runs in isolated lanes (git worktrees) with exclusive path territories. A lane-readiness gate rebases each lane in a scratch worktree, runs the exit gates, validates a structured return packet, and re-validates the lane's write-scope against the actual diff (anti-spoofing) before accepting or deferring — so parallel agents can't collide or quietly exceed their scope.

### 5.14 Framework Self-Upgrade Engine
VibeOS upgrades itself in governed projects: a deterministic delta engine computes what changed, a cognition review layer evaluates the change against the project's own anchor, an apply/preserve/rollback engine integrates it without clobbering local edits, and a fixture smoke test proves the upgrade is safe — the harness dogfoods its own governance on itself.

### 5.15 Evidence & Provability
- **Generated inventory.** A source-derived inventory artifact counts every skill, agent, hook, script, gate, decision file, reference, test, and work order directly from the repository — so public claims are *generated from source*, never copied from stale numbers.
- **Claim ledger.** Each claim is marked with its public status — "proven with this artifact," "asserted," or blocked as an overclaim — so positioning never outruns evidence.
- **Verdict vocabulary.** Status escalates through evidenced levels: `planning-only → locally implemented → nonproduction proven → production/runtime approved → public-link ready`. Nothing may claim a level it hasn't evidenced.

### 5.16 Reusable-Object Registry & Internal Marketplace
A registry and spec for reusable objects, an own-repo reuse scanner, a secure ingestion sandbox for external sources, a marketplace indexer wired into project setup, and an enterprise internal-marketplace mode — so proven components compound across projects instead of being rebuilt.

---

## 6. The "First-Class" Concerns

VibeOS treats these as architectural invariants — not features bolted on, but properties the harness enforces everywhere:

1. **Flow integrity** — the primary user journey and original objective survive every WO, test, audit, and scorecard.
2. **System invariants** — state, ownership, side-effect, retry, recovery, and auditability rules are explicit and evidenced.
3. **Dependency intelligence** — dependency choices carry current-source evidence, compatibility proof, lockfile discipline, security-audit output, and an upgrade path.
4. **Delivery infrastructure** — CI/CD, deployment, observability, environment/secrets, smoke checks, rollback, and runbooks are explicit and evidenced.
5. **Long-run autonomy** — multi-day runs are resumable with heartbeat evidence, checkpoints, audit cadence, and explicit terminal states.
6. **Truthful status** — misleading "done" and plan/index drift are structurally rejected.

---

## 7. Technology & Footprint

- **Pure Claude Code plugin** — no external frameworks. Skills + hooks + agents + deterministic scripts.
- **Deterministic substrate:** Bash 3.2+ (macOS-compatible, no external deps) and Python 3.7+ for gate scripts, hooks, and convergence logic; `jq` for JSON; `git` for version control and worktree isolation; optional Codex CLI for complementary audit.
- **Source-derived component counts (generated inventory):**
  - **15** user-invocable skills
  - **32** specialized agents (20 base + 12 same-tree audit variants)
  - **12** event-driven hooks (manifest-synced)
  - **89** deterministic gate & utility scripts
  - **10** decision-engine trees
  - **5** convergence/loop-control scripts
  - **122** annotated reference files
  - **113** governed work orders
  - Quality gates spanning **7 lifecycle phases** (pre_commit, wo_entry, wo_exit, comp_gauntlet, full_audit, session_start, session_end)

---

## 8. How It's Used (Harness Engineering in Practice)

VibeOS is the operating layer beneath a solo founder building enterprise-grade, compliance-targeted production systems with AI agents — across multiple large, security-critical projects, each growing toward hundreds of thousands of lines. It is the connective tissue that makes "vibe coding" safe at enterprise scale:

- **You describe intent; the harness governs execution.** Discovery and planning turn an idea into an anchored map; the build engine executes the map autonomously without drifting from it.
- **The harness, not the human, holds the line.** Quality, security, scope, and truthful status are enforced by deterministic floor controls and an independent auditor panel — so autonomy never means abandoning rigor.
- **It compounds.** Proven components flow into a reusable-object registry and internal marketplace; the framework upgrades itself across projects; baselines ratchet quality monotonically upward.
- **It is model-resilient.** Because every blocking guarantee lives on the deterministic floor and model policy uses verified capability tiers rather than pinned IDs, the harness keeps working — and keeps its guarantees — as the underlying models evolve.

This is harness engineering: treating the *governance substrate* as the product, and the model as a powerful, replaceable component plugged into it.

---

## 9. Differentiators (Why It Matters)

- **Deterministic guarantees under a probabilistic model.** Blocking controls never depend on the model behaving.
- **Zero-debt by enforcement, not aspiration.** Ratcheting baselines make quality monotonic; partial-state honesty prevents false "done."
- **Independent, adversarial audit built in.** A read-only, isolated auditor panel — plus an optional external Codex second opinion — reviews every change from multiple perspectives with consensus and convergence control.
- **Anti-drift as a first-class system.** The document pyramid, product-drift/flow auditors, scope guards, and generated/contract-validated tracking structurally prevent the drift that sinks large vibe-coded projects.
- **Provable claims.** A generated inventory and claim ledger mean every public number traces to source and every status traces to evidence.
- **Conversational, autonomous, resumable.** Natural-language routing, full autonomous mode, and 24–48h resumable runs — without surrendering governance.

---

*Source of facts: the VibeOS repository and its generated inventory artifact. Component counts are source-derived. This dossier describes the harness's capabilities and mechanisms as the product; downstream positioning, narrative framing, and visual treatment are the case-study team's to compose.*
