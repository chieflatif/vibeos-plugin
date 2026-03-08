# WO-007a: Test Fixture Project

## Status

`Complete`

## Phase

Phase 1: Plugin Foundation

## Objective

Create a minimal test project with known issues that validate each audit layer catches what it should — hardcoded secrets, stubs, security issues, and fallback-masked tests.

## Scope

### In Scope
- [x] Create `test-fixture/` directory with a small Python project
- [x] Include hardcoded API key (Layer 0 — secrets hook should catch)
- [x] Include `raise NotImplementedError` (Layer 0 — Stop hook + Layer 1 — stub gate)
- [x] Include swallowed error (Layer 1 — stub gate)
- [x] Include vacuous test (Layer 1 — test-integrity gate)
- [x] Include SQL injection vulnerability (Layer 2 — security auditor, Phase 4)
- [x] Include fallback-masked test (Layer 2 — test auditor, Phase 4)
- [x] Include stub test (Layer 1 — stub gate)

### Out of Scope
- Architecture violation fixture (requires project-specific rules config)
- Using this fixture for automated CI (future)
- Frontend test fixtures (future)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-006 | Hooks must exist to test against | Complete |

## Acceptance Criteria

- [x] AC-1: Hardcoded API key catchable by secrets hook
- [x] AC-2: `NotImplementedError` catchable by Stop hook and stub gate
- [x] AC-3: Vacuous test (`assert True`) catchable by test-integrity gate
- [x] AC-4: Stub test (`pass` body) catchable by stub gate
- [x] AC-5: SQL injection catchable by security auditor (Phase 4 — deferred)
- [x] AC-6: Fallback-masked test catchable by test auditor (Phase 4 — deferred)
- [x] AC-7: Each issue documented in KNOWN-ISSUES.md with detection layer

## Implementation Notes

7 known issues across 2 files:
- `src/app.py` — 4 issues (secret, SQL injection, stub, swallowed error)
- `tests/test_app.py` — 3 issues (vacuous test, fallback-masked test, stub test)

Architecture violation omitted — requires project-specific architecture-rules.json config which is project-dependent, not fixture-dependent.

## Evidence

- [x] Fixture project created (test-fixture/src/, test-fixture/tests/)
- [x] 7 known issues documented in KNOWN-ISSUES.md
- [x] Each issue mapped to detection layer and specific gate/hook
- [x] Validation commands included in KNOWN-ISSUES.md
