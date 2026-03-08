# WO-049: Mid-WO Resume & Error Recovery

## Status

`Complete`

## Phase

Phase 8: Resilience & Transparency

## Objective

Enable the build loop to resume a work order from where it left off if interrupted (context window reset, user pause, crash), and ensure every error recovery action is announced to the user before it happens — no silent retries.

## Scope

### In Scope
- [x] Checkpoint mechanism: save build state after each agent completes within a WO
- [x] Checkpoint file: `.vibeos/checkpoints/WO-NNN.json` with completed steps, agent outputs, state hash
- [x] Resume detection: on `/vibeos:build WO-NNN`, check for existing checkpoint before starting fresh
- [x] Resume flow: skip completed agents, resume from next pending step
- [x] Clear user messaging on resume: "Resuming WO-NNN from step 5/8 (tester, backend already complete)"
- [x] Error recovery pre-action notifications: tell user what's about to happen before every retry
- [x] Gate retry notification: "Quality check [gate-name] failed. I'm going to fix [specific issue] and re-run the check (attempt 2 of 3)..."
- [x] Audit retry notification: "Audit found [N] issues. I'm going to fix them and re-run the auditors (iteration 2 of 5)..."
- [x] Agent timeout notification: "The [agent-name] agent timed out. I'm going to retry with a simplified prompt..."
- [x] Checkpoint cleanup: remove checkpoint file after WO completes successfully
- [x] Remove token tracking references from build skill (token-tracker.sh calls, overhead checks, token usage in WO summary)

### Out of Scope
- Token budget enforcement (user explicitly deprioritized)
- Mid-agent-dispatch pause (agent tool doesn't support interruption)
- Undo/rollback of completed WOs

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 7 | All Phase 7 WOs | Complete |

## Impact Analysis

- **Files modified:** `skills/build/SKILL.md` (checkpoint save/restore at each step, error recovery notifications, remove token tracking references)
- **Files created:** None (checkpoint files created at runtime in user's project)
- **Systems affected:** Build loop orchestration, error recovery, convergence cycle

## Acceptance Criteria

- [x] AC-1: Checkpoint file created after each agent dispatch completes within a WO
- [x] AC-2: `/vibeos:build WO-NNN` detects existing checkpoint and resumes from correct step
- [x] AC-3: Resumed WO does not re-run agents that already completed
- [x] AC-4: User sees clear message on resume showing what's done and what's next
- [x] AC-5: Every gate retry is preceded by a user-facing notification explaining what failed and what's being tried
- [x] AC-6: Every audit convergence retry is preceded by a notification explaining remaining findings
- [x] AC-7: Every agent timeout retry is preceded by a notification
- [x] AC-8: Checkpoint file cleaned up after successful WO completion
- [x] AC-9: Token tracking references removed from build skill (token-tracker.sh calls, overhead checks)
- [x] AC-10: Communication contract compliance: all pre-action notifications follow contract patterns

## Test Strategy

- **Resume:** Simulate interrupted WO (checkpoint exists with 3/8 steps done), verify resume skips completed steps
- **Notifications:** Trace through every retry path, verify user sees notification before action
- **Cleanup:** Verify checkpoint removed after WO completes
- **Token removal:** Verify no token-tracker.sh references remain in build skill

## Implementation Plan

### Step 1: Define Checkpoint Schema
```json
{
  "wo": "WO-NNN",
  "started_at": "ISO-8601",
  "last_updated": "ISO-8601",
  "current_step": 5,
  "total_steps": 8,
  "completed_agents": [
    {"agent": "investigator", "step": 4, "result": "PROCEED", "completed_at": "ISO-8601"},
    {"agent": "tester", "step": 5, "result": "tests-written", "completed_at": "ISO-8601"}
  ],
  "gate_attempts": 0,
  "audit_iterations": 0,
  "state_hash": "sha256"
}
```

### Step 2: Add Checkpoint Save Points to Build Skill
After each agent dispatch completes (Steps 4-9), write/update checkpoint:
- Step 4 (investigator): save checkpoint with step=4
- Step 5 (tester): save checkpoint with step=5
- Step 6 (implementation): save checkpoint with step=6
- Step 7 (gates): save checkpoint with step=7 + gate_attempts
- Step 8 (audit): save checkpoint with step=8 + audit_iterations
- Step 9 (doc writer): save checkpoint with step=9

### Step 3: Add Resume Detection to Build Skill Step 1
Before starting a WO:
1. Check for `.vibeos/checkpoints/WO-NNN.json`
2. If exists: read checkpoint, announce resume, skip to next pending step
3. If not: proceed normally (fresh start)

### Step 4: Add Pre-Action Notifications to All Retry Paths
Update build skill error recovery sections:
- Gate retry (Step 7): Before re-dispatching implementation agent, tell user what failed
- Audit convergence (Step 8): Before re-dispatching, tell user which findings remain
- Agent timeout: Before retrying, tell user which agent timed out and what's being tried

### Step 5: Remove Token Tracking References
Remove from build skill:
- Token recording calls (`token-tracker.sh record`)
- Overhead checks (`token-tracker.sh overhead`)
- Token usage line in WO completion summary
- 30% overhead threshold warning

### Step 6: Checkpoint Cleanup
In Step 10 (WO completion), after marking WO complete:
- Delete `.vibeos/checkpoints/WO-NNN.json`
- If `.vibeos/checkpoints/` is empty, remove directory

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: Trace build skill for all resume and notification paths
- Risk: Checkpoint file could become stale if WO spec changes between sessions; include WO file hash in checkpoint for staleness detection

## Evidence

- [x] Checkpoint file created after each agent step
- [x] Resume detection works from checkpoint
- [x] Pre-action notifications present for all retry paths
- [x] Token tracking references removed
- [x] Checkpoint cleaned up after WO completion
