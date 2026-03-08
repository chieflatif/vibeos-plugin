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
| WO-008 | `/vibeos:discover` Skill | Draft | Phase 1 |
| WO-009 | `/vibeos:plan` Skill | Draft | WO-008 |
| WO-010 | Plan Auditor Agent | Draft | WO-007 |
| WO-011 | Autonomy Negotiation | Draft | WO-009 |
| WO-012 | Project Intake Integration | Draft | WO-009 |

### Phase 3: Autonomous Build Loop

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-013 | Investigator Agent (Phase 0) | Draft | Phase 2 |
| WO-014 | Tester Agent | Draft | WO-013 |
| WO-015 | Test File Protection Hook | Draft | WO-014 |
| WO-016 | Backend Agent | Draft | WO-015 |
| WO-017 | Frontend Agent | Draft | WO-015 |
| WO-018 | Doc Writer Agent | Draft | WO-016 |
| WO-019 | `/vibeos:build` Orchestrator — Agent Dispatch Loop | Draft | WO-013 |
| WO-020 | `/vibeos:build` Orchestrator — WO Lifecycle | Draft | WO-019, WO-014-018 |
| WO-021 | `/vibeos:build` Orchestrator — Gate Integration | Draft | WO-020 |
| WO-022 | `/vibeos:wo` Skill (WO Management) | Draft | WO-020 |

### Phase 4: Fresh-Context Audit Agents

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-023 | Security Auditor Agent | Draft | Phase 3 |
| WO-024 | Architecture Auditor Agent | Draft | Phase 3 |
| WO-025 | Correctness Auditor Agent | Draft | Phase 3 |
| WO-026 | Test Auditor Agent | Draft | Phase 3 |
| WO-027 | Evidence Auditor Agent | Draft | Phase 3 |
| WO-028 | `/vibeos:audit` Skill (Full Audit Cycle) | Draft | WO-023-027 |
| WO-029 | Integrate Auditors into Build Loop | Draft | WO-028, WO-021 |

### Phase 5: Convergence & Full Autonomous Loop

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-030 | Convergence Controls | Draft | WO-029 |
| WO-031 | Token Budget Tracking | Draft | WO-030 |
| WO-032 | Multi-WO Orchestration | Draft | WO-030 |
| WO-033 | Phase Boundary Audit (Layer 5) | Draft | WO-032 |
| WO-034 | Human Check-in Protocol (Layer 6) | Draft | WO-032 |

### Phase 6: Midstream Embedding & Production Readiness

| WO | Title | Status | Dependencies |
|---|---|---|---|
| WO-035 | Midstream Embedding | Draft | Phase 5 |
| WO-036 | Known Baselines Integration | Draft | WO-035 |
| WO-037 | Enhanced Test Quality Enforcement | Draft | WO-026 |
| WO-038 | Test Diff Auditing | Draft | WO-037 |
| WO-039 | Plugin Upgrade Mechanism | Draft | WO-035 |
| WO-040 | End-to-End Integration Testing | Draft | WO-035-039 |

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
