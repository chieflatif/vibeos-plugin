# WO-000: Technical Spike — Plugin Architecture Validation

## Status

`Complete`

## Phase

Phase 0: Architecture Validation (pre-Phase 1)

## Objective

Validate the 4 critical assumptions the entire plugin architecture depends on before committing to the development plan. If any assumption fails, the architecture must be revised.

## Scope

### In Scope
- [ ] **Spike 1: Plugin Manifest Schema** — Create a minimal plugin with plugin.json, run `claude plugin install`, document what fields are accepted
- [ ] **Spike 2: Skills vs Commands** — Determine whether slash-invoked workflows use `skills/` or `commands/` directory. Test both.
- [ ] **Spike 3: Agent Dispatch** — Create a trivial agent .md file, dispatch it from a skill/command, verify structured output is returned to caller
- [ ] **Spike 4: Hook Exit Codes** — Create a minimal PreToolUse hook, test exit code 0 (allow), 1 (fail?), 2 (block?). Document actual semantics.
- [ ] Document all findings in `docs/planning/SPIKE-RESULTS.md`

### Out of Scope
- Building any real functionality
- Full hook implementation
- Full agent implementation

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Claude Code with plugin support | External tool | Must be available |

## Impact Analysis

- **Files created:** Minimal spike files (temporary), SPIKE-RESULTS.md (permanent)
- **Architecture impact:** Findings may require renaming directories, changing manifest schema, or revising agent dispatch strategy

## Acceptance Criteria

- [ ] AC-1: Plugin installs successfully with the verified manifest schema
- [ ] AC-2: Correct directory convention for slash-invoked workflows is documented
- [ ] AC-3: Agent dispatch from skill/command works and returns usable output
- [ ] AC-4: Hook exit code semantics are verified and documented
- [ ] AC-5: SPIKE-RESULTS.md exists with all 4 findings documented
- [ ] AC-6: Development plan updated based on spike findings

## Test Strategy

- Each spike is its own test — create minimal files, run Claude Code, observe behavior
- Document exact commands run and exact results observed

## Implementation Plan

### Step 1: Minimal Plugin Install Test
- Create plugin with only name, version, description in plugin.json
- Run `claude plugin install`
- Progressively add fields (skills, agents, hooks) and test each
- Document which fields are accepted, which cause errors

### Step 2: Skills vs Commands Test
- Create a simple SKILL.md in both `skills/test/` and `commands/test/`
- Attempt to invoke via `/vibeos:test`
- Document which directory convention triggers slash invocation

### Step 3: Agent Dispatch Test
- Create `agents/test-agent.md` with minimal frontmatter
- From a skill/command, use Agent tool to dispatch
- Verify: Does the agent run? Does output return to caller? Is it structured?
- Test `disallowedTools` and `isolation: worktree` if basic dispatch works

### Step 4: Hook Exit Code Test
- Create `hooks/hooks.json` with a simple PreToolUse command hook
- Hook script exits with code 0, then 1, then 2
- Document which code allows vs blocks the operation

### Step 5: Document and Update Plan
- Write SPIKE-RESULTS.md
- Update DEVELOPMENT-PLAN.md, CLAUDE.md, plugin.json based on findings
- Update affected WO files if directory names or conventions change

## Contingency Plans

### If plugin.json schema is different
- Adapt manifest to actual schema
- Update all WO files referencing plugin.json structure
- Impact: Low (documentation changes only)

### If skills/ must be commands/
- Rename all 8 skill directories
- Update all WO files, DEVELOPMENT-PLAN.md, CLAUDE.md, plugin.json
- Impact: Medium (rename across 40+ files)

### If agent dispatch doesn't return structured output
- Option A: Parse freeform agent output with conventions (e.g., JSON blocks in markdown)
- Option B: Use agent memory files instead of return values (agent writes to file, orchestrator reads)
- Option C: Redesign orchestrator to not depend on structured agent returns
- Impact: High (architecture revision for Phase 3+)

### If hooks use different exit codes
- Update all hook scripts to use correct codes
- Update WO-006, WO-015, and all hook-related documentation
- Impact: Low (constant changes in scripts)

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: The spike IS the test — each step validates an assumption
- Risk: If multiple assumptions fail simultaneously, compound rework

## Evidence

- [ ] `claude plugin install` output captured
- [ ] Directory convention tested and documented
- [ ] Agent dispatch output captured
- [ ] Hook exit code behavior documented
- [ ] SPIKE-RESULTS.md complete
- [ ] Development plan updated
