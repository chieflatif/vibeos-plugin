# VibeOS Plugin — Codex Surface (Experimental)

This file provides Codex with structured instructions for working in this repository. It coexists with `CLAUDE.md` and `.claude/`, which provide the full enforcement surface for Claude Code and Cursor.

## What Codex Gets

- Structured build instructions via `.codex/skills/` and `.codex/agents/`
- Quality gate scripts in `.vibeos/scripts/` (run manually)
- Decision engine and reference materials in `.vibeos/`
- Shared project state: plans, checkpoints, baselines, and logs in `.vibeos/`

## What Codex Does Not Get

- **No hooks.** No intent routing, secrets scanning, test file protection, or stub detection on stop. These require Claude Code's hook system.
- **No subagent spawning.** Agent files in `.codex/agents/` are role contracts — Codex reads them and performs the phase itself, in a single context. There is no isolation or parallel execution.
- **No automatic enforcement.** Quality gates and architecture rules are available as scripts but must be run manually. Nothing blocks a bad write automatically.

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
