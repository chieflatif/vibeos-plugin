# VibeOS — Autonomous Development Engine

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

### Option 1: Claude Code Plugin (recommended)

If you just want the easiest setup, use this option.

From your shell:

```bash
# Add the VibeOS marketplace
claude plugin marketplace add chieflatif/vibeos-plugin

# Install the plugin
claude plugin install vibeos@vibeos
```

Inside an active Claude Code session, the equivalent commands are:

```text
/plugin marketplace add chieflatif/vibeos-plugin
/plugin install vibeos@vibeos
```

After installing, restart Claude Code so the new plugin is loaded.

### Option 2: Project-Level Bootstrap

Use this if you prefer per-project installation or if you use Cursor:

```bash
# Clone the framework
git clone https://github.com/chieflatif/vibeos-plugin.git

# Navigate to your project
cd your-project

# Run the bootstrap
bash /path/to/vibeos-plugin/vibeos-init.sh
```

This installs VibeOS into your project's `.claude/` and `.vibeos/` directories.

### Option 3: Codex Project Bootstrap

Use this if you want the Codex runtime surface alongside the shared VibeOS engine:

```bash
# Clone the framework
git clone https://github.com/chieflatif/vibeos-plugin.git

# Navigate to your project
cd your-project

# Run the Codex bootstrap
bash /path/to/vibeos-plugin/vibeos-init-codex.sh
```

This installs VibeOS into your project's `AGENTS.md`, `.codex/`, and `.vibeos/` surfaces. If `.claude/` or `CLAUDE.md` already exist, they are preserved so Claude/Cursor and Codex can work side-by-side in the same project.

### Upgrade

```bash
# Refresh marketplace metadata (optional)
claude plugin marketplace update vibeos

# Update the installed plugin
claude plugin update vibeos@vibeos

# Bootstrap:
bash /path/to/vibeos-plugin/vibeos-init.sh --upgrade

# Codex bootstrap:
bash /path/to/vibeos-plugin/vibeos-init-codex.sh --upgrade
```

After a plugin update, restart Claude Code to apply the new version.

### Uninstall

```bash
# Plugin:
claude plugin uninstall vibeos@vibeos

# Bootstrap:
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
| `/help` | Explain any concept |

## What Gets Installed

Most people do not need to think about this section day to day, but this is what VibeOS adds behind the scenes:

```
your-project/
├── AGENTS.md              ← Codex control plane (if Codex bootstrap used)
├── .codex/                ← Codex-local skills and agent templates
│   ├── skills/            ← 12 VibeOS Codex skills
│   └── agents/            ← Role contracts reused by Codex workflows
├── .claude/               ← Claude/Cursor surface (if Claude bootstrap used)
│   ├── CLAUDE.md          ← Agent instructions and routing rules
│   ├── settings.json      ← Hooks configuration
│   ├── skills/            ← 12 skills (discover, plan, build, status, project-status, etc.)
│   ├── agents/            ← 13 specialized subagents
│   └── hooks/             ← 6 hook scripts (intent routing, security, etc.)
├── .vibeos/               ← Shared runtime used by both surfaces
│   ├── scripts/           ← 25 quality gate scripts
│   ├── decision-engine/   ← 8 decision trees
│   ├── reference/         ← 40+ annotated reference files plus prompt-engineering guidance
│   └── convergence/       ← Loop control scripts
└── docs/
    ├── planning/          ← Generated development plan and work orders
    ├── product/           ← PRD, architecture, and product anchor
    ├── research/          ← Current evidence for high-impact decisions
    └── decisions/         ← Explicit trade-offs and deviations
```

## Requirements

- Claude Code (CLI or Cursor IDE) and/or OpenAI Codex
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
