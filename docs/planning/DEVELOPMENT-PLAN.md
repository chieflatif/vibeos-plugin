# VibeOS Plugin — Development Plan

## Vision

Transform Claude Code from a reactive coding assistant into an autonomous, self-governing development engine. A user describes what they want to build, the plugin guides them through product discovery and planning, then autonomously builds the project with continuous multi-layered audits ensuring zero technical debt.

## Architecture Decision

Use Claude Code's native capabilities exclusively (skills + hooks + agents + MCP). No external frameworks (LangGraph, CrewAI, Docker, etc.) for v1. Pure Bash + Markdown. Re-evaluate for v2 if complexity outgrows native capabilities.

## Phases Overview

| Phase | Name | WOs | Goal |
|---|---|---|---|
| 0 | Architecture Validation | WO-000 | Technical spike: verify plugin manifest, skills/commands, agent dispatch, hook exit codes |
| 1 | Plugin Foundation | WO-001 — WO-007a | Plugin loads, skills invoke, gates run, hooks block, agent dispatches |
| 2 | Product Discovery & Planning | WO-008 — WO-012 | User goes from rough idea to reviewed development plan |
| 3 | Autonomous Build Loop | WO-013 — WO-022 | Full WO cycle: investigate → plan → test → implement → audit → commit |
| 4 | Fresh-Context Audit Agents | WO-023 — WO-029 | 5 isolated audit agents + consensus aggregation |
| 5 | Convergence & Full Loop | WO-030 — WO-034 | Multi-WO autonomy, convergence controls, phase boundaries |
| 6 | Midstream Embedding & Polish | WO-035 — WO-040 | Existing projects, baselines, test quality, upgrade, e2e testing |
| 7 | Informed Onboarding & User Comprehension | WO-041 — WO-048 | Architecture-first midstream, finding-level baselines, communication layer |
| 8 | Resilience & Transparency | WO-049 — WO-053 | Mid-WO resume, decision engine explainability, baseline bootstrap, first-run polish, safety hardening |
| 9 | Conversational Experience | WO-054 | Voice-led intent routing, natural language interaction, slash command elimination |
| 10 | Distribution & Runtime | WO-055+ | Pivot from broken plugin system to project-level bootstrap model |
| 11 | Advanced Governance (v2.1) | WO-056 — WO-065 | Joan-extracted enhancements: same-tree auditing, Codex integration, scope guards, parallel worktree isolation |
| 12 | Harness Convergence | WO-067 — WO-068 | Fold proven reusable harness improvements back into the framework |
| 13 | Evidence Memory Research | WO-069 — WO-071 | Test and implement structured evidence recall when it materially reduces context/token usage |
| 14 | VibOS Comp — Enterprise MVP Battle Harness | WO-072 — WO-081 | Build a competition-grade enterprise MVP harness with modern Codex/Claude swarms, foundation blueprints, quality gauntlets, red-team review, and scorecard evidence |
| 15 | Flow Integrity & Objective Fidelity | WO-082 — WO-083 | Make the primary user journey and original objective first-class across mission, planning, implementation, testing, auditing, and scorecards |
| 16 | System Invariants & State Safety | WO-084 — WO-085 | Make state, ownership, idempotency, recovery, and auditability rules first-class across mission, planning, testing, auditing, and scorecards |
| 17 | Dependency Intelligence & Current Evidence | WO-086 — WO-087 | Make dependency decisions current, compatible, lockfile-backed, audited, and upgradeable instead of driven by stale model memory |
| 18 | Stack Dependency Currency Packs | WO-088 — WO-089 | Add stack-specific currency packs so runtime, framework, SDK, auth, database, AI, and deployment dependency evidence is concrete |
| 19 | Delivery Infrastructure & Operational Spine | WO-090 — WO-091 | Make CI/CD, deployment, observability, environment/secrets, smoke checks, rollback, and runbooks first-class Comp foundations |
| 20 | Comp Validation Hardening | WO-092 | Prevent generated governance artifacts from creating false-positive Comp validation failures |
| 21 | Long-Run Autonomy | WO-093 — WO-094 | Make 24-48 hour autonomous runs resumable, auditable, heartbeat-driven, and safely stoppable |
| 22 | Long-Run Supervisor | WO-095 | Add deterministic resume-plan decisions above the heartbeat/checkpoint/audit loop |
| 23 | Long-Run Runner Adapter | WO-096 | Safely classify and execute allowlisted resume-plan commands while preserving Codex/Claude handoff work |
| 24 | Long-Run Loop Entrypoint | WO-097 | Add a scheduler-safe supervisor-plus-runner tick entrypoint for durable 24-48 hour operation |
| 25 | Runtime Handoff Adapter | WO-098 | Turn long-run handoff state into dry-run-first Codex/Claude runtime launch plans |
| 26 | Autonomy Scheduler Profiles | WO-099 | Generate reviewed shell, cron, launchd, and GitHub Actions profiles for long-run autonomy ticks |
| 27 | Disposable Autonomy Smoke | WO-100 | Prove the autonomy chain in a disposable target before trusting scheduler profiles |
| 28 | Autonomy Run Lease Guard | WO-101 | Prevent concurrent schedulers or runtime adapters from driving the same long-run autonomy session |
| 29 | Autonomy Failure Loop Detector | WO-102 | Detect repeated handoff, runner, runtime, lease, and provider/session failures before the scheduler loops |
| 30 | Autonomy Recovery Planner | WO-103 | Convert autonomy failures into plan-only recovery actions before another scheduler tick |
| 31 | Autonomy Scheduler Guard | WO-104 | Refuse scheduler ticks while recovery-plan actions lack matching resolution evidence |
| 32 | Autonomy Recovery Resolution Protocol | WO-105 | Record evidence-backed recovery action resolution before scheduler ticks resume |

## Mandatory Audits

- **Post-Phase 1:** Validates 3 critical assumptions — plugin context works for gate scripts, hooks reliably block with exit code 2, subagent dispatch and return works. Architecture revision required if any fail.
- **Post-Phase 3:** Validates orchestration under real conditions — run build loop on test fixture project, verify agents dispatch correctly, gates catch known issues, test file protection works, error recovery handles failures.

