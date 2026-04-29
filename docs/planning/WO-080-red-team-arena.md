# WO-080: Red Team Arena

## Status

`Complete`

## Phase

Phase 14: VibOS Comp — Enterprise MVP Battle Harness

## Objective

Add a red-team arena that attacks VibOS Comp outputs with adversarial prompts, malformed inputs, abuse cases, auth bypass attempts, concurrency risks, dependency risks, and fake-completion checks before completion is claimed.

## Scope

### In Scope
- [x] Define adversarial test categories for enterprise MVPs
- [x] Extend red-team auditor prompts for Comp mode
- [x] Add abuse-case and threat-model checks sourced from `MISSION.md`
- [x] Capture red-team findings in `SCORECARD.md`
- [x] Require fix, accepted risk, or follow-up WO for material findings

### Out of Scope
- Full penetration test certification
- Network scanning against production systems
- Exploit generation that targets third-party systems

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-074 | VibOS Comp mission skill | Complete |
| WO-079 | Quality gauntlet | Complete |

## Findings

1. Enterprise reviewers and competition judges will try to break the system, not only use the happy path.
2. Existing red-team auditors are useful but need mission-aware threat model inputs and scorecard output.
3. Red-team findings must reconcile through the same zero-drop discipline as other audits.

## Research & Freshness

- Verified on: 2026-04-29.
- Local sources: red-team auditor agents, security auditor agents, evidence auditor, codex-audit integration.
- External sources: current OWASP and framework-specific security guidance as needed per stack.

## Impact Analysis

- **Files created:** `plugins/vibeos/scripts/comp-red-team.py`, `plugins/vibeos/reference/comp/RED-TEAM-ARENA.md.ref`, `tests/test_comp_red_team.py`
- **Files modified:** quality gate manifest utility references, upgrade metadata, README/CLAUDE counts
- **Systems affected:** pre-completion adversarial review and risk disposition

## Acceptance Criteria

- [x] AC-1: Arena derives abuse cases from mission threat model
- [x] AC-2: Arena runs adversarial checks across input validation, auth, data access, error handling, concurrency, and dependency risks where relevant
- [x] AC-3: Arena records findings with severity, evidence, and recommended fix
- [x] AC-4: Critical/high findings block Comp completion unless explicitly overridden with logged justification
- [x] AC-5: Medium/low findings are fixed or linked to follow-up WOs
- [x] AC-6: Scorecard shows red-team result and unresolved risk state

## Test Strategy

- **Fixture tests:** vulnerable fixture apps with known issues
- **Prompt tests:** verify arena instructions produce structured findings
- **Real-path verification:** run arena against a fixture Comp output
- **Verification command:** execute Comp red-team flow and inspect `SCORECARD.md`

## Implementation Plan

### Step 1: Define Arena
- Create mission-aware adversarial categories
- Expected outcome: red-team scope is repeatable and not generic

### Step 2: Wire Auditors
- Update red-team and security audit paths for Comp mode
- Expected outcome: findings map to scorecard and risk decisions

### Step 3: Reconcile
- Enforce fix/defer/override discipline
- Expected outcome: material adversarial findings cannot be silently dropped

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Comp outputs need mission-aware adversarial categories rather than generic review.
- Test status: Red-team arena reference created.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Critical/high red-team findings must block completion unless explicitly accepted.
- Test status: High-risk fixture added.

### Pre-Commit Audit
- Status: `complete`
- Findings: Missing inputs and high-risk mission terms block; clean passing scorecard artifacts produce reviewed status.
- Test status: `tests/test_comp_red_team.py` passes.

## Evidence

- [x] Arena implemented
- [x] Fixture risks detected
- [x] Red-team evidence output verified
