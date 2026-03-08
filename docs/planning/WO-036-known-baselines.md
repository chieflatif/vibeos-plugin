# WO-036: Known Baselines Integration

## Status

`Draft`

## Phase

Phase 6: Midstream Embedding & Production Readiness

## Objective

Integrate known baselines into the gate and audit systems so that pre-existing failures are tracked with max_allowed_failures, new failures block, and baselines ratchet down over time.

## Scope

### In Scope
- [ ] Modify gate-runner to support max_allowed_failures per gate
- [ ] Read baseline counts from .vibeos/baselines/ files
- [ ] Pre-existing failures: tracked but do not block builds
- [ ] New failures (count exceeds baseline): block builds
- [ ] Baseline ratcheting: when findings are fixed, reduce max_allowed_failures
- [ ] Ratchet is one-way: baseline can only decrease, never increase
- [ ] Apply same logic to audit findings: pre-existing = tracked, new = block
- [ ] Update baseline files after successful ratchet

### Out of Scope
- Midstream detection (WO-035)
- Phase boundary audit (WO-033, uses baselines but different scope)
- Individual gate implementation

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-035 | Must complete first | Draft |

## Impact Analysis

- **Files modified:** Gate-runner integration, audit skill
- **Files modified:** .vibeos/baselines/ files (ratcheting)
- **Systems affected:** Quality gates, audit pipeline, build loop

## Acceptance Criteria

- [ ] AC-1: Gates accept max_allowed_failures parameter from baseline
- [ ] AC-2: Pre-existing failures (within baseline) do not block
- [ ] AC-3: New failures (exceeding baseline) block with clear message
- [ ] AC-4: When findings are fixed: baseline ratchets down automatically
- [ ] AC-5: Baseline can never increase (one-way ratchet)
- [ ] AC-6: Same logic applies to audit findings
- [ ] AC-7: Baseline updates logged to build-log.md

## Test Strategy

- **Unit:** Test baseline comparison logic (within, exceeding, ratcheting)
- **Integration:** Run gates with baseline, verify pre-existing pass and new failures block
- **Ratchet:** Fix a finding, re-run, verify baseline decreased

## Implementation Plan

### Step 1: Implement Baseline Reading
- Read .vibeos/baselines/ for gate and audit baselines
- Parse max_allowed_failures per gate/audit category
- Handle missing baseline (treat as 0 — all failures block)

### Step 2: Modify Gate Evaluation
- After gate runs: compare failure count against baseline
- If failures <= baseline: PASS (pre-existing, tracked)
- If failures > baseline: FAIL (new failures detected)
- Report: "N pre-existing issues tracked, M new issues found"

### Step 3: Implement Ratcheting
- After successful run with fewer failures than baseline: update baseline
- New baseline = current failure count
- Log ratchet: "Baseline for [gate] improved from N to M"
- Never increase baseline (if current > baseline, it's a failure, not a ratchet)

### Step 4: Apply to Audit Findings
- Same logic for audit findings by severity category
- Pre-existing critical findings tracked in baseline
- New critical findings block

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Unit tests for baseline logic, integration test with gate-runner
- Risk: Baseline file corruption could cause false blocks or false passes; must validate file integrity

## Evidence

- [ ] Baseline reading works
- [ ] Pre-existing failures pass within baseline
- [ ] New failures block correctly
- [ ] Ratcheting works (baseline decreases on improvement)
- [ ] One-way ratchet enforced (baseline never increases)