---

## Phase 0: Architecture Validation

**Goal:** Validate the 4 critical assumptions the plugin architecture depends on before committing to implementation.

**Exit Criteria:** All 4 assumptions verified, SPIKE-RESULTS.md documented, development plan updated based on findings.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-000 | Technical Spike — Plugin Architecture Validation | None | Complete |

**Assumptions to validate:**
1. Plugin manifest schema — what fields does `plugin.json` accept?
2. Skills vs Commands — which directory for slash-invoked workflows?
3. Agent dispatch — can a skill dispatch an agent and get structured output back?
4. Hook exit codes — what code blocks vs allows operations?

---

## Phase 1: Plugin Foundation

**Goal:** Plugin loads, skills invoke, gates run from plugin context, basic agent dispatch works.

**Exit Criteria:** Plugin installs, 2 skills invoke correctly, gates run from plugin context, hooks block dangerous operations, one agent dispatches and returns. Test fixture validates each layer.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-001 | Repo Setup & Plugin Manifest | None | Complete |
| WO-002 | Bundle Gate Scripts | WO-001 | Complete |
| WO-003 | Bundle Decision Engine & Reference Files | WO-001 | Complete |
| WO-004 | `/vibeos:gate` Skill | WO-002 | Complete |
| WO-005 | `/vibeos:status` Skill | WO-001 | Complete |
| WO-006 | Basic hooks.json (Layer 0) | WO-001 | Complete |
| WO-007 | Planner Agent (Proof of Concept) | WO-001 | Complete |
| WO-007a | Test Fixture Project | WO-006 | Complete |

---

## Phase 2: Product Discovery & Planning

**Goal:** Full idea-to-plan flow. User goes from rough idea to reviewed development plan.

**Exit Criteria:** User says "I want to build X", gets complete product docs + reviewed development plan + governance installed + autonomy configured.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-008 | `/vibeos:discover` Skill | Phase 1 complete | Complete |
| WO-009 | `/vibeos:plan` Skill | WO-008 | Complete |
| WO-010 | Plan Auditor Agent | WO-007 | Complete |
| WO-011 | Autonomy Negotiation | WO-009 | Complete |
| WO-012 | Project Intake Integration | WO-009 | Complete |

---

## Phase 3: Autonomous Build Loop

**Goal:** Orchestrator executes a full WO cycle: investigate → plan → test → implement → audit → document → commit.

**Exit Criteria:** `/vibeos:build` executes one WO end-to-end with TDD. Tests written before implementation. Implementation cannot modify tests. Gates pass after implementation. Error recovery handles agent failures gracefully.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-013 | Investigator Agent (Phase 0) | Phase 2 complete | Complete |
| WO-014 | Tester Agent | WO-013 | Complete |
| WO-015 | Test File Protection Hook | WO-014 | Complete |
| WO-016 | Backend Agent | WO-015 | Complete |
| WO-017 | Frontend Agent | WO-015 | Complete |
| WO-018 | Doc Writer Agent | WO-016 | Complete |
| WO-019 | `/vibeos:build` Orchestrator — Agent Dispatch Loop | WO-013 | Complete |
| WO-020 | `/vibeos:build` Orchestrator — WO Lifecycle | WO-019, WO-014-018 | Complete |
| WO-021 | `/vibeos:build` Orchestrator — Gate Integration | WO-020 | Complete |
| WO-022 | `/vibeos:wo` Skill (WO Management) | WO-020 | Complete |

---

## Phase 4: Fresh-Context Audit Agents (The Governor)

**Goal:** Full Layer 2 audit system with isolated, bias-free, multi-perspective auditing.

**Exit Criteria:** All 5 audit agents run in isolation, catch their respective issue classes, consensus aggregation works, auditors integrated into build loop.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-023 | Security Auditor Agent | Phase 3 complete | Complete |
| WO-024 | Architecture Auditor Agent | Phase 3 complete | Complete |
| WO-025 | Correctness Auditor Agent | Phase 3 complete | Complete |
| WO-026 | Test Auditor Agent | Phase 3 complete | Complete |
| WO-027 | Evidence Auditor Agent | Phase 3 complete | Complete |
| WO-028 | `/vibeos:audit` Skill (Full Audit Cycle) | WO-023-027 | Complete |
| WO-029 | Integrate Auditors into Build Loop | WO-028, WO-021 | Complete |

---

## Phase 5: Convergence & Full Autonomous Loop

**Goal:** Multi-WO autonomous execution with convergence controls and phase boundary audits.

**Exit Criteria:** Plugin autonomously builds a 3+ WO phase. Convergence prevents infinite loops. Phase boundary audit runs. Human check-in fires. Token budget tracked.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-030 | Convergence Controls | WO-029 | Complete |
| WO-031 | Token Budget Tracking | WO-030 | Complete |
| WO-032 | Multi-WO Orchestration | WO-030 | Complete |
| WO-033 | Phase Boundary Audit (Layer 5) | WO-032 | Complete |
| WO-034 | Human Check-in Protocol (Layer 6) | WO-032 | Complete |

---

## Phase 6: Midstream Embedding & Production Readiness

**Goal:** Plugin works for existing projects. Edge cases handled. Ship-ready.

**Exit Criteria:** Plugin works for greenfield and existing projects. Baselines work. Test quality enforcement catches all anti-patterns. Upgrade preserves config. End-to-end scenarios pass.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-035 | Midstream Embedding | Phase 5 complete | Complete |
| WO-036 | Known Baselines Integration | WO-035 | Complete |
| WO-037 | Enhanced Test Quality Enforcement | WO-026 | Complete |
| WO-038 | Test Diff Auditing | WO-037 | Complete |
| WO-039 | Plugin Upgrade Mechanism | WO-035 | Complete |
| WO-040 | End-to-End Integration Testing | WO-035-039 | Complete |

---

