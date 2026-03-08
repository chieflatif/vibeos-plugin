---
name: plan
description: Run project intake questionnaire, apply decision engine, and generate a complete development plan with phased work orders. Use after /vibeos:discover has produced product documents.
argument-hint: "[optional: path to project-definition.json]"
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
---

# /vibeos:plan — Project Planning & Intake

Turn validated product documents into a complete development plan with governance setup.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

**Skill-specific addenda:**
- Present inferred defaults explicitly: "I inferred X from your product definition. Keep or change?"
- Before each question, briefly explain what you're asking and why it matters

## Prerequisites

Before starting, verify these exist (from `/vibeos:discover`):
- `project-definition.json` in the project root
- `docs/product/PRD.md`
- `docs/product/ARCHITECTURE-OUTLINE.md` or `docs/ARCHITECTURE.md`

If any are missing, tell the user to run `/vibeos:discover` first.

## Planning Flow

### Step 1: Load Discovery Context

Read `project-definition.json` from the project root (or `$ARGUMENTS` path if provided).

Extract pre-filled values for:
- Project name, slug, description
- Product type, platforms
- Sensitive data, compliance targets
- Technical recommendation (language, framework, database)
- Governance profile (team size, risk level, deployment context)

Tell the user what was found:
> "I found your project definition from discovery. Here's what I already know: [summary]. I'll confirm a few things and fill in the remaining details."

### Step 1b: Midstream Detection

Check if the project has existing source code:

1. Look for source directories: `src/`, `lib/`, `app/`, `pkg/`, `cmd/`, `internal/`
2. Look for language indicators: `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, `*.csproj`, `Gemfile`, `composer.json`
3. Count source files (excluding test files and generated files)

**If existing code is found (midstream project):**

Tell the user:
> "I detected existing source code in this project ([N] files across [directories]). I'll run a baseline audit to understand the current state before planning new work."

Then run the midstream baseline flow:

1. Run all gates: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/gate-runner.sh" pre_commit --project-dir "${CLAUDE_PROJECT_DIR:-.}"`
2. Dispatch all 5 audit agents following `skills/audit/SKILL.md` protocol
3. Collect and merge all findings with consensus logic

Store the baseline:
```bash
mkdir -p .vibeos/baselines
```
Write `.vibeos/baselines/midstream-baseline.json`:
```json
{
  "type": "midstream",
  "date": "ISO-8601",
  "source_files": N,
  "gates": { "total": N, "passed": N, "failed": N },
  "findings": {
    "critical": N, "high": N, "medium": N, "low": N,
    "total": N, "all_pre_existing": true
  }
}
```

For critical and high findings, create remediation WOs:
- Read the WO template from `${CLAUDE_PLUGIN_ROOT}/reference/governance/WO-TEMPLATE.md.ref`
- Create one WO per critical finding, group related high findings into WOs
- Add remediation WOs to the development plan (Phase 0: Remediation)
- Mark all findings as "pre-existing" — they don't block new work

Report to user:
> "Here's the current state of your codebase:
> - [N] quality gates passed, [M] failed
> - [critical] critical, [high] high, [medium] medium, [low] low findings
>
> These are pre-existing issues. They won't block your new work, but I've created [K] remediation work orders to track improvements.
>
> [Top 3 findings explained in plain English]"

**If no existing code (greenfield project):**

Skip midstream flow. Continue to Step 2.

### Step 2: Run Project Intake Questionnaire

Run the 18-question intake from 4 rounds. **Pre-fill from project-definition.json** — only ask questions where the answer is missing, confidence is low, or impact is high enough to justify confirmation.

#### Round 1: Project Identity (Q1-Q4)

| # | Question | Pre-fill Source |
|---|---|---|
| Q1 | Project name | `idea.name.value` |
| Q2 | Project slug (lowercase, hyphens) | Derive from Q1 |
| Q3 | One-line description | `idea.summary.value` |
| Q4 | Repository URL (optional) | Ask if not set |

Validate Q2 matches `^[a-z][a-z0-9-]*$`.

#### Round 2: Technical Stack (Q5-Q10)

| # | Question | Pre-fill Source |
|---|---|---|
| Q5 | Primary language | `technical_recommendation.language.value` |
| Q6 | Framework | `technical_recommendation.framework.value` |
| Q7 | Source directories | Derive from language convention |
| Q8 | Test directory | Derive from language convention |
| Q9 | Package manager | Derive from language |
| Q10 | Database | `technical_recommendation.database.value` |

For each pre-filled answer with medium+ confidence, present it:
> "I inferred [language] based on your product type. Keep or change?"

For low-confidence or missing answers, ask the full question with options, pros/cons, and recommendation.

Framework options are filtered by language:
- python: fastapi, django, flask, none
- typescript: express, nestjs, nextjs, none
- javascript: express, nextjs, react-only, none
- go: gin, echo, chi, none
- rust: actix, axum, rocket, none
- java: spring-boot, quarkus, none

#### Round 3: Governance Profile (Q11-Q15)

