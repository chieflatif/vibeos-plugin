---
name: upgrade
description: Framework upgrade orchestrator that copies new framework files, reconciles configuration, re-evaluates the decision engine against the project, runs all gates and auditors as a discovery sweep (not a baseline), and produces prioritized recommendations for integration and correction. Use when the user says "upgrade VibeOS", "update the framework", "I pulled the latest version", "run the upgrade", or wants to apply a newer version of the VibeOS framework to their project.
argument-hint: "[optional: source path to VibeOS framework, e.g. '/path/to/vibeos-plugin']"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /vibeos:upgrade — Framework Upgrade & Re-Audit

Upgrade the VibeOS framework in a project, reconcile configuration, sweep the entire codebase with all gates and auditors, and produce prioritized recommendations for integration and issue correction. This is NOT a baseline operation — everything found is surfaced as actionable.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

**Skill-specific addenda:**
- Explain what changed between versions in plain English
- Frame gate findings as opportunities, not failures (the project was fine before; these are new checks)
- Clearly distinguish between "new issues found by new gates" and "existing issues found by existing gates"
- Never baseline findings during upgrade — all findings are recommendations until the user decides to act

## Prerequisites

Before starting, verify:
- `.vibeos/` directory exists (project has VibeOS installed)
- `.vibeos/version.txt` or `.vibeos/config.json` exists (version tracking)
- `project-definition.json` exists (needed for decision engine re-evaluation)

If `.vibeos/` doesn't exist, this is a fresh install — tell the user to use `vibeos-init.sh` instead.

## Upgrade Flow

### Step 1: Detect Current State

Read the current framework state:

1. Read `.vibeos/version.txt` for installed version
2. Read `.vibeos/config.json` for project configuration
3. Read `project-definition.json` for project context
4. Inventory current framework files:
   ```bash
   # Count current gate scripts
   ls -1 .vibeos/scripts/*.sh .vibeos/scripts/*.py 2>/dev/null | wc -l
   # Count current decision trees
   ls -1 .vibeos/decision-engine/*.md 2>/dev/null | wc -l
   # Count current agents
   ls -1 .claude/agents/*.md 2>/dev/null | wc -l
   # Count current skills
   find .claude/skills -name "SKILL.md" 2>/dev/null | wc -l
   ```

Store these as `before_counts` for the changelog.

### Step 2: Locate Source Framework

Determine the source of the new framework files:

1. If `$ARGUMENTS` contains a path, use it as the source
2. If not, check `.vibeos/config.json` for `"source_path"`
3. If not, check common locations:
   - `../vibeos-plugin/plugins/vibeos/`
   - `~/vibeos-plugin/plugins/vibeos/`
   - Look for `vibeos-init.sh` in parent directories
4. If source cannot be found, ask the user:
   > "I need the path to your updated VibeOS framework source (the vibeos-plugin repository or the `plugins/vibeos/` directory within it). Where is it located?"

Validate the source has the expected structure:
```bash
test -d "$SOURCE/skills" && test -d "$SOURCE/agents" && test -d "$SOURCE/scripts" && test -d "$SOURCE/decision-engine"
```

### Step 3: Create Pre-Upgrade Snapshot

Before modifying anything, create a snapshot for rollback:

1. Record current file hashes:
   ```bash
   mkdir -p .vibeos/upgrade-snapshots
   TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
   SNAPSHOT_DIR=".vibeos/upgrade-snapshots/${TIMESTAMP}"
   mkdir -p "$SNAPSHOT_DIR"

   # Save current version info
   cp .vibeos/version.txt "$SNAPSHOT_DIR/version.txt" 2>/dev/null || true

   # Save current CLAUDE.md and settings.json for diff
   cp .claude/CLAUDE.md "$SNAPSHOT_DIR/CLAUDE.md" 2>/dev/null || true
   cp .claude/settings.json "$SNAPSHOT_DIR/settings.json" 2>/dev/null || true

   # Save current gate config if it exists
   cp .vibeos/gate-config.json "$SNAPSHOT_DIR/gate-config.json" 2>/dev/null || true
   ```

