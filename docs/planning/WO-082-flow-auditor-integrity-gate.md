# WO-082: Flow Auditor and Flow Integrity Gate

## Status

`Complete`

## Phase

Phase 15: Flow Integrity & Objective Fidelity

## Objective

Add a first-class Flow Auditor and deterministic flow integrity gate so VibOS Comp validates whether the primary user can actually complete the mission-critical journey through UI, auth/session, backend/API, data or side effects, feedback states, and evidence.

## Scope

### In Scope
- [x] Add isolated and same-tree Flow Auditor role contracts
- [x] Add flow integrity reference template and checklist
- [x] Add deterministic `validate-flow-integrity.py` gate
- [x] Wire flow validation into `comp_gauntlet`
- [x] Include flow auditor in high-tier audit dispatch manifests
- [x] Install Flow Auditor through Claude/Cursor and Codex bootstrap surfaces

### Out of Scope
- Replacing security, correctness, contract, test, evidence, or product-drift auditors
- Guaranteeing runtime browser automation for every project
- Claiming a flow passed without user-flow evidence

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-074 | Comp mission skill | Complete |
| WO-077 | Swarm Worktree Planner | Complete |
| WO-079 | Quality Gauntlet | Complete |

## Findings

1. AI-generated software often passes isolated code, UI, API, security, or database checks while failing the human journey.
2. VibeOS already had product drift and contract validation, but no role whose sole question was whether the user can complete the intended flow end to end.
3. Comp missions need deterministic minimum flow context before implementation so Work Orders and audits can trace the same user path.

## Research & Freshness

- Verified on: 2026-04-29.
- Local sources: existing audit agents, Comp mission skill, `comp-plan.py`, quality gate manifest, bootstrap scripts.
- External sources: none required.

## Impact Analysis

- **Files created:** `plugins/vibeos/agents/flow-auditor.md`, `plugins/vibeos/agents/flow-auditor-same-tree.md`, `plugins/vibeos/reference/comp/FLOW-INTEGRITY.md.ref`, `plugins/vibeos/reference/comp/flow-integrity-checklist.json`, `plugins/vibeos/scripts/validate-flow-integrity.py`, `tests/test_flow_integrity.py`
- **Files modified:** Comp mission templates, planner, integration captain, gate manifests, audit dispatcher, bootstraps, bootstrap tests
- **Systems affected:** mission intake, planning, audit dispatch, Comp gauntlet, Codex/Claude install surfaces

## Acceptance Criteria

- [x] AC-1: Flow Auditor role contract exists for isolated and same-tree reviews
- [x] AC-2: Flow integrity gate fails when `MISSION.md` is missing or lacks required flow sections
- [x] AC-3: Flow integrity gate warns without blocking for advisory handoff context gaps
- [x] AC-4: `comp_gauntlet` includes the flow integrity gate
- [x] AC-5: High-tier audit dispatch includes flow review
- [x] AC-6: Codex bootstrap installs Flow Auditor TOML and contract artifacts

## Test Strategy

- **Unit tests:** validate checklist schema and validator pass/fail/warn behavior
- **Bootstrap tests:** verify Codex agent TOML and contract generation includes Flow Auditor
- **Manifest tests:** covered by JSON validation and full test discovery

## Evidence

- [x] `tests/test_flow_integrity.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] Full repository validation run
