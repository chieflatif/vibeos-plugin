# VibeOS Plugin — Codex Surface (Experimental)

This file provides Codex with structured instructions for working in this repository. It coexists with `CLAUDE.md` and `.claude/`, which provide the full enforcement surface for Claude Code and Cursor.

## What Codex Gets

- Structured build instructions via `.codex/skills/` and `.codex/agents/`
- Shared quality gate scripts in `.vibeos/scripts/`
- Decision engine and reference materials in `.vibeos/`
- Shared project state: plans, checkpoints, baselines, and logs in `.vibeos/`
- Commit-boundary Git hooks via `.vibeos/scripts/setup-git-hooks.sh` when the repo can install them

## What Codex Does Not Get

- **No runtime hooks.** No prompt/edit/stop event enforcement such as intent routing, secrets scanning, test file protection, or stub detection on stop. These require Claude Code's hook system.
- **No subagent spawning.** Agent files in `.codex/agents/` are role contracts — Codex reads them and performs the phase itself, in a single context. There is no isolation or parallel execution.
- **No automatic write-time enforcement.** Quality gates and architecture rules still run manually; Git hooks only block at commit time after they are installed.

## Core Rules

1. No remediation without a Work Order.
2. No Work Order without an evidence-backed finding.
3. No finding without investigation.

## What To Read First

1. `README.md`
2. `CLAUDE.md` (the full enforcement surface — Codex should understand what it cannot enforce)
3. `plugins/vibeos/reference/codex/AGENTS.md.ref` (template for target projects)
4. `docs/planning/DEVELOPMENT-PLAN.md`

## Current Architecture

- `plugins/vibeos/skills/`, `plugins/vibeos/agents/`, and `plugins/vibeos/hooks/` are the Claude/Cursor source assets (full enforcement).
- `plugins/vibeos/reference/codex/skills/` and `plugins/vibeos/reference/codex/AGENTS.md.ref` are the Codex source assets (instruction-only).
- `vibeos-init.sh` installs the Claude/Cursor surface.
- `vibeos-init-codex.sh` installs the Codex surface.
- Both bootstraps share the `.vibeos/` runtime: scripts, decision engine, references, and convergence logic.

## Working Rule

When editing Codex support, prefer additive changes. Do not break the Claude/Cursor surface. Do not pretend Codex has capabilities it does not have.

Codex's truthful enforcement stack is: `AGENTS.md` + skills for behavior, `.vibeos/scripts/gate-runner.sh` for explicit checks, and Git `pre-commit` / `commit-msg` hooks for commit-boundary blocking.
