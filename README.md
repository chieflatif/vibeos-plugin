# VibeOS — Autonomous Development Engine

An autonomous, self-governing development engine for Claude Code. Describe what you want to build — VibeOS guides you through product discovery, creates a development plan, then autonomously builds your project with layered quality audits at every step.

## What It Does

- **Product Discovery** — Turn a rough idea into a complete product definition, PRD, technical spec, and architecture outline
- **Development Planning** — Generate a phased development plan with ordered work orders and governance tailored to your project
- **Autonomous Build** — TDD-driven implementation with specialized agents (planner, tester, backend, frontend, doc writer)
- **Layered Audits** — 7-layer quality system: real-time hooks, deterministic gates, fresh-context audit agents, semantic completion, evidence validation, phase boundary audits, and human check-ins
- **Zero Technical Debt** — No stubs, no placeholders, no shortcuts. Tests prove real-world behavior, not just passing.

## Installation

### Option 1: Claude Code Plugin (recommended)

```bash
# Add the VibeOS marketplace
/plugin marketplace add chieflatif/vibeos-plugin

# Install the plugin
/plugin install vibeos@vibeos
```

That's it. All skills, agents, and hooks are automatically available in every Claude Code session.

### Option 2: Project-Level Bootstrap

If you prefer per-project installation (or use Cursor IDE):

```bash
# Clone the framework
git clone https://github.com/chieflatif/vibeos-plugin.git

# Navigate to your project
cd your-project

# Run the bootstrap
bash /path/to/vibeos-plugin/vibeos-init.sh
```

This installs VibeOS into your project's `.claude/` and `.vibeos/` directories.

### Upgrade

```bash
# Plugin: marketplace updates automatically
/plugin marketplace update vibeos

# Bootstrap:
bash /path/to/vibeos-plugin/vibeos-init.sh --upgrade
```

### Uninstall

```bash
# Plugin:
/plugin uninstall vibeos

# Bootstrap:
bash /path/to/vibeos-plugin/vibeos-init.sh --uninstall
```

## Quick Start

VibeOS is voice-led. You don't need to type slash commands — just talk naturally.

### New Project

Open your project in Claude Code or Cursor and say:

> "I want to build a task management app"

VibeOS will guide you through discovery, planning, and building. It figures out what to do based on what you say.

### Existing Project

> "Help me understand this codebase" or "Set up governance for this project"

VibeOS will audit your code, identify issues, and create a remediation plan before building new features.

### Other Things You Can Say

- "What's the status?" — project dashboard
- "Check the code quality" — run quality gates
- "Continue building" — resume the build loop
- "What is ratcheting?" — explain any concept

### Power-User Shortcuts

Slash commands still work if you prefer them:

| Command | Description |
|---|---|
| `/discover` | Product discovery — idea to product artifacts |
| `/plan` | Generate development plan with governance |
| `/build` | Autonomous build loop |
| `/audit` | Run full audit cycle |
| `/gate` | Run quality gates |
| `/wo` | Work order management |
| `/status` | Project dashboard |
| `/checkpoint` | Phase boundary report |
| `/help` | Explain any concept |

## What Gets Installed

```
your-project/
├── .claude/
│   ├── CLAUDE.md          ← Agent instructions and routing rules
│   ├── settings.json      ← Hooks configuration
│   ├── skills/            ← 9 skills (discover, plan, build, etc.)
│   ├── agents/            ← 11 specialized subagents
│   └── hooks/             ← 6 hook scripts (intent routing, security, etc.)
├── .vibeos/
│   ├── scripts/           ← 25 quality gate scripts
│   ├── decision-engine/   ← 8 decision trees
│   ├── reference/         ← 40+ annotated reference files
│   └── convergence/       ← Loop control scripts
└── docs/
    └── planning/          ← Generated development plan and work orders
```

## Requirements

- Claude Code (CLI or Cursor IDE)
- bash 3.2+
- python3 3.7+
- jq
- git

## Status

**In development.** See [DEVELOPMENT-PLAN.md](docs/planning/DEVELOPMENT-PLAN.md) for current progress.

## License

[CC BY-NC 4.0](LICENSE) — Free for personal and non-commercial use. See LICENSE for details.
