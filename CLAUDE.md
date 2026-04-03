# VibeOS Plugin — Agent Instructions

## What Is This Project

A Claude Code plugin that turns Claude into an autonomous, self-governing development engine. Users describe what they want to build, the plugin guides discovery and planning, then autonomously builds with layered quality audits enforcing zero technical debt.

## Architecture

```
.claude-plugin/marketplace.json  ← Marketplace catalog (for plugin install)
plugins/vibeos/                  ← Plugin root
  .claude-plugin/plugin.json     ← Plugin manifest
  skills/                        ← 14 user-invocable skills (/vibeos:discover, :plan, :build, :codex-audit, etc.)
  agents/                        ← 23 specialized subagents (15 base + 8 same-tree variants)
  hooks/hooks.json               ← Event-driven enforcement (11 hooks: governance, proof, budget, scope, routing)
  scripts/                       ← 56 deterministic gate scripts + gate-runner.sh (bash)
  decision-engine/               ← 10 decision tree files (markdown)
  reference/                     ← 85 annotated reference files
  convergence/                   ← Loop control scripts (state hashing, convergence checks)
  docs/                          ← User communication contract
docs/planning/                   ← Development plan, WO index, individual WO files
vibeos-init.sh                   ← Bootstrap script (alternative install method)
```

## Key Constraints

1. **Subagents cannot spawn subagents** — only the main thread dispatches agents
2. **Audit agents are read-only** — `disallowedTools: Write, Edit, Agent` + `isolation: worktree`
3. **Same-tree audit agents** — 8 agent variants that run in the current worktree for session-scoped review without isolation overhead
4. **Tests are written from spec, not code** — tester agent never sees implementation
5. **Implementation agents cannot modify test files** — enforced by PreToolUse hook
6. **No external frameworks** — pure Claude Code plugin system (skills + hooks + agents)
7. **All scripts are bash 3.2+ compatible** — macOS default, no external dependencies
8. **Audit visibility modes** — three modes: inline (same-tree agent), isolated (fresh worktree), codex (external Codex CLI)
9. **Parallel worktree scope enforcement** — worktree-scope-guard.sh blocks writes outside the assigned WO scope when agents run in parallel worktrees

## Technology

| Tool | Purpose |
|---|---|
| Bash 3.2+ | Gate scripts, hooks, convergence scripts |
| Python 3.7+ | Stub detection script |
| jq | JSON parsing in gate scripts |
| git | Version control, worktree isolation |
| Codex CLI | Optional: external complementary audit via /vibeos:codex-audit skill |

## Conventions

- Shell scripts: `#!/usr/bin/env bash`, `set -euo pipefail` (exception: hook scripts that read stdin omit pipefail)
- Exit codes: 0 = pass, 1 = fail, 2 = skip/block
- Logging: `echo "[COMPONENT] PASS|FAIL|WARN|SKIP: message"`
- Version: `FRAMEWORK_VERSION="2.1.0"` in every script
- Skills: SKILL.md with YAML frontmatter in skill directories
- Agents: .md files with YAML frontmatter in agents/
- State files: `.vibeos/session-state.json` tracks active session context; `.vibeos/quality-gate-manifest.json` is the authoritative gate registry
- Hook manifests: `.vibeos/hook-manifest.json` documents all registered hooks and their event bindings
- No stubs, no placeholders, no TODOs in any file

## Voice-Led Intent Routing

VibeOS is conversational. Users should NEVER need to type slash commands. When a user speaks naturally, the `UserPromptSubmit` hook (`intent-router.sh`) analyzes their message and injects a routing hint into your context as `[VibeOS Intent Router]`.

### How to Handle Routing Hints

1. **High confidence** — Invoke the suggested skill immediately using the Skill tool. Do not ask the user to confirm. Example: user says "I want to build a task management app" → invoke `/vibeos:discover`.

2. **Medium confidence** — Briefly confirm before invoking. One sentence, not an interrogation. Example: "It sounds like you want to run a code review. Should I start the audit?"

3. **Low confidence** — Ask a brief clarifying question. Do not guess. Example: "I can help with that — are you looking to check project status, or would you like me to continue building?"

4. **No hint (explicit slash command or direct help)** — The router stays silent. If the user typed a `/vibeos:*` command, invoke it normally. If the user is asking about specific code/errors, help them directly without invoking a skill.

### Conflict Resolution: Skill vs. Direct Help

Not every message should trigger a skill. Use these rules:

- **File paths, line numbers, error messages, code snippets** → Help directly. Do not invoke a skill.
- **Conceptual questions** ("what is ratcheting?", "how do phases work?") → Invoke `/vibeos:help`.
- **Product ideas or feature requests** → Invoke `/vibeos:discover` (new project) or `/vibeos:wo` (existing project with plan).
- **"Continue", "next", "keep going"** → Invoke `/vibeos:build`.
- **"Upgrade", "update the framework", "pulled the latest"** → Invoke `/vibeos:upgrade`.
- **Vague messages with no clear intent** → Check lifecycle state from the routing hint. At `virgin` stage, suggest discovery. At `building` stage, show status.

### Slash Commands Are Power-User Shortcuts

Slash commands (`/vibeos:discover`, `/vibeos:build`, etc.) still work and always take precedence. But never instruct users to type them. Instead of "Run `/vibeos:discover`", say "Just tell me what you want to build."

## Development Governance

- **DEVELOPMENT-PLAN.md** defines phases and ordered Work Orders
- Agent determines next WO from the plan, never asks "what next?"
- Every WO has a file in `docs/planning/` with status, scope, acceptance criteria
- WO-INDEX.md tracks all WOs and their status
- WO-AUDIT-FRAMEWORK.md defines audit checkpoints

## Quality Gates

```bash
# Validate all scripts
for f in plugins/vibeos/scripts/*.sh; do bash -n "$f"; done

# Validate JSON
for f in $(find . -name "*.json" -not -path './.git/*'); do jq . "$f" > /dev/null; done

# No placeholders
grep -rn '{{.*}}' plugins/vibeos/scripts/ plugins/vibeos/hooks/ plugins/vibeos/decision-engine/ || echo "Clean"
```

## Source Material

This plugin was built from VibeOS-2 (dev-local: `/Users/latifhorst/cursor projects/VibeOS-2/`, not required at runtime). Key source files:

- `scripts/` — 41 gate scripts + gate-runner.sh (copied, paths adapted)
- `decision-engine/` — 10 decision trees (copy as-is)
- `reference/` — 40+ annotated references (copy as-is)
- `reference/hooks/` — 8 hook .ref files (convert to executable hooks)
- `reference/skills/` — 5 skill .ref files (convert to SKILL.md format)
- `docs/USER-COMMUNICATION-CONTRACT.md` — embed in every agent prompt
- `reference/governance/WO-AUDIT-FRAMEWORK.md.ref` — core of audit agents
- `PRODUCT-DISCOVERY.md` — source for /vibeos:discover
- `PROJECT-INTAKE.md` — source for /vibeos:plan
- `AGENT-BOOTSTRAP.md` — decomposed into discover/plan/build skills
