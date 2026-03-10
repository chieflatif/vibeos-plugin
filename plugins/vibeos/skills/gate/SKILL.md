---
name: gate
description: Run quality gates for a specific WO lifecycle phase. Use when the user says "check the code", "run quality checks", "are we passing?", "validate this", or wants to run pre-commit checks or verify code quality before completing a work order.
argument-hint: "[phase] [--wo NUMBER]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# /vibeos:gate — Quality Gate Check

Run quality gates for the specified lifecycle phase and report results in plain English.

## Instructions

Parse `$ARGUMENTS` to determine the subcommand:

### Subcommand: Run Gates (default)

If `$ARGUMENTS` is a phase name (`pre_commit`, `wo_exit`, `full_audit`, `post_deploy`, `session_start`), `--wo`, or empty:

1. **Determine the phase** from `$ARGUMENTS`:
   - If user specifies a phase (e.g., `pre_commit`, `wo_exit`, `full_audit`), use it
   - If `--wo` is provided without a phase, use `wo_exit`
   - Default to `pre_commit` if no arguments given

2. **Run the gate runner** from the plugin's scripts directory:
   ```bash
   bash ".vibeos/scripts/gate-runner.sh" <phase> --continue-on-failure --framework-dir ".vibeos" [--wo NUMBER if provided]
   ```

3. **Report results** clearly:
   - **Lead with the bottom line**: "All gates passed" or "2 blocking failures need attention"
   - **List each gate** with PASS/FAIL/SKIP status
   - **For failures**: explain what the gate checks, why it matters, and what to fix
   - **Distinguish blocking vs advisory**: blocking must be fixed before proceeding, advisory are warnings
   - **Recommend next step**: proceed, fix blockers first, or acknowledge advisories

### Subcommand: `list`

If `$ARGUMENTS` is `list`:

1. Read `scripts/quality-gate-manifest.json` from the project root
2. Present a formatted table of all gates:

> **Quality Gates**
>
> | Gate | Status | Tier | Blocking | Phase | Compliance |
> |---|---|---|---|---|---|
> | [name] | Enabled/Disabled | [0-3] | Yes/No | [phase] | [target or —] |
>
> **[N] gates total:** [enabled] enabled ([blocking] blocking, [advisory] advisory), [disabled] disabled.

3. Explain tier meaning on first use:
   > "Tier 0 = always on, Tier 1 = important (blocking by default), Tier 2 = recommended (advisory), Tier 3 = optional."

### Subcommand: `enable <gate-name>`

If `$ARGUMENTS` starts with `enable`:

1. Read `scripts/quality-gate-manifest.json`
2. Find the gate by name (match against `script` field, strip `.sh` extension for matching)
3. If not found: list available gates and suggest closest match
4. If already enabled: inform user, no action needed
5. Set `enabled: true` (or add field if missing) in the manifest
6. Write updated manifest
7. Explain what the gate checks:
   > "Enabled **[gate-name]**. This gate checks [plain English description of what it validates]. It runs during the [phase] phase."

### Subcommand: `disable <gate-name>`

If `$ARGUMENTS` starts with `disable`:

1. Read `scripts/quality-gate-manifest.json`
2. Find the gate by name
3. **Check compliance lock:** If the gate has a `compliance_locked` field set to `true`, or if the gate's tier is 0:
   > "Cannot disable **[gate-name]** — [reason]. [If compliance]: This gate is required by your [compliance target]. [If tier 0]: This is a core safety gate that catches [critical issue type]."
   Stop. Do not disable.
4. If not locked, present consequences before disabling:
   > "Disabling **[gate-name]** means [specific quality check] won't run during [phase].
   >
   > Your options:
   > 1. **Keep it enabled** — leave the protection in place.
   >    - Pros: safer default and fewer gaps in your quality checks
   >    - Cons: may slow progress if this gate is noisy or not yet configured well
   >    - Technical note: the gate continues to run on its configured phase
   > 2. **Disable it for now** — stop running this gate until you re-enable it.
   >    - Pros: removes immediate friction
   >    - Cons: [specific risk in plain English] could slip through without being checked
   >    - Technical note: you can re-enable it later with `/vibeos:gate enable [gate-name]`
   >
   > I recommend option 1 unless this gate is clearly misconfigured, because disabling a gate removes a safety check from your workflow."
5. Wait for user confirmation
6. Set `enabled: false` in the manifest
7. Write updated manifest
8. Log to `.vibeos/build-log.md`: `[timestamp] gate-config disable [gate-name] [user-confirmed]`

## Available Phases

| Phase | When to use |
|---|---|
| `pre_commit` | Before committing — fast checks (secrets, security, stubs, lint) |
| `wo_exit` | Before completing a work order — includes pre_commit + architecture, WO validation |
| `full_audit` | Comprehensive compliance check — includes wo_exit + OWASP, PII, tenant isolation |
| `post_deploy` | After deployment — smoke tests, health checks |
| `session_start` | Session prerequisites — tool availability |

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

Skill-specific addenda:
- Distinguish between blocking failures and advisory warnings
- Always recommend a specific next step
- Explain in plain English first; add technical detail only when it helps the user understand the risk
- When the user must choose, include options, pros, cons, and a recommendation
