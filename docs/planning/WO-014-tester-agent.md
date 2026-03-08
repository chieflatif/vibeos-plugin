# WO-014: Tester Agent

## Status

`Complete`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Create a tester agent that receives a WO spec and acceptance criteria (not implementation code) and writes tests from the spec, enforcing true TDD where tests define expected behavior before code exists.

## Scope

### In Scope
- [x] Create `agents/tester.md` with appropriate tool access and model
- [x] Agent reads WO spec and acceptance criteria as input
- [x] Agent writes unit tests from acceptance criteria
- [x] Agent writes integration tests from WO scope
- [x] Agent writes smoke test definitions for end-to-end verification
- [x] Tests written BEFORE implementation code exists (TDD)
- [x] Tests use standard test framework for the target project's language
- [x] Tests are specific, not generic — each test maps to an AC

### Out of Scope
- Implementation code (WO-016, WO-017)
- Test file protection enforcement (WO-015)
- Test quality auditing (WO-026)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-013 | Must complete first | Draft |

## Impact Analysis

- **Files created:** agents/tester.md
- **Systems affected:** TDD pipeline, test directory in target project

## Acceptance Criteria

- [x] AC-1: Agent writes tests from spec only — never reads implementation code
- [x] AC-2: Each acceptance criterion has at least one corresponding test
- [x] AC-3: Tests are syntactically valid (parseable by test framework)
- [x] AC-4: Tests fail initially (no implementation exists yet) — this is correct TDD behavior
- [x] AC-5: Test file names and locations follow target project conventions
- [x] AC-6: Integration tests cover cross-component interactions defined in WO scope
- [x] AC-7: Smoke tests cover the "happy path" end-to-end scenario

## Test Strategy

- **Verification:** Generated tests are syntactically valid
- **TDD check:** Tests fail before implementation, pass after
- **Coverage:** Every AC maps to at least one test

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (sonnet), tools (Read, Write, Glob, Grep), maxTurns
- Instructions: read WO, extract ACs, write tests — never look at implementation code
- Language-agnostic test generation strategy

### Step 2: Implement Test Generation Logic
- Parse acceptance criteria from WO file
- For each AC: generate one or more test cases
- For integration scope: generate cross-component tests
- For end-to-end: generate smoke test outline

### Step 3: Implement Language Detection
- Detect target project language from existing files or project config
- Select appropriate test framework (pytest, jest, go test, etc.)
- Generate tests in correct framework syntax

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Verify generated tests are syntactically valid and map to ACs
- Risk: Test quality depends on AC specificity — vague ACs produce vague tests

## Evidence

- [x] Agent file created
- [x] Tests generated from sample WO
- [x] Each AC has corresponding test(s)
- [x] Tests are syntactically valid
- [x] Tests fail before implementation (TDD verified)
