# Work Order Index

## Active

| WO | Title | Phase | Status | Dependencies |
|---|---|---|---|---|
| WO-106 | vNext Generated Inventory and Claim Ledger | 33 | Implemented Locally | WO-072, WO-121/WO-122 read-only evidence |

## Backlog

### Phase 0: Architecture Validation

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-000 | Technical Spike — Plugin Architecture Validation | Complete | None |

### Phase 1: Plugin Foundation

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-001 | Repo Setup & Plugin Manifest | Complete | None |
| WO-002 | Bundle Gate Scripts | Complete | WO-001 |
| WO-003 | Bundle Decision Engine & Reference Files | Complete | WO-001 |
| WO-004 | `/vibeos:gate` Skill | Complete | WO-002 |
| WO-005 | `/vibeos:status` Skill | Complete | WO-001 |
| WO-006 | Basic hooks.json (Layer 0) | Complete | WO-001 |
| WO-007 | Planner Agent (Proof of Concept) | Complete | WO-001 |
| WO-007a | Test Fixture Project | Complete | WO-006 |

### Phase 2: Product Discovery & Planning

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-008 | `/vibeos:discover` Skill | Complete | Phase 1 |
| WO-009 | `/vibeos:plan` Skill | Complete | WO-008 |
| WO-010 | Plan Auditor Agent | Complete | WO-007 |
| WO-011 | Autonomy Negotiation | Complete | WO-009 |
| WO-012 | Project Intake Integration | Complete | WO-009 |

### Phase 3: Autonomous Build Loop

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-013 | Investigator Agent (Phase 0) | Complete | Phase 2 |
| WO-014 | Tester Agent | Complete | WO-013 |
| WO-015 | Test File Protection Hook | Complete | WO-014 |
| WO-016 | Backend Agent | Complete | WO-015 |
| WO-017 | Frontend Agent | Complete | WO-015 |
| WO-018 | Doc Writer Agent | Complete | WO-016 |
| WO-019 | `/vibeos:build` Orchestrator — Agent Dispatch Loop | Complete | WO-013 |
| WO-020 | `/vibeos:build` Orchestrator — WO Lifecycle | Complete | WO-019, WO-014-018 |
| WO-021 | `/vibeos:build` Orchestrator — Gate Integration | Complete | WO-020 |
| WO-022 | `/vibeos:wo` Skill (WO Management) | Complete | WO-020 |

### Phase 4: Fresh-Context Audit Agents

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-023 | Security Auditor Agent | Complete | Phase 3 |
| WO-024 | Architecture Auditor Agent | Complete | Phase 3 |
| WO-025 | Correctness Auditor Agent | Complete | Phase 3 |
| WO-026 | Test Auditor Agent | Complete | Phase 3 |
| WO-027 | Evidence Auditor Agent | Complete | Phase 3 |
| WO-028 | `/vibeos:audit` Skill (Full Audit Cycle) | Complete | WO-023-027 |
| WO-029 | Integrate Auditors into Build Loop | Complete | WO-028, WO-021 |

### Phase 5: Convergence & Full Autonomous Loop

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-030 | Convergence Controls | Complete | WO-029 |
| WO-031 | Token Budget Tracking | Complete | WO-030 |
| WO-032 | Multi-WO Orchestration | Complete | WO-030 |
| WO-033 | Phase Boundary Audit (Layer 5) | Complete | WO-032 |
| WO-034 | Human Check-in Protocol (Layer 6) | Complete | WO-032 |

### Phase 6: Midstream Embedding & Production Readiness

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-035 | Midstream Embedding | Complete | Phase 5 |
| WO-036 | Known Baselines Integration | Complete | WO-035 |
| WO-037 | Enhanced Test Quality Enforcement | Complete | WO-026 |
| WO-038 | Test Diff Auditing | Complete | WO-037 |
| WO-039 | Plugin Upgrade Mechanism | Complete | WO-035 |
| WO-040 | End-to-End Integration Testing | Complete | WO-035-039 |

