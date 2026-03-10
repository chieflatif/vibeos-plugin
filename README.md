# VibeOS — Autonomous Development Engine

VibeOS turns Claude Code into a hands-on development partner. You do not need to learn a complicated workflow to get started. Open your project, describe what you want in plain English, and VibeOS figures out whether to discover, plan, audit, explain, or keep building.

Think of it like this:

- You say what you want
- VibeOS asks follow-up questions only when it truly needs them
- VibeOS creates the plan, writes the code, runs checks, and keeps you updated
- When VibeOS needs your input, it explains the options in simple terms, gives pros and cons, and recommends what to do

You can learn a few commands later if you want, but the normal way to use VibeOS is to talk to it naturally.

## Start Here

If you are not technical, this is the only part you really need:

1. Install VibeOS.
2. Open Claude Code inside your project.
3. Say what you want, like:
   - "I want to build a task management app"
   - "Help me understand this codebase"
   - "Continue building"
   - "What's the status?"

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
| "Check the code quality" | Runs quality gates and explains the result |
| "What is ratcheting?" | Explains the concept in plain English |
| "Help me understand this codebase" | Audits the project and maps what exists |

## What It Does

- **Discovery** — Helps turn a rough idea into something clear and buildable
- **Planning** — Breaks the work into phases and work orders so progress stays organized
- **Building** — Writes tests first, then implements the feature
- **Quality Checks** — Runs automated checks and audits so problems get caught early
- **Anti-Drift Anchors** — Keeps the build tied to the product promise, engineering standards, and current evidence instead of slowly drifting off course
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

### Upgrade

```bash
# Refresh marketplace metadata (optional)
claude plugin marketplace update vibeos

# Update the installed plugin
claude plugin update vibeos@vibeos

# Bootstrap:
bash /path/to/vibeos-plugin/vibeos-init.sh --upgrade
```

After a plugin update, restart Claude Code to apply the new version.

### Uninstall

```bash
# Plugin:
claude plugin uninstall vibeos@vibeos

# Bootstrap:
bash /path/to/vibeos-plugin/vibeos-init.sh --uninstall
```

## Quick Start

VibeOS is voice-led. You do not need to type slash commands to use it.

### The Simplest Way To Use It

Open Claude Code in your project and start with a sentence like:

> "I want to build a task management app"

Then keep talking to it naturally:

> "Make a plan for that"
>
> "Start building"
>
> "What's the status?"
>
> "Keep going"

That is the main workflow.

### New Project

Open your project in Claude Code or Cursor and say:

> "I want to build a task management app"

VibeOS will guide you through discovery, planning, and building. You do not need to tell it which command to use.

### Existing Project

> "Help me understand this codebase" or "Set up governance for this project"

VibeOS will audit your code, identify issues, and create a remediation plan before building new features.

### Other Useful Things You Can Say

- "What's the status?" — project dashboard
- "Check the code quality" — run quality gates
- "Continue building" — resume the build loop
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
| `/audit` | Run full audit cycle |
| `/gate` | Run quality gates |
| `/wo` | Work order management |
| `/status` | Project dashboard |
| `/checkpoint` | Phase boundary report |
| `/help` | Explain any concept |

## What Gets Installed

Most people do not need to think about this section day to day, but this is what VibeOS adds behind the scenes:

```
your-project/
├── .claude/
│   ├── CLAUDE.md          ← Agent instructions and routing rules
│   ├── settings.json      ← Hooks configuration
│   ├── skills/            ← 9 skills (discover, plan, build, etc.)
│   ├── agents/            ← 12 specialized subagents
│   └── hooks/             ← 6 hook scripts (intent routing, security, etc.)
├── .vibeos/
│   ├── scripts/           ← 25 quality gate scripts
│   ├── decision-engine/   ← 8 decision trees
│   ├── reference/         ← 40+ annotated reference files
│   └── convergence/       ← Loop control scripts
└── docs/
    ├── planning/          ← Generated development plan and work orders
    ├── product/           ← PRD, architecture, and product anchor
    ├── research/          ← Current evidence for high-impact decisions
    └── decisions/         ← Explicit trade-offs and deviations
```

## Requirements

- Claude Code (CLI or Cursor IDE)
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

### What should I type first?

For a new project:

> "I want to build..."

For an existing project:

> "Help me understand this codebase"

For a project already in progress:

> "What's the status?" or "Continue building"

## Status

**In development.** See [DEVELOPMENT-PLAN.md](docs/planning/DEVELOPMENT-PLAN.md) for current progress.

## License

[CC BY-NC 4.0](LICENSE) — Free for personal and non-commercial use. See LICENSE for details.
