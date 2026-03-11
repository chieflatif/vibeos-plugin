# VibeOS Plugin — Codex Control Plane

This repository is the source project for VibeOS across two runtime surfaces:

- Claude/Cursor: `CLAUDE.md`, `.claude/`, plugin/bootstrap assets
- Codex: `AGENTS.md`, `vibeos-init-codex.sh`, and `plugins/vibeos/reference/codex/`

The goal is side-by-side compatibility. Both runtimes should be able to work in the same target project without breaking each other, and they should share the same `.vibeos/` state model where possible.

## Core Rules

1. Do not break the Claude/Cursor runtime while adding Codex support.
2. Do not fake Codex parity by renaming Claude concepts without implementing the Codex surface.
3. Shared runtime state belongs in `.vibeos/`; runtime-specific behavior belongs in the runtime-specific surface.

## What To Read First

1. `README.md`
2. `CLAUDE.md`
3. `plugins/vibeos/reference/codex/AGENTS.md.ref`
4. `docs/planning/DEVELOPMENT-PLAN.md`
5. `docs/planning/WO-055-project-level-bootstrap-pivot.md`

## Current Architecture Intent

- `plugins/vibeos/skills/`, `plugins/vibeos/agents/`, and `plugins/vibeos/hooks/` remain the Claude/Cursor source assets.
- `plugins/vibeos/reference/codex/skills/` and `plugins/vibeos/reference/codex/AGENTS.md.ref` are the Codex source assets.
- `vibeos-init.sh` installs the Claude/Cursor surface.
- `vibeos-init-codex.sh` installs the Codex surface.
- Both bootstraps reuse the shared `.vibeos/` runtime assets: scripts, decision engine, references, and convergence logic.

## Codex-Specific Constraints

- Treat `.codex/agents/*.md` as role contracts, not executable subagents.
- Favor repo-local Codex skills over a fictional marketplace model.
- Keep Codex instructions honest about what is and is not runtime-enforced.

## Working Rule

When editing Codex support, prefer additive changes:

- add Codex bootstrap assets
- add Codex skill templates
- add dual-runtime docs
- preserve existing Claude/Cursor behavior unless a bug requires correction
