# WO-050: Decision Engine Transparency & Gate Management

## Status

`Complete`

## Phase

Phase 8: Resilience & Transparency

## Objective

Make the decision engine's choices visible and understandable — after each decision tree runs, the user sees what was selected and why. Add a gate management capability so users can enable/disable gates without editing JSON files manually.

## Scope

### In Scope
- [x] After each decision tree (Steps 4a-4e in plan skill), explain results to user in plain English
- [x] Gate selection explanation: "I enabled [N] gates. Here's why: [gate] — [reason based on governance profile]"
- [x] Phase selection explanation: "Your project has [N] phases. Phase 1 covers [scope] because [reason]"
- [x] Hook selection explanation: "I enabled [N] hooks: [list with one-line purpose each]"
- [x] Architecture rules explanation: "Architecture rules enforce [pattern] because your stack uses [framework]"
- [x] Compliance mapping explanation: "Based on your [compliance target], these gates are mandatory: [list]"
- [x] Gate management via `/vibeos:gate` skill: add `enable`, `disable`, `list` subcommands
- [x] `list`: Show all gates with status (enabled/disabled), tier, blocking status, phase
- [x] `enable <gate-name>`: Enable a gate, update manifest, explain what it checks
- [x] `disable <gate-name>`: Disable a gate with consequence explanation and confirmation
- [x] Compliance-locked gates cannot be disabled: explain why ("This gate is required by your SOC 2 compliance target")
- [x] After gate manifest changes, re-run gate readiness check

### Out of Scope
- Creating new custom gates (future WO)
- Modifying gate script behavior (only enable/disable)
- Decision engine logic changes (only adding explanations)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 7 | All Phase 7 WOs | Complete |

## Impact Analysis

- **Files modified:** `skills/plan/SKILL.md` (add explanations after Steps 4a-4e), `skills/gate/SKILL.md` (add enable/disable/list subcommands)
- **Files created:** None
- **Systems affected:** Plan skill decision engine application, gate skill capabilities

## Acceptance Criteria

- [x] AC-1: After gate selection, user sees which gates are enabled and why each was chosen
- [x] AC-2: After phase selection, user sees phase structure with reasoning
- [x] AC-3: After hook selection, user sees which hooks are enabled with purpose
- [x] AC-4: After architecture rules, user sees which rules apply and why
- [x] AC-5: After compliance mapping, user sees which gates are compliance-mandatory
- [x] AC-6: `/vibeos:gate list` shows all gates with status, tier, and phase
- [x] AC-7: `/vibeos:gate enable <name>` enables a gate and updates manifest
- [x] AC-8: `/vibeos:gate disable <name>` shows consequences before disabling, requires confirmation
- [x] AC-9: Compliance-locked gates cannot be disabled — clear explanation why
- [x] AC-10: All decision explanations follow Communication Contract patterns

## Test Strategy

- **Explanation coverage:** Run plan skill on test project, verify all 5 decision trees produce user-facing explanations
- **Gate management:** Test enable/disable/list subcommands against quality-gate-manifest.json
- **Compliance lock:** Attempt to disable a compliance-locked gate, verify block with explanation
- **Contract compliance:** Verify all explanations follow USER-COMMUNICATION-CONTRACT.md patterns

## Implementation Plan

### Step 1: Add Explanation Output After Each Decision Tree
In plan skill Steps 4a-4e, after reading each decision tree and generating output, add a user-facing summary:

**Step 4a (Gate Selection):**
> "Based on your project profile ([language], [compliance], [team size]), I've configured [N] quality gates:
> - **[gate-name]** (blocking) — [what it checks]. Enabled because [reason].
> - **[gate-name]** (advisory) — [what it checks]. Enabled because [reason].
> [If compliance]: [M] of these gates are required by your [compliance target] and cannot be disabled."

**Step 4b (Phase Selection):**
> "Your development plan has [N] phases:
> - Phase 1: [name] — [what it covers]. This comes first because [reason].
> - Phase 2: [name] — [what it covers]. Depends on Phase 1 because [reason].
> This structure was chosen because [governance intensity] projects benefit from [reasoning]."

**Step 4c-4e:** Similar pattern for hooks, architecture rules, compliance mapping.

### Step 2: Add Gate Management Subcommands to Gate Skill
Update `skills/gate/SKILL.md` with new subcommands:

**`/vibeos:gate list`:**
- Read `scripts/quality-gate-manifest.json`
- Present formatted table: name, status, tier, blocking, phase, compliance-locked
- Group by phase for readability

**`/vibeos:gate enable <gate-name>`:**
- Find gate in manifest by name
- Set `enabled: true`
- Explain what the gate checks and its impact
- Update manifest file

**`/vibeos:gate disable <gate-name>`:**
- Find gate in manifest by name
- Check if compliance-locked → if yes, block with explanation
- Present consequences: "Disabling [gate-name] means [specific quality check] won't run. [Risk in plain English]."
- Require user confirmation
- Update manifest file
- Log decision to `.vibeos/build-log.md`

### Step 3: Add Compliance Lock Check
In gate manifest schema, add `compliance_locked: true|false` field (set by decision engine Step 4e).
Gates with `compliance_locked: true` cannot be disabled — explain which compliance target requires them.

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: Review decision engine output for all 5 trees
- Risk: Explanations could be verbose — keep to 2-3 lines per decision tree, expandable with `/vibeos:help`

## Evidence

- [x] All 5 decision trees produce user-facing explanations
- [x] Gate list shows complete inventory with status
- [x] Gate enable/disable works and updates manifest
- [x] Compliance-locked gates cannot be disabled
- [x] All explanations follow Communication Contract
