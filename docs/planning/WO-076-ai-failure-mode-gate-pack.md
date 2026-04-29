# WO-076: AI Failure Mode Gate Pack

## Status

`Complete`

## Phase

Phase 14: VibOS Comp — Enterprise MVP Battle Harness

## Objective

Add a gate pack that directly targets common AI coding failures: stale dependencies, hallucinated APIs, fake completion, mock-only tests, missing observability, weak security boundaries, and incoherent architecture.

## Scope

### In Scope
- [x] Define AI failure mode registry and gate mapping
- [x] Strengthen dependency freshness and API version validation paths
- [x] Add checks for fake/demo-only completion signals
- [x] Add observability baseline validation
- [x] Add architecture coherence checks for generated MVPs
- [x] Add gate manifest entries for Comp mode

### Out of Scope
- Perfect semantic proof of implementation correctness
- Network access during every gate run
- Blocking all advisory findings in low-risk local proofs

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-075 | Enterprise MVP foundation blueprint | Complete |

## Findings

1. AI-generated projects often appear complete while missing real-path behavior, current dependency choices, error handling, or operational visibility.
2. Existing VibeOS gates cover many quality dimensions, but Comp mode needs an explicit AI-failure taxonomy and scorecard mapping.
3. Mid-2026 dependency freshness matters because stale model knowledge can recommend deprecated APIs or package versions.

## Research & Freshness

- Verified on: 2026-04-29.
- Sources to verify during implementation: current package registries or official docs for selected stacks.
- Local sources: `validate-dependency-versions.sh`, `validate-model-versions.sh`, `validate-devmode-fallbacks.sh`, `validate-observability.sh`, `validate-api-contracts.sh`.

## Impact Analysis

- **Files created:** `plugins/vibeos/reference/comp/ai-failure-modes.json`, `plugins/vibeos/scripts/validate-comp-ai-failure-modes.py`, `tests/test_ai_failure_modes.py`
- **Files modified:** gate manifest, quality gate manifest reference, gate runner help, upgrade metadata
- **Systems affected:** gate execution, scorecard scoring, enterprise MVP acceptance

## Acceptance Criteria

- [x] AC-1: Registry lists common AI failure modes with detection method and severity
- [x] AC-2: Comp gate manifest maps each mandatory foundation area to at least one check
- [x] AC-3: Dependency freshness checks require current evidence for high-impact packages
- [x] AC-4: Fake-completion checks prevent fallback-only or mock-only proof from scoring as complete
- [x] AC-5: Observability and security baseline failures are surfaced in scorecard
- [x] AC-6: Advisory versus blocking behavior is configurable by MVP readiness threshold

## Test Strategy

- **Fixture tests:** seed sample projects with known AI failure patterns
- **Gate tests:** verify each seeded pattern is detected or explicitly marked out of scope
- **Real-path verification:** run Comp gate pack against a fixture mission
- **Verification command:** `bash .vibeos/scripts/gate-runner.sh comp_gauntlet --project-dir <fixture>`

## Implementation Plan

### Step 1: Define Registry
- Capture failure modes, examples, severity, and checks
- Expected outcome: explicit AI risk map

### Step 2: Wire Gates
- Add or adapt deterministic checks for the highest-value failure modes
- Expected outcome: repeatable quality enforcement

### Step 3: Score Results
- Send gate output into the Comp scorecard
- Expected outcome: failures are visible to users and reviewers

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Comp mode needs explicit AI failure taxonomy so quality claims are judged against known model failure modes.
- Test status: Registry schema covered.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Highest-value deterministic check is validating mission/foundation evidence and scanning for demo-only, mock-only, placeholder, and fallback-only markers.
- Test status: Validator fixture tests added.

### Pre-Commit Audit
- Status: `complete`
- Findings: `comp_gauntlet` is documented in the manifest reference and dry-runs through the gate runner.
- Test status: `tests/test_ai_failure_modes.py` passes.

## Evidence

- [x] Registry complete
- [x] Gate tests pass
- [x] Fixture failures detected
- [x] Documentation updated