2. Report to user:
   > "Pre-upgrade snapshot saved. If anything goes wrong, I can restore your previous configuration."

### Step 4: Copy Framework Files

Copy new framework files while preserving project-specific state:

**Always overwrite (framework-owned):**
- `.vibeos/scripts/` — all gate scripts, gate-runner, Python scripts
- `.vibeos/decision-engine/` — all decision trees
- `.vibeos/reference/` — all reference materials
- `.vibeos/convergence/` — convergence scripts
- `.claude/skills/*/SKILL.md` — all skill definitions
- `.claude/agents/*.md` — all agent definitions
- `.claude/hooks/*.sh` — all hook scripts

**Never overwrite (project-owned):**
- `.vibeos/config.json` — project configuration and autonomy settings
- `.vibeos/baselines/` — quality baselines (these are earned, not installed)
- `.vibeos/findings-registry.json` — tracked findings
- `.vibeos/build-log.md` — build history
- `.vibeos/checkpoints/` — resume state
- `.vibeos/session-state.json` — session tracking
- `.vibeos/audit-reports/` — historical audit reports
- `project-definition.json` — project definition
- `docs/planning/` — development plan, WO files, WO index
- `docs/product/` — product anchor, PRD
- `docs/` — all project documentation

**Smart merge (requires reconciliation):**
- `.claude/CLAUDE.md` — update framework references, preserve project customizations
- `.claude/settings.json` — add new hooks, preserve existing configuration

Copy framework-owned files:
```bash
# Scripts
cp "$SOURCE"/scripts/*.sh .vibeos/scripts/ 2>/dev/null || true
cp "$SOURCE"/scripts/*.py .vibeos/scripts/ 2>/dev/null || true
cp "$SOURCE"/scripts/*.json .vibeos/scripts/ 2>/dev/null || true
chmod +x .vibeos/scripts/*.sh 2>/dev/null || true

# Decision engine
cp "$SOURCE"/decision-engine/*.md .vibeos/decision-engine/

# Reference
cp -R "$SOURCE"/reference/* .vibeos/reference/ 2>/dev/null || true

# Convergence
cp "$SOURCE"/convergence/*.sh .vibeos/convergence/ 2>/dev/null || true
chmod +x .vibeos/convergence/*.sh 2>/dev/null || true

# Skills
for skill_dir in "$SOURCE"/skills/*/; do
  skill_name=$(basename "$skill_dir")
  mkdir -p ".claude/skills/$skill_name"
  cp "$skill_dir/SKILL.md" ".claude/skills/$skill_name/SKILL.md"
done

# Agents
cp "$SOURCE"/agents/*.md .claude/agents/

# Hooks
cp "$SOURCE"/hooks/scripts/*.sh .claude/hooks/ 2>/dev/null || true
chmod +x .claude/hooks/*.sh 2>/dev/null || true
```

Update version marker:
```bash
echo "$NEW_VERSION" > .vibeos/version.txt
```

### Step 5: Reconcile CLAUDE.md

Read the current `.claude/CLAUDE.md` and the source's template CLAUDE.md. Intelligently merge:

1. **Update framework file counts** — scan `.vibeos/scripts/`, `.vibeos/decision-engine/`, `.claude/agents/`, `.claude/skills/` and update the architecture section with actual counts
2. **Add new architecture notes** — if the source template has sections not present in the project's CLAUDE.md, add them
3. **Update skill routing rules** — if new skills were added (e.g., `/upgrade`), add routing guidance
4. **Preserve project-specific content** — any sections the user added that aren't in the template should be kept intact
5. **Update conventions** — if new conventions were introduced, add them

Report what changed:
> "Updated your project's CLAUDE.md: [list of changes, e.g., 'updated gate script count from 25 to 37, added upgrade skill routing, added VC audit gate documentation']"

