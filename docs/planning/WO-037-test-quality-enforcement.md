# WO-037: Enhanced Test Quality Enforcement

## Status

`Complete`

## Phase

Phase 6: Midstream Embedding & Production Readiness

## Objective

Implement enhanced test quality checks including fallback masking detection, mock density analysis, test-to-spec coverage mapping, and git history analysis for test modifications after implementation.

## Scope

### In Scope
- [x] Fallback masking detection: identify tests that pass because of catch-all/default behavior
- [x] Mock density check: calculate mock-to-real dependency ratio per test file
- [x] Test-to-spec coverage mapping: verify each acceptance criterion has a corresponding test
- [x] Git history analysis: detect test files modified after implementation files (TDD violation)
- [x] Configurable thresholds for mock density (default: warn at >60% mocked)
- [x] Integration as a gate or audit check in the build pipeline
- [x] Structured report with findings and recommendations

### Out of Scope
- Test writing (WO-014)
- Test file protection (WO-015)
- Test diff auditing (WO-038)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-026 | Test auditor agent | Complete |

## Impact Analysis

- **Files created:** Test quality check scripts or gate additions
- **Systems affected:** Test quality pipeline, gate-runner

## Acceptance Criteria

- [x] AC-1: Fallback masking patterns detected (empty catch, catch-all returns, default-only switches)
- [x] AC-2: Mock density calculated per test file with warning at threshold
- [x] AC-3: Test-to-spec mapping generated showing coverage gaps
- [x] AC-4: Git history analysis identifies TDD violations (test modified after implementation)
- [x] AC-5: Thresholds configurable via .vibeos/config.json
- [x] AC-6: Results available as gate check or audit finding
- [x] AC-7: Language-agnostic detection patterns

## Test Strategy

- **Unit:** Test pattern detection with sample code containing each anti-pattern
- **Mock density:** Test calculation with sample test files of varying mock levels
- **Git history:** Test with known commit ordering

## Implementation Plan

### Step 1: Implement Fallback Masking Detection
- Scan test files for patterns: empty catch blocks, catch-all exception handlers
- Detect tests that assert on default/fallback values only
- Detect tests where assertion is inside a try block (may not execute)
- Flag with evidence (file, line, pattern)

### Step 2: Implement Mock Density Analysis
- Count mock/stub/spy declarations per test file
- Count real dependency usages per test file
- Calculate ratio: mocks / (mocks + real)
- Warn if ratio exceeds threshold

### Step 3: Implement Test-to-Spec Mapping
- Read WO acceptance criteria
- Map test function names/descriptions to ACs
- Identify ACs without corresponding tests
- Identify tests without corresponding ACs (orphaned tests)

### Step 4: Implement Git History Analysis
- For each WO: find test files and implementation files
- Check git log for modification order
- Flag if test files modified after implementation files committed
- Exclude legitimate test updates (bug fixes, refactoring)

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: Unit tests for each detection pattern
- Risk: False positives in pattern detection; thresholds need tuning per project

## Evidence

- [x] Fallback masking detection works
- [x] Mock density calculation accurate
- [x] Test-to-spec mapping identifies gaps
- [x] Git history analysis detects TDD violations
- [x] Thresholds configurable
