# Profile-Driven Install Implementation Plan

Status: active source remediation plan

## Phase 1: Plan-First Installer

- Add `vibeos analyze --target <repo> --source <source>`.
- Detect target canon, protected files, validators, and existing VibeOS surfaces.
- Require or synthesize a project profile before active surfaces are generated.
- Emit `.vibeos/install-plan.json` with enabled modules, skipped modules, active
  gates, dormant payload, overwrite actions, and post-install checks.

Tests:

- analyze writes all required plan sections.
- minimal and product-engineering plans list dormant reference payload as skipped.

## Phase 2: Profile-Generated Active Surfaces

- Add `vibeos apply --plan <plan>`.
- Generate Codex skills, Markdown role contracts, TOML agents, hooks, config,
  gate manifest, project profile, install lock, and active-surface audit from
  the same profile-aware role/template source.
- Keep generic prompt scanning, intent routing, and commit-message enforcement
  opt-in.

Tests:

- Codex TOML agents mention the target project and use the same profile source
  as Markdown contracts.
- default hooks omit `UserPromptSubmit` governance scanning.
- default plan omits commit-message enforcement.

## Phase 3: Active-Surface Audit

- Generate `.vibeos/scripts/vibeos-active-surface-audit.py`.
- Fail on generic active instructions, rejected generic paths, dormant payload
  references, writable read-only auditors, and non-opt-in prompt/commit hooks.

Tests:

- audit passes immediately after a profile-generated install.
- audit fails after injecting generic VibeOS operating-truth language into an
  active surface.

## Phase 4: Upgrade Safety

- Stamp generated files with template/source/profile hashes.
- Preserve locally customized generated files.
- Write proposed upgraded content to `.vibeos/merge-conflicts/` instead of
  overwriting local edits.
- Preserve the legacy `vibeos-init-codex.sh --upgrade` no-overwrite behavior
  while the new flow becomes canonical.

Tests:

- unchanged generated files update cleanly.
- locally modified generated files are preserved with a merge-conflict candidate.
- existing bootstrap upgrade preservation tests still pass.
