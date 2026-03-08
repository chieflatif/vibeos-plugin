# VibeOS Plugin for Claude Code

An autonomous, self-governing development engine for Claude Code. Describe what you want to build — VibeOS guides you through product discovery, creates a development plan, then autonomously builds your project with layered quality audits at every step.

## What It Does

- **Product Discovery** — Turn a rough idea into a complete product definition, PRD, technical spec, and architecture outline
- **Development Planning** — Generate a phased development plan with ordered work orders and governance tailored to your project
- **Autonomous Build** — TDD-driven implementation with specialized agents (planner, tester, backend, frontend, doc writer)
- **Layered Audits** — 7-layer quality system: real-time hooks, deterministic gates, fresh-context audit agents, semantic completion, evidence validation, phase boundary audits, and human check-ins
- **Zero Technical Debt** — No stubs, no placeholders, no shortcuts. Tests prove real-world behavior, not just passing.

## Installation

```bash
claude plugin install ./vibeos-plugin
```

## Quick Start

### New Project
1. `/vibeos:discover` — Describe what you want to build. I'll ask questions and create product docs.
2. `/vibeos:plan` — I'll generate a phased development plan with work orders and quality gates.
3. `/vibeos:build` — I'll build autonomously, checking in at natural pause points.

### Existing Project
1. `/vibeos:discover` — I'll analyze your codebase and create architecture docs.
2. `/vibeos:plan` — I'll audit your code for issues and create a remediation + feature plan.
3. `/vibeos:build` — Critical issues first (Phase 0), then feature work.

### Anytime
- `/vibeos:status` — See where things stand
- `/vibeos:help` — Learn any concept
- `/vibeos:gate` — Run quality checks manually
- `/vibeos:help files` — See what files the plugin creates in your project

## Skills

| Skill | Description |
|---|---|
| `/vibeos:discover` | Product discovery — idea to product artifacts |
| `/vibeos:plan` | Generate development plan with governance |
| `/vibeos:build` | Autonomous build loop |
| `/vibeos:audit` | Run full audit cycle |
| `/vibeos:gate` | Run quality gates |
| `/vibeos:wo` | Work order management |
| `/vibeos:status` | Project dashboard |
| `/vibeos:checkpoint` | Phase boundary report |

## Requirements

- Claude Code (desktop app or CLI)
- bash 3.2+
- python3 3.7+
- jq
- git

## Status

**In development.** See [DEVELOPMENT-PLAN.md](docs/planning/DEVELOPMENT-PLAN.md) for current progress.

## License

MIT
