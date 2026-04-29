# WO-092: Comp Validation Generated Artifact Hardening

## Status

`Complete`

## Phase

Phase 20: Comp Validation Hardening

## Objective

Prevent the AI failure-mode validator from treating VibeOS-generated review artifact category labels as project failure markers, while preserving detection for real mission, source, and evidence risks.

## Scope

### In Scope
- [x] Exclude generated red-team and dossier review artifacts from AI failure-marker scanning
- [x] Preserve marker detection in non-generated evidence files
- [x] Add regression coverage for generated review-report false positives

### Out of Scope
- Weakening mission validation requirements
- Ignoring project-authored evidence files
- Changing red-team report categories

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-076 | AI Failure Mode Gate Pack | Complete |
| WO-080 | Red Team Arena | Complete |
| WO-091 | Delivery Scorecard and Evidence Integration | Complete |

## Findings

1. The comp pipeline smoke generated `docs/evidence/RED-TEAM-REPORT.md`.
2. The report intentionally lists `fake completion or demo-only evidence` as a red-team category.
3. `validate-comp-ai-failure-modes.py` scanned that generated report and raised `COMP-AI-FAKE-COMPLETION`, even though the marker was a review category label, not project evidence of fake completion.

## Acceptance Criteria

- [x] AC-1: Generated red-team category labels do not fail the AI failure-mode validator
- [x] AC-2: Real fake-completion markers in non-generated evidence still fail validation
- [x] AC-3: Full comp smoke can run red-team output before AI failure-mode validation without a generated-artifact false positive

## Evidence

- [x] `tests/test_ai_failure_modes.py`
- [x] Comp pipeline smoke
- [x] Full repository validation run
