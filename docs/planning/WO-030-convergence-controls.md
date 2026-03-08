# WO-030: Convergence Controls

## Status

`Complete`

## Phase

Phase 5: Convergence & Full Autonomous Loop

## Objective

Implement convergence detection to prevent infinite fix-audit loops by hashing code state between cycles, tracking iteration counts, and detecting semantic completion.

## Scope

### In Scope
- [x] Create `convergence/state-hash.sh` — hash the code state (source files) between cycles
- [x] Create `convergence/convergence-check.sh` — evaluate convergence criteria
- [x] Max iteration limit: configurable, default 5
- [x] Identical findings detection: if same findings appear in consecutive cycles, stop
- [x] State hash comparison: if code state unchanged after fix attempt, stop
- [x] Semantic completion: if tests pass and no critical findings, declare converged
- [x] Escalation: if state unchanged after 2 cycles, escalate to user
- [x] Integration with build loop fix cycles

### Out of Scope
- Token budget tracking (WO-031)
- Multi-WO orchestration (WO-032)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-029 | Must complete first | Complete |

## Impact Analysis

- **Files created:** convergence/state-hash.sh, convergence/convergence-check.sh
- **Files modified:** skills/build/SKILL.md (integrate convergence checks)
- **Systems affected:** Build loop fix cycles, audit cycles

## Acceptance Criteria

- [x] AC-1: state-hash.sh produces deterministic hash of source files
- [x] AC-2: convergence-check.sh evaluates: max iterations, identical findings, state hash, test status
- [x] AC-3: Unchanged state after 2 cycles triggers escalation
- [x] AC-4: Tests pass + no critical findings = converged (stop iterating)
- [x] AC-5: Max iteration limit enforced
- [x] AC-6: Convergence status logged to build-log.md
- [x] AC-7: Scripts are bash 3.2+ compatible

## Test Strategy

- **Unit:** Test state-hash.sh produces consistent hashes
- **Unit:** Test convergence-check.sh with various scenarios (converged, stuck, max iterations)
- **Integration:** Run build loop, verify convergence detection works

## Implementation Plan

### Step 1: Implement State Hash
- Hash all source files (exclude .git, node_modules, etc.)
- Use sha256sum or shasum
- Output single hash representing code state
- Must be deterministic (file ordering, content-only)

### Step 2: Implement Convergence Check
- Inputs: current hash, previous hash, iteration count, findings, test results
- Logic:
  - If iteration >= max: STOP (max iterations)
  - If current_hash == previous_hash for 2 cycles: STOP (stuck)
  - If findings identical to previous cycle: STOP (not converging)
  - If tests pass AND no critical findings: STOP (converged)
  - Otherwise: CONTINUE

### Step 3: Integrate with Build Loop
- After each fix cycle: run state-hash, store result
- Before next fix cycle: run convergence-check
- If STOP: log reason, take appropriate action (escalate or declare success)

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Unit tests for hash and convergence logic
- Risk: Hash must be truly deterministic across platforms; file ordering differences could cause false "unchanged"

## Evidence

- [x] state-hash.sh produces consistent hashes
- [x] convergence-check.sh handles all scenarios correctly
- [x] Build loop respects convergence decisions
- [x] Escalation works when stuck
- [x] Successful convergence detected and logged
