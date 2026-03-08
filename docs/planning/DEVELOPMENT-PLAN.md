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
