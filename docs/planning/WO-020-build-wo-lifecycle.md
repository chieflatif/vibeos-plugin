# WO-020: /vibeos:build Orchestrator — WO Lifecycle

## Status

`Draft`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Extend the `/vibeos:build` orchestrator to manage the full WO lifecycle: read the plan, dispatch the investigator, planner, plan-auditor, tester, implementer, and doc writer in sequence, then mark the WO complete.

## Scope

### In Scope
- [ ] Read DEVELOPMENT-PLAN.md to determine current WO
- [ ] Full WO execution sequence:
  1. Investigator agent — revalidate assumptions
  2. Planner agent — refine implementation steps if needed
  3. Plan auditor agent — audit the plan
  4. Tester agent — write tests from spec (TDD)
  5. Backend/frontend agent — implement to pass tests
  6. Doc writer agent — update documentation
- [ ] Pass outputs between agents (investigator findings to planner, etc.)
- [ ] Mark WO as complete in WO file and WO-INDEX.md
- [ ] Handle agent failure at any step: log, attempt recovery, escalate

### Out of Scope
- Gate integration (WO-021)
- Multi-WO loop (WO-032)
- Audit agent integration (WO-029)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-019 | Must complete first | Draft |
| WO-014 | Tester agent | Draft |
| WO-015 | Test file protection | Draft |
| WO-016 | Backend agent | Draft |
| WO-017 | Frontend agent | Draft |
| WO-018 | Doc writer agent | Draft |

## Impact Analysis

- **Files modified:** skills/build.md (extend orchestrator)
- **Systems affected:** Full build pipeline, WO tracking

## Acceptance Criteria

- [ ] AC-1: Orchestrator reads DEVELOPMENT-PLAN.md and identifies correct next WO
- [ ] AC-2: All 6 agents dispatched in correct sequence
- [ ] AC-3: Output from each agent passed as input to the next
- [ ] AC-4: If investigator flags critical risk: pause and escalate
- [ ] AC-5: If plan auditor finds critical issue: pause and escalate
- [ ] AC-6: WO marked complete only after all agents succeed
- [ ] AC-7: WO-INDEX.md updated with completion status
- [ ] AC-8: Failure at any step: logged, recovery attempted, escalated if unrecoverable

## Test Strategy

- **Integration:** Run full WO lifecycle on a simple sample WO
- **Sequence:** Verify agents dispatched in correct order
- **Failure:** Simulate failure at each step, verify graceful handling

## Implementation Plan

### Step 1: Implement Plan Reader
- Parse DEVELOPMENT-PLAN.md for WO ordering
- Identify next incomplete WO based on status
- Read WO file for spec and acceptance criteria

### Step 2: Implement Agent Sequencing
- Define the 6-step pipeline
- Pass structured output from each agent to the next
- Handle conditional steps (frontend agent only if WO has frontend scope)

### Step 3: Implement Completion Logic
- After all agents succeed: update WO status to `Complete`
- Update WO-INDEX.md
- Log completion to build-log.md

### Step 4: Implement Failure Handling
- Critical failures (investigator/auditor flags): immediate escalation
- Implementation failures: retry once, then escalate
- Documentation failures: warn but don't block WO completion

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — full lifecycle on sample WO
- Risk: 6-agent pipeline has many failure points; each handoff is a potential failure

## Evidence

- [ ] Full WO lifecycle executes end-to-end
- [ ] Agents dispatch in correct sequence
- [ ] Inter-agent data passing works
- [ ] WO marked complete with evidence
- [ ] Failure handling tested at each step
