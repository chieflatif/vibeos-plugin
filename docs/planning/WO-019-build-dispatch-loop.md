# WO-019: /vibeos:build Orchestrator — Agent Dispatch Loop

## Status

`Complete`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Implement the core `/vibeos:build` orchestrator skill with basic agent dispatch: spawn an agent, collect its result, decide what to do next, and handle errors.

## Scope

### In Scope
- [x] Create `skills/build/SKILL.md` as the main orchestrator entry point
- [x] Basic agent dispatch: spawn agent with input, wait for result
- [x] Result collection: parse structured output from agent
- [x] Decision logic: based on result, determine next action
- [x] Error recovery: timeout detection, garbage output detection
- [x] Retry logic: on error, log, retry once, then escalate to user
- [x] Logging: all dispatch events written to `.vibeos/build-log.md`
- [x] Log format: timestamp, agent name, WO, action, result summary

### Out of Scope
- Full WO lifecycle (WO-020)
- Gate integration (WO-021)
- Multi-WO orchestration (WO-032)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-013 | Must complete first | Draft |

## Impact Analysis

- **Files created:** skills/build/SKILL.md, .vibeos/build-log.md template
- **Systems affected:** Agent dispatch infrastructure, build pipeline

## Acceptance Criteria

- [x] AC-1: Orchestrator spawns an agent with structured input
- [x] AC-2: Orchestrator receives and parses structured result from agent
- [x] AC-3: On timeout: logged, retried once, escalated if retry fails
- [x] AC-4: On garbage output: logged, retried once with clarified instructions, escalated if retry fails
- [x] AC-5: All events logged to .vibeos/build-log.md with timestamps
- [x] AC-6: Escalation pauses build and communicates issue to user in plain English
- [x] AC-7: Build log is append-only (no overwrites)

## Test Strategy

- **Integration:** Dispatch a simple agent, verify result collected and logged
- **Error handling:** Simulate timeout/failure, verify retry and escalation
- **Logging:** Verify build-log.md entries after dispatch

## Implementation Plan

### Step 1: Create Orchestrator Skill
- Define skill metadata and entry point
- Implement agent dispatch wrapper
- Define structured input/output contracts between orchestrator and agents

### Step 2: Implement Dispatch Loop
- Spawn agent with input (WO spec, context)
- Wait for result with timeout
- Parse result into structured format
- Log dispatch event

### Step 3: Implement Error Recovery
- Detect timeout (agent exceeds maxTurns or wall time)
- Detect garbage (result doesn't match expected structure)
- Retry once with additional context
- Escalate to user with clear description of what failed

### Step 4: Implement Logging
- Create .vibeos/build-log.md if not exists
- Append each event: `[timestamp] [agent] [WO] [action] [result]`
- Include error details in log

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — dispatch agent, verify result and log
- Risk: Agent dispatch reliability is the foundation of the entire build loop; must be robust

## Evidence

- [x] Orchestrator skill file created
- [x] Agent dispatch works end-to-end
- [x] Error recovery tested (timeout, garbage)
- [x] Build log populated correctly
- [x] Escalation produces clear user-facing message
