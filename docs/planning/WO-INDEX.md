# Work Order Index

## Active

| WO | Title | Phase | Status | Dependencies |
|---|---|---|---|---|
| — | — | — | — | — |

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
