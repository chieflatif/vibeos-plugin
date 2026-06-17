---
wo: WO-148
title: "New Machine Bootstrap Package"
status: Draft
phase: 47
phase_name: Workstation Bootstrap
wo_class: tooling
write_scope:
  - README.md
  - vibeos-machine-init.sh
  - docs/planning/WO-148-new-machine-bootstrap-package.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/wo-148-new-machine-bootstrap-package/**
  - workstation-bootstrap/macos/**
no_touch:
  - /Users/latifhorst/Joan4U/**
  - /Users/latifhorst/pipeline-rebel-cowork/**
  - /Users/latifhorst/revenue-team-os/**
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/meeting-sidekick/**
required_auditors:
  - evidence-auditor
  - security-auditor
model_policy: drafting
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-148: New Machine Bootstrap Package

## Status

`Draft` - investigation and scaffold created. This WO is not complete until the package is tested on a clean macOS account or new Mac and any install failures are captured as evidence.

## Phase

Phase 47: Workstation Bootstrap

## Objective

Create a reviewable macOS bootstrap package, callable from a GitHub checkout of VibeOS, that gets Latif's typical Claude Code, Codex, Python, Node, Docker, Azure, media, deployment, and VibeOS workflows running on a new machine without pretending the per-project VibeOS installer is the same thing as workstation provisioning.

## Source Findings

1. VibeOS is currently a per-project governance bootstrap. It installs `.claude/`, `.codex/`, `.agents/`, `.vibeos/`, and project docs into target repos, but it does not install Homebrew, Docker, Node, Python, cloud CLIs, or editor apps.
2. The current VibeOS 2.2.0 development branch has a known publish/install integrity gap in WO-147. A new machine that only pulls the public marketplace source may not reproduce the current local VibeOS state until that gap is resolved.
3. Sampling active local projects showed recurring Python, Node/npm, Docker, Azure Functions, Render, media, and document/PDF tooling. There was no recurring evidence that Go, Rust, Java, or Kubernetes should be mandatory for the first bootstrap.
4. Runtime detection on this machine reports Claude Code as the primary runtime and Codex as present but without detected hooks or subagents. A new machine must rerun local capability detection after install.

## Scope

### In Scope
- [x] Record an evidence-backed investigation summary.
- [x] Add a macOS Brewfile for common tools and apps.
- [x] Add an install script that defaults to dry-run and requires `--apply` before installing.
- [x] Add a current-machine doctor script and partial-install handling for unmanaged apps/binaries.
- [x] Add a verification script that checks the installed tool spine and reruns VibeOS runtime detection when this repo is present.
- [x] Add a top-level `vibeos-machine-init.sh` wrapper so a fresh GitHub checkout exposes the machine bootstrap path directly.
- [x] Document the new Mac bootstrap path in the root README.
- [x] Document post-install sign-in and per-project VibeOS install steps.

### Out of Scope
- Running the package on this current machine.
- Storing or copying secrets, API keys, OAuth tokens, SSH private keys, browser sessions, or cloud credentials.
- Re-running all project dependency installs across every repo.
- Resolving WO-147's plugin publication gap.
- Enabling Claude agent teams or Codex subagents by default.
- Creating an enterprise MDM package.

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-147 | Plugin install integrity before public VibeOS reproduction | Draft |
| Homebrew | macOS package manager | Official install source verified |
| Claude Code | AI coding runtime | Official install source verified |
| Codex CLI/App | AI coding runtime | Official install source verified |
| Docker Desktop | Container runtime | Official install source verified |

## Impact Analysis

- **Files created:** this WO, `vibeos-machine-init.sh`, `docs/evidence/vnext/wo-148-new-machine-bootstrap-package/investigation.md`, `docs/evidence/vnext/wo-148-new-machine-bootstrap-package/verification.md`, and `workstation-bootstrap/macos/*`
- **Files modified:** `README.md`, generated WO index refresh if accepted
- **Systems affected:** developer workstation setup only; no runtime project code and no production resources

## Acceptance Criteria

- [ ] AC-1: On a clean macOS machine or clean user account, `./install-macos.sh --apply` installs the declared Brewfile tools or reports a precise failure.
- [ ] AC-1a: From a fresh GitHub checkout, `./vibeos-machine-init.sh` dry-runs and `./vibeos-machine-init.sh --apply` delegates to the macOS package.
- [ ] AC-2: `./verify.sh` passes for required tools after first-run app launches and sign-ins are completed.
- [ ] AC-2a: `./doctor.sh` distinguishes missing tools, outdated tools, Homebrew-managed casks, and unmanaged equivalents on a partially configured machine.
- [ ] AC-3: Docker Desktop is opened, license accepted where required, and `docker info` succeeds.
- [ ] AC-4: Claude Code and Codex both start interactively and authenticate successfully.
- [ ] AC-5: A test repo can run `vibeos-init.sh`, `vibeos-init-codex.sh`, and `.vibeos/scripts/detect-runtime-capabilities.sh`.
- [ ] AC-6: No secrets or credentials are written into the package.

## Test Strategy

- **Static:** `bash -n vibeos-machine-init.sh workstation-bootstrap/macos/install-macos.sh workstation-bootstrap/macos/verify.sh workstation-bootstrap/macos/doctor.sh`
- **Dry-run:** `workstation-bootstrap/macos/install-macos.sh`
- **Doctor:** `workstation-bootstrap/macos/doctor.sh`
- **Local verification:** `workstation-bootstrap/macos/verify.sh` on the current machine, accepting that it may surface local gaps instead of proving new-machine success
- **Real-path verification:** run `install-macos.sh --apply` on the new Mac, then run `verify.sh`

## Implementation Plan

### Step 1: Review Package Contents
- Inspect the Brewfile and scripts.
- Decide whether Claude should use stable `claude-code` or latest `claude-code@latest`.

### Step 2: Run On New Mac
- Install Xcode Command Line Tools if prompted.
- Run `./install-macos.sh --apply` from this repo.
- Open Docker Desktop, Cursor, Claude Code, and Codex once.

### Step 3: Authenticate
- Run `gh auth login`, `az login`, `claude`, and `codex`.
- Do not script credential transfer.

### Step 4: Install VibeOS Per Project
- Clone or restore project repos.
- Run `vibeos-init.sh` and `vibeos-init-codex.sh` in each project that should use VibeOS governance.
- Run VibeOS runtime detection in each project after install.

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

- [x] Investigation recorded
- [x] Scaffold created
- [x] Local dry-run and static verification recorded
- [x] Current-machine upgrade drift investigated
- [ ] Clean-machine install tested
- [ ] Verification script passes after first-run app setup
- [ ] VibeOS per-project install tested on a sample repo