### Phase 7: Informed Onboarding & User Comprehension

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-045 | User Communication Contract | Complete | Phase 6 |
| WO-041 | Architecture-First Midstream Discovery | Complete | Phase 6 |
| WO-042 | Guided Codebase Audit with User Decisions | Complete | WO-041, WO-045 (soft) |
| WO-046 | System Onboarding & Concept Introduction | Complete | WO-045, WO-041 (soft) |
| WO-043 | Finding-Level Baseline Model | Complete | WO-042 |
| WO-044 | Remediation Roadmap & Phase 0 Enforcement | Complete | WO-043 |
| WO-047 | Build Loop Visibility & Progress Reporting | Complete | WO-045, WO-044 (soft) |
| WO-048 | Consequence-Aware Decision Support | Complete | WO-045, WO-044 (soft) |

### Phase 8: Resilience & Transparency

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-049 | Mid-WO Resume & Error Recovery | Complete | Phase 7 |
| WO-050 | Decision Engine Transparency & Gate Management | Complete | Phase 7 |
| WO-051 | Midstream Baseline Bootstrap | Complete | Phase 7 |
| WO-052 | First-Run Experience & Handoffs | Complete | Phase 7 |
| WO-053 | Validation & Safety Hardening | Complete | Phase 7 |

## Completed

| WO | Title | Phase | Completed |
|---|---|---|---|
| WO-000 | Technical Spike — Plugin Architecture Validation | 0 | 2026-03-07 |
| WO-001 | Repo Setup & Plugin Manifest | 1 | 2026-03-07 |
| WO-002 | Bundle Gate Scripts | 1 | 2026-03-07 |
| WO-003 | Bundle Decision Engine & Reference Files | 1 | 2026-03-07 |
| WO-004 | `/vibeos:gate` Skill | 1 | 2026-03-07 |
| WO-005 | `/vibeos:status` Skill | 1 | 2026-03-07 |
| WO-006 | Basic hooks.json (Layer 0) | 1 | 2026-03-07 |
| WO-007 | Planner Agent (Proof of Concept) | 1 | 2026-03-07 |
| WO-007a | Test Fixture Project | 1 | 2026-03-07 |
| WO-008 | `/vibeos:discover` Skill | 2 | 2026-03-07 |
| WO-009 | `/vibeos:plan` Skill | 2 | 2026-03-07 |
| WO-010 | Plan Auditor Agent | 2 | 2026-03-07 |
| WO-011 | Autonomy Negotiation | 2 | 2026-03-07 |
| WO-012 | Project Intake Integration | 2 | 2026-03-07 |
| WO-013 | Investigator Agent (Phase 0) | 3 | 2026-03-07 |
| WO-014 | Tester Agent | 3 | 2026-03-07 |
| WO-015 | Test File Protection Hook | 3 | 2026-03-07 |
| WO-016 | Backend Agent | 3 | 2026-03-07 |
| WO-017 | Frontend Agent | 3 | 2026-03-07 |
| WO-018 | Doc Writer Agent | 3 | 2026-03-07 |
| WO-019 | `/vibeos:build` Orchestrator — Agent Dispatch Loop | 3 | 2026-03-07 |
| WO-020 | `/vibeos:build` Orchestrator — WO Lifecycle | 3 | 2026-03-07 |
| WO-021 | `/vibeos:build` Orchestrator — Gate Integration | 3 | 2026-03-07 |
| WO-022 | `/vibeos:wo` Skill (WO Management) | 3 | 2026-03-07 |
| WO-023 | Security Auditor Agent | 4 | 2026-03-07 |
| WO-024 | Architecture Auditor Agent | 4 | 2026-03-07 |
| WO-025 | Correctness Auditor Agent | 4 | 2026-03-07 |
| WO-026 | Test Auditor Agent | 4 | 2026-03-07 |
| WO-027 | Evidence Auditor Agent | 4 | 2026-03-07 |
| WO-028 | `/vibeos:audit` Skill (Full Audit Cycle) | 4 | 2026-03-07 |
| WO-029 | Integrate Auditors into Build Loop | 4 | 2026-03-07 |
| WO-030 | Convergence Controls | 5 | 2026-03-08 |
| WO-031 | Token Budget Tracking | 5 | 2026-03-08 |
| WO-032 | Multi-WO Orchestration | 5 | 2026-03-08 |
| WO-033 | Phase Boundary Audit (Layer 5) | 5 | 2026-03-08 |
| WO-034 | Human Check-in Protocol (Layer 6) | 5 | 2026-03-08 |
| WO-035 | Midstream Embedding | 6 | 2026-03-08 |
| WO-036 | Known Baselines Integration | 6 | 2026-03-08 |
| WO-037 | Enhanced Test Quality Enforcement | 6 | 2026-03-08 |
| WO-038 | Test Diff Auditing | 6 | 2026-03-08 |
| WO-039 | Plugin Upgrade Mechanism | 6 | 2026-03-08 |
| WO-040 | End-to-End Integration Testing | 6 | 2026-03-08 |
| WO-045 | User Communication Contract | 7 | 2026-03-08 |
| WO-041 | Architecture-First Midstream Discovery | 7 | 2026-03-08 |
| WO-042 | Guided Codebase Audit with User Decisions | 7 | 2026-03-08 |
| WO-046 | System Onboarding & Concept Introduction | 7 | 2026-03-08 |
| WO-043 | Finding-Level Baseline Model | 7 | 2026-03-08 |
| WO-044 | Remediation Roadmap & Phase 0 Enforcement | 7 | 2026-03-08 |
| WO-047 | Build Loop Visibility & Progress Reporting | 7 | 2026-03-08 |
| WO-048 | Consequence-Aware Decision Support | 7 | 2026-03-08 |
| WO-049 | Mid-WO Resume & Error Recovery | 8 | 2026-03-08 |
| WO-050 | Decision Engine Transparency & Gate Management | 8 | 2026-03-08 |
| WO-051 | Midstream Baseline Bootstrap | 8 | 2026-03-08 |
| WO-052 | First-Run Experience & Handoffs | 8 | 2026-03-08 |
| WO-053 | Validation & Safety Hardening | 8 | 2026-03-08 |

