# WO-021: /vibeos:build Orchestrator — Gate Integration

## Status

`Complete`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Extend the `/vibeos:build` orchestrator to run gate-runner.sh pre_commit after implementation, with a fix-and-rerun loop (max 3 cycles) for gate failures.

## Scope

### In Scope
- [x] After implementation agents complete: run `gate-runner.sh pre_commit`
- [x] Parse gate results (pass/fail per gate)
- [x] On gate failure: dispatch implementation agent to fix specific failures
- [x] Re-run gates after fix
- [x] Max 3 fix cycles; after 3 failures, escalate to user
- [x] Log all gate runs and results to build-log.md
- [x] Report which gates passed/failed in structured format

### Out of Scope
- Audit agent integration (WO-029)
- Phase boundary audit (WO-033)
- Convergence controls (WO-030)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-020 | Must complete first | Draft |
| WO-002 | Gate scripts bundled | Draft |
| WO-004 | Gate skill | Draft |

## Impact Analysis

- **Files modified:** skills/build/SKILL.md (add gate integration step)
- **Systems affected:** Build pipeline, quality enforcement

## Acceptance Criteria

- [x] AC-1: gate-runner.sh pre_commit runs after implementation completes
- [x] AC-2: Gate results parsed into structured format (gate name, pass/fail, output)
- [x] AC-3: On failure: implementation agent receives specific failure details
- [x] AC-4: Fix cycle repeats until gates pass or max 3 cycles reached
- [x] AC-5: After 3 failed cycles: escalation to user with failure details
- [x] AC-6: All gate runs logged with timestamps and results
- [x] AC-7: Successful gate run advances WO to documentation step

## Test Strategy

- **Integration:** Run build with implementation that causes gate failure, verify fix cycle
- **Max cycles:** Simulate persistent failure, verify escalation after 3 cycles
- **Logging:** Verify gate results logged correctly

## Implementation Plan

### Step 1: Add Gate Step to Pipeline
- After implementation agents complete, before doc writer
- Run gate-runner.sh pre_commit via Bash
- Capture stdout/stderr for parsing

### Step 2: Implement Result Parsing
- Parse gate-runner output for individual gate results
- Identify which gates failed and with what error
- Structure failures for agent consumption

### Step 3: Implement Fix Loop
- On failure: re-dispatch implementation agent with failure details
- Agent reads failure, fixes code, confirms fix
- Re-run gates
- Track cycle count

### Step 4: Implement Escalation
- After 3 failed cycles: stop build
- Report to user: which gates fail, what was tried, agent's assessment of the issue
- User can: fix manually, adjust gates, or skip

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — gate failure, fix, and re-run cycle
- Risk: Fix agent may introduce new failures while fixing others; cycle may not converge

## Evidence

- [x] Gates run after implementation
- [x] Gate failures trigger fix cycle
- [x] Fix cycle converges (gates pass) or escalates (max cycles)
- [x] All gate runs logged
- [x] Escalation message is clear and actionable
