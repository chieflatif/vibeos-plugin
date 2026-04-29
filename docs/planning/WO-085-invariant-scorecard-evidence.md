# WO-085: Invariant Scorecard and Evidence Integration

## Status

`Complete`

## Phase

Phase 16: System Invariants & State Safety

## Objective

Promote System Invariants into enterprise foundation requirements, AI failure-mode detection, scorecards, integration evidence, red-team review, and closeout dossiers so invalid state and broken ownership rules cannot hide behind passing happy-path demos.

## Scope

### In Scope
- [x] Add System Invariants section to the mission template
- [x] Add invariant expectations to Comp mission skills
- [x] Add invariant checkpoints to Comp planning and merge-readiness expectations
- [x] Add System Invariants scorecard dimension
- [x] Add system invariant AI failure mode
- [x] Add invariant evidence to integration evidence, red-team review, and evidence dossier

### Out of Scope
- Formal methods or exhaustive model checking
- Replacing normal data integrity, auth, or security reviews
- Certifying correctness beyond available evidence

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-084 | System Invariant Auditor and Gate | Complete |

## Findings

1. Enterprise MVPs need explicit "must never break" rules as much as user-facing workflows.
2. Invariants should be visible to non-technical users because they capture product truth in plain language.
3. Scorecards need invariant evidence so reviewers can distinguish real engineering foundations from happy-path prototypes.

## Research & Freshness

- Verified on: 2026-04-29.
- Local sources: Comp charter, mission template, foundation blueprint, AI failure mode registry, scorecard generator, red-team and dossier scripts.
- External sources: none required.

## Impact Analysis

- **Files modified:** `docs/planning/VIBOS-COMP-CHARTER.md`, `plugins/vibeos/reference/product/MISSION.md.ref`, `plugins/vibeos/reference/comp/enterprise-mvp-foundation.json`, `plugins/vibeos/reference/comp/ai-failure-modes.json`, `plugins/vibeos/reference/comp/scorecard-dimensions.json`, `plugins/vibeos/scripts/comp-scorecard.py`, `plugins/vibeos/scripts/comp-red-team.py`, `plugins/vibeos/scripts/comp-dossier.py`
- **Systems affected:** mission intake, Work Order planning, AI failure-mode gauntlet, final scorecard, evidence dossier expectations

## Acceptance Criteria

- [x] AC-1: Mission template captures system invariants
- [x] AC-2: Comp skill instructions require invariant identification
- [x] AC-3: Scorecard includes System Invariants dimension
- [x] AC-4: AI failure mode registry includes system invariant violation
- [x] AC-5: Enterprise foundation blueprint treats invariant proof as non-deferrable where it protects durable state, user data, external side effects, or recovery
- [x] AC-6: Scorecard, red-team, and dossier tests prove invariant evidence is represented

## Test Strategy

- **Scorecard tests:** verify System Invariants dimension exists and passes with required evidence
- **AI failure-mode tests:** registry validates invariant detection mappings and updated mission sections
- **Dossier/red-team tests:** verify invariant evidence is visible in closeout artifacts
- **JSON validation:** all machine-readable references parse cleanly

## Evidence

- [x] `tests/test_comp_scorecard.py`
- [x] `tests/test_ai_failure_modes.py`
- [x] `tests/test_comp_red_team.py`
- [x] `tests/test_comp_dossier.py`
- [x] Full repository validation run