### Phase 9: Conversational Experience

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-054 | Voice-Led Intent Routing | Complete | Phase 8 |

### Phase 10: Distribution & Runtime

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-055 | Architectural Pivot — Plugin to Project-Level Bootstrap | Complete | WO-054 |

### Phase 11: Advanced Governance (v2.1) — Joan Extraction

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-056 | Session State & Gate Manifest Infrastructure | Complete | Phase 10 |
| WO-057 | Same-Tree Audit Agents | Complete | WO-056 |
| WO-058 | Audit Visibility & Registration System | Complete | WO-056 |
| WO-059 | Scope Discipline & File Budget Guards | Complete | WO-056 |
| WO-060 | Proof Protection & Governance Guard Hooks | Complete | WO-056 |
| WO-061 | Enhanced Parallel Worktree Isolation | Complete | WO-056 |
| WO-062 | Codex Audit Integration | Complete | WO-058 |
| WO-063 | Enhanced Investigator & CLI-vs-MCP Reference | Complete | WO-056 |
| WO-064 | Build/Audit Skill Enhancements | Complete | WO-057, WO-058, WO-062 |
| WO-065 | v2.1 Release Packaging | Complete | WO-056-064 |
| WO-066 | Stop Hook False-Positive Loop Remediation | Complete | WO-060, WO-065 |

### Phase 12: Harness Convergence

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-067 | Signal Claw Harness Convergence | Complete | WO-065 |
| WO-068 | Codex Cross-Surface Hardening | Complete | WO-067 |

### Phase 13: Evidence Memory Research

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-069 | Structured Evidence Memory Spike | Complete | WO-031, WO-049, WO-056, WO-068 |
| WO-070 | Evidence Recall Indexer and Query Command | Complete | WO-069 |
| WO-071 | v2.2 Release Hygiene | Complete | WO-070 |

### Phase 14: VibOS Comp — Enterprise MVP Battle Harness

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-072 | Runtime Capability Matrix | Complete | WO-068, WO-071 |
| WO-073 | Modern Codex Surface | Complete | WO-072 |
| WO-074 | VibOS Comp Mission Skill | Complete | WO-072, WO-073 |
| WO-075 | Enterprise MVP Foundation Blueprint | Complete | WO-074 |
| WO-076 | AI Failure Mode Gate Pack | Complete | WO-075 |
| WO-077 | Swarm Worktree Planner | Complete | WO-074, WO-075 |
| WO-078 | Integration Captain | Complete | WO-076, WO-077 |
| WO-079 | Quality Gauntlet | Complete | WO-076, WO-078 |
| WO-080 | Red Team Arena | Complete | WO-074, WO-079 |
| WO-081 | Scorecard and Evidence Dossier | Complete | WO-079, WO-080 |

