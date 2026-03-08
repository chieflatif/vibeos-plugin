# WO-033: Phase Boundary Audit (Layer 5)

## Status

`Draft`

## Phase

Phase 5: Convergence & Full Autonomous Loop

## Objective

Create a `/vibeos:checkpoint` skill that runs all 21 gates and all 5 audit agents on the entire codebase at phase boundaries, establishing and ratcheting quality baselines.

## Scope

### In Scope
- [ ] Create `skills/checkpoint.md` as the phase boundary audit skill
- [ ] Run all 21 gate scripts via gate-runner.sh on entire codebase
- [ ] Run all 5 audit agents on entire codebase
- [ ] Compare results against previous phase boundary baseline (if exists)
- [ ] Baseline ratcheting: new findings count must be <= previous count
- [ ] Store baseline in `.vibeos/baselines/phase-N-baseline.json`
- [ ] Generate comprehensive phase report
- [ ] Block phase transition if ratchet violated (more findings than baseline)

### Out of Scope
- Individual gate implementation (Phase 1)
- Individual audit agent implementation (Phase 4)
- Midstream baselines (WO-036)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-032 | Must complete first | Draft |
| WO-028 | Audit skill | Draft |
| WO-004 | Gate skill | Draft |

## Impact Analysis

- **Files created:** skills/checkpoint.md, .vibeos/baselines/ directory
- **Systems affected:** Phase transitions, quality enforcement

## Acceptance Criteria

- [ ] AC-1: All 21 gates run on entire codebase
- [ ] AC-2: All 5 audit agents run on entire codebase
- [ ] AC-3: Results compared against previous baseline
- [ ] AC-4: Ratchet enforced: finding count cannot increase between phases
- [ ] AC-5: Baseline stored for future comparison
- [ ] AC-6: Phase report includes: gate results, audit findings, baseline comparison, ratchet status
- [ ] AC-7: Phase transition blocked if ratchet violated

## Test Strategy

- **Integration:** Run checkpoint on sample codebase, verify comprehensive report
- **Ratchet:** Run checkpoint twice, introduce new finding, verify ratchet blocks
- **Baseline:** Verify baseline file created and read correctly

## Implementation Plan

### Step 1: Create Checkpoint Skill
- Dispatch gate-runner.sh with all gates
- Dispatch /vibeos:audit for full audit cycle
- Collect all results

### Step 2: Implement Baseline Management
- First run: store results as baseline
- Subsequent runs: load previous baseline, compare
- Store in .vibeos/baselines/phase-N-baseline.json

### Step 3: Implement Ratchet
- Count findings by severity in current run
- Compare against baseline counts
- If current > baseline for any severity: ratchet violated
- Report which categories regressed

### Step 4: Generate Phase Report
- Header: phase number, date, scope
- Gate results: pass/fail per gate
- Audit findings: by severity and auditor
- Baseline comparison: improved/regressed/unchanged
- Ratchet status: pass/fail
- Recommendation: proceed to next phase or fix regressions

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — full checkpoint run with baseline comparison
- Risk: Running all gates + all auditors is expensive; should be reserved for phase boundaries only

## Evidence

- [ ] Checkpoint skill created
- [ ] All gates and auditors run
- [ ] Baseline stored and loaded correctly
- [ ] Ratchet enforced
- [ ] Phase report generated
