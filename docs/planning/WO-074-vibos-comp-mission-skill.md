# WO-074: VibOS Comp Mission Skill

## Status

`Complete`

## Phase

Phase 14: VibOS Comp — Enterprise MVP Battle Harness

## Objective

Add a VibOS Comp mission workflow that turns an idea, competition prompt, or commercial MVP brief into a compact enterprise MVP mission brief without the full discovery/planning paperwork burden.

## Scope

### In Scope
- [x] Add `vibeos-comp` skill for Claude/Cursor and Codex surfaces
- [x] Generate a compact `MISSION.md` artifact
- [x] Capture objective, users, core workflow, non-goals, stack assumptions, threat model, observability requirements, performance budgets, and acceptance criteria
- [x] Prefer scope cutting over foundation cutting
- [x] Route high-risk or unclear missions back to full discovery/planning when needed

### Out of Scope
- Full PRD generation by default
- Implementation work inside mission intake
- Replacing existing discover/plan skills

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-072 | Runtime capability matrix | Complete |
| WO-073 | Modern Codex surface | Complete |

## Findings

1. The commercial target is enterprise MVP delivery, not disposable prototyping.
2. Existing VibeOS discovery/planning is quality-oriented but too heavy for competitive rapid MVP cycles.
3. A compact mission artifact can preserve quality-critical context while reducing administrative overhead.

## Research & Freshness

- Verified on: 2026-04-29.
- Source evidence: operator requirements captured in this planning session and existing VibeOS communication/build contracts.
- External version freshness is required only when stack or dependency choices are introduced.

## Impact Analysis

- **Files created:** `plugins/vibeos/skills/comp/SKILL.md`, `plugins/vibeos/reference/codex/skills/vibeos-comp/SKILL.md`, `plugins/vibeos/reference/product/MISSION.md.ref`, `tests/test_comp_skill.py`
- **Files modified:** bootstrap scripts, README, AGENTS/CLAUDE references, WO index, file inventory
- **Systems affected:** entry routing and initial project planning for VibOS Comp mode

## Acceptance Criteria

- [x] AC-1: User can invoke VibOS Comp naturally without slash command knowledge
- [x] AC-2: Mission flow produces `MISSION.md` with enterprise MVP baseline fields
- [x] AC-3: Mission flow asks only essential questions before producing a first draft
- [x] AC-4: Mission flow explicitly separates product scope cuts from engineering foundation cuts
- [x] AC-5: High-risk missions trigger a recommendation to run full VibeOS discovery/planning
- [x] AC-6: Generated mission artifacts are compatible with downstream swarm planning

## Test Strategy

- **Fixture tests:** run mission generation against sample MVP prompts
- **Content validation:** verify required sections exist and no placeholder fields remain
- **Real-path verification:** bootstrap fixture project and invoke skill instructions through a simulated mission
- **Verification command:** run the skill against a sample prompt and inspect generated `MISSION.md`

## Implementation Plan

### Step 1: Define Mission Template
- Create the compact artifact schema and required sections
- Expected outcome: stable handoff contract for swarm planning

### Step 2: Add Skills
- Add Claude/Cursor and Codex skill instructions
- Expected outcome: same mission behavior across both surfaces

### Step 3: Wire Routing
- Update intent guidance and install inventory
- Expected outcome: natural language requests route into Comp mode

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Mission intake needed to reduce paperwork while preserving security, observability, testing, deployment, and evidence.
- Test status: Scope covered by template and skill tests.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Routing needed to catch enterprise MVP and competition-grade requests before generic discovery/build routing.
- Test status: Intent-router fixture added.

### Pre-Commit Audit
- Status: `complete`
- Findings: Claude/Cursor and Codex installs include the Comp skill and mission template through shared runtime references.
- Test status: `tests/test_comp_skill.py` and Codex bootstrap tests pass.

## Evidence

- [x] Implementation complete
- [x] Tests pass: `python3 -m unittest tests/test_comp_skill.py`
- [x] Skill behavior verified through mission template, Codex/Claude skill, and intent-router tests
- [x] Documentation updated