### Step 6: Reconcile settings.json

Read the current `.claude/settings.json` and compare against the expected hook configuration:

1. **Check for missing hooks** — compare current hook entries against the full expected set
2. **Add new hooks** — if new hook scripts were installed that aren't in settings.json, add them
3. **Preserve custom hooks** — any hooks the user added that aren't framework hooks should be kept
4. **Preserve hook ordering** — framework hooks have a defined order; don't rearrange user customizations

If changes are needed, show the user what will change and apply:
> "Your hook configuration needs updating: [adding test-diff-audit hook to PreToolUse, etc.]"

If no changes needed:
> "Hook configuration is up to date."

### Step 7: Re-evaluate Decision Engine

This is the core intelligence of the upgrade — re-running all decision trees against the project to determine what new capabilities should be activated.

1. Read `project-definition.json` for:
   - `stack.language`, `stack.framework`, `stack.database`
   - `governance.deployment_context`
   - `governance.compliance_targets`
   - `ai_provider` (if any)
   - `features` and `workflows`

2. Walk each decision tree and collect recommendations:

   **Gate Selection** (`.vibeos/decision-engine/gate-selection.md`):
   - Determine which of the new gates should be active for this project
   - Classify each as tier 1 (blocking) or tier 2/3 (advisory) based on deployment context
   - Map environment variables for each gate (e.g., `REQUIRE_HEALTH=true`)

   **AI Integration** (`.vibeos/decision-engine/ai-integration-patterns.md`):
   - If project uses AI: classify depth (surface/core_pipeline/autonomous/model_owner)
   - Determine AI-specific gates and WO recommendations
   - Check for provider abstraction needs

   **Observability** (`.vibeos/decision-engine/observability-patterns.md`):
   - If deployment is production+: classify observability depth
   - Recommend stack per language
   - Determine health endpoint requirements

   **Testing Strategy** (`.vibeos/decision-engine/testing-strategy.md`):
   - Re-evaluate test configuration against any new testing requirements

   **Architecture Strategy** (`.vibeos/decision-engine/architecture-strategy.md`):
   - Check if architecture rules need updating for new gate capabilities

   **Development Plan Generation** (`.vibeos/decision-engine/development-plan-generation.md`):
   - Identify new mandatory WO types that should be added to the plan (e.g., AI Cost Control, Observability Foundation)

3. Produce a decision engine summary:
   > "Based on your project definition, here's what the decision engine recommends:
   > - **New gates to activate:** [list with tier and blocking status]
   > - **Gate configuration:** [env vars per gate]
   > - **New WOs recommended:** [list with rationale]
   > - **Architecture rules:** [any new rules to add]"

### Step 8: Full Gate Sweep (Discovery Mode)

Run ALL gate scripts against the project — including newly installed ones. This is a discovery sweep, NOT a baseline operation.

```bash
bash ".vibeos/scripts/gate-runner.sh" pre_commit --project-dir "${CLAUDE_PROJECT_DIR:-.}" --continue-on-failure
```

Additionally, run the new VC audit gates individually to capture detailed output:

```bash
# Run each new gate and capture output
for gate in validate-observability.sh validate-resilience-patterns.sh validate-data-integrity.sh \
            validate-api-contracts.sh validate-auth-boundaries.sh validate-ai-integration.sh \
            validate-code-complexity.sh validate-dev-environment.sh; do
  if [ -f ".vibeos/scripts/$gate" ]; then
    echo "--- $gate ---"
    bash ".vibeos/scripts/$gate" 2>&1 || true
  fi
done
```

Categorize results into three buckets:

1. **Existing gate results** — gates that were already installed. Compare against previous baseline if available. These show whether the project maintained quality.
2. **New gate results** — gates that were just installed. Everything they find is a new discovery. These are opportunities, not regressions.
3. **Enhanced gate results** — gates that were upgraded with new checks. New findings from enhanced checks are discoveries.

