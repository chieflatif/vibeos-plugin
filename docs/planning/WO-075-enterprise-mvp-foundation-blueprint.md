# WO-075: Enterprise MVP Foundation Blueprint

## Status

`Complete`

## Phase

Phase 14: VibOS Comp — Enterprise MVP Battle Harness

## Objective

Define the default enterprise MVP foundation that every VibOS Comp mission must include unless the mission explicitly and safely scopes it out.

## Scope

### In Scope
- [x] Define baseline controls for frontend, backend, data, auth, configuration, testing, observability, deployment, security, and performance
- [x] Add stack-specific blueprint variants for common TypeScript/Node, Python/FastAPI, and frontend app shapes
- [x] Define what may be skipped for a local-only proof and what may not be skipped for enterprise design partner readiness
- [x] Connect blueprint requirements to gates and scorecard fields

### Out of Scope
- Mandating a single tech stack
- Building starter templates for every framework
- Replacing project-specific architecture decisions

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-074 | VibOS Comp mission skill | Complete |

## Findings

1. MVPs fail commercially when they are small in feature scope and also weak in engineering foundation.
2. Many foundation items are inexpensive when added early and expensive when retrofitted later: auth boundaries, env management, data migrations, logging, tests, health checks, and CI.
3. AI agents routinely omit these foundations unless they are explicit acceptance criteria.

## Research & Freshness

- Verified on: 2026-04-29.
- Local sources: existing VibeOS quality gates, VC technical due diligence audit dimensions, engineering principles, and quality manifest.
- External sources: current framework/library docs must be checked per stack choice during mission execution.

## Impact Analysis

- **Files created:** `plugins/vibeos/reference/comp/ENTERPRISE-MVP-FOUNDATION.md.ref`, `plugins/vibeos/reference/comp/enterprise-mvp-foundation.json`, stack variant JSON files, `tests/test_comp_blueprint.py`
- **Files modified:** Comp mission skills, quality gate manifest references, README/install docs
- **Systems affected:** mission acceptance criteria, swarm planning, scorecard quality dimensions

## Acceptance Criteria

- [x] AC-1: Blueprint defines mandatory enterprise MVP baseline fields
- [x] AC-2: Blueprint maps each baseline field to verification evidence
- [x] AC-3: Blueprint distinguishes local proof, design-partner MVP, and production-ready thresholds
- [x] AC-4: Blueprint integrates with scorecard and quality gauntlet
- [x] AC-5: Blueprint allows safe scope reduction without hiding missing foundation work

## Test Strategy

- **Static validation:** verify every blueprint requirement maps to a gate, audit, or evidence field
- **Fixture missions:** apply blueprint to at least two sample MVP prompts
- **Real-path verification:** generated mission and scorecard include all mandatory baseline fields
- **Verification command:** run blueprint validation script or checklist against fixture artifacts

## Implementation Plan

### Step 1: Define Baseline
- Write the foundation blueprint and threshold taxonomy
- Expected outcome: clear minimum standard for enterprise MVP readiness

### Step 2: Map To Evidence
- Link each foundation requirement to tests, gates, audits, or manual evidence
- Expected outcome: no unverified quality claims

### Step 3: Integrate
- Wire blueprint into mission, planning, quality gauntlet, and scorecard
- Expected outcome: Comp missions inherit the baseline automatically

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Comp missions need a machine-readable foundation baseline so agents cannot treat enterprise MVP as a thin demo.
- Test status: Blueprint schema and domains defined.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Requirements must map to existing gates or evidence fields to avoid unverifiable standards.
- Test status: Gate mapping test added.

### Pre-Commit Audit
- Status: `complete`
- Findings: Stack variants are parseable and the Comp skill reads the blueprint before drafting missions.
- Test status: `tests/test_comp_blueprint.py` and `tests/test_comp_skill.py` pass.

## Evidence

- [x] Blueprint complete
- [x] Stack variants verified
- [x] Documentation updated
