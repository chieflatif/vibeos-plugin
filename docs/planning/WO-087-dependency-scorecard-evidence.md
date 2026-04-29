# WO-087: Dependency Scorecard and Evidence Integration

## Status

`Complete`

## Phase

Phase 17: Dependency Intelligence & Current Evidence

## Objective

Promote Dependency Intelligence into enterprise foundation requirements, AI failure-mode detection, scorecards, integration evidence, red-team review, and closeout dossiers so stale, incompatible, or unaudited dependencies cannot hide behind passing application behavior.

## Scope

### In Scope
- [x] Add Dependency Intelligence section to the mission template
- [x] Add dependency intelligence expectations to Comp mission skills
- [x] Add dependency intelligence checkpoints to Comp planning and merge-readiness expectations
- [x] Add Dependency Intelligence scorecard dimension
- [x] Add stale/incompatible dependency AI failure mode
- [x] Add dependency intelligence evidence to integration evidence, red-team review, and evidence dossier

### Out of Scope
- Selecting default stacks for every possible ecosystem
- Replacing current-source research inside target projects
- Certifying package safety beyond available evidence and audit output

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-086 | Dependency Intelligence Auditor and Gate | Complete |

## Findings

1. Dependency decisions are architectural decisions because they shape runtime compatibility, deployment path, security posture, and maintainability.
2. Non-technical users need dependency evidence surfaced in plain language because stale dependency choices can look like obscure technical errors later.
3. Scorecards and dossiers need dependency intelligence so reviewers can distinguish a serious enterprise MVP from a prototype assembled on outdated defaults.

## Research & Freshness

- Verified on: 2026-04-29.
- Local sources: Comp charter, mission template, foundation blueprint, AI failure mode registry, scorecard generator, red-team and dossier scripts.
- External sources: none required for harness wiring; target projects must attach current dependency source evidence.

## Impact Analysis

- **Files modified:** `plugins/vibeos/reference/product/MISSION.md.ref`, `plugins/vibeos/reference/comp/enterprise-mvp-foundation.json`, `plugins/vibeos/reference/comp/ai-failure-modes.json`, `plugins/vibeos/reference/comp/scorecard-dimensions.json`, `plugins/vibeos/scripts/comp-scorecard.py`, `plugins/vibeos/scripts/comp-red-team.py`, `plugins/vibeos/scripts/comp-dossier.py`, `plugins/vibeos/scripts/comp-plan.py`, `plugins/vibeos/scripts/comp-integration-check.py`
- **Systems affected:** mission intake, Work Order planning, AI failure-mode gauntlet, final scorecard, integration evidence, evidence dossier expectations

## Acceptance Criteria

- [x] AC-1: Mission template captures dependency intelligence
- [x] AC-2: Comp skill instructions require current dependency evidence and compatibility reasoning
- [x] AC-3: Scorecard includes Dependency Intelligence dimension
- [x] AC-4: AI failure mode registry includes stale or incompatible dependency choices
- [x] AC-5: Enterprise foundation blueprint treats dependency intelligence as non-deferrable when high-impact packages are added or upgraded
- [x] AC-6: Scorecard, red-team, integration, and dossier tests prove dependency intelligence evidence is represented

## Test Strategy

- **Scorecard tests:** verify Dependency Intelligence dimension exists and passes with required evidence
- **AI failure-mode tests:** registry validates dependency detection mappings and updated mission sections
- **Dossier/red-team/integration tests:** verify dependency evidence is visible in closeout artifacts
- **JSON validation:** all machine-readable references parse cleanly

## Evidence

- [x] `tests/test_comp_scorecard.py`
- [x] `tests/test_ai_failure_modes.py`
- [x] `tests/test_comp_red_team.py`
- [x] `tests/test_comp_integration.py`
- [x] `tests/test_comp_dossier.py`
- [x] Full repository validation run