**Do NOT update baselines.** Do NOT run `baseline-check.sh ratchet`. The baseline stays where it was. New findings are surfaced as recommendations.

### Step 9: Full Audit Cycle (Discovery Mode)

Dispatch all 6 audit agents with their enhanced capabilities:

1. Dispatch agents (in parallel where possible):
   - `agents/security-auditor.md` — now includes auth boundary coverage, supply chain analysis
   - `agents/architecture-auditor.md` — standard checks
   - `agents/correctness-auditor.md` — now includes data integrity, concurrency checks
   - `agents/test-auditor.md` — standard checks
   - `agents/evidence-auditor.md` — standard checks
   - `agents/product-drift-auditor.md` — now includes feature completeness, IP originality

2. Apply consensus logic (2+ agents = true positive, 1 = warning)

3. Categorize findings as:
   - **New capability findings** — found by enhanced agent capabilities that didn't exist before
   - **Existing findings** — found by capabilities that were already present
   - **Already tracked** — findings that match entries in `.vibeos/findings-registry.json`

**Do NOT baseline these findings.** They are recommendations until the user acts.

### Step 10: Generate Upgrade Report

Produce a comprehensive upgrade report. Display to user and save to `.vibeos/upgrade-reports/upgrade-[timestamp].md`:

```
## VibeOS Upgrade Report

**Date:** [today]
**Previous version:** [from snapshot]
**New version:** [current]

### What Changed

| Category | Before | After | Delta |
|---|---|---|---|
| Gate scripts | [N] | [N] | +[N] new |
| Decision trees | [N] | [N] | +[N] new |
| Agents | [N] | [N] | [N] enhanced |
| Skills | [N] | [N] | +[N] new |
| Hook scripts | [N] | [N] | [changes] |

**New capabilities:**
- [List each new gate with 1-line description]
- [List each enhanced agent capability]
- [List each new decision tree]
- [List new skills]

### Configuration Reconciliation

- **CLAUDE.md:** [changes made]
- **settings.json:** [changes made]
- **Decision engine:** [new recommendations]

### Decision Engine Recommendations

**Newly recommended gates for this project:**

| Gate | Tier | Blocking | Rationale |
|---|---|---|---|
| [gate-name] | [tier] | [yes/no] | [why this project needs it] |

**Newly recommended WOs:**

| WO Title | Phase | Rationale |
|---|---|---|
| [title] | [suggested phase] | [why] |

### Gate Sweep Results (Discovery — Not Baselined)

**Existing gates:**

| Gate | Status | Notes |
|---|---|---|
| [gate] | [PASS/FAIL] | [summary] |

**New gates (first-time findings):**

| Gate | Status | Findings | Top Issue |
|---|---|---|---|
| [gate] | [PASS/FAIL] | [count] | [description] |

### Audit Results (Discovery — Not Baselined)

| Auditor | Findings | New Capability Findings | Top Issue |
|---|---|---|---|
| Security | [N] | [N from new checks] | [description] |
| Architecture | [N] | [N] | [description] |
| Correctness | [N] | [N from new checks] | [description] |
| Test Quality | [N] | [N] | [description] |
| Evidence | [N] | [N] | [description] |
| Product Drift | [N] | [N from new checks] | [description] |

### Prioritized Recommendations

#### Fix Now (blocking issues or security risks)

| # | Finding | Source | Severity | File | Recommendation |
|---|---|---|---|---|---|
| 1 | [description] | [gate/auditor] | [severity] | [path] | [fix] |

#### Integrate Soon (high-value improvements from new capabilities)

| # | Finding | Source | Category | Recommendation |
|---|---|---|---|---|
| 1 | [description] | [gate/auditor] | [category] | [what to do] |

#### Integrate When Ready (advisory improvements)

| # | Finding | Source | Category | Recommendation |
|---|---|---|---|---|
| 1 | [description] | [gate/auditor] | [category] | [what to do] |

### Suggested Next Steps

1. [Most impactful action]
2. [Second most impactful]
3. [Third most impactful]

**To create work orders for these recommendations:**
> "Create WOs for the upgrade recommendations"

**To run the full build loop with the new framework:**
> "Continue building" or "Keep going"

**To baseline the current state (after addressing fix-now items):**
> "Run a checkpoint" or "Baseline the project"
```

