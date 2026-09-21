# VibeOS — Autonomous Development Engine

> **2.4.0 — provider-bound companion audit efficiency.**
> Codex-led projects can opt into one frozen first-party Claude audit and then
> verify only the named corrections. Exact contract, commit, scope, diff,
> provider/model and drift receipts now provide checkable integrity evidence at
> closeout without repeatedly
> paying for a broad audit. See
> [Claude companion audit](docs/CLAUDE-COMPANION-AUDIT.md) and
> [release evidence](docs/release/2.4.0.md).

> **2.3.2 — canonical acceptance closeout.**
> Accepted product source can no longer be treated as adopted while it exists
> only in a temporary worktree, archive or topic branch. The new closeout
> validator proves the exact acceptance binding from a fresh clone of the remote
> default branch and keeps evidence-only acceptance explicitly separate.
> See [installation and customization](docs/INSTALLATION.md),
> [controlled evaluation](docs/CONTROLLED-EVALUATION.md) and
> [release evidence](docs/release/2.3.2.md).


> **v2.2.0 — Evidence Recall Upgrade (2026-04-24)**
>
> This update adds a local, source-cited evidence recall utility. VibeOS can now build a compact index of work orders, audits, gate manifests, skills, session state, baselines, and checkpoints, then return bounded excerpts with citations instead of rereading large context bundles. It uses a generated `.vibeos/cache/` file, has no network dependency, and does not add any external memory service.

> **v2.1.0 — Advanced Governance Upgrade (2026-04-03)**
>
> This update makes VibeOS smarter about how it reviews its own work. It can now check code quality *while it's still building* (instead of waiting until everything is saved), ask a second AI (Codex) to independently verify what it built, and automatically prevent work orders from growing too large or messy. It also blocks attempts to skip safety checks and protects test files from being weakened during implementation. If you're running multiple builds in parallel, VibeOS now enforces clear boundaries so they don't step on each other. Say *"Upgrade VibeOS"* inside any active session to get these improvements.

> **v2.0.0 — Verification Integrity Upgrade (2026-03-16)**
>
> This update came after VibeOS ran a fully autonomous 8-hour build session — 156 work orders, 6,175 passing tests, zero human intervention. Running at that scale revealed places where the system needed to be more careful about verifying its own work: catching stale code reviews, validating that the front-end and back-end agree with each other, remembering issues between sessions, and making sure old problems don't get quietly ignored forever. The system now verifies its own verification.

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
| "Build this as a competition-grade enterprise MVP" | Creates a compact VibOS Comp mission brief |
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
- **VibOS Comp** — Creates compact enterprise MVP mission briefs and applies a foundation blueprint so scope can shrink without cutting security, observability, tests, delivery infrastructure, dependency intelligence, flow integrity, objective fidelity, or system invariants
- **Planning** — Breaks the work into phases and work orders so progress stays organized
- **Building** — Writes tests first, then implements the feature
- **Long-Run Autonomy** — Supports deliberate 24-48 hour autonomous runs with durable heartbeats, checkpoints, audit cadence, run leases, safe resume-plan execution, generated scheduler profiles, scheduler guards, disposable smoke tests, Codex/Claude runtime handoff plans, stale-run detection, failure-loop detection, recovery planning, evidence-backed recovery resolution, and resumable handoff state
- **Quality Checks** — Runs automated checks and audits so problems get caught early
- **Session Audits** — Reviews the current or most recent build session end-to-end so you can close out autonomous work with confidence
- **Evidence Recall** — Builds a local source-cited index so status, build, audit, and planning work can find the right prior evidence with less context
- **Optional Local Intake** — Routes opted-in, low-consequence engineering logs and receipts through a loopback local model behind closed-schema and evidence validation, while the parent keeps every decision and effect
- **Optional Claude Companion Audit** — Runs one provider-reported full Claude audit for a frozen Codex-authored work unit, then checks only the named fixes unless the acceptance contract or scope changes
- **Anti-Drift Anchors** — Keeps the build tied to the product promise, engineering standards, and current evidence instead of slowly drifting off course
- **Prompt Engineering Standards** — Routes prompt and agent-instruction changes through a dedicated prompt-engineering path using the embedded Prompt Engineering Bible
- **Progress Guidance** — Tells you what is happening, what is done, and what should happen next
- **Zero Technical Debt** — No stubs, no placeholders, no pretending something is finished when it is not

## Installation

### Optional Mac workstation package

If this is a new Mac or a partially configured Mac, VibeOS includes an optional
harness utility that can check or install the baseline development tool spine
before you install VibeOS into individual projects:

```bash
git clone https://github.com/chieflatif/vibeos-plugin.git
cd vibeos-plugin

# Dry-run first. This detects what would be installed.
./vibeos-machine-init.sh

# Apply the baseline workstation package.
./vibeos-machine-init.sh --apply
```

The same capability is available after a project install as a harness utility:

```bash
bash .vibeos/scripts/workstation-package.sh check
bash .vibeos/scripts/workstation-package.sh verify
```

