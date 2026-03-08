# WO-021: /vibeos:build Orchestrator — Gate Integration

## Status

`Draft`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Extend the `/vibeos:build` orchestrator to run gate-runner.sh pre_commit after implementation, with a fix-and-rerun loop (max 3 cycles) for gate failures.

## Scope

### In Scope
- [ ] After implementation agents complete: run `gate-runner.sh pre_commit`
- [ ] Parse gate results (pass/fail per gate)
- [ ] On gate failure: dispatch implementation agent to fix specific failures
- [ ] Re-run gates after fix
- [ ] Max 3 fix cycles; after 3 failures, escalate to user
- [ ] Log all gate runs and results to build-log.md
- [ ] Report which gates passed/failed in structured format

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

- **Files modified:** skills/build.md (add gate integration step)
- **Systems affected:** Build pipeline, quality enforcement

## Acceptance Criteria

- [ ] AC-1: gate-runner.sh pre_commit runs after implementation completes
- [ ] AC-2: Gate results parsed into structured format (gate name, pass/fail, output)
- [ ] AC-3: On failure: implementation agent receives specific failure details
- [ ] AC-4: Fix cycle repeats until gates pass or max 3 cycles reached
- [ ] AC-5: After 3 failed cycles: escalation to user with failure details
- [ ] AC-6: All gate runs logged with timestamps and results
- [ ] AC-7: Successful gate run advances WO to documentation step

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

- [ ] Gates run after implementation
- [ ] Gate failures trigger fix cycle
- [ ] Fix cycle converges (gates pass) or escalates (max cycles)
- [ ] All gate runs logged
- [ ] Escalation message is clear and actionable
