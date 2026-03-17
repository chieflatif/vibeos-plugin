# VibeOS — Autonomous Development Engine

> **v2.0.0 — Verification Integrity Upgrade (2026-03-16)**
>
> Six systemic failure modes found during production use: 67% false positive rate from stale worktrees, frontend-backend contract drift, silent pass guards masking broken tests, WO status inflation, audit timeouts on large codebases, and no finding memory across sessions. This release adds **4 verification integrity gates**, **2 new audit agents** (red-team + contract validator), **5 convergence scripts** with finding lifecycle management, **baseline expiry** (2-phase limit), **ground truth checkpoints**, and **module-targeted audit dispatch**. Gate count: 24 → 42. Agent count: 13 → 15. See the [upgrade instructions](#upgrade) or say *"Upgrade VibeOS"* inside any active session.

VibeOS turns Claude Code, Cursor, and Codex into a hands-on development partner. You do not need to learn a complicated workflow to get started. Open your project in the runtime you prefer, describe what you want in plain English, and VibeOS figures out whether to discover, plan, audit, explain, or keep building.

Think of it like this:

- You say what you want
- VibeOS asks follow-up questions only when it truly needs them
- VibeOS creates the plan, writes the code, runs checks, and keeps you updated
- When VibeOS needs your input, it explains the options in simple terms, gives pros and cons, and recommends what to do

You can learn a few commands later if you want, but the normal way to use VibeOS is to talk to it naturally.

## Start Here

If you are not technical, this is the only part you really need:

1. Install VibeOS.
2. Open Claude Code, Cursor, or Codex inside your project.
3. Say what you want, like:
   - "I want to build a task management app"
   - "Help me understand this codebase"
   - "Continue building"
   - "What's the status?"
   - "Give me a project status"

That is enough to get started.

## How It Feels To Use

VibeOS is voice-driven and conversation-first. In practice, that means:

- You do **not** need to remember slash commands to use it
- You do **not** need to know GitHub pull requests, branching, or formal project management
- You do **not** need to tell it which internal mode to use
- You **can** just type what you want as if you were talking to a strong technical teammate

Examples:

| You say | VibeOS does |
|---|---|
| "I want to build a booking app for dog groomers" | Starts discovery and helps shape the product |
| "Make a plan for this" | Creates a phased development plan |
| "Keep going" | Continues the build loop |
| "What's the status?" | Gives a tactical update on the current or most recent session |
| "Give me a project status" | Gives an executive big-picture briefing on the whole project |
| "Go autonomous" | Puts VibeOS back into full autonomous session mode |
| "Audit this session" | Reviews everything completed in the current or last build session |
| "Check the code quality" | Runs quality gates and explains the result |
| "What is ratcheting?" | Explains the concept in plain English |
| "Help me understand this codebase" | Audits the project and maps what exists |

## What It Does

- **Discovery** — Helps turn a rough idea into something clear and buildable
- **Planning** — Breaks the work into phases and work orders so progress stays organized
- **Building** — Writes tests first, then implements the feature
- **Quality Checks** — Runs automated checks and audits so problems get caught early
- **Session Audits** — Reviews the current or most recent build session end-to-end so you can close out autonomous work with confidence
- **Anti-Drift Anchors** — Keeps the build tied to the product promise, engineering standards, and current evidence instead of slowly drifting off course
- **Prompt Engineering Standards** — Routes prompt and agent-instruction changes through a dedicated prompt-engineering path using the embedded Prompt Engineering Bible
- **Progress Guidance** — Tells you what is happening, what is done, and what should happen next
- **Zero Technical Debt** — No stubs, no placeholders, no pretending something is finished when it is not

## Installation

### The recommended way: project-level bootstrap

```bash
# Clone VibeOS
git clone https://github.com/chieflatif/vibeos-plugin.git

# Go to your project
cd your-project

# Install
bash /path/to/vibeos-plugin/vibeos-init.sh
```

Or with a one-liner if you don't want to clone first:

```bash
bash <(curl -s https://raw.githubusercontent.com/chieflatif/vibeos-plugin/main/vibeos-init.sh)
```

This installs VibeOS into your project's `.claude/` and `.vibeos/` directories. Skills, agents, hooks, and gate scripts are all wired up and ready immediately — no restart required.

### Why bootstrap instead of plugin install?

VibeOS is a skills-based plugin. Claude Code's `plugin install` command works reliably for MCP-based plugins (those that run a background server process), but as of early 2026 there is [an open bug](https://github.com/anthropics/claude-code/issues/10568) where skills-based plugins silently fail on marketplace install — the command exits with no error but the skills are never registered.

The project-level bootstrap sidesteps this entirely. Claude Code has always discovered skills and agents placed directly in a project's `.claude/skills/` and `.claude/agents/` directories, so that is what the bootstrap does. The result is the same end state you would get from a working plugin install, without the flaky intermediate step.

We maintain a [custom marketplace catalog](https://github.com/chieflatif/vibeos-plugin/blob/main/.claude-plugin/marketplace.json) so that the standard `plugin marketplace add` and `plugin install` flow is available. If Anthropic fixes the skills registration bug, users who prefer the plugin install path can switch to it with no changes to their projects. Until then, the bootstrap is the reliable path.

### Codex (Experimental)

Codex support is available but limited. Codex does not support hooks, subagent spawning, or runtime enforcement — it gets structured instructions and shared gate scripts but not the full enforcement layer that Claude Code gets. Think of it as "guided mode" vs. the full "enforced mode."

```bash
bash /path/to/vibeos-plugin/vibeos-init-codex.sh
```

This installs `AGENTS.md`, `.codex/skills/`, `.codex/agents/` (as role contracts), and the shared `.vibeos/` runtime alongside any existing `.claude/` setup.

**What Codex gets:** Structured build instructions, quality gate scripts (run manually), decision engine, reference materials, and role contracts for each build phase.

**What Codex does not get:** Intent routing hooks, secrets scanning, test file protection, parallel audit agents, or automatic enforcement boundaries. These require Claude Code's hook and subagent system.

### Upgrade

```bash
# Bootstrap (Claude/Cursor):
bash /path/to/vibeos-plugin/vibeos-init.sh --upgrade

# Bootstrap (Codex):
bash /path/to/vibeos-plugin/vibeos-init-codex.sh --upgrade
```

Or inside an active Claude Code session, say: *"Upgrade VibeOS"* and provide the path to the updated framework.

### Uninstall

```bash
# Claude/Cursor bootstrap:
bash /path/to/vibeos-plugin/vibeos-init.sh --uninstall

# Codex bootstrap:
bash /path/to/vibeos-plugin/vibeos-init-codex.sh --uninstall
```

## Quick Start

VibeOS is voice-led. You do not need to type slash commands to use it.

### The Simplest Way To Use It

Open Claude Code, Cursor, or Codex in your project and start with a sentence like:

> "I want to build a task management app"

Then keep talking to it naturally:

> "Make a plan for that"
>
> "Start building"
>
> "What's the status?"
>
> "Give me a project status"
>
> "Keep going"

That is the main workflow.

### New Project

Open your project in Claude Code, Cursor, or Codex and say:

> "I want to build a task management app"

VibeOS will guide you through discovery, planning, and building. You do not need to tell it which command to use.

### Existing Project

> "Help me understand this codebase" or "Set up governance for this project"

VibeOS will audit your code, identify issues, and create a remediation plan before building new features.

### Other Useful Things You Can Say

- "What's the status?" — tactical session update
- "Give me a project status" — overall founder-level project briefing
- "Check the code quality" — run quality gates
- "Continue building" — resume the build loop
- "Go autonomous" — switch back into full autonomous session mode
- "Audit this session" — run a closeout review of the current or last build session
- "What is ratcheting?" — explain any concept
- "Upgrade VibeOS" — upgrade framework and sweep the project with new capabilities
- "What should I do next?" — recommend the next step
- "Explain this in simple terms" — simplify technical language

### Power-User Shortcuts

Slash commands still work if you prefer them, but they are optional:

| Command | Description |
|---|---|
| `/discover` | Product discovery — idea to product artifacts |
| `/plan` | Generate development plan with governance |
| `/build` | Autonomous build loop |
| `/autonomous` | Full autonomous session override |
| `/audit` | Run full audit cycle |
| `/session-audit` | Audit the current or last build session |
| `/gate` | Run quality gates |
| `/wo` | Work order management |
| `/status` | Tactical session status |
| `/project-status` | Executive project briefing |
| `/checkpoint` | Phase boundary report |
| `/upgrade` | Framework upgrade and re-audit |
| `/help` | Explain any concept |

## What Gets Installed

Most people do not need to think about this section day to day, but this is what VibeOS adds behind the scenes:

```
your-project/
├── AGENTS.md              ← Codex instructions (if Codex bootstrap used, experimental)
├── .codex/                ← Codex-local skills and role contracts (no runtime enforcement)
│   ├── skills/            ← 12 VibeOS Codex skills (instruction-based, not hook-enforced)
│   └── agents/            ← Role contracts (read by agent, not spawned as subagents)
├── .claude/               ← Claude/Cursor surface (full enforcement)
│   ├── CLAUDE.md          ← Agent instructions and routing rules
│   ├── settings.json      ← Hooks configuration
│   ├── skills/            ← 13 skills (discover, plan, build, upgrade, status, project-status, etc.)
│   ├── agents/            ← 15 specialized subagents
│   └── hooks/             ← 6 hook scripts (intent routing, security, etc.)
├── .vibeos/               ← Shared runtime used by both surfaces
│   ├── scripts/           ← 41 quality gate scripts
│   ├── decision-engine/   ← 10 decision trees
│   ├── reference/         ← 45+ annotated reference files plus prompt-engineering guidance
│   └── convergence/       ← Loop control scripts
└── docs/
    ├── planning/          ← Generated development plan and work orders
    ├── product/           ← PRD, architecture, and product anchor
    ├── research/          ← Current evidence for high-impact decisions
    └── decisions/         ← Explicit trade-offs and deviations
```

## Requirements

- Claude Code (CLI or Cursor IDE) — full enforcement
- OpenAI Codex — experimental, instruction-only (no hooks or subagents)
- bash 3.2+
- python3 3.7+
- jq
- git

## Non-Technical FAQ

### Do I need to learn commands?

No. The normal workflow is conversational. Commands are there only if you want shortcuts.

### Do I need to understand GitHub or pull requests?

No. You can use VibeOS by opening a project and telling it what you want. GitHub workflows are optional.

### Do I need to know what discovery, planning, or work orders mean before I start?

No. VibeOS can explain those as you go. You can start with a simple sentence like:

> "I want to build a client portal for my business"

### If VibeOS asks me to choose, how will it explain the options?

It should explain the choice in simple terms first, then give the tradeoffs:

- what each option means
- the pros and cons of each option
- which option it recommends and why

You should not have to guess what a choice means or why one path is better.

### How does VibeOS avoid drifting away from what I asked for?

It creates a few simple anchor documents during discovery:

- a product anchor that keeps the core promise and user experience clear
- engineering principles that define the quality bar
- a research registry for important up-to-date technical decisions
- a deviation log for any deliberate compromises

That gives the system a memory of what it is trying to protect as it keeps building.

### How do I send VibeOS back into full autonomous mode?

Say:

> "Go autonomous"

That tells VibeOS to stop routine check-ins for the current session and keep building until it hits a real blocker, needs a decision, or finishes the available work.

### How do I audit everything it did in a session?

Say:

> "Audit this session"

VibeOS will review the work orders completed in that session, re-run verification, check for drift, and save a session audit report.

### How does VibeOS keep prompt and agent behavior high quality?

If a work order changes prompts, agent instructions, `CLAUDE.md`, `AGENTS.md`, or other behavior-governing files, VibeOS should route that work through its dedicated prompt-engineering path.

That path uses an embedded local snapshot of the Prompt Engineering Bible so prompt changes are treated like governed system assets, not casual copy edits.

### What should I type first?

For a new project:

> "I want to build..."

For an existing project:

> "Help me understand this codebase"

For a project already in progress:

> "What's the status?", "Give me a project status", or "Continue building"

## Status

**In development.** See [DEVELOPMENT-PLAN.md](docs/planning/DEVELOPMENT-PLAN.md) for current progress.

## License

[CC BY-NC 4.0](LICENSE) — Free for personal and non-commercial use. See LICENSE for details.
