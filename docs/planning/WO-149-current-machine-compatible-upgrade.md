---
wo: WO-149
title: "Current Machine Compatible Toolchain Upgrade"
status: Draft
phase: 47
phase_name: Workstation Bootstrap
wo_class: tooling
write_scope:
  - docs/planning/WO-149-current-machine-compatible-upgrade.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/wo-149-current-machine-compatible-upgrade/**
no_touch:
  - /Users/latifhorst/Joan4U/**
  - /Users/latifhorst/pipeline-rebel-cowork/**
  - /Users/latifhorst/revenue-team-os/**
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/meeting-sidekick/**
  - ~/.ssh/**
  - ~/.azure/**
  - ~/.config/gh/**
  - ~/.codex/**
  - ~/.claude/**
required_auditors:
  - evidence-auditor
  - security-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-149: Current Machine Compatible Toolchain Upgrade

## Status

`Draft` - upgrade work order created from current-machine drift evidence. No upgrade commands have been executed under this WO.

## Phase

Phase 47: Workstation Bootstrap

## Objective

Upgrade this current Mac to the latest compatible versions of the development toolchain while preserving project compatibility, account state, and tool ownership boundaries.

## Source Findings

1. `workstation-package.sh check` shows the current machine has the core tool spine installed, but several baseline utilities are missing: `yq`, `fd`, `tree`, `wget`, and ImageMagick's `magick`.
2. `brew outdated --verbose` reports many outdated Homebrew formulae, including `azure-cli`, `gh`, `node`, `uv`, `render`, `ruff`, `go`, `cloudflared`, `opentofu`, `pandoc`, `poppler`, Redis, PostgreSQL, and Python formulae.
3. `npm outdated -g --depth=0` reports outdated global packages, including `@anthropic-ai/claude-code`, `@openai/codex`, `azure-functions-core-tools`, `npm`, `pnpm`, `typescript`, `tsx`, and several MCP packages.
4. Claude Code, Codex, Cursor, and Docker Desktop are present but not Homebrew cask-managed. The upgrade must not silently convert app ownership unless explicitly approved.
5. Azure Functions Core Tools is present as an npm global, while the new bootstrap prefers the official Homebrew tap. The upgrade must choose one owner before changing `func`.
6. Node currently reports `v24.3.0`. Homebrew offers a newer major version. Since active repos include Node projects and at least one project declares Node `>=24`, Node major upgrades require project smoke tests, not a blind upgrade claim.

## Scope

### In Scope
- [ ] Capture a pre-upgrade doctor report.
- [ ] Decide ownership for duplicated or unmanaged tools: Claude Code, Codex CLI/App, Cursor, Docker Desktop, Google Cloud CLI, Azure Functions Core Tools.
- [ ] Install missing baseline formulae from the workstation bootstrap where low risk.
- [ ] Upgrade Homebrew formulae that are compatible with active projects.
- [ ] Upgrade npm globals only after deciding whether they should remain npm-managed.
- [ ] Install uv-managed Python 3.10 and 3.11 if still needed for project compatibility.
- [ ] Run post-upgrade verification and VibeOS runtime capability detection.
- [ ] Run focused smoke checks for representative projects without modifying their source.

### Out of Scope
- Copying, exporting, or rotating credentials.
- Reinstalling macOS or migrating accounts.
- Converting unmanaged GUI apps to Homebrew casks without approval.
- Upgrading project dependencies inside repo lockfiles.
- Running production deploys, cloud mutations, or paid provider changes.
- Cleaning unrelated git worktrees.

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-148 | Optional workstation package harness | Complete |
| Docker Desktop | First-run/daemon check | CLI present; daemon not running in latest check |
| Active project smoke commands | Read-only verification | Must be selected before upgrade completion |

## Impact Analysis

- **Files created:** this WO and `docs/evidence/vnext/wo-149-current-machine-compatible-upgrade/*`
- **Files modified:** generated `docs/planning/WO-INDEX.md`
- **Systems affected:** local Mac developer toolchain only

## Acceptance Criteria

- [ ] AC-1: Pre-upgrade doctor report saved under `docs/evidence/vnext/wo-149-current-machine-compatible-upgrade/`.
- [ ] AC-2: Tool ownership decision recorded for Claude Code, Codex, Cursor, Docker, Google Cloud CLI, and Azure Functions Core Tools.
- [ ] AC-3: Missing baseline command-line tools are installed or explicitly deferred with reason.
- [ ] AC-4: Homebrew formula upgrades complete without unresolved brew doctor or bundle errors relevant to the baseline.
- [ ] AC-5: npm global upgrades complete or are deferred because ownership moved to Homebrew/native installers.
- [ ] AC-6: `workstation-package.sh verify` passes with no hard failures after upgrade.
- [ ] AC-7: VibeOS runtime detection succeeds after upgrade and records the actual Claude/Codex capabilities.
- [ ] AC-8: Representative project smoke checks pass or blockers are documented with rollback/defer decisions.

## Test Strategy

- **Preflight:** `bash plugins/vibeos/scripts/workstation-package.sh check`
- **Install/upgrade plan only:** inspect `brew outdated --verbose`, optional `workstation_check`, and `npm outdated -g --depth=0`
- **Post-upgrade:** `bash plugins/vibeos/scripts/workstation-package.sh verify`
- **VibeOS runtime:** `bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .`
- **Project smoke candidates:**
  - `Joan4U`: Python test/gate smoke and `control_plane/web` npm smoke
  - `meeting-sidekick`: `uv`/pytest or Makefile smoke
  - `latifhorstweb`: Docker Compose config check plus frontend npm smoke
  - `pipeline-rebel-cowork`: service `uv` smoke and video npm script smoke

## Implementation Plan

### Step 1: Snapshot Current State
- Run `workstation-package.sh check` and save output.
- Save `brew outdated --verbose`, `npm outdated -g --depth=0`, `uv python list --only-installed`, `claude --version`, `codex --version`, and VibeOS runtime detection.

### Step 2: Ownership Decisions
- Keep unmanaged apps as unmanaged unless there is a concrete reason to convert.
- Choose whether `func` should remain npm-managed or move to `azure/functions/azure-functions-core-tools@4`.
- Decide whether Codex/Claude should be updated through npm/native/Homebrew, avoiding duplicate binaries on PATH.

### Step 3: Low-Risk Baseline Installs
- Install missing shell utilities from the optional workstation package formula list: `yq`, `fd`, `tree`, `wget`, and `imagemagick`.
- Install uv Python 3.10 and 3.11 if compatibility still requires them.

### Step 4: Compatible Upgrades
- Upgrade formulae in batches, starting with dev tooling and avoiding major runtime jumps until smoke-tested.
- Treat Node major upgrade separately; verify active Node projects before accepting.
- Upgrade npm globals only after ownership decisions.

### Step 5: Verification and Closeout
- Run `workstation-package.sh verify`, runtime detection, and selected project smokes.
- Record remaining defers, exact versions, and rollback notes.

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Findings: -
- Test status: -

### Pre-Implementation Audit
- Status: `pending`
- Findings: -
- Test status: -

### Pre-Commit Audit
- Status: `pending`
- Findings: -
- Test status: -

## Evidence

- [x] Drift evidence summarized
- [ ] Pre-upgrade snapshot saved
- [ ] Ownership decisions recorded
- [ ] Upgrade commands executed
- [ ] Post-upgrade verification saved
- [ ] Project smoke evidence saved
