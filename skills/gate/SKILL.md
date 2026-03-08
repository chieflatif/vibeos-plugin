---
name: gate
description: Run quality gates for a specific WO lifecycle phase. Use when the user wants to check code quality, run pre-commit checks, validate before completing a work order, or perform a full audit.
argument-hint: "[phase] [--wo NUMBER]"
allowed-tools: Bash, Read, Glob, Grep
---

# /vibeos:gate — Quality Gate Check

Run quality gates for the specified lifecycle phase and report results in plain English.

## Instructions

1. **Determine the phase** from `$ARGUMENTS`:
   - If user specifies a phase (e.g., `pre_commit`, `wo_exit`, `full_audit`), use it
   - If `--wo` is provided without a phase, use `wo_exit`
   - Default to `pre_commit` if no arguments given

2. **Run the gate runner** from the plugin's scripts directory:
   ```bash
   bash "${CLAUDE_SKILL_DIR}/../../scripts/gate-runner.sh" <phase> --continue-on-failure --framework-dir "${CLAUDE_SKILL_DIR}/../.." [--wo NUMBER if provided]
   ```

3. **Report results** clearly:
   - **Lead with the bottom line**: "All gates passed" or "2 blocking failures need attention"
   - **List each gate** with PASS/FAIL/SKIP status
   - **For failures**: explain what the gate checks, why it matters, and what to fix
   - **Distinguish blocking vs advisory**: blocking must be fixed before proceeding, advisory are warnings
   - **Recommend next step**: proceed, fix blockers first, or acknowledge advisories

## Available Phases

| Phase | When to use |
|---|---|
| `pre_commit` | Before committing — fast checks (secrets, security, stubs, lint) |
| `wo_exit` | Before completing a work order — includes pre_commit + architecture, WO validation |
| `full_audit` | Comprehensive compliance check — includes wo_exit + OWASP, PII, tenant isolation |
| `post_deploy` | After deployment — smoke tests, health checks |
| `session_start` | Session prerequisites — tool availability |

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

Skill-specific addenda:
- Distinguish between blocking failures and advisory warnings
- Always recommend a specific next step