### Phase 15: Flow Integrity & Objective Fidelity

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-082 | Flow Auditor and Flow Integrity Gate | Complete | WO-074, WO-077, WO-079 |
| WO-083 | Objective Fidelity Scorecard Integration | Complete | WO-081, WO-082 |

### Phase 16: System Invariants & State Safety

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-084 | System Invariant Auditor and Gate | Complete | WO-082, WO-083 |
| WO-085 | Invariant Scorecard and Evidence Integration | Complete | WO-084 |

### Phase 17: Dependency Intelligence & Current Evidence

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-086 | Dependency Intelligence Auditor and Gate | Complete | WO-084, WO-085 |
| WO-087 | Dependency Scorecard and Evidence Integration | Complete | WO-086 |

### Phase 18: Stack Dependency Currency Packs

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-088 | Stack Dependency Currency Pack Reference | Complete | WO-086, WO-087 |
| WO-089 | Stack Currency Validator Integration | Complete | WO-088 |

### Phase 19: Delivery Infrastructure & Operational Spine

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-090 | Delivery Infrastructure Auditor and Gate | Complete | WO-088, WO-089 |
| WO-091 | Delivery Scorecard and Evidence Integration | Complete | WO-090 |

### Phase 20: Comp Validation Hardening

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-092 | Comp Validation Generated Artifact Hardening | Complete | WO-076, WO-080, WO-091 |

### Phase 21: Long-Run Autonomy

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-093 | Long-Run Autonomy Control Plane | Complete | WO-056, WO-077, WO-091 |
| WO-094 | Long-Run Heartbeat Validator | Complete | WO-093 |

### Phase 22: Long-Run Supervisor

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-095 | Long-Run Supervisor Resume Plan | Complete | WO-093, WO-094 |

### Phase 23: Long-Run Runner Adapter

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-096 | Long-Run Runner Adapter | Complete | WO-093, WO-094, WO-095 |

### Phase 24: Long-Run Loop Entrypoint

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-097 | Long-Run Loop Entrypoint | Complete | WO-093, WO-095, WO-096 |

### Phase 25: Runtime Handoff Adapter

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-098 | Runtime Handoff Adapter | Complete | WO-072, WO-096, WO-097 |

### Phase 26: Autonomy Scheduler Profiles

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-099 | Autonomy Scheduler Profiles | Complete | WO-097, WO-098 |

### Phase 27: Disposable Autonomy Smoke

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-100 | Disposable Autonomy Smoke | Complete | WO-094, WO-097, WO-098, WO-099 |

### Phase 28: Autonomy Run Lease Guard

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-101 | Autonomy Run Lease Guard | Complete | WO-097, WO-098, WO-100 |

### Phase 29: Autonomy Failure Loop Detector

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-102 | Autonomy Failure Loop Detector | Complete | WO-097, WO-098, WO-100, WO-101 |

### Phase 30: Autonomy Recovery Planner

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-103 | Autonomy Recovery Planner | Complete | WO-098, WO-100, WO-101, WO-102 |

### Phase 31: Autonomy Scheduler Guard

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-104 | Autonomy Scheduler Guard | Complete | WO-099, WO-100, WO-102, WO-103 |

### Phase 32: Autonomy Recovery Resolution Protocol

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-105 | Autonomy Recovery Resolution Protocol | Complete | WO-100, WO-103, WO-104 |

### Phase 33: VibeOS vNext Public Proof Foundation

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-106 | vNext Generated Inventory and Claim Ledger | Implemented Locally | WO-072, WO-121/WO-122 read-only evidence |

### Phases 34–46: VibeOS vNext Upgrade (approved 2026-06-10)

Authoritative scope: `docs/planning/VNEXT-UPGRADE-AUDIT-AND-MASTER-PLAN-2026-06-10.md` (Section 7). This index becomes a generated view at WO-113. WO numbers are allocation order; WO-139 executes in Phase 39.

