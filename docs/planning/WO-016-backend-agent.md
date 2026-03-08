# WO-016: Backend Agent

## Status

`Complete`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Create a backend implementation agent that receives a WO spec and pre-written test files, then implements code to make the tests pass while following architecture rules and the no-stub policy.

## Scope

### In Scope
- [x] Create `agents/backend.md` with appropriate tool access and model
- [x] Agent receives WO spec and test file paths as input
- [x] Agent implements backend code to make tests pass
- [x] Agent follows architecture rules from ARCHITECTURE-OUTLINE.md
- [x] Agent follows security patterns (input validation, error handling, no hardcoded secrets)
- [x] No stubs, no placeholders, no TODOs in generated code
- [x] Agent cannot modify test files (enforced by WO-015 hook)
- [x] Agent runs tests locally to verify they pass before completing

### Out of Scope
- Frontend code (WO-017)
- Test writing (WO-014)
- Documentation updates (WO-018)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-015 | Must complete first | Draft |

## Impact Analysis

- **Files created:** agents/backend.md
- **Systems affected:** Implementation pipeline, target project source code

## Acceptance Criteria

- [x] AC-1: Agent implements code that makes pre-written tests pass
- [x] AC-2: Agent cannot modify test files (hook enforcement verified)
- [x] AC-3: No stubs, placeholders, or TODOs in generated code
- [x] AC-4: Code follows architecture rules from ARCHITECTURE-OUTLINE.md
- [x] AC-5: Input validation and error handling present on all public interfaces
- [x] AC-6: Agent runs test suite and confirms tests pass before completing
- [x] AC-7: Agent reports which tests pass/fail in its return output

## Test Strategy

- **Integration:** Dispatch backend agent with sample WO and tests, verify tests pass
- **Quality:** Verify no stubs/TODOs in generated code
- **Architecture:** Verify generated code follows architecture rules

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (sonnet), tools (Read, Write, Edit, Glob, Grep, Bash), maxTurns
- Instructions: read WO, read tests, implement code, run tests, iterate
- Embed no-stub policy and architecture rules

### Step 2: Implement Coding Protocol
- Read WO spec for context and requirements
- Read test files to understand expected behavior
- Implement code in correct project locations
- Run tests after each significant implementation step
- Fix failures iteratively

### Step 3: Implement Quality Checks
- Self-check: grep for TODO, FIXME, stub, placeholder in generated code
- Self-check: verify type annotations present (if Python/TypeScript)
- Self-check: verify error handling on public functions

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — dispatch with sample WO and tests, verify passing
- Risk: Agent may need many iterations to make complex tests pass; maxTurns must be sufficient

## Evidence

- [x] Agent file created
- [x] Tests pass after agent implementation
- [x] No stubs/TODOs in generated code
- [x] Architecture rules followed
- [x] Test files not modified by agent
