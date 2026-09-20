---
wo: WO-156
title: "Opt-In Local Engineering Intake and Triage"
status: Complete
phase: 48
phase_name: Local Model Task Routing
wo_class: logic-change
write_scope:
  - docs/planning/WO-156-local-engineering-intake-triage.md
  - docs/planning/WO-INDEX.md
  - docs/planning/DEVELOPMENT-PLAN.md
  - docs/architecture/profile-driven-install.md
  - docs/LOCAL-ENGINEERING-INTAKE.md
  - README.md
  - plugins/vibeos/scripts/local-engineering-intake.py
  - plugins/vibeos/scripts/profile_install.py
  - plugins/vibeos/quality-gate-manifest.json
  - tests/test_local_engineering_intake.py
  - tests/test_profile_install.py
  - docs/evidence/WO-156/**
no_touch:
  - external-projects/**
required_auditors:
  - correctness-auditor
  - security-auditor
  - test-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-156: Opt-In Local Engineering Intake and Triage

## Status

`Complete`

## Phase

Phase 48: Local Model Task Routing

## Objective

Add a reusable, disabled-by-default VibeOS module that can send bounded engineering
artifacts to a loopback-only OpenAI-compatible local model for structured intake and
triage, validate the returned evidence, retry once, and then return control to the
parent runtime without granting the local worker implementation or acceptance
authority.

## Finding

Matched local testing showed that a 120B open-weight model can classify routine CI,
test, lint, build, dependency, static-analysis, and release-receipt artifacts when the
assignment and output contract are narrow. It remains materially slower and less
reliable than the frontier coding worker for implementation work. VibeOS currently has
no reusable lane that captures that useful boundary, so projects must either hand-roll
unsafe routing or continue spending frontier-model tokens on mechanically checkable
intake work.

## Scope

### In Scope

- [x] Add a profile-controlled `local-engineering-intake` module that is absent from
      default installs and requires an explicit enabled configuration.
- [x] Install a stdlib-only CLI with `schema`, `probe`, and `run` commands; allow only
      loopback endpoints and a closed set of low-consequence task types.
- [x] Require exact JSON output, artifact-grounded evidence quotes, bounded inputs and
      outputs, a maximum of two attempts, and an explicit `fallback_required` receipt.
- [x] Generate the same narrowly triggered skill contract for Codex, Claude, and Cursor.
- [x] Prove default-off behavior, profile installation, accepted output, invalid-output
      retry, fallback, prompt-injection refusal, and remote-endpoint refusal.
- [x] Document configuration, authority limits, operating behavior, and verification.

### Out of Scope

- Local-model code writing, source edits, test authorship, planning, acceptance, audit
  sign-off, Git operations, deployment, or any other external effect.
- Automatic cloud fallback. The current parent decides whether and how to continue.
- Model hosting, model downloads, credentials, or LM Studio lifecycle management.
- Replacing deterministic parsers for artifacts that already have a reliable parser.

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Profile-driven installer | Reusable install boundary | Complete |
| Local-model matched comparison | Task qualification evidence | Complete |
| Loopback OpenAI-compatible endpoint | Optional operator runtime | External, probed at use time |

## Impact Analysis

- **Files created:** `plugins/vibeos/scripts/local-engineering-intake.py`,
  `tests/test_local_engineering_intake.py`, `docs/LOCAL-ENGINEERING-INTAKE.md`, and
  the `docs/evidence/WO-156/` verification receipt.
- **Files modified:** `plugins/vibeos/scripts/profile_install.py`,
  `tests/test_profile_install.py`, `plugins/vibeos/quality-gate-manifest.json`,
  `README.md`, `docs/architecture/profile-driven-install.md`, and the planning index.
- **Systems affected:** profile-installed VibeOS project surfaces only when a project
  explicitly enables this module; existing installs remain unchanged.

## Acceptance Criteria

- [x] AC-1: An ordinary profile does not install the CLI or skill and lists the module
      as skipped.
- [x] AC-2: An explicit valid profile installs the CLI and all three skill surfaces,
      while mismatched or unsafe configuration fails during analysis.
- [x] AC-3: The CLI rejects non-loopback endpoints, unsupported task types, oversized
      input, prompt-injection signals, and output evidence not present in the artifact.
- [x] AC-4: A schema-valid local response returns `accepted`; a first invalid response
      is retried once; two failures return `fallback_required` without a third call.
- [x] AC-5: The local worker has no file, shell, Git, deployment, approval, or cloud
      execution capability, and automatic fallback is not implemented.
- [x] AC-6: Focused tests, full tests, work-order lint/index validation, and the canonical
      pre-commit gate pass from a clean isolated worktree.

## Test Strategy

- **Unit tests:** configuration, request schema, result schema, evidence grounding,
  injection detection, and endpoint validation.
- **Integration tests:** an in-process loopback OpenAI-compatible fixture exercises
  probe, accepted output, one retry, and bounded fallback.
- **Install tests:** analyze/apply a temporary project with the module disabled and
  enabled, then run the installed active-surface audit.
- **Real-path verification:** install into a disposable project and call the installed
  CLI against the loopback fixture through its public command-line interface.
- **Verification command:** `python3 -m pytest tests` followed by the repository's
  canonical pre-commit gate.

## Implementation Plan

### Step 1: Add the closed local intake runtime

- Implement configuration, loopback transport, prompt isolation, response validation,
  retry ceiling, and structured receipts in one stdlib-only CLI.
- Expected outcome: no unvalidated model prose reaches the parent as an accepted result.

### Step 2: Add profile installation and skill routing

- Add a disabled-by-default optional module and generate its precise skill contract only
  for opted-in projects.
- Expected outcome: existing project installs do not change; opted-in projects receive
  the same authority boundary on every supported surface.

### Step 3: Prove and document the installed behavior

- Exercise positive, failure, injection, endpoint, and installer paths; record evidence
  and update operator documentation.
- Expected outcome: the module is usable without implying that the local model is an
  implementer, auditor, or acceptance authority.

## Audit Checkpoints

### Planning Audit

- Status: `complete`
- Findings: Scope is limited to structured intake; cloud fallback and effectful work are
  explicitly excluded.
- Test status: Matched comparison and five-case triage fixture already complete.

### Pre-Implementation Audit

- Status: `complete`
- Findings: Reuse the profile installer and OpenAI-compatible local endpoint; no new
  router service or external dependency is warranted.
- Test status: Existing profile installer baseline is green.

### Pre-Commit Audit

- Status: `complete`
- Findings: Four boundary gaps found during correctness, security, and test-quality
  review were corrected before closeout; no blocking or deferred finding remains. The
  exact review record and fresh-context limitation are in
  `docs/evidence/WO-156/audit-report.md`.
- Test status: 28 focused tests plus 13 subtests passed; 354 product tests plus 70
  subtests passed; canonical pre-commit gates passed 9 with 1 advisory skip and 0
  failures.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated
- [x] Audit findings reconciled
