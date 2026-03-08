# WO-034: Human Check-in Protocol (Layer 6)

## Status

`Draft`

## Phase

Phase 5: Convergence & Full Autonomous Loop

## Objective

Implement a human check-in protocol that pauses at the negotiated frequency and provides a full report of what was built, what was found, and what comes next, with options for the user to continue, adjust, or redirect.

## Scope

### In Scope
- [ ] Pause at frequency matching autonomy config (WO-011)
- [ ] Generate full check-in report: what was built, what was found, what's next
- [ ] Report in communication contract format (plain English, no jargon)
- [ ] User options at each check-in: continue, adjust plan, change autonomy level, redirect to different work, stop
- [ ] If user adjusts plan: update DEVELOPMENT-PLAN.md before continuing
- [ ] If user changes autonomy: update .vibeos/config.json
- [ ] If user redirects: create new WO or reprioritize existing WOs
- [ ] Log all check-in interactions in build-log.md

### Out of Scope
- Autonomy negotiation (WO-011, initial setup)
- Multi-WO orchestration (WO-032, triggers the check-in)
- Build loop implementation (WO-019-021)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-032 | Must complete first | Draft |
| WO-011 | Autonomy config | Draft |

## Impact Analysis

- **Files modified:** skills/build.md (add check-in step)
- **Systems affected:** Build loop, user interaction, plan management

## Acceptance Criteria

- [ ] AC-1: Check-in triggers at correct frequency per autonomy config
- [ ] AC-2: Report includes: completed WOs summary, findings summary, next WO preview
- [ ] AC-3: Report uses communication contract language throughout
- [ ] AC-4: User can continue without changes
- [ ] AC-5: User can adjust plan (modifications saved to DEVELOPMENT-PLAN.md)
- [ ] AC-6: User can change autonomy level (saved to .vibeos/config.json)
- [ ] AC-7: User can redirect to different work (new WO created or priorities changed)
- [ ] AC-8: User can stop (build loop exits gracefully)

## Test Strategy

- **Integration:** Trigger check-in, verify report generated
- **Options:** Test each user option (continue, adjust, change autonomy, redirect, stop)
- **Persistence:** Verify changes saved to correct files

## Implementation Plan

### Step 1: Implement Check-in Trigger
- Read autonomy config
- After WO/phase/major decision: evaluate if check-in needed
- Pause build loop

### Step 2: Generate Check-in Report
- Completed WOs: name, status, key findings
- Current state: what's been built, overall progress
- Next up: next WO name, objective, estimated complexity
- Issues: any escalated items, warnings, concerns

### Step 3: Implement User Options
- Present options clearly with consequences
- Continue: resume build loop from where paused
- Adjust plan: interactive plan modification, save changes
- Change autonomy: present options again, save new selection
- Redirect: create new WO or reorder existing WOs
- Stop: graceful exit with progress saved

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — trigger check-in, test each option
- Risk: User interaction quality depends on report clarity; must be genuinely useful, not just a formality

## Evidence

- [ ] Check-in triggers at correct frequency
- [ ] Report is clear and actionable
- [ ] All user options work correctly
- [ ] Changes persisted to correct files
- [ ] Build loop resumes correctly after check-in
