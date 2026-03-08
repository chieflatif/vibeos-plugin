# WO-026: Test Auditor Agent

## Status

`Complete`

## Phase

Phase 4: Fresh-Context Audit Agents

## Objective

Create a test auditor agent that evaluates test quality: whether tests were written from spec, fallback masking, mock density, edge coverage, and git history integrity.

## Scope

### In Scope
- [x] Create `agents/test-auditor.md` with strict isolation
- [x] Agent config: isolation: worktree, disallowedTools: Write, Edit, Agent, model: sonnet
- [x] Spec-first check: do tests map to acceptance criteria (not reverse-engineered from code)?
- [x] Fallback masking detection: tests that pass because of catch-all/default behavior, not correct logic
- [x] Mock density check: excessive mocking that hides real behavior
- [x] Edge coverage: boundary conditions, empty inputs, error paths tested
- [x] Git history check: were test files modified after implementation files? (TDD violation indicator)
- [x] Structured findings with severity

### Out of Scope
- Security analysis (WO-023)
- Writing tests (WO-014)
- Test file protection (WO-015)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-023 | Must complete first | Complete |

## Impact Analysis

- **Files created:** agents/test-auditor.md
- **Systems affected:** Audit pipeline, test quality enforcement

## Acceptance Criteria

- [x] AC-1: Agent runs in isolated worktree
- [x] AC-2: Agent cannot use Write, Edit, or Agent tools
- [x] AC-3: Tests mapped to acceptance criteria — unmapped tests flagged
- [x] AC-4: Fallback masking patterns detected (catch-all returns, empty catch blocks in tests)
- [x] AC-5: Mock density reported (mocks per test, percentage of mocked dependencies)
- [x] AC-6: Missing edge case coverage identified
- [x] AC-7: Git history analyzed — test modifications after implementation flagged
- [x] AC-8: Structured output with findings and recommendations

## Test Strategy

- **Integration:** Dispatch against tests with known quality issues
- **Git history:** Verify git log analysis correctly identifies TDD violations
- **Fallback masking:** Verify detection of tests that pass for wrong reasons

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (sonnet), isolation (worktree), disallowedTools (Write, Edit, Agent), maxTurns
- Instructions: test quality audit protocol

### Step 2: Implement Test Quality Checks
- Phase 1: Read WO acceptance criteria, map each to test functions
- Phase 2: Analyze test assertions — are they specific or generic?
- Phase 3: Count mocks per test, flag excessive mocking
- Phase 4: Check for edge cases: null, empty, boundary, error paths
- Phase 5: Check for fallback masking: try/catch that swallows, default returns

### Step 3: Implement Git History Analysis
- `git log --oneline -- <test_files>` — when were tests last modified?
- `git log --oneline -- <impl_files>` — when was implementation last modified?
- If test modified after implementation: flag as potential TDD violation
- Include git commit details in finding

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — dispatch against tests with planted quality issues
- Risk: Git history analysis may be misleading for legitimate test updates; need context awareness

## Evidence

- [x] Agent file created with correct isolation config
- [x] Test-to-AC mapping works
- [x] Fallback masking detected
- [x] Mock density reported
- [x] Git history analyzed for TDD violations
- [x] Structured findings returned
