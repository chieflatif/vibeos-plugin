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
