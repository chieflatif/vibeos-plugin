# WO-038: Test Diff Auditing

## Status

`Complete`

## Phase

Phase 6: Midstream Embedding & Production Readiness

## Objective

Create a hook or gate that detects test file modifications during implementation, requires justification, and dispatches an audit agent to review the test diff.

## Scope

### In Scope
- [x] Hook or gate: detect when test files are modified during implementation phase
- [x] Require justification for any test modification (comment or commit message)
- [x] Dispatch audit agent to review the test diff specifically
- [x] Audit checks: was the test weakened? was an assertion removed? was a test deleted?
- [x] Distinguish legitimate modifications (bug fix, refactor) from TDD violations (weakening tests to pass)
- [x] Log all test modifications with justification and audit result
- [x] Block unjustified test modifications

### Out of Scope
- Test file protection during implementation (WO-015, prevents modification entirely)
- Test quality enforcement (WO-037, broader quality checks)
- Test writing (WO-014)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-037 | Must complete first | Complete |
| WO-015 | Test file protection | Complete |

## Impact Analysis

- **Files created:** Test diff audit hook/gate
- **Systems affected:** Hook chain, audit pipeline

## Acceptance Criteria

- [x] AC-1: Test file modifications detected during implementation
- [x] AC-2: Justification required before modification proceeds
- [x] AC-3: Audit agent reviews test diff for weakening patterns
- [x] AC-4: Weakening patterns detected: assertion removal, threshold relaxation, test deletion
- [x] AC-5: Legitimate modifications allowed with justification
- [x] AC-6: Unjustified or weakening modifications blocked
- [x] AC-7: All test modifications logged with justification and audit verdict

## Test Strategy

- **Integration:** Simulate test modification during implementation, verify detection
- **Weakening:** Modify test to remove assertion, verify audit catches it
- **Legitimate:** Modify test with valid justification, verify allowed

## Implementation Plan

### Step 1: Implement Modification Detection
- Monitor git diff for changes to test files
- Trigger when test files appear in staged changes during implementation phase
- Determine current phase from build loop context

### Step 2: Implement Justification Requirement
- When test modification detected: prompt for justification
- Justification stored with the diff for audit trail
- No justification = blocked

### Step 3: Implement Diff Audit
- Dispatch lightweight audit agent to review test diff
- Check for: removed assertions, relaxed thresholds, deleted test functions
- Check for: added assertions (usually fine), refactored assertions (usually fine)
- Return verdict: safe, suspicious, dangerous

### Step 4: Implement Block/Allow Logic
- Safe + justified: allow
- Suspicious + justified: allow with warning logged
- Dangerous or unjustified: block
- All decisions logged

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — simulate test weakening, verify detection and block
- Risk: Diff analysis may produce false positives for complex refactors; needs context awareness

## Evidence

- [x] Test modification detected during implementation
- [x] Justification required and captured
- [x] Audit agent reviews diff correctly
- [x] Weakening patterns blocked
- [x] Legitimate modifications allowed
- [x] All modifications logged
