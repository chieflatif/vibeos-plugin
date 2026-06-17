# macOS Workstation Bootstrap

This package prepares a new Mac for Latif's usual Claude Code, Codex, VibeOS, Python, Node, Docker, Azure, media, and deployment work.

It is deliberately separate from `vibeos-init.sh`. VibeOS is a per-project governance bootstrap. This folder is the machine bootstrap that installs the tools VibeOS and the projects need.

## Run Order

From a cloned copy of this repo, you can use the root wrapper:

```bash
./vibeos-machine-init.sh
./vibeos-machine-init.sh --apply
```

Or run the macOS package directly:

```bash
cd workstation-bootstrap/macos
./install-macos.sh
```

The default run is a dry-run. To install:

```bash
./install-macos.sh --apply
```

Then verify:

```bash
./verify.sh
```

For a current-machine or partially configured new-machine audit without
installing anything:

```bash
./doctor.sh
./doctor.sh --include-auth
```

## What It Installs

- Homebrew packages from `Brewfile`
- Claude Code via the Homebrew cask
- Codex CLI via the Homebrew cask
- Codex app, Cursor, Docker Desktop, and Google Cloud CLI casks
- Node/npm/corepack, uv, Python versions via uv, Azure CLI, Azure Functions Core Tools, GitHub CLI, Render CLI, Stripe CLI, OpenTofu, Redis, PostgreSQL, ffmpeg, poppler, pandoc, and supporting shell tools

Optional npm globals are listed in `optional-npm-globals.txt`. They are not installed unless you pass:

```bash
./install-macos.sh --apply --with-npm-globals
```

If a partially configured Mac already has apps or binaries such as Docker,
Cursor, Claude, or Codex installed outside Homebrew, the installer reports them
as unmanaged and skips those casks. This avoids failing the setup because an app
already exists. If you intentionally want Homebrew to try to own those casks,
rerun with:

```bash
./install-macos.sh --apply --force-cask-ownership
```

## First-Run Manual Steps

These must stay interactive because they involve accounts, licenses, or credentials:

```bash
gh auth login
az login
claude
codex
```

Open Docker Desktop once, accept the license if appropriate, and wait until Docker reports it is running.

## Per-Project VibeOS Install

After cloning a project:

```bash
cd /path/to/project
bash /path/to/vibeos-plugin/vibeos-init.sh
bash /path/to/vibeos-plugin/vibeos-init-codex.sh
bash .vibeos/scripts/detect-runtime-capabilities.sh --project-dir .
```

Read `.vibeos/runtime-capabilities.json` before claiming Claude, Codex, hook, subagent, worktree, or automation support.

## VibeOS Migration Warning

Before using this on a new computer, resolve or consciously work around WO-147. The current 2.2.0 VibeOS work may be ahead of the public marketplace source, so a plain plugin update or public clone may not reproduce this laptop's current runtime until the branch is pushed, tagged, or otherwise bundled.

## Source Notes

The package is based on:

- Active local project manifests sampled in WO-148 evidence
- VibeOS README/CLAUDE/Codex reference requirements
- Official Homebrew, Claude Code, Codex, Docker Desktop, uv, pnpm, Azure CLI, and Azure Functions installation docs checked on 2026-06-17
