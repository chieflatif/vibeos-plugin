# WO-029: Integrate Auditors into Build Loop

## Status

`Draft`

## Phase

Phase 4: Fresh-Context Audit Agents

## Objective

Update `/vibeos:build` to run the full audit cycle after implementation, creating a two-layer quality enforcement system: Layer 1 (gates) then Layer 2 (audit agents) with fix-and-reaudit cycles.

## Scope

### In Scope
- [ ] Add audit cycle step to build orchestrator after gate integration
- [ ] Sequence: implement -> Layer 1 gates -> Layer 2 audit agents -> fix -> re-audit
- [ ] On audit findings: dispatch implementation agent to fix
- [ ] Re-run audit after fixes (max 3 cycles)
- [ ] After 3 failed cycles: escalate to user with remaining findings
- [ ] Log all audit runs and findings to build-log.md
- [ ] Only critical and high findings trigger fix cycle; medium/low logged as warnings

### Out of Scope
- Individual audit agent implementation (WO-023-027)
- Audit skill implementation (WO-028)
- Convergence controls (WO-030)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-028 | Audit skill | Draft |
| WO-021 | Gate integration | Draft |

## Impact Analysis

- **Files modified:** skills/build.md (add audit step)
- **Systems affected:** Build pipeline, quality enforcement

## Acceptance Criteria

- [ ] AC-1: Audit cycle runs after gates pass
- [ ] AC-2: Critical/high findings trigger fix cycle
- [ ] AC-3: Medium/low findings logged as warnings (do not block)
- [ ] AC-4: Fix cycle: dispatch implementer with finding details, re-audit
- [ ] AC-5: Max 3 audit-fix cycles before escalation
- [ ] AC-6: Escalation includes remaining findings and what was attempted
- [ ] AC-7: All audit runs logged with timestamps and finding counts

## Test Strategy

- **Integration:** Run build with code that has audit findings, verify fix cycle
- **Escalation:** Simulate persistent findings, verify escalation after 3 cycles
- **Severity:** Verify medium/low findings don't trigger fix cycle

## Implementation Plan

### Step 1: Add Audit Step to Build Pipeline
- After gate-runner passes: dispatch /vibeos:audit
- Collect composite report

### Step 2: Implement Fix Cycle
- Filter findings: critical and high only
- For each finding: pass to implementation agent with context
- After fixes: re-run audit
- Track cycle count

### Step 3: Implement Escalation
- After 3 cycles: compile remaining findings
- Report to user: what was found, what was fixed, what remains
- User decides: accept remaining, fix manually, create follow-up WO

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — build with audit findings, verify fix cycle
- Risk: Audit-fix-reaudit loop may not converge; convergence controls (WO-030) address this

## Evidence

- [ ] Audit step added to build pipeline
- [ ] Fix cycle works for critical/high findings
- [ ] Medium/low findings logged but don't block
- [ ] Escalation after 3 cycles works
- [ ] All audit runs logged