| # | Question | Pre-fill Source |
|---|---|---|
| Q11 | Team size (solo/small/enterprise) | `governance_profile.team_size.value` |
| Q12 | Compliance targets (soc2/gdpr/owasp/none) | `constraints.compliance_targets` |
| Q12b | Deployment context (prototype/production/customer-facing/scale) | `governance_profile.deployment_context.value` |
| Q13 | Work order directory | Default: `docs/planning/` |
| Q14 | Frozen files (never edit) | Ask |
| Q15 | Production URLs (never target) | Ask |

**Solo compliance warning**: If team_size is "solo" AND compliance targets are not "none":
> "Running full compliance governance as a solo developer adds overhead. I recommend starting with compliance gates at tier 2 (important but non-blocking) until your team grows. Options: (a) Keep tier 1 (full enforcement), (b) Set to tier 2 (recommended), (c) Set to tier 3 (advisory only)"

#### Round 4: Agent Preferences (Q16-Q18)

| # | Question | Pre-fill Source |
|---|---|---|
| Q16 | Cloud provider (azure/aws/gcp/vercel/none) | Ask or infer |
| Q17 | CI/CD platform (github-actions/gitlab-ci/azure-devops/none) | Ask or infer |
| Q18 | MCP servers (comma-separated or none) | Ask |

### Step 3: Validate and Confirm

After all answers are collected, validate:
1. `project.name` is not empty
2. `project.slug` matches `^[a-z][a-z0-9-]*$`
3. `stack.language` is in [python, typescript, javascript, go, rust, java]
4. `stack.source_dirs` — warn if directories don't exist yet
5. `governance.team_size` is in [solo, small, enterprise]
6. `governance.compliance_targets` is a non-empty list
7. `governance.deployment_context` is in [prototype, production, customer-facing, scale]

Present a complete summary showing each field and its source (user-confirmed, inferred from discovery, or defaulted). Ask:
> "Does this look correct? [Y/n]"

If the user says no, ask what to change, update, re-validate.

Write the final answers to `project-definition.json` in the project root, merging with existing discovery data. Use the full answer schema:

```json
{
  "project": { "name": "", "slug": "", "description": "", "repo_url": "" },
  "stack": { "language": "", "framework": "", "source_dirs": [], "test_dir": "", "package_manager": "", "database": "" },
  "governance": { "team_size": "", "compliance_targets": [], "deployment_context": "", "wo_dir": "", "frozen_files": [], "production_urls": [] },
  "agent": { "cloud_provider": "", "ci_cd_platform": "", "mcp_servers": [] }
}
```

### Step 4: Apply Decision Engine

Read and apply the 5 decision engine trees from `${CLAUDE_SKILL_DIR}/../../decision-engine/`:

#### 4a. Gate Selection (`gate-selection.md`)

Determine which of the gate scripts to enable based on:
- `stack.language` and `stack.database`
- `governance.compliance_targets`
- `governance.production_urls`
- `governance.deployment_context`

Produces: list of enabled gates with tier, blocking status, and config.

#### 4b. Phase Selection (`phase-selection.md`)

Determine which gate phases to enable based on:
- `governance.team_size`
- `governance.compliance_targets`
- `governance.production_urls`

Produces: list of enabled phases with gate assignments.

#### 4c. Hook Selection (`hook-selection.md`)

Determine which hooks to enable based on:
- Agent type (claude-code for this plugin)
- `governance.production_urls`
- `governance.frozen_files`
- `governance.compliance_targets`

Produces: list of enabled hooks with config.

#### 4d. Architecture Rules (`architecture-rules.md`)

Select architecture enforcement rules based on:
- `stack.language`
- `stack.framework`
- `stack.source_dirs`

Produces: `architecture-rules.json` with framework-specific rules.

#### 4e. Compliance Mapping (`compliance-mapping.md`)

Map compliance targets to gate tiers, evidence requirements, and documentation:
- SOC 2: evidence bundles, audit completeness
- GDPR: PII handling, tenant isolation
- OWASP: security patterns strict mode
- Combined: union of all rules

Produces: tier overrides and compliance-specific configuration.

Tell the user what the decision engine determined:
> "Based on your project profile, here's the governance setup: [N] gates enabled, [M] phases active, [K] hooks configured. [summary of key decisions]"

### Step 5: Generate Development Plan

Read `${CLAUDE_SKILL_DIR}/../../decision-engine/development-plan-generation.md` for the plan structure.

Read `${CLAUDE_SKILL_DIR}/../../reference/governance/DEVELOPMENT-PLAN.md.ref` for the output template.

Generate `docs/planning/DEVELOPMENT-PLAN.md` with:

1. **Phase 1: Foundation** — scaffold, shared packages, database, auth, config baseline
2. **Phase 2..N: Core Workflows** — one phase per `scope.core_workflows` from project-definition.json, ordered by dependencies and critical path
3. **Phase N+1..: V1 Features** — remaining features from `scope.v1_features`
4. **Conditional production phases** based on `governance.deployment_context`:
   - IF production+: Security headers, health probes, structured logging, input validation
   - IF customer-facing+: Observability, resilience, security hardening

