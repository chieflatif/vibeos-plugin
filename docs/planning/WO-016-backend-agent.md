# WO-016: Backend Agent

## Status

`Draft`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Create a backend implementation agent that receives a WO spec and pre-written test files, then implements code to make the tests pass while following architecture rules and the no-stub policy.

## Scope

### In Scope
- [ ] Create `agents/backend.md` with appropriate tool access and model
- [ ] Agent receives WO spec and test file paths as input
- [ ] Agent implements backend code to make tests pass
- [ ] Agent follows architecture rules from ARCHITECTURE-OUTLINE.md
- [ ] Agent follows security patterns (input validation, error handling, no hardcoded secrets)
- [ ] No stubs, no placeholders, no TODOs in generated code
- [ ] Agent cannot modify test files (enforced by WO-015 hook)
- [ ] Agent runs tests locally to verify they pass before completing

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

- [ ] AC-1: Agent implements code that makes pre-written tests pass
- [ ] AC-2: Agent cannot modify test files (hook enforcement verified)
- [ ] AC-3: No stubs, placeholders, or TODOs in generated code
- [ ] AC-4: Code follows architecture rules from ARCHITECTURE-OUTLINE.md
- [ ] AC-5: Input validation and error handling present on all public interfaces
- [ ] AC-6: Agent runs test suite and confirms tests pass before completing
- [ ] AC-7: Agent reports which tests pass/fail in its return output

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

- [ ] Agent file created
- [ ] Tests pass after agent implementation
- [ ] No stubs/TODOs in generated code
- [ ] Architecture rules followed
- [ ] Test files not modified by agent