| WO | Title | Phase | Status | Dependencies |
|---|---|---|---|---|
| WO-107 | Gate-Runner Tier-Schema Fix | 34 | Planned | WO-106 commit |
| WO-108 | Fixture Secret Quarantine + Pytest Scoping | 34 | Planned | — |
| WO-109 | Runtime Capability Detection Repair + Extension | 34 | Planned | — |
| WO-110 | Hook-Manifest Sync + WO Status Reconciliation | 34 | Planned | — |
| WO-111 | WO Frontmatter Schema + Template | 35 | Planned | Phase 34 |
| WO-112 | Frontmatter Generators | 35 | Planned | WO-111 |
| WO-113 | Migration + Drift Lint + Generated WO-INDEX | 35 | Planned | WO-112 |
| WO-114 | Lane Return-Packet Schema | 36 | Planned | Phase 35 |
| WO-115 | Lane-Readiness Gate (check-lane-readiness.sh) | 36 | Planned | WO-107, WO-114 |
| WO-116 | PostToolUse + SubagentStop + SessionEnd/PreCompact Hooks | 37 | Planned | Phase 34 |
| WO-117 | Worktree + Team-Governance Hooks (dormant) | 37 | Planned | WO-116 |
| WO-118 | Model Policy Table + Lint | 38 | Planned | Phase 35 |
| WO-119 | ConfigChange Downgrade Guard + Cost Capture | 38 | Planned | WO-118 |
| WO-120 | Lane-Loop Ceilings + Goal-Verified Stop | 39 | Planned | Phases 35, 37, 38 |
| WO-121 | Night-Loop Headless Wrapper | 39 | Planned | WO-120, Decision D-3 |
| WO-122 | Recovery-Loop Execution Shell | 39 | Planned | WO-121 |
| WO-139 | Session-Limit-Aware Self-Rescheduling | 39 | Planned | WO-116, WO-121 |
| WO-123 | Workflow Governance Policy + Capability Detection | 40 | Planned | WO-109 |
| WO-124 | Bounded First Use: Audit Fan-Out Workflow | 40 | Planned | WO-123 |
| WO-125 | Agent-Team Pilot Plan + Evidence Model | 41 | Planned | Phases 36, 37 |
| WO-126 | Agent-Team Pilot Execution | 41 | Planned | WO-125 |
| WO-127 | Auditor-Artifact + Waiver-Expiry + Executed-vs-Declared Gates | 42 | Planned | Phase 35 |
| WO-128 | Product-Direction Lint + Hygiene Policy + Doc Budget | 42 | Planned | WO-127 |
| WO-129 | Framework-Ownership Manifest | 43 | Planned | Phases 34–38, 42 |
| WO-130 | Deterministic Upgrade Delta Engine | 43 | Planned | WO-129 |
| WO-131 | Upgrade Cognition Review Layer | 43 | Planned | WO-130 |
| WO-132 | Upgrade Apply + Preserve + Rollback Engine | 43 | Planned | WO-131 |
| WO-133 | Upgrade Fixture Smoke Test | 43 | Planned | WO-132 |
| WO-134 | Product Docs (VISION, PRODUCT-ANCHOR, PRD) | 44 | Planned | Phase 43, Decision D-7 |
| WO-135 | Architecture/Runtime/Limitations/Proof/Upgrade Docs + CLAUDE.md Slim | 44 | Planned | WO-134 |
| WO-136 | Independent vNext Audit | 45 | Planned | Phases 34–44 |
| WO-137 | Proof Package Assembly | 45 | Planned | WO-136 |
| WO-138 | Public-Readiness Gate + Website Handoff | 45 | Planned | WO-137, Decision D-8 |
| WO-140 | Reusable-Object Registry + Spec | 46 | Planned | Phase 45 / Decision D-9 |
| WO-141 | Own-Repo Reuse Scanner | 46 | Planned | WO-140 |
| WO-142 | Secure Ingestion Sandbox | 46 | Planned | WO-140, Decision D-10 |
| WO-143 | Marketplace Indexer + Project-Setup Integration | 46 | Planned | WO-142 |
| WO-144 | Enterprise Internal-Marketplace Mode | 46 | Planned | WO-143 |