Each WO in the plan must have:
- WO number
- Title
- Dependencies (other WO numbers)
- Status (Draft)
- Objective
- Acceptance criteria

Order WOs so dependencies complete before dependents. Typical WO size: one feature area or one integration.

### Step 6: Generate WO Index

Read `${CLAUDE_SKILL_DIR}/../../reference/governance/WO-INDEX.md.ref` for the template.

Generate `docs/planning/WO-INDEX.md` with all WOs listed, organized by phase, with columns:
- WO Number
- Title
- Phase
- Dependencies
- Status

### Step 7: Mechanical Setup

#### 7a. Create Project Directory Structure

Create the standard directories based on stack:
- `{source_dirs}` from intake
- `{test_dir}` from intake
- `{wo_dir}` from intake (default: `docs/planning/`)
- `docs/` for documentation
- `.claude/` for Claude Code configuration

#### 7b. Generate Gate Manifest

Create `scripts/quality-gate-manifest.json` in the target project with the gate selection results:

```json
{
  "gates": [
    { "script": "filename.sh", "tier": 0, "blocking": true, "phase": "pre_commit", "config": {} }
  ],
  "phases": { "phase_name": { "gates": [], "enabled": true } }
}
```

#### 7c. Generate Hook Manifest

Create `.claude/hook-manifest.json` in the target project with hook selection results:

```json
{
  "hooks": [
    { "name": "hook-name", "event": "PreToolUse", "config": {} }
  ]
}
```

#### 7d. Generate Architecture Rules

Create `scripts/architecture-rules.json` in the target project with the rules from Step 4d.

#### 7e. Copy Gate Scripts

Copy gate scripts from `${CLAUDE_SKILL_DIR}/../../scripts/` to the target project's `scripts/` directory.

#### 7f. Generate CLAUDE.md

Generate the target project's `CLAUDE.md` with:
- Project name and description
- Architecture reference
- Technology stack
- Governance rules (frozen files, compliance)
- Quality gate commands
- Agent constraints

### Step 8: Autonomy Negotiation

After the plan is generated and setup is complete, negotiate how much control the user wants to retain during autonomous build.

Present three options in plain English:

> "Before we start building, I want to understand how you'd like to work together. Here are three modes:"

**Option A — Stop after every work order (most control):**
> "I'll build one thing at a time and check in with you after each piece. You'll see what was built and approve before I continue. Best if this is your first time using VibeOS or you want to stay closely involved."

**Option B — Stop after every phase (recommended):**
> "I'll build a complete group of related features, then check in. You'll see a working chunk before I move to the next group. Good balance of speed and oversight."

**Option C — Stop at major decisions only (most autonomous):**
> "I'll build continuously and only pause when I hit something that needs your input — like a design choice or an unexpected problem. Fastest, but you'll see less intermediate work."

Make a recommendation:
> "I recommend **Option B** (stop after every phase) for this project because [reason based on project complexity, team size, and risk level]. You can change this later."

Store the selection in `.vibeos/config.json`:

```json
{
  "autonomy": {
    "level": "wo|phase|major",
    "negotiated_at": "ISO-8601 timestamp"
  }
}
```

Create the `.vibeos/` directory if it doesn't exist.

### Step 9: Gate Readiness

Before completing, verify all outputs exist:
- [ ] `project-definition.json` updated with full intake answers
- [ ] `docs/planning/DEVELOPMENT-PLAN.md` generated with phases and WOs
- [ ] `docs/planning/WO-INDEX.md` generated with all WOs
- [ ] `scripts/quality-gate-manifest.json` generated
- [ ] `.claude/hook-manifest.json` generated
- [ ] `scripts/architecture-rules.json` generated
- [ ] Gate scripts copied
- [ ] Project directories created
- [ ] `CLAUDE.md` generated for target project
- [ ] `.vibeos/config.json` created with autonomy selection

Report the result:
> "Planning is complete. Here's your development plan:
> - [N] phases with [M] work orders
> - [K] quality gates configured ([B] blocking)
> - [H] hooks enabled
> - Governance profile: [team_size], [compliance], [deployment_context]
>
> Your next step is to start building. Run `/vibeos:build` to begin WO-001, or use `/vibeos:status` to see the full plan."

If any gate fails, explain what's missing and offer to fix it.

## Output Summary

| Artifact | Path | Purpose |
|---|---|---|
| project-definition.json | project root | Updated with full intake answers |
| DEVELOPMENT-PLAN.md | docs/planning/ | Phased work orders |
| WO-INDEX.md | docs/planning/ | Work order tracking |
| quality-gate-manifest.json | scripts/ | Gate configuration |
| hook-manifest.json | .claude/ | Hook configuration |
| architecture-rules.json | scripts/ | Architecture enforcement rules |
| Gate scripts | scripts/ | Quality gate scripts |
| CLAUDE.md | project root | Agent instructions |
| config.json | .vibeos/ | Autonomy configuration |
