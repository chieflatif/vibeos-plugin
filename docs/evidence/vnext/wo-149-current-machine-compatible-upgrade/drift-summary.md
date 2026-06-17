# WO-149 Drift Summary

Date: 2026-06-17

## Purpose

Summarize the current-machine evidence that justifies a separate upgrade work order. This is planning evidence only; no upgrades were executed.

## Current Machine State

- macOS: 26.2 on arm64
- GitHub CLI auth: configured for `chieflatif`
- Azure auth: configured for `chief@sidekickgenius.com`
- VibeOS runtime detection: Claude Code available and recommended as primary; Codex available but hooks/subagents not detected in the current detector path
- Docker CLI: present, but Docker daemon was not running during verification

## Missing Baseline Utilities

Reported by `workstation-package.sh check` against the optional workstation package:

- `yq`
- `fd`
- `tree`
- `wget`
- ImageMagick command `magick`

## Outdated Homebrew Formulae

Observed examples from `brew outdated --verbose`:

- `azure-cli` 2.82.0 -> 2.87.0
- `gh` 2.81.0 -> 2.94.0
- `node` 24.3.0 -> 26.3.0
- `uv` 0.9.28 -> 0.11.21
- `render` 2.10 -> 2.20.0
- `ruff` 0.15.0 -> 0.15.17
- `go` 1.25.3 -> 1.26.4
- `cloudflared` 2026.2.0 -> 2026.6.0
- `opentofu` 1.11.5 -> 1.12.2
- `pandoc` 3.8.2.1 -> 3.10
- `poppler` 26.04.0 -> 26.06.0
- Redis and PostgreSQL formulae
- Homebrew Python formulae

## Outdated npm Globals

Observed examples from `npm outdated -g --depth=0`:

- `@anthropic-ai/claude-code` 2.1.177 -> 2.1.179
- `@openai/codex` 0.125.0 -> 0.140.0
- `azure-functions-core-tools` 4.6.0 -> 4.12.0
- `npm` 11.4.2 -> 11.17.0
- `pnpm` 10.30.3 -> 11.7.0
- `typescript` 5.9.3 -> 6.0.3
- `tsx` 4.20.6 -> 4.22.4
- Multiple MCP packages

## Ownership Risks

- Claude Code exists as an unmanaged app/binary, not the `claude-code` cask.
- Codex exists as unmanaged CLI/App, not the `codex` or `codex-app` cask.
- Cursor exists as unmanaged app/binary, not the `cursor` cask.
- Docker Desktop exists as unmanaged app, not the `docker-desktop` cask.
- Azure Functions Core Tools exists as an npm global, while the new baseline prefers the Homebrew `azure/functions` tap.

## Compatibility Risks

- Node has a newer major version available. Active Node projects should be smoke-tested before accepting the upgrade.
- npm globals include major upgrades for `pnpm` and `typescript`; these can affect project scripts and should not be treated as universally safe.
- Tool ownership changes can move binaries on PATH. The upgrade should record `which claude`, `which codex`, `which func`, and `which docker` before and after.
