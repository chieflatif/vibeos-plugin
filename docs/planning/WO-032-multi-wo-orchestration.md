# WO-032: Multi-WO Orchestration

## Status

`Complete`

## Phase

Phase 5: Convergence & Full Autonomous Loop

## Objective

Extend the build orchestrator to loop across multiple WOs, checking autonomy configuration between WOs and updating DEVELOPMENT-PLAN.md as WOs complete.

## Scope

### In Scope
- [x] Loop across WOs in DEVELOPMENT-PLAN.md order
- [x] After each WO completes: check autonomy config (.vibeos/config.json)
- [x] If autonomy = "wo": pause and report to user after each WO
- [x] If autonomy = "phase": pause at phase boundaries
- [x] If autonomy = "major": continue unless major decision needed
- [x] Update DEVELOPMENT-PLAN.md WO statuses as each completes
- [x] Update WO-INDEX.md after each WO
- [x] Handle WO dependency chains (don't start WO if dependencies incomplete)
- [x] Skip WOs with unmet dependencies, continue with next eligible WO

### Out of Scope
- Single WO execution (WO-020)
- Convergence controls (WO-030)
- Phase boundary audit (WO-033)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-030 | Must complete first | Complete |
| WO-011 | Autonomy config | Complete |

## Impact Analysis

- **Files modified:** skills/build/SKILL.md (extend to multi-WO loop)
- **Systems affected:** Build orchestration, plan tracking

## Acceptance Criteria

- [x] AC-1: Orchestrator processes multiple WOs in dependency order
- [x] AC-2: Autonomy config respected between WOs
- [x] AC-3: DEVELOPMENT-PLAN.md updated after each WO completion
- [x] AC-4: WOs with unmet dependencies skipped with explanation
- [x] AC-5: Phase boundary detected (transition from Phase N to Phase N+1)
- [x] AC-6: User pause includes: what was built, what's next, any issues
- [x] AC-7: User can continue, adjust plan, or stop at any pause point

## Test Strategy

- **Integration:** Run build with 3+ WOs, verify sequential execution
- **Autonomy:** Test each autonomy level (wo, phase, major)
- **Dependencies:** Test with WO that has unmet dependency, verify skip

## Implementation Plan

### Step 1: Implement WO Ordering
- Read DEVELOPMENT-PLAN.md for WO order
- Build dependency graph
- Determine next eligible WO (all dependencies complete)

### Step 2: Implement Multi-WO Loop
- Execute WO using existing lifecycle (WO-020)
- After completion: update plan, check autonomy
- Determine next WO or pause

### Step 3: Implement Autonomy Checks
- Read .vibeos/config.json for autonomy level
- "wo": pause after every WO
- "phase": check if next WO is in different phase, pause at boundary
- "major": continue unless escalation or major decision flagged

### Step 4: Implement User Pause
- Generate progress report: completed WOs, current status, next WO
- Present options: continue, adjust plan, change autonomy, stop
- Resume from where paused

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — multi-WO execution with autonomy checks
- Risk: Complex state management across WO transitions; must preserve context correctly

## Evidence

- [x] Multi-WO loop executes correctly
- [x] Autonomy config respected
- [x] DEVELOPMENT-PLAN.md updated after each WO
- [x] Dependency ordering enforced
- [x] User pause works at correct points
