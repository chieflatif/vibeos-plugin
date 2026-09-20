---
wo: WO-157
title: "Claude Companion Audit and Targeted Correction Verification"
status: In Progress
phase: 49
phase_name: Cross-Identity Audit Efficiency
wo_class: logic-change
write_scope:
  - .claude-plugin/marketplace.json
  - docs/planning/WO-157-claude-companion-audit-verification.md
  - docs/planning/WO-INDEX.md
  - docs/planning/DEVELOPMENT-PLAN.md
  - docs/CLAUDE-COMPANION-AUDIT.md
  - docs/INSTALLATION.md
  - docs/release/2.4.0.md
  - docs/evidence/vnext/generated-inventory.json
  - README.md
  - plugins/vibeos/**
  - pyproject.toml
  - tests/test_claude_companion_audit.py
  - tests/test_profile_install.py
  - vibeos-init.sh
  - vibeos-init-codex.sh
  - docs/evidence/WO-157/**
no_touch:
  - external-projects/**
required_auditors:
  - claude-companion-review
model_policy: frontier-audit
budget_posture:
  token_ceiling: null
  turn_ceiling: 20
  cost_ceiling_usd: 20
---

# WO-157: Claude Companion Audit and Targeted Correction Verification

## Status

`In Progress`

## Objective

Add an opt-in, provider-proven cross-identity review lane for Codex-authored
engineering work. Run one full Claude audit against a frozen work order, scope and
candidate; after fixes, check the original finding IDs and correction diff only.

## Finding

VibeOS says Codex-authored Tier 3/4 work needs a Claude companion audit, but its
generic dispatcher does not call Claude and its closeout validator proves only that a
plausible Markdown report exists. Existing project-specific adapters call Claude but
do not bind the review to exact commits, acceptance-contract bytes or a correction
scope, and their default fix loop repeats the broad audit after every correction.

## Scope

### In scope

- [x] Add an optional profile module that is disabled by default.
- [x] Pin first-party `claude-fable-5-1`, restricted tool-free CLI execution,
      structured output, bounded spend/turns and no session persistence.
- [x] Bind the full audit receipt to the exact work order, acceptance contract,
      scope manifest, base/candidate commits, review snapshot, diff and evidence.
- [x] Bind correction verification to every original finding ID and reject changed
      contracts or corrections outside the original review scope.
- [x] Make work-order closure fail when an enabled receipt is absent, unresolved,
      stale, drifted or lacks exact model/provider provenance.
- [x] Update the build/audit contracts so routine corrections do not trigger another
      full audit.
- [ ] Obtain a real independent Claude review, resolve any findings with targeted
      verification, then publish and selectively adopt the reviewed release.

### Out of scope

- Replacing deterministic gates or the existing internal reasoning-auditor layer.
- Giving the Claude audit tool shell, file, Git, deployment or write authority.
- Automatically sending private or client code to a provider without project opt-in.
- Treating an audit receipt as product, deployment or owner acceptance.

## Impact analysis

The implementation adds `claude-companion-audit.py`, updates
`profile_install.py` and `validate-independent-audit.sh`, and changes the audit/build
skill and protocol text. Installer, audit-contract and profile-install tests cover the
new behavior. README, installation guidance and the dedicated operator document explain
the opt-in boundary; WO-157 evidence retains research, test and live-review receipts.
The same approved scope packages the reviewed additive feature as VibeOS 2.4.0 by
updating live framework metadata under `plugins/vibeos`, `pyproject.toml`, the two
bootstrap entrypoints and generated inventory without rewriting historical release
evidence.

## Acceptance criteria

- [x] AC-1: Default profile installation does not install or activate the module.
- [x] AC-2: Explicit opt-in installs the CLI, skill on all three surfaces, and a
      blocking work-order-close gate.
- [x] AC-3: Full receipts prove exact first-party Fable model use and bind the frozen
      contract, scope, commit, diff, evidence and reviewed-byte snapshot.
- [x] AC-4: Verification covers every original finding and refuses a changed contract
      or correction outside the original scope before a provider call.
- [x] AC-5: A closed receipt becomes invalid if reviewed bytes, its scope manifest,
      report, raw provider result or acceptance contract later drifts.
- [x] AC-6: Mocked provider contract tests exercise the complete full-audit-to-focused-
      verification path, provenance refusal and drift refusal.
- [ ] AC-7: The exact candidate receives a real Claude audit, all material findings
      are closed, the full suite and release gates pass, and published-source readback
      succeeds before project adoption.

## Test strategy

- Unit/contract tests use a fixed fake Claude CLI to prove command boundaries,
  structured contracts, receipts and refusal paths without claiming provider proof.
- Installer tests prove default-off and explicit opt-in behavior on disposable repos.
- The release candidate is committed before the live audit so the provider packet is
  bound to immutable Git bytes.
- A real first-party Claude receipt is required for release; mocked tests cannot
  satisfy AC-7.