## Phase 7: Informed Onboarding & User Comprehension

**Goal:** Replace blind baselining with informed user-driven decisions. Make the system visible and understandable. Two tracks: (A) midstream onboarding that audits architecture first and lets the user decide finding dispositions, (B) communication layer that explains what's happening at every step.

**Exit Criteria:** Midstream user makes informed decisions about every critical/high finding before baseline is established. Finding-level baselines prevent new issues hiding behind fixed ones. User understands what the system is doing at every step. All communication follows the contract.

**Implementation Order:** While the two tracks have independent dependency chains, they share file modifications (`skills/discover/SKILL.md`, `skills/plan/SKILL.md`, `skills/build/SKILL.md`) and semantic dependencies (Track A defines user-facing communication patterns that should follow Track B's contract). The recommended implementation order is:

1. WO-045 (communication contract — no dependencies, unlocks consistent communication)
2. WO-041 (architecture-first discovery)
3. WO-042 (guided audit — references WO-045 contract for communication patterns)
4. WO-046 (onboarding — depends on WO-045, coordinates with WO-041 on discover skill)
5. WO-043 (finding-level baseline)
6. WO-044 (remediation roadmap)
7. WO-047 (build visibility — Track A done modifying build skill)
8. WO-048 (consequence decisions — all decision points now exist)

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-045 | User Communication Contract | Phase 6 complete | Draft |
| WO-041 | Architecture-First Midstream Discovery | Phase 6 complete | Draft |
| WO-042 | Guided Codebase Audit with User Decisions | WO-041, WO-045 (soft) | Draft |
| WO-046 | System Onboarding & Concept Introduction | WO-045, WO-041 (soft) | Draft |
| WO-043 | Finding-Level Baseline Model | WO-042 | Draft |
| WO-044 | Remediation Roadmap & Phase 0 Enforcement | WO-043 | Draft |
| WO-047 | Build Loop Visibility & Progress Reporting | WO-045, WO-044 (soft) | Draft |
| WO-048 | Consequence-Aware Decision Support | WO-045, WO-044 (soft) | Draft |

---

## Phase 8: Resilience & Transparency

**Goal:** Close gaps found during end-to-end audit: build loop can resume interrupted WOs, decision engine explains its choices, midstream baseline creation works end-to-end, first-run experience guides users, and validation catches missing prerequisites.

**Exit Criteria:** Mid-WO resume works from checkpoint. Decision engine explains every selection. Gate management works without manual JSON editing. Midstream baseline bootstrap is seamless. First-run user knows what to do. Git repo validated. Test file protection logged. PRD merge preserves user edits.

**Implementation Order:** WO-049 first (build skill changes foundation for others), then WO-050 and WO-051 (both modify plan/build skills), then WO-052 and WO-053 (polish and hardening).

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-049 | Mid-WO Resume & Error Recovery | Phase 7 complete | Draft |
| WO-050 | Decision Engine Transparency & Gate Management | Phase 7 complete | Draft |
| WO-051 | Midstream Baseline Bootstrap | Phase 7 complete | Draft |
| WO-052 | First-Run Experience & Handoffs | Phase 7 complete | Draft |
| WO-053 | Validation & Safety Hardening | Phase 7 complete | Draft |

---

## Phase 9: Conversational Experience

**Goal:** Eliminate slash command dependency. Users interact with VibeOS through natural language. The system detects intent, reads project lifecycle state, and routes to the correct skill automatically.

**Exit Criteria:** User can go from "I want to build a task management app" to discovery flow without typing any slash command. All lifecycle states route correctly. Disambiguation handles ambiguous intents. Slash commands still work as power-user shortcuts.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-054 | Voice-Led Intent Routing | Phase 8 complete | Complete |

---

## Phase 10: Distribution & Runtime

**Goal:** Replace broken Claude Code plugin distribution with a project-level bootstrap model. User runs a single script that installs the full VibeOS governance framework into their project's `.claude/` and `.vibeos/` directories, using Claude Code's proven project-level config system.

**Context:** The Claude Code plugin system (`claude plugin install`) silently fails for skills-based plugins. The `--plugin-dir` flag works but is session-only and unavailable in Cursor IDE. This phase pivots from plugin distribution to project-level bootstrap — same content, reliable delivery mechanism.

**Exit Criteria:** `bash vibeos-init.sh` installs framework into any project. All 9 skills register, all hooks fire, all agents dispatch. Works in both Claude Code CLI and Cursor IDE. Supports greenfield, midstream, and upgrade modes.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-055 | Architectural Pivot — Plugin to Project-Level Bootstrap | WO-054 | Draft |

---

## Phase 11: Advanced Governance (v2.1) — Joan Extraction

**Goal:** Extract battle-tested governance enhancements from Joan into generalizable VibeOS platform capabilities. Same-tree auditing, Codex complementary auditing, scope discipline, proof protection, parallel worktree isolation, and enhanced build/audit skill integration.

**Source:** `/Users/latifhorst/Joan` — production-hardened VibeOS deployment with 27 agents, 14 skills, 62 gate scripts, 11 hooks.

**Exit Criteria:** All 20 enhancement items extracted from Joan, generalized (no Joan-specific references), integrated into existing skills/agents/hooks, version bumped to 2.1.0, upgrade script updated. Framework installs and runs cleanly on any project.

**Implementation Strategy:** Copy-and-adapt from Joan. Each WO reads the Joan source, strips Joan-specific references (kernel, NWO, Microsoft boundary, canon index), generalizes the pattern, and integrates into the VibeOS plugin structure.

**Implementation Order (optimized for parallelism):**
1. WO-056 (foundation — all others depend on this)
2. WO-057, WO-058, WO-059, WO-060, WO-061, WO-063 (all parallel after WO-056)
3. WO-062 (after WO-058)
4. WO-064 (after WO-057, WO-058, WO-062)
5. WO-065 (after all)

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-056 | Session State & Gate Manifest Infrastructure | Phase 10 | Complete |
| WO-057 | Same-Tree Audit Agents | WO-056 | Draft |
| WO-058 | Audit Visibility & Registration System | WO-056 | Draft |
| WO-059 | Scope Discipline & File Budget Guards | WO-056 | Draft |
| WO-060 | Proof Protection & Governance Guard Hooks | WO-056 | Draft |
| WO-061 | Enhanced Parallel Worktree Isolation | WO-056 | Draft |
| WO-062 | Codex Audit Integration | WO-058 | Draft |
| WO-063 | Enhanced Investigator & CLI-vs-MCP Reference | WO-056 | Draft |
| WO-064 | Build/Audit Skill Enhancements | WO-057, WO-058, WO-062 | Draft |
| WO-065 | v2.1 Release Packaging | WO-056-064 | Draft |

---

## Phase 12: Harness Convergence

**Goal:** Port the reusable governance and harness improvements proven during real project setup back into the core framework, then harden the Codex surface so cross-runtime installs share truthful enforcement boundaries without leaking project-specific doctrine.

**Exit Criteria:** Canonical manifest and version paths are consistent, lightweight governance assets are bundled as references, planning/bootstrap guidance points future installs at the upgraded harness spine, and the Codex surface uses the shared runtime plus commit-boundary Git hooks as its truthful enforcement substitute.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-067 | Signal Claw Harness Convergence | WO-065 | Complete |
| WO-068 | Codex Cross-Surface Hardening | WO-067 | Complete |

---

## Phase 13: Evidence Memory Research

**Goal:** Determine whether VibeOS should add a narrow, structured evidence-memory index that recalls existing Work Orders, findings, audits, gates, checkpoints, and decision artifacts with citations and measurable token/context savings, then implement the smallest proven local utility if the spike clears the threshold.

**Context:** Reviews of Lucas's memory setup and Ruflo suggest that broad chat memory, Obsidian import, swarms, daemons, and external orchestration are not appropriate for VibeOS core. The plausible opportunity is smaller: rank existing evidence artifacts so workflows read less repeated context while preserving the "finding -> Work Order -> evidence" discipline.

**Exit Criteria:** The spike produces an adopt, defer, or abandon recommendation backed by benchmark data. Proceeding requires at least 2x reduction in relevant context/read tokens or at least 40% workflow token reduction with zero missed critical evidence in the benchmark set.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-069 | Structured Evidence Memory Spike | WO-031, WO-049, WO-056, WO-068 | Complete |
| WO-070 | Evidence Recall Indexer and Query Command | WO-069 | Complete |
| WO-071 | v2.2 Release Hygiene | WO-070 | Complete |

---

## Phase 14: VibOS Comp — Enterprise MVP Battle Harness

**Goal:** Add a high-performance enterprise MVP delivery mode that uses current Codex and Claude capabilities to move fast without producing fragile prototypes. VibOS Comp should generate small-scope but foundation-complete MVPs: secure, observable, testable, deployable, scalable, and backed by inspectable evidence.

**Commercial Thesis:** MVPs should be small in product scope, not small in engineering standards. VibOS Comp is designed to help users rapidly build software that can withstand review by enterprise design partners, senior engineers, security reviewers, and competition judges.

**Context:** Current VibeOS already has layered governance, worktree isolation, audit agents, Codex complementary audit, and evidence recall. The gap is a competition control plane: runtime-aware agent capability selection, modern Codex-native surface, compact mission intake, enterprise foundation blueprint, swarm planning, integration ownership, quality gauntlet, red-team arena, and scorecard evidence.

**Exit Criteria:** A user can give VibOS Comp an MVP or competition prompt and receive a compact mission brief, parallel execution plan, enterprise foundation checklist, scoped worktree swarm setup, final integrated quality gauntlet, adversarial red-team review, and scorecard/evidence dossier. Completion claims must distinguish proven, partial, deferred, and overridden evidence.

**Implementation Order:**
1. WO-072 (runtime truth foundation)
2. WO-073 (modern Codex surface)
3. WO-074 and WO-075 (mission and enterprise MVP foundation)
4. WO-076 and WO-077 (AI failure gates and swarm planning)
5. WO-078 (integration captain)
6. WO-079 and WO-080 (quality gauntlet and red-team arena)
7. WO-081 (scorecard/evidence dossier)

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-072 | Runtime Capability Matrix | WO-068, WO-071 | Complete |
| WO-073 | Modern Codex Surface | WO-072 | Complete |
| WO-074 | VibOS Comp Mission Skill | WO-072, WO-073 | Complete |
| WO-075 | Enterprise MVP Foundation Blueprint | WO-074 | Complete |
| WO-076 | AI Failure Mode Gate Pack | WO-075 | Complete |
| WO-077 | Swarm Worktree Planner | WO-074, WO-075 | Complete |
| WO-078 | Integration Captain | WO-076, WO-077 | Complete |
| WO-079 | Quality Gauntlet | WO-076, WO-078 | Complete |
| WO-080 | Red Team Arena | WO-074, WO-079 | Complete |
| WO-081 | Scorecard and Evidence Dossier | WO-079, WO-080 | Complete |

---

## Phase 15: Flow Integrity & Objective Fidelity

**Goal:** Make the human user journey a first-class harness dimension from mission intake through Work Order planning, implementation evidence, integrated testing, audit dispatch, and scorecard closeout. VibeOS Comp must not let isolated code, UI, API, database, or security checks pass while the actual user flow is broken or drifting from the original objective.

**Context:** The existing Comp harness covered enterprise foundations, AI failure modes, parallel worktree planning, integration ownership, red-team review, and evidence dossiers. The gap was a dedicated perspective for how humans experience the system: whether a user can move through UI, auth/session, backend/API, data or side effects, feedback states, and evidence to achieve the mission promise.

**Exit Criteria:** `MISSION.md` and `COMP-PLAN.md` include primary flow and objective fidelity context; a Flow Auditor role exists for isolated and same-tree review; `comp_gauntlet` includes deterministic flow integrity validation; scorecards track Flow Integrity and Objective Fidelity; audit dispatch includes flow review for high-tier WO exits, phase exits, and live-fire audits.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-082 | Flow Auditor and Flow Integrity Gate | WO-074, WO-077, WO-079 | Complete |
| WO-083 | Objective Fidelity Scorecard Integration | WO-081, WO-082 | Complete |

---

## Phase 16: System Invariants & State Safety

**Goal:** Make system invariants a first-class harness dimension from mission intake through Work Order planning, implementation evidence, testing, audit dispatch, and scorecard closeout. VibeOS Comp must not let happy-path functionality pass while the product can enter invalid states, break ownership rules, duplicate side effects, lose recovery paths, or hide sensitive transitions.

**Context:** Flow integrity proves that the user can complete the journey. System invariants prove that the system remains correct before, during, and after that journey, including bad inputs, retries, concurrency, partial failure, future changes, and recovery.

**Exit Criteria:** `MISSION.md` and `COMP-PLAN.md` include system invariant context; a System Invariant Auditor role exists for isolated and same-tree review; `comp_gauntlet` includes deterministic invariant validation; scorecards track System Invariants; audit dispatch includes invariant review for high-tier WO exits, phase exits, live-fire audits, and security changes.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-084 | System Invariant Auditor and Gate | WO-082, WO-083 | Complete |
| WO-085 | Invariant Scorecard and Evidence Integration | WO-084 | Complete |

---

## Phase 17: Dependency Intelligence & Current Evidence

**Goal:** Make dependency intelligence a first-class harness dimension from mission intake through Work Order planning, implementation evidence, testing, audit dispatch, and scorecard closeout. VibeOS Comp must not let stale model memory pick outdated packages, incompatible SDKs, broken peer dependency sets, missing lockfiles, unaudited transitive risk, or upgrade dead ends.

**Context:** Dependency versioning is a fast failure point for AI-generated software because model training dates lag current framework, SDK, and package ecosystems. Existing dependency freshness and vulnerability gates are useful, but they need upstream governance: current-source evidence, compatibility reasoning, lockfile discipline, security audit output, and upgrade path before the build claims enterprise readiness.

**Exit Criteria:** `MISSION.md` and `COMP-PLAN.md` include dependency intelligence context; a Dependency Intelligence Auditor role exists for isolated and same-tree review; `comp_gauntlet` includes deterministic dependency intelligence validation; scorecards track Dependency Intelligence; audit dispatch includes dependency review for high-tier WO exits, phase exits, live-fire audits, security changes, and dependency/runtime/package changes.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-086 | Dependency Intelligence Auditor and Gate | WO-084, WO-085 | Complete |
| WO-087 | Dependency Scorecard and Evidence Integration | WO-086 | Complete |

---

## Phase 18: Stack Dependency Currency Packs

**Goal:** Make dependency intelligence stack-aware without hardcoding stale "latest" versions. VibeOS Comp should detect common runtime and dependency surfaces, then require concrete evidence for the specific stack: Node/TypeScript, frontend frameworks, Python/FastAPI, AI SDKs, auth/security packages, database/ORM packages, and deployment runtimes.

**Context:** A generic dependency evidence rule catches missing lockfiles and audit output, but real failures often come from stack-specific compatibility: React/router/build-tool mismatches, FastAPI/Pydantic changes, AI SDK/model API drift, auth/session library behavior, database driver/ORM migration changes, and hosting runtime constraints.

**Exit Criteria:** Stack currency packs are machine-readable, referenced by stack variants and dependency evidence templates, consumed by `validate-dependency-intelligence.py`, and tested for detection and enforcement without embedding version numbers that will go stale.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-088 | Stack Dependency Currency Pack Reference | WO-086, WO-087 | Complete |
| WO-089 | Stack Currency Validator Integration | WO-088 | Complete |

---

## Phase 19: Delivery Infrastructure & Operational Spine

**Goal:** Make delivery infrastructure a first-class harness dimension from mission intake through Work Order planning, implementation evidence, testing, audit dispatch, and scorecard closeout. VibeOS Comp must not let local app behavior pass while CI/CD, deployment, observability, environment/secrets, smoke checks, rollback, or runbooks are missing.

**Context:** The user wants autonomous enterprise MVPs that include the silent foundations world-class teams often leave implicit. Existing observability and production-readiness gates are useful, but the harness needs an explicit operational spine: pipeline-as-code or local-proof substitute, deployability, observable runtime behavior, manageable environments, secret hygiene, smoke/health checks, rollback, and runbook evidence.

**Exit Criteria:** `MISSION.md` and `COMP-PLAN.md` include delivery infrastructure context; a Delivery Infrastructure Auditor role exists for isolated and same-tree review; `comp_gauntlet` includes deterministic delivery infrastructure validation; scorecards track Delivery Infrastructure; audit dispatch includes delivery review for high-tier WO exits, phase exits, live-fire audits, security changes, and delivery/runtime changes.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-090 | Delivery Infrastructure Auditor and Gate | WO-088, WO-089 | Complete |
| WO-091 | Delivery Scorecard and Evidence Integration | WO-090 | Complete |

---

## Phase 20: Comp Validation Hardening

**Goal:** Keep the Comp validation pipeline strict without letting generated governance artifacts create self-inflicted false positives.

**Context:** The comp pipeline smoke proved that `validate-comp-ai-failure-modes.py` could scan `docs/evidence/RED-TEAM-REPORT.md`, see the generated review category `fake completion or demo-only evidence`, and fail the project even when the category label was not a project-authored failure marker.

**Exit Criteria:** Generated red-team and dossier artifacts are excluded from AI failure-marker scanning; non-generated mission, source, and evidence files remain scanned; regression tests prove both behaviors.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-092 | Comp Validation Generated Artifact Hardening | WO-076, WO-080, WO-091 | Complete |

---

## Phase 21: Long-Run Autonomy

**Goal:** Make 24-48 hour autonomy an intentional, resumable operating mode with heartbeat evidence, checkpoint cadence, audit cadence, stale-run detection, and explicit terminal states.

**Context:** Existing autonomous mode can keep building without routine check-ins, but a credible battle harness needs more than persistence. A long-running run must survive context resets, runtime interruptions, tool failures, and handoff between Codex and Claude/Cursor. That requires durable state: what is active, what changed, what was checked, what failed, what stops the run, and how another session resumes.

**Exit Criteria:** Long-run autonomy policy is machine-readable; heartbeat and validator scripts exist; session-state schema documents long-run fields; build/autonomous/status/checkpoint/session-audit skills use heartbeat and cadence controls; `session_start` and `session_end` can validate long-run state.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-093 | Long-Run Autonomy Control Plane | WO-056, WO-077, WO-091 | Complete |
| WO-094 | Long-Run Heartbeat Validator | WO-093 | Complete |

---

## Phase 22: Long-Run Supervisor

**Goal:** Add a deterministic supervisor layer that decides the next long-run autonomy action from durable state instead of leaving control-flow in model memory.

**Context:** Heartbeats and validators prove that a long-running session has state and policy, but the harness still needs a resumable decision artifact between loops. The supervisor reads config, session state, heartbeat age, checkpoint cadence, audit cadence, runtime limits, and loop iteration ceiling, then writes `.vibeos/autonomy/resume-plan.json` for the next Codex/Claude/human action.

**Exit Criteria:** `autonomy-supervisor.py` exists, writes `resume-plan.json` and `supervisor-state.json`, emits continue/checkpoint/audit/heartbeat/stop decisions, and is covered by deterministic tests.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-095 | Long-Run Supervisor Resume Plan | WO-093, WO-094 | Complete |

---

## Phase 23: Long-Run Runner Adapter

**Goal:** Add a safe runner adapter that turns supervisor resume plans into classified, auditable actions without opening an arbitrary shell execution surface.

**Context:** The supervisor can now write `.vibeos/autonomy/resume-plan.json`, but a long-run harness still needs a deterministic adapter between that artifact and the active runtime. The runner must execute only allowlisted local VibeOS scripts, block unsafe shell commands, and truthfully report Codex/Claude continuation text as handoff-required work.

**Exit Criteria:** `autonomy-runner.py` exists, writes `runner-report.json`, dry-run classifies resume plans, executes allowlisted local VibeOS scripts with `--execute`, blocks untrusted commands, and is covered by deterministic tests.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-096 | Long-Run Runner Adapter | WO-093, WO-094, WO-095 | Complete |

---

## Phase 24: Long-Run Loop Entrypoint

**Goal:** Add a scheduler-safe loop entrypoint that runs supervisor plus runner ticks and writes durable loop state.

**Context:** The supervisor decides what should happen next and the runner safely classifies or executes allowlisted local commands. A 24-48 hour harness still needs a stable entrypoint that a terminal, cron, launchd, CI job, or future runtime adapter can invoke repeatedly. The loop must default to one tick, write `.vibeos/autonomy/loop-state.json`, and stop truthfully at handoff, blocked, failed, scheduled, or terminal states.

**Exit Criteria:** `autonomy-loop.py` exists, writes `loop-state.json`, invokes supervisor and runner, supports dry-run and `--execute`, stops at model-handoff boundaries, and is covered by deterministic tests.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-097 | Long-Run Loop Entrypoint | WO-093, WO-095, WO-096 | Complete |

---

## Phase 25: Runtime Handoff Adapter

**Goal:** Add a dry-run-first adapter that turns autonomy handoff state into explicit local Codex or Claude runtime commands.

**Context:** The loop can stop at `handoff_required`, but that still leaves an external scheduler or human to translate the handoff into the right runtime invocation. Local detection confirms Codex supports `codex exec` and Claude supports non-interactive `--print`, but these launches can use provider/session capacity and edit files, so the adapter must write a plan by default and execute only when explicitly requested.

**Exit Criteria:** `autonomy-runtime-adapter.py` exists, writes `runtime-adapter-plan.json`, selects Codex or Claude from capability evidence, builds build/audit handoff prompts, reports `no_handoff` when appropriate, and keeps launching behind `--execute`.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-098 | Runtime Handoff Adapter | WO-072, WO-096, WO-097 | Complete |

---

## Phase 26: Autonomy Scheduler Profiles

**Goal:** Generate reviewed scheduler profile files for long-run autonomy without installing system or CI scheduler jobs automatically.

**Context:** The loop and runtime adapter provide the commands needed for a 24-48 hour run, but users still need safe profiles for terminal, cron, launchd, or GitHub Actions scheduling. Profile generation must be explicit, reviewable, and dry-run-first for model runtime launch.

**Exit Criteria:** `autonomy-scheduler-profile.py` exists, writes `scheduler-profile.json`, generates shell/cron/launchd/GitHub Actions profiles, keeps runtime launch disabled unless `--launch-runtime` is requested, and is covered by deterministic tests.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-099 | Autonomy Scheduler Profiles | WO-097, WO-098 | Complete |

---

## Phase 27: Disposable Autonomy Smoke

**Goal:** Add a disposable smoke path that proves the heartbeat, loop, runtime-adapter planning, validator, failure-detector, recovery-planner, recovery-resolution, and scheduler-guard chain works before a scheduler profile is trusted.

**Context:** Scheduler profiles can run for hours, so the harness needs a cheap preflight that exercises the autonomy chain in a fresh target. The smoke path must avoid launching model runtimes by default and write a durable report for audit.

**Exit Criteria:** `autonomy-smoke.py` exists, copies required autonomy scripts into a disposable or specified target, runs heartbeat, loop, runtime-adapter planning, validation, failure detection, recovery planning, recovery resolution, and scheduler guarding, writes `smoke-report.json`, and is covered by deterministic tests.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-100 | Disposable Autonomy Smoke | WO-094, WO-097, WO-098, WO-099 | Complete |

---

## Phase 28: Autonomy Run Lease Guard

**Goal:** Prevent multiple scheduler or runtime processes from mutating the same long-run autonomy state at the same time.

**Context:** Scheduler profiles and runtime handoff adapters make 24-48 hour autonomy operational, but they also create a concurrency risk: two processes can read the same state, choose the same next action, and write conflicting artifacts. The lease guard gives loop and runtime-adapter drivers a shared `.vibeos/autonomy/run-lease.json`, blocks live conflicts, and recovers expired leases.

**Exit Criteria:** `autonomy_lease.py` exists, `autonomy-loop.py` and `autonomy-runtime-adapter.py` acquire leases before mutation, live conflicts write `lease-conflict.json`, released leases write `last-lease.json`, expired leases recover, and deterministic tests cover conflict and stale recovery.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-101 | Autonomy Run Lease Guard | WO-097, WO-098, WO-100 | Complete |

---

## Phase 29: Autonomy Failure Loop Detector

**Goal:** Detect repeated no-progress autonomy loops and operational failures before an external scheduler keeps running the same broken path.

**Context:** Long-run autonomy should run for 24-48 hours only while it is making real progress. The core risk is not abstract token, cost, or elapsed-time accounting; it is repeated handoff with no runtime pickup, blocked runner commands, failed runtime launches, active lease conflicts, and provider/session limit failures. The detector turns loop and runtime histories into a blocking report when those issues repeat.

**Exit Criteria:** `autonomy-failure-detector.py` exists, writes `failure-report.json`, reads loop/runtime histories and latest control-plane reports, flags repeated handoff/no-progress/failure/provider-limit patterns, is included in smoke/bootstrap/upgrade paths, and is covered by deterministic tests.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-102 | Autonomy Failure Loop Detector | WO-097, WO-098, WO-100, WO-101 | Complete |

---

## Phase 30: Autonomy Recovery Planner

**Goal:** Convert autonomy failure findings into safe plan-only recovery actions before another scheduler tick repeats the same broken path.

**Context:** The failure detector can now identify repeated handoffs, blocked runners, failed runtime launches, lease conflicts, no-progress decisions, and provider/session limits. The harness still needs an explicit management layer that says what to do next without taking unsafe action automatically. Recovery planning must preserve autonomy, but it must not clear leases, install schedulers, or launch providers without reviewed intent.

**Exit Criteria:** `autonomy-recovery-planner.py` exists, writes `recovery-plan.json`, maps each detector finding class to a safe response, pauses scheduling when blocking recovery actions exist, is included in smoke/bootstrap/upgrade paths, and is covered by deterministic tests.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-103 | Autonomy Recovery Planner | WO-098, WO-100, WO-101, WO-102 | Complete |

---

## Phase 31: Autonomy Scheduler Guard

**Goal:** Refuse another scheduler-driven loop tick while unresolved recovery actions remain.

**Context:** Recovery planning tells the harness what must happen next, but a cron, launchd, shell, or CI scheduler can still keep invoking loop ticks if the guard is not enforced at the scheduler boundary. The guard must be the first generated scheduler command and `autonomy-loop.py` must also honor unresolved recovery state directly, so hand-written scheduler invocations do not bypass the stop signal by accident.

**Exit Criteria:** `autonomy-scheduler-guard.py` exists, writes `scheduler-guard-report.json`, blocks unresolved `recovery-plan.json` actions unless matching `recovery-resolution.json` evidence exists, blocks blocking failure reports that have no recovery plan, is included in generated scheduler profiles and smoke/bootstrap/upgrade paths, and is covered by deterministic tests.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-104 | Autonomy Scheduler Guard | WO-099, WO-100, WO-102, WO-103 | Complete |

---

## Phase 32: Autonomy Recovery Resolution Protocol

**Goal:** Record evidence-backed resolution for recovery-plan actions without mutating the recovery plan itself.

**Context:** The scheduler guard can pause long-run autonomy, but a serious 24-48 hour harness also needs a deterministic way to prove the pause condition has been resolved. Resolutions must be bound to the current recovery-plan generation so stale evidence cannot unblock a fresh failure, and the guard must rely on that evidence instead of implicit human judgment.

**Exit Criteria:** `autonomy-recovery-resolution.py` exists, writes `recovery-resolution.json`, appends `recovery-resolution-history.jsonl`, requires action id, summary, and evidence for recorded resolutions, makes scheduler guard and loop ticks pass only when current blocking actions have matching resolution evidence, is included in smoke/bootstrap/upgrade paths, and is covered by deterministic tests.

| WO | Title | Dependencies | Status |
|---|---|---|---|
| WO-105 | Autonomy Recovery Resolution Protocol | WO-100, WO-103, WO-104 | Complete |

---

## Contingency Plans

If Phase 0 spike or Phase 1 post-audit reveals failed assumptions:

| Assumption | If It Fails | Rework Scope | Can Later Phases Proceed? |
|---|---|---|---|
| Plugin manifest accepts agents/hooks fields | Adapt to actual schema; may need MCP or CLAUDE.md-based wiring | Low — config changes only | Yes, with revised wiring |
| Skills dir = slash commands | Rename skills/ to commands/ across all files | Medium — rename in 40+ files | Yes, after rename |
| Agent dispatch returns structured output | Use file-based communication (agent writes JSON, orchestrator reads) | High — redesign Phase 3 orchestrator | Yes, but Phase 3 delayed |
| Hook exit code 2 = block | Update exit codes in all hook scripts | Low — constant changes | Yes, immediately |

## Risk Register

| Risk | Severity | Mitigation | Phase |
|---|---|---|---|
| Plugin manifest schema differs from docs | **P0** | **WO-000 spike** — verify before any implementation | 0 |
| Skills vs Commands directory confusion | **P0** | **WO-000 spike** — test both conventions | 0 |
| Subagent dispatch doesn't return structured results | **P0** | **WO-000 spike** — dispatch test agent, verify return | 0 |
| Hook exit code semantics unverified | **P1** | **WO-000 spike** — test exit codes 0, 1, 2 | 0 |
| Hooks can't identify which agent is calling | High | Marker file fallback + prompt-level enforcement | 1, 3 |
| Gate scripts can't resolve plugin root path | High | `${CLAUDE_PLUGIN_ROOT}` env var + `--framework-dir` flag | 1 |
| Fresh-context isolation doesn't prevent context leakage | Medium | Measure after Phase 4, worktree provides filesystem isolation | 4 |
| Audit loops don't converge | High | State hashing + max iteration limits + semantic completion | 5 |
| Large codebase exceeds agent context window | Medium | Chunking strategy, defer to Phase 6 | 6 |
| Sonnet for 4/5 audit agents, Opus for correctness | Medium | Monitor quality; upgrade model if audit miss rate too high | 4 |
| Codex or Claude runtime capabilities drift after docs change | High | WO-072 runtime capability matrix gates orchestration choices before Comp mode runs | 14 |
| Parallel agents produce isolated success but integrated failure | High | WO-077 scope planning plus WO-078 integration captain owns merge order and cross-boundary verification | 14 |
| AI agents choose stale or incompatible dependencies from model memory | High | WO-086/087 dependency intelligence gate, auditor, scorecard, evidence template, and Comp gauntlet enforce current-source and compatibility proof | 17 |
| Stack-specific dependency compatibility breaks despite generic evidence | High | WO-088/089 stack currency packs require concrete evidence for runtime, framework, SDK, auth, database, AI, and deployment surfaces | 18 |
| MVP works locally but has no repeatable delivery path | High | WO-090/091 delivery infrastructure gate, auditor, scorecard, evidence template, and Comp gauntlet enforce CI/CD, deployability, observability, smoke, rollback, and runbook proof | 19 |
| Long autonomous runs lose state after context reset or runtime interruption | High | WO-093/094 long-run autonomy control plane records heartbeats, checkpoints, audit cadence, stale-run validation, and terminal closeout state | 21 |
| Long autonomous runs continue without a deterministic next-action decision | High | WO-095 supervisor writes resume plans from durable state and stops on cadence and loop/runtime limits | 22 |
| Resume plans become unsafe shell execution surfaces or require manual interpretation | High | WO-096 runner adapter dry-runs by default, executes only allowlisted local VibeOS scripts, blocks unsafe commands, and reports Codex/Claude handoff items | 23 |
| External schedulers cannot resume the autonomy loop consistently | High | WO-097 loop entrypoint runs one supervisor-plus-runner tick, writes durable loop state, and exits at clear scheduler/model handoff boundaries | 24 |
| Model handoff state cannot be launched consistently across Codex and Claude | High | WO-098 runtime adapter writes dry-run-first Codex/Claude handoff command plans from capability evidence and launches only with explicit `--execute` | 25 |
| Scheduler profiles are installed without review or with unsafe runtime launch settings | High | WO-099 profile generator writes reviewed artifacts only and leaves runtime launch disabled unless explicitly requested | 26 |
| Scheduler automation fails after installation because the autonomy chain was not preflighted | High | WO-100 disposable smoke command runs heartbeat, loop, runtime-adapter planning, validation, failure detection, recovery planning, recovery resolution, and scheduler guarding before profile trust | 27 |
| Long-run scheduler repeats handoff, blocked runner, runtime failure, lease conflict, or provider/session limit without progress | High | WO-102 failure detector writes blocking findings from loop/runtime history and latest control-plane reports | 29 |
| Autonomy detects failures but has no deterministic next response | High | WO-103 recovery planner maps findings to plan-only scheduler pause, runtime handoff, lease review, runner repair, capability refresh, or provider/session recovery actions | 30 |
| Scheduler continues ticking after recovery plan says to pause | High | WO-104 scheduler guard blocks generated profiles and loop ticks while recovery actions lack matching resolution evidence | 31 |
| Stale or informal recovery evidence unblocks a new failure | High | WO-105 recovery resolution protocol binds action evidence to the current recovery-plan generation and keeps an append-only resolution history | 32 |
| Multiple schedulers or runtimes drive the same long-run state concurrently | High | WO-101 run lease guard blocks live concurrent drivers, records conflicts, and recovers expired leases | 28 |
| VibOS Comp optimizes for speed at the expense of enterprise foundations | High | WO-075 foundation blueprint and WO-079 quality gauntlet make foundation requirements explicit acceptance criteria | 14 |
| Scorecard becomes marketing instead of proof | High | WO-081 requires evidence links and separates proven, partial, deferred, and overridden claims | 14 |
| Individual components pass while the human flow fails | High | WO-082 Flow Auditor and flow-integrity gate trace mission objective through UI, auth/session, backend/API, data, feedback, and evidence | 15 |
| Happy path passes while system invariants fail | High | WO-084 System Invariant Auditor and invariant gate trace state, ownership, idempotency, recovery, and auditability rules through implementation and tests | 16 |

## Source Material

All source files are from VibeOS-2 (dev-local: `/Users/latifhorst/cursor projects/VibeOS-2/`, not required at runtime):

| Component | Source Path | Action |
|---|---|---|
| 25 gate scripts | `scripts/*.sh`, `scripts/*.py` | Copy as-is |
| Gate runner | `scripts/gate-runner.sh` | Adapt for plugin context |
| Decision engine | `decision-engine/*.md` | Copy as-is |
| Reference files | `reference/**/*.ref` | Copy as-is |
| Hook references | `reference/hooks/*.sh.ref` | Convert to executable hooks |
| Skill references | `reference/skills/*.md.ref` | Convert to SKILL.md format |
| Communication contract | `docs/USER-COMMUNICATION-CONTRACT.md` | Embed in agent prompts |
| Audit framework | `reference/governance/WO-AUDIT-FRAMEWORK.md.ref` | Core of audit agents |
| WO template | `reference/governance/WO-TEMPLATE.md.ref` | Template for WO creation |
| Product discovery | `PRODUCT-DISCOVERY.md` | Source for /vibeos:discover |
| Project intake | `PROJECT-INTAKE.md` | Source for /vibeos:plan |
| Bootstrap playbook | `AGENT-BOOTSTRAP.md` | Decompose into skills |
