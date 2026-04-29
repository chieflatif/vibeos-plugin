# WO-078: Integration Captain

## Status

`Complete`

## Phase

Phase 14: VibOS Comp — Enterprise MVP Battle Harness

## Objective

Add an Integration Captain workflow that merges parallel agent work back into a coherent product, resolves shared-path risks, runs final verification, and prevents isolated wins from becoming integrated failure.

## Scope

### In Scope
- [x] Define integration captain role contract for Claude and Codex
- [x] Read `COMP-PLAN.md`, branch/worktree state, and scorecard obligations
- [x] Verify work package completion evidence before merge
- [x] Rebase or merge in planned order
- [x] Run cross-boundary tests, contracts, and quality gauntlet after integration
- [x] Record integration evidence and unresolved risks

### Out of Scope
- Replacing human code review for production deployments
- Automatically approving security overrides
- Directly merging to protected remote branches

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-077 | Swarm worktree planner | Complete |
| WO-076 | AI failure mode gate pack | Complete |

## Findings

1. Parallel work increases integration risk around shared routers, configs, schemas, fixtures, dependency files, and UI/API contracts.
2. Existing VibeOS build flow handles one WO at a time; Comp mode needs a final integration owner.
3. Judges and enterprise reviewers care about the integrated system, not isolated branch success.

## Research & Freshness

- Verified on: 2026-04-29.
- Local sources: parallel worktree guides, build skill, audit skill, contract validator agents.
- External sources: Codex worktrees and Claude agent teams docs for current parallel-work constraints.

## Impact Analysis

- **Files created:** `plugins/vibeos/agents/integration-captain.md`, `plugins/vibeos/scripts/comp-integration-check.py`, `plugins/vibeos/reference/comp/INTEGRATION-EVIDENCE.md.ref`, `tests/test_comp_integration.py`
- **Files modified:** quality gate manifest utility references, bootstrap docs/counts, Codex bootstrap expectations
- **Systems affected:** branch integration, final verification, completion evidence

## Acceptance Criteria

- [x] AC-1: Integration Captain reads and enforces `COMP-PLAN.md` merge order
- [x] AC-2: Integration refuses branch closure when required evidence is missing
- [x] AC-3: Integration runs cross-boundary contract checks after merging
- [x] AC-4: Integration runs quality gauntlet and red-team checks on the integrated result
- [x] AC-5: Integration writes scorecard evidence and unresolved risk entries
- [x] AC-6: Integration never claims remote merge or production deployment without actual evidence

## Test Strategy

- **Fixture tests:** simulate multiple work packages with shared-path conflicts
- **Integration tests:** verify missing evidence blocks integration
- **Real-path verification:** merge fixture branches or simulated branch artifacts in planned order
- **Verification command:** run Integration Captain workflow against a fixture Comp plan

## Implementation Plan

### Step 1: Define Role
- Add role contract and skill routing for integration captain
- Expected outcome: one clear owner for integration quality

### Step 2: Enforce Evidence
- Validate work package evidence before merge
- Expected outcome: incomplete branch output cannot disappear into main

### Step 3: Final Verify
- Run cross-boundary checks and update scorecard
- Expected outcome: integrated result is what gets judged

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Parallel branch success needs a separate integrated evidence owner before completion claims are valid.
- Test status: Integration readiness rules defined.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The integration checker must block missing package evidence and write an evidence artifact either way.
- Test status: Missing-evidence fixture added.

### Pre-Commit Audit
- Status: `complete`
- Findings: Integration Captain role is installed as a Claude/Cursor agent and generated as a Codex-native TOML agent by the Codex bootstrap.
- Test status: `tests/test_comp_integration.py` and Codex bootstrap tests pass.

## Evidence

- [x] Workflow complete
- [x] Fixture integration verified
- [x] Integration evidence recorded
