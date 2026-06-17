---
wo: WO-148
title: "Optional Workstation Package Harness"
status: Complete
phase: 47
phase_name: Workstation Bootstrap
wo_class: harness
write_scope:
  - README.md
  - vibeos-machine-init.sh
  - plugins/vibeos/quality-gate-manifest.json
  - plugins/vibeos/scripts/workstation-package.sh
  - tests/test_gate_runner.py
  - tests/test_codex_bootstrap.py
  - docs/planning/WO-148-new-machine-bootstrap-package.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - docs/evidence/vnext/wo-148-new-machine-bootstrap-package/**
no_touch:
  - /Users/latifhorst/Joan4U/**
  - /Users/latifhorst/pipeline-rebel-cowork/**
  - /Users/latifhorst/revenue-team-os/**
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/meeting-sidekick/**
required_auditors:
  - evidence-auditor
  - security-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-148: Optional Workstation Package Harness

## Status

`Complete` - the workstation package is now part of the VibeOS harness as an optional checker/installer utility. Clean-machine `--apply` execution is still first-use operational evidence, not claimed by this WO.

## Phase

Phase 47: Workstation Bootstrap

## Objective

Publish the new-machine tool setup as an optional VibeOS harness capability, not as a side package. A GitHub checkout should expose a simple root wrapper, while installed projects receive the same checker through `.vibeos/scripts/workstation-package.sh`.

## Source Findings

1. VibeOS is primarily a per-project governance bootstrap; workstation package management must remain optional.
2. A top-level `workstation-bootstrap/` directory made the setup look like a separate side project rather than part of the harness.
3. The harness already distributes `plugins/vibeos/scripts` into installed projects for both Claude/Cursor and Codex surfaces.
4. Runtime detection must remain local and evidence-backed; the package cannot claim Claude/Codex parity or fixed orchestration support.
5. Partial machines may already contain Claude, Codex, Cursor, or Docker outside Homebrew cask ownership, so package checks must distinguish unmanaged equivalents from missing tools.

## Scope Completed

- [x] Replace the side-package directory with `plugins/vibeos/scripts/workstation-package.sh`.
- [x] Keep `vibeos-machine-init.sh` as a thin root convenience wrapper that delegates to the harness utility.
- [x] Add an optional `workstation_check` phase to `plugins/vibeos/quality-gate-manifest.json`.
- [x] Register the utility in the manifest `utility_scripts` list.
- [x] Preserve dry-run-first install behavior; `install --apply` is required for package mutation.
- [x] Preserve checker and verifier behavior without copying credentials or account sessions.
- [x] Add tests proving the optional gate phase is registered and Codex bootstrap installs the utility.
- [x] Update README language so the public story is one harness, not a side package.

## Out of Scope

- Running package installation on this current machine.
- Claiming a clean new Mac has completed `--apply` successfully.
- Storing or copying secrets, API keys, OAuth tokens, SSH keys, browser sessions, or cloud credentials.
- Upgrading the current Mac toolchain; that remains WO-149.
- Resolving WO-147's marketplace/plugin publication gap.
- Enabling Claude agent teams or Codex subagents by default.

## Public Entry Points

```bash
./vibeos-machine-init.sh
./vibeos-machine-init.sh --apply
```

Installed-project harness utility:

```bash
bash .vibeos/scripts/workstation-package.sh check
bash .vibeos/scripts/workstation-package.sh install
bash .vibeos/scripts/workstation-package.sh install --apply
bash .vibeos/scripts/workstation-package.sh verify
```

Optional gate-runner phase:

```bash
bash .vibeos/scripts/gate-runner.sh workstation_check --continue-on-failure
```

## Acceptance Criteria

- [x] AC-1: Workstation package logic lives under `plugins/vibeos/scripts`, not a separate top-level package tree.
- [x] AC-2: Root `vibeos-machine-init.sh` dry-runs by delegating to `workstation-package.sh install`.
- [x] AC-3: `workstation-package.sh check` audits current machine state without installing.
- [x] AC-4: `workstation-package.sh install` is dry-run by default and requires `--apply` before mutation.
- [x] AC-5: `workstation-package.sh verify` checks required tools and reruns local runtime capability detection when available.
- [x] AC-6: `workstation_check` appears as an optional manifest phase and is not included in default pre-commit/session gates.
- [x] AC-7: Codex bootstrap installs the utility into `.vibeos/scripts`.
- [x] AC-8: The package writes no secrets and copies no account sessions.

## Verification

- `bash -n vibeos-machine-init.sh plugins/vibeos/scripts/workstation-package.sh`
- `bash plugins/vibeos/scripts/workstation-package.sh install`
- `bash plugins/vibeos/scripts/workstation-package.sh check`
- `bash plugins/vibeos/scripts/gate-runner.sh workstation_check --framework-dir plugins/vibeos --project-dir . --manifest plugins/vibeos/quality-gate-manifest.json --dry-run`
- `python3 -m pytest tests/test_gate_runner.py tests/test_codex_bootstrap.py`
- `python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .`
- `git diff --check`

## Evidence

- [x] Investigation recorded.
- [x] Harness integration implemented.
- [x] Optional gate registration tested.
- [x] Bootstrap install-surface test updated.
- [x] Local dry-run and checker evidence recorded.
- [ ] Clean-machine `install --apply` first-use evidence remains pending.
