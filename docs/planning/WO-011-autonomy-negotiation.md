# WO-011: Autonomy Negotiation

## Status

`Complete`

## Phase

Phase 2: Product Discovery & Planning

## Objective

Add an autonomy negotiation flow to `/vibeos:plan` that lets the user choose how much control to retain during autonomous build, storing the configuration in `.vibeos/config.json`.

## Scope

### In Scope
- [x] Add autonomy negotiation step to the /vibeos:plan skill
- [x] Three autonomy levels: stop after every WO, stop after every phase, stop at major decisions only
- [x] Explain each option in outcome language (what the user will experience, not technical details)
- [x] Include a recommendation with rationale
- [x] Store selected autonomy config in `.vibeos/config.json`
- [x] Config schema: `{ "autonomy": { "level": "wo|phase|major", "negotiated_at": "ISO timestamp" } }`

### Out of Scope
- Build loop implementation (WO-019)
- Human check-in protocol (WO-034)
- Runtime autonomy changes (WO-034)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-009 | Must complete first | Draft |

## Impact Analysis

- **Files modified:** skills/plan/SKILL.md (add autonomy step)
- **Files created:** autonomy negotiation logic, .vibeos/config.json schema
- **Systems affected:** Plan skill, future build orchestrator reads this config

## Acceptance Criteria

- [x] AC-1: User presented with 3 autonomy options after plan generation
- [x] AC-2: Each option explained in plain English with concrete examples
- [x] AC-3: Recommendation provided (default: stop after every phase for new users)
- [x] AC-4: Selection stored in `.vibeos/config.json`
- [x] AC-5: Config file is valid JSON and readable by future build orchestrator
- [x] AC-6: Communication contract enforced — no jargon, outcome language only

## Test Strategy

- **Integration:** Run plan skill, verify autonomy question appears after plan generation
- **Config:** Verify .vibeos/config.json created with correct schema
- **UX:** Verify explanations are clear to non-technical users

## Implementation Plan

### Step 1: Define Autonomy Options
- **Stop after every WO:** "I'll build one thing at a time and check in with you after each piece. You'll see what was built and approve before I continue."
- **Stop after every phase:** "I'll build a complete group of related features, then check in. You'll see a working chunk before I move to the next group."
- **Stop at major decisions only:** "I'll build continuously and only pause when I hit something that needs your input — like a design choice or an unexpected problem."

### Step 2: Add to Plan Skill
- Insert autonomy negotiation after DEVELOPMENT-PLAN.md generation
- Present options with recommendation
- Capture selection

### Step 3: Persist Configuration
- Create .vibeos/ directory if not exists
- Write config.json with autonomy selection and timestamp
- Validate JSON before writing

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — verify config persisted correctly
- Risk: Low complexity; main risk is unclear language in option descriptions

## Evidence

- [x] Autonomy options presented in plan skill
- [x] .vibeos/config.json created with valid schema
- [x] Option descriptions verified as plain English
- [x] Recommendation included
