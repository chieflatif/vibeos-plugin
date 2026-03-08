# WO-017: Frontend Agent

## Status

`Draft`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Create a frontend implementation agent that follows the same TDD pattern as the backend agent, implementing UI code to make pre-written tests pass while following architecture and accessibility standards.

## Scope

### In Scope
- [ ] Create `agents/frontend.md` with appropriate tool access and model
- [ ] Agent receives WO spec and test file paths as input
- [ ] Agent implements frontend code to make tests pass
- [ ] Agent follows architecture rules from ARCHITECTURE-OUTLINE.md
- [ ] Agent follows accessibility standards (semantic HTML, ARIA, keyboard navigation)
- [ ] No stubs, no placeholders, no TODOs in generated code
- [ ] Agent cannot modify test files (enforced by WO-015 hook)
- [ ] Agent runs tests locally to verify they pass before completing
- [ ] Language-agnostic: works for React, Vue, Svelte, vanilla JS, or any frontend framework

### Out of Scope
- Backend code (WO-016)
- Test writing (WO-014)
- Documentation updates (WO-018)
- Visual design decisions (deferred to user)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-015 | Must complete first | Draft |

## Impact Analysis

- **Files created:** agents/frontend.md
- **Systems affected:** Implementation pipeline, target project UI code

## Acceptance Criteria

- [ ] AC-1: Agent implements code that makes pre-written tests pass
- [ ] AC-2: Agent cannot modify test files (hook enforcement verified)
- [ ] AC-3: No stubs, placeholders, or TODOs in generated code
- [ ] AC-4: Code follows architecture rules from ARCHITECTURE-OUTLINE.md
- [ ] AC-5: Semantic HTML and accessibility patterns used where applicable
- [ ] AC-6: Agent runs test suite and confirms tests pass before completing
- [ ] AC-7: Agent reports which tests pass/fail in its return output

## Test Strategy

- **Integration:** Dispatch frontend agent with sample WO and tests, verify tests pass
- **Quality:** Verify no stubs/TODOs in generated code
- **Accessibility:** Verify semantic HTML and ARIA attributes where applicable

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (sonnet), tools (Read, Write, Edit, Glob, Grep, Bash), maxTurns
- Instructions: read WO, read tests, implement UI code, run tests, iterate
- Embed no-stub policy and architecture rules

### Step 2: Implement Coding Protocol
- Same TDD protocol as backend agent
- Additional awareness of component structure, state management, API integration
- Framework detection from project config (package.json, etc.)

### Step 3: Implement Quality Checks
- Self-check: grep for TODO, FIXME, stub, placeholder
- Self-check: verify semantic HTML usage
- Self-check: verify no inline styles where CSS modules/classes expected

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — dispatch with sample WO and tests, verify passing
- Risk: Frontend testing frameworks vary widely; agent must adapt to project's framework

## Evidence

- [ ] Agent file created
- [ ] Tests pass after agent implementation
- [ ] No stubs/TODOs in generated code
- [ ] Architecture rules followed
- [ ] Test files not modified by agent