The package covers Homebrew, Git/GitHub tooling, Claude Code, Codex, Cursor,
Docker Desktop, Node/npm/Corepack, uv/Python, Azure CLI, Azure Functions Core
Tools, Render/Stripe/deployment tools, local service tools, and media/document
tools. It is optional and does not copy secrets or account sessions.
Authentication remains manual: `gh auth login`, `az login`, `claude`, and
`codex`.

### Recommended: a pinned project-profile installation

Use the [installation guide](docs/INSTALLATION.md) to clone a reviewed release,
analyze the target project, inspect the plan, verify it and apply it. Generated
framework files and project-owned rules have separate provenance. Upgrades preserve
customized files and produce merge candidates instead of overwriting them.

The supported release proof targets macOS with Codex. Python 3.12+, Bash 3.2+,
Git and jq are required. The controlled evaluator additionally requires configured
Codex, Python/pytest and Ruff tools; it never installs or authenticates them for you.
Claude/Cursor instruction surfaces remain available; their host runtimes must be
verified locally before making enforcement claims.

### Existing bootstrap and marketplace users

`vibeos-init.sh` and `vibeos-init-codex.sh` remain compatibility entrypoints.
For project customization and upgrade recovery, use the profile installer guide.
Avoid mixing legacy wholesale runtime replacement with a customized profile install.

Profile-installed projects may also opt into the disabled-by-default local engineering
intake lane. It handles bounded CI, test, lint, build, dependency, static-analysis, and
release-receipt triage only; it is not a coding or audit worker. See
[Local Engineering Intake and Triage](docs/LOCAL-ENGINEERING-INTAKE.md).

Consequential Codex-authored work may opt into the separate Claude companion audit
module. It pins first-party `claude-fable-5-1`, binds review to exact Git and
acceptance-contract bytes, and replaces repeated broad audits with targeted correction
verification. See [Claude Companion Audit](docs/CLAUDE-COMPANION-AUDIT.md).

The Claude marketplace catalog remains available. Current Claude documentation
supports skills, agents and hooks in plugins, but a successful marketplace install
alone does not establish project binding or native Codex enforcement. Verify exact
source and installed paths; do not use version text alone as proof of currency.

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
| `/comp` | Compact enterprise MVP mission brief |
| `/plan` | Generate development plan with governance |
| `/build` | Autonomous build loop |
| `/autonomous` | Full autonomous session override |
| `/audit` | Run full audit cycle |
| `/session-audit` | Audit the current or last build session |
| `/codex-audit` | Request a Codex-powered complementary audit (experimental) |
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
├── .agents/               ← Repo-scoped Codex skills
│   └── skills/            ← 13 VibeOS Codex skills
├── .codex/                ← Codex-native project config, agents, hooks, and legacy fallback contracts
│   ├── config.toml        ← Codex hook feature flag and agent concurrency settings
│   ├── hooks.json         ← Codex-compatible guardrail hooks
│   ├── hooks/             ← Hook scripts for governance, secrets, and worktree safety
│   ├── agents/            ← Codex-native TOML subagents
│   ├── agent-contracts/   ← Legacy Markdown role contracts
│   └── skills/            ← Legacy skill mirror for older Codex surfaces
├── .claude/               ← Claude/Cursor surface (full enforcement)
│   ├── CLAUDE.md          ← Agent instructions and routing rules
│   ├── settings.json      ← Hooks configuration
│   ├── skills/            ← 15 skills (discover, comp, plan, build, upgrade, codex-audit, status, project-status, etc.)
│   ├── agents/            ← 32 specialized subagents (20 base + 12 same-tree variants)
│   └── hooks/             ← 11 hook scripts (intent routing, governance, proof, budget, scope)
├── .vibeos/               ← Shared runtime used by both surfaces
│   ├── scripts/           ← 89 quality gate and utility scripts
│   ├── cache/             ← Generated local evidence recall index
│   ├── autonomy/          ← Generated long-run heartbeat and resume evidence
│   ├── runtime-capabilities.json ← Generated local Codex/Claude capability matrix
│   ├── decision-engine/   ← 10 decision trees
│   ├── reference/         ← 122 annotated reference files plus prompt-engineering guidance
│   └── convergence/       ← 5 scripts that prevent infinite build loops
└── docs/
    ├── planning/          ← Generated development plan and work orders
    ├── product/           ← PRD, architecture, and product anchor
    ├── research/          ← Current evidence for high-impact decisions
    └── decisions/         ← Explicit trade-offs and deviations
```

## Requirements

- Claude Code (CLI or Cursor IDE) — full enforcement
- OpenAI Codex — experimental, capability-detected support
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

That tells VibeOS to stop routine check-ins for the current session and keep building until it hits a real blocker, needs a decision, or finishes the available work. For deliberate 24-48 hour runs, VibeOS records heartbeat, checkpoint, and audit evidence so another session can resume from durable state instead of relying on memory.

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