### Step 11: Offer Action Plan

After presenting the report, offer the user options:

> "The upgrade is complete and I've swept your entire project with the new capabilities. Here's what I recommend:
>
> Your options:
> 1. **Create WOs for recommendations** — I'll generate work orders for the fix-now and integrate-soon items and add them to your development plan.
>    - Pros: formalizes the work with proper tracking, dependencies, and acceptance criteria
>    - Cons: adds planning overhead before fixes begin
> 2. **Fix critical issues now** — I'll immediately address the fix-now items without formal WOs.
>    - Pros: fastest path to resolving blocking issues
>    - Cons: less formal tracking of what was changed and why
> 3. **Review and decide** — You review the findings and tell me which ones to address.
>    - Pros: maximum control over what gets changed
>    - Cons: requires your time to review each finding
> 4. **Continue building** — Accept the upgrade, park the recommendations, and resume the development plan.
>    - Pros: maintains momentum on feature work
>    - Cons: recommendations remain unaddressed and may compound
>
> I recommend option 1 for fix-now items and option 4 for integrate-when-ready items — this addresses critical issues formally while keeping momentum on your roadmap."

## Rollback

If the user says "roll back the upgrade" or "undo the upgrade":

1. Find the most recent snapshot in `.vibeos/upgrade-snapshots/`
2. Restore `.claude/CLAUDE.md` and `.claude/settings.json` from snapshot
3. Restore `.vibeos/version.txt` from snapshot
4. Re-run `vibeos-init.sh --upgrade` with the previous source (if available)
5. Report what was restored

> "Rolled back to your previous configuration from [timestamp]. Framework files, CLAUDE.md, and settings.json have been restored."

If no snapshot exists:
> "No upgrade snapshot found. I can't automatically roll back, but I can help you manually restore specific files if needed."

## Version Tracking

After a successful upgrade, update `.vibeos/config.json` with upgrade metadata:

```json
{
  "last_upgrade": {
    "date": "ISO-8601",
    "from_version": "previous",
    "to_version": "current",
    "source_path": "/path/to/source",
    "snapshot_path": ".vibeos/upgrade-snapshots/TIMESTAMP",
    "findings_at_upgrade": {
      "fix_now": N,
      "integrate_soon": N,
      "integrate_when_ready": N
    }
  }
}
```

## Error Handling

- If source validation fails: ask user for correct path
- If file copy fails: report which files failed, continue with others
- If a gate script fails to execute (not fail-as-in-findings, but crash): log the error, skip that gate, continue
- If an audit agent fails: log, continue with remaining agents
- If CLAUDE.md reconciliation is ambiguous: show the user both versions and ask which to keep
- Never lose project-owned files — the preserved list is sacrosanct

## Output Summary

| Artifact | Path | Purpose |
|---|---|---|
| Upgrade report | `.vibeos/upgrade-reports/upgrade-[timestamp].md` | Full upgrade analysis |
| Pre-upgrade snapshot | `.vibeos/upgrade-snapshots/[timestamp]/` | Rollback capability |
| Updated config | `.vibeos/config.json` | Upgrade metadata |
| Updated CLAUDE.md | `.claude/CLAUDE.md` | Reconciled framework references |
| Updated settings.json | `.claude/settings.json` | Reconciled hook configuration |
| Framework files | `.vibeos/`, `.claude/skills/`, `.claude/agents/`, `.claude/hooks/` | New framework version |
