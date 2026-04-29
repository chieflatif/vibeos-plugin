# WO-077: Swarm Worktree Planner

## Status

`Complete`

## Phase

Phase 14: VibOS Comp — Enterprise MVP Battle Harness

## Objective

Create a planner that splits a VibOS Comp mission into parallel work packages with explicit branch ownership, worktree paths, exclusive territories, shared files, dependencies, and merge order.

## Scope

### In Scope
- [x] Generate `COMP-PLAN.md`
- [x] Generate or update `.vibeos/worktree-scopes.json`
- [x] Assign roles for frontend, backend, data, infra, tests, observability, security, and docs where applicable
- [x] Mark main-only WOs and blocking dependencies
- [x] Define merge order and shared-path conflict expectations
- [x] Refuse unsafe parallelization when ownership is unclear

### Out of Scope
- Automatically resolving merge conflicts
- Running the workers
- Creating branches or worktrees directly

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-074 | VibOS Comp mission skill | Complete |
| WO-075 | Enterprise MVP foundation blueprint | Complete |

## Findings

1. Parallel agents increase speed only when file ownership and integration order are explicit.
2. Existing VibeOS worktree scope guards already support branch ownership, but setup is manual and not mission-aware.
3. Enterprise MVP builds need specialized capabilities beyond generic frontend/backend delivery.

## Research & Freshness

- Verified on: 2026-04-29.
- Local sources: parallel worktree guide, worktree scope schema, worktree guard hooks, build skill.
- External sources: Claude agent teams and Codex subagents/worktrees docs for current orchestration options.

## Impact Analysis

- **Files created:** `plugins/vibeos/scripts/comp-plan.py`, `plugins/vibeos/reference/comp/COMP-PLAN.md.ref`, `tests/test_comp_plan.py`
- **Files modified:** Comp skill, Codex Comp skill, quality gate manifest utility references, upgrade metadata
- **Systems affected:** parallel execution setup, worktree enforcement, integration handoff

## Acceptance Criteria

- [x] AC-1: Planner creates a valid `COMP-PLAN.md` from `MISSION.md`
- [x] AC-2: Planner creates valid `.vibeos/worktree-scopes.json`
- [x] AC-3: Planner identifies exclusive paths, shared paths, and unsafe overlaps
- [x] AC-4: Planner assigns role-specific work packages and verification obligations
- [x] AC-5: Planner records merge order and main-only blockers
- [x] AC-6: Planner refuses or downgrades to sequential mode when safe parallelization is not possible

## Test Strategy

- **Fixture tests:** sample missions with safe, unsafe, and mixed parallelization
- **Schema tests:** validate generated worktree scopes against schema
- **Real-path verification:** generate Comp plan for a fixture MVP mission
- **Verification command:** run planner against fixture `MISSION.md` and validate JSON output

## Implementation Plan

### Step 1: Define Plan Schema
- Specify mission-to-work-package mapping
- Expected outcome: predictable parallel plan output

### Step 2: Generate Scopes
- Emit worktree scope JSON and branch contracts
- Expected outcome: guard hooks can enforce territory

### Step 3: Validate Safety
- Detect overlaps and dependency conflicts before work starts
- Expected outcome: parallelism is fast without being reckless

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Parallel work is only safe when branch ownership and shared-path conflict expectations are explicit.
- Test status: Planner schema and mode behavior defined.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Existing ambiguous code layouts must downgrade to sequential mode instead of pretending parallelism is safe.
- Test status: Ambiguous source fixture added.

### Pre-Commit Audit
- Status: `complete`
- Findings: Greenfield missions generate parallel branch scopes; ambiguous existing source generates no branch scopes and records the downgrade.
- Test status: `tests/test_comp_plan.py` passes.

## Evidence

- [x] Planner complete
- [x] Fixture plans verified
- [x] Worktree scope JSON validated
