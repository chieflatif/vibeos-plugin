# VibeOS Plugin — Agent Instructions

## What Is This Project

A Claude Code plugin that turns Claude into an autonomous, self-governing development engine. Users describe what they want to build, the plugin guides discovery and planning, then autonomously builds with layered quality audits enforcing zero technical debt.

## Architecture

```
.claude-plugin/plugin.json   ← Plugin manifest
skills/                       ← 8 user-invocable skills (/vibeos:discover, :plan, :build, etc.)
agents/                       ← 12 specialized subagents (planner, auditors, tester, etc.)
hooks/hooks.json              ← Event-driven enforcement (secrets, stubs, frozen files)
scripts/                      ← 25 deterministic gate scripts + gate-runner.sh (bash)
decision-engine/              ← 8 decision tree files (markdown)
reference/                    ← 40+ annotated reference files
convergence/                  ← Loop control scripts (state hashing, convergence checks)
docs/planning/                ← Development plan, WO index, individual WO files
```

## Key Constraints

1. **Subagents cannot spawn subagents** — only the main thread dispatches agents
2. **Audit agents are read-only** — `disallowedTools: Write, Edit, Agent` + `isolation: worktree`
3. **Tests are written from spec, not code** — tester agent never sees implementation
4. **Implementation agents cannot modify test files** — enforced by PreToolUse hook
5. **No external frameworks** — pure Claude Code plugin system (skills + hooks + agents)
6. **All scripts are bash 3.2+ compatible** — macOS default, no external dependencies

## Technology

| Tool | Purpose |
|---|---|
| Bash 3.2+ | Gate scripts, hooks, convergence scripts |
| Python 3.7+ | Stub detection script |
| jq | JSON parsing in gate scripts |
| git | Version control, worktree isolation |

## Conventions

- Shell scripts: `#!/usr/bin/env bash`, `set -euo pipefail` (exception: hook scripts that read stdin omit pipefail)
- Exit codes: 0 = pass, 1 = fail, 2 = skip/block
- Logging: `echo "[COMPONENT] PASS|FAIL|WARN|SKIP: message"`
- Version: `FRAMEWORK_VERSION="1.0.0"` in every script
- Skills: SKILL.md with YAML frontmatter in skill directories
- Agents: .md files with YAML frontmatter in agents/
- No stubs, no placeholders, no TODOs in any file

## Development Governance

- **DEVELOPMENT-PLAN.md** defines phases and ordered Work Orders
- Agent determines next WO from the plan, never asks "what next?"
- Every WO has a file in `docs/planning/` with status, scope, acceptance criteria
- WO-INDEX.md tracks all WOs and their status
- WO-AUDIT-FRAMEWORK.md defines audit checkpoints

## Quality Gates

```bash
# Validate all scripts
for f in scripts/*.sh; do bash -n "$f"; done

# Validate JSON
for f in $(find . -name "*.json" -not -path './.git/*'); do jq . "$f" > /dev/null; done

# No placeholders
grep -rn '{{.*}}' scripts/ hooks/ decision-engine/ || echo "Clean"
```

## Source Material

This plugin was built from VibeOS-2 (dev-local: `/Users/latifhorst/cursor projects/VibeOS-2/`, not required at runtime). Key source files:

- `scripts/` — 25 gate scripts + gate-runner.sh (copied, paths adapted)
- `decision-engine/` — 8 decision trees (copy as-is)
- `reference/` — 40+ annotated references (copy as-is)
- `reference/hooks/` — 8 hook .ref files (convert to executable hooks)
- `reference/skills/` — 5 skill .ref files (convert to SKILL.md format)
- `docs/USER-COMMUNICATION-CONTRACT.md` — embed in every agent prompt
- `reference/governance/WO-AUDIT-FRAMEWORK.md.ref` — core of audit agents
- `PRODUCT-DISCOVERY.md` — source for /vibeos:discover
- `PROJECT-INTAKE.md` — source for /vibeos:plan
- `AGENT-BOOTSTRAP.md` — decomposed into discover/plan/build skills
