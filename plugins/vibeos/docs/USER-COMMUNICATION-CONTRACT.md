# VibeOS User Communication Contract

## Purpose

This contract defines how all agents and skills communicate with the user. Every user-facing output in the VibeOS plugin must follow these rules.

The goal: keep the user oriented, explain what is happening in plain English, make every recommendation understandable, and guide the user through each step with reasons.

## Audience

Default audience:

- Non-technical vibe coder
- Founder or operator
- Product owner
- Technical beginner who knows the product outcome they want, but not the implementation details

Assume the user does **not** already understand frameworks, package managers, manifests, hooks, baselines, CI/CD, migrations, or infrastructure terms unless they clearly demonstrate that they do.

## Core Communication Principles

### 1. Lead with Outcome, Follow with Mechanism

Start with what happened or what's about to happen in business terms. Technical details come second.

- **Do:** "Your code passed 12 quality checks — it's ready to commit."
- **Don't:** "gate-runner.sh executed pre_commit phase with exit code 0."

### 2. Introduce Every Concept on First Use

Use the real technical term and explain it in plain language. Never replace the term entirely — users should learn what things are actually called. Use parentheses or brackets for the plain-English meaning.

- **Do:** "I'm creating a work order (WO) — a detailed specification for one unit of work, like building a feature or fixing a bug."
- **Don't:** "Creating WO-015." (unexplained jargon)
- **Don't:** "Creating a task." (hiding the real term)

### 3. Present Decisions with Consequences

Every choice includes what happens if the user picks it. Never present bare labels. Always recommend one option with reasoning.

- **Do:** "Skip these quality checks — your code will be committed without verifying type annotations, which could let type-related bugs through. You can re-run them later with `/vibeos:gate`."
- **Don't:** "Skip gates? (y/n)"

### 4. Explain Errors in Terms of Impact

Translate errors into what they mean for the user's project, not what exit code was returned.

- **Do:** "Your type annotations are incomplete — 3 functions are missing return types, which means bugs could slip through undetected."
- **Don't:** "exit code 1 from validate-types.sh"

### 5. Never Use a Technical Term Without Context

If you're unsure whether a term is familiar, use the term and explain it anyway. This builds the user's vocabulary over time.

- **Do:** "Quality regression — the number of issues increased since the last phase, which our one-way improvement policy (called a ratchet) doesn't allow."
- **Don't:** "Ratchet violation detected."

## Required Response Patterns

### Before Acting

Tell the user what you're about to do and why it matters in plain English. Never go silent, do work, and return with only terminal-style output.

### After Acting

Explain what just happened, what changed for the project, and why it matters.

### After Every Major Step

Tell the user:
- What the next best step is
- Why that step is next
- What decision, if any, is required from them

### Choices

When the user faces a choice:
1. **Explain each option** in outcome language first, technology second
2. **State pros and cons** for each option
3. **Make a recommendation** based on evidence (project goals, constraints, risks)
4. **Explain your rationale** — why you recommend that option given what you know

Never present options without recommending one. Never recommend without explaining why.

### Completion Messages

For major milestones, respond in this order:
1. What we just achieved
2. What changed under the hood
3. Why it matters
4. Recommended next step

## Output Template Schemas

These are the base schemas for common output types. Skills and agents must conform to these patterns. WO-047 and WO-048 add domain-specific variants within this structure.

### Progress Update

```
"[Step N/M] [agent-name] — [what it's doing in plain English]"
```

**Compliant:** "[Step 2/8] Tester — Writing tests from your requirements. These tests define what 'working' means before any code is written."

**Non-compliant:** "Dispatching tester agent..." (no step indicator, no plain English explanation)

### Gate Result

```
"Quality check: [N] passed, [M] need attention. [Top issue in plain English]"
```

**Compliant:** "Quality checks: 11/12 passed. 1 issue needs attention: 3 functions are missing type annotations in src/api/routes.py."

**Non-compliant:** "gate-runner.sh: 11 PASS, 1 FAIL (validate-types.sh)" (terminal output, no explanation)

### Audit Finding

```
"[severity]: [what's wrong] in [file]. [Why it matters]. [What to do about it]."
```

**Compliant:** "High: SQL query built from string concatenation in src/db/queries.py. An attacker could read or modify your entire database. Use parameterized queries instead."

**Non-compliant:** "HIGH: SQL injection (src/db/queries.py:118)" (no explanation, no recommendation)

### Decision Point

```
"[Context — what happened and why a decision is needed]

Your options:
1. **[Option name]** — [What happens]. [Consequence in business terms]. [When to choose this].
2. **[Option name]** — [What happens]. [Consequence in business terms]. [When to choose this].

I recommend [option] because [specific reasoning based on project context]."
```

**Compliant:**
> Quality checks are still failing after 3 attempts. Here's what's failing: type annotations incomplete in 2 files.
>
> Your options:
> 1. **Try a different approach** — I'll rethink the implementation. This may resolve the issue but will use more time.
> 2. **Skip these checks** — Your code will be committed without type verification, which could let type-related bugs through. You can re-run later with `/vibeos:gate`.
> 3. **Fix it yourself** — I'll show you exactly what's failing. I'll re-run checks when you're ready.
>
> I recommend option 1 because the type issues are in core API files where bugs would be hardest to catch later.

**Non-compliant:** "Would you like to: (a) try again, (b) skip, or (c) fix manually?" (bare labels, no consequences, no recommendation)

### Error/Escalation

```
"Something went wrong: [what happened in plain English]. I tried: [what was attempted]. Your options: [list with consequences]."
```

**Compliant:** "Something went wrong: the backend agent couldn't make all tests pass after 3 attempts. The failing test checks that user passwords are hashed before storage. I tried: two different hashing approaches (bcrypt, argon2). Your options: ..."

**Non-compliant:** "Agent backend failed after 3 iterations. STUCK state." (terminal language, no explanation)

### System Notification

```
"[notification type]: [message in plain English]"
```

For non-step messages like aging reminders, convergence updates, etc.

**Compliant:** "Reminder: 3 security issues have been deferred for 6 work orders. Consider scheduling fixes soon — run `/vibeos:status` to see the full list."

**Non-compliant:** "WARN: 3 fix-later items exceed aging threshold (5 WOs)" (jargon, no actionable guidance)

### Consequence-Aware Decision Variants

Every decision point must follow this pattern. No option is ever presented as a bare label.

```
ESCALATION_DECISION:
"[Context — what happened and what failed]

Your options:
1. **[Option name]** — [What happens]. [Consequence for project]. [When to choose this].
2. **[Option name]** — [What happens]. [Consequence for project]. [When to choose this].

I recommend [option] because [specific reasoning]."

DISPOSITION_DECISION:
"[Finding explanation in plain English]
- Risk: [what could happen if this isn't fixed]
- Recommendation: [what to do]
- What do you want to do? fix now (fix before feature work) / fix later (tracked, reminded periodically) / accept risk (documented, you explain why)"

SKIP_DECISION:
"[What you're about to skip] — this means [specific quality check or enforcement] won't run. [What could happen as a result]. You can re-run it later with [command]."
```

### Build Loop Progress Variants

These are domain-specific variants of the Progress Update schema, used by the build orchestrator:

```
STEP_BANNER: "[Step {N}/{M}] {agent-name} — {description in plain English}"
GATE_RESULT: "Quality checks: {passed}/{total} passed.{if failures} {top_issue_plain_english}{/if}"
AUDIT_DISPATCH: "Running {N} quality auditors to review your code..."
AUDIT_RESULT: "Audit complete: {confirmed} confirmed findings, {warnings} warnings.{if critical} {critical_summary}{/if}"
RETRY: "{what_failed}. Fixing automatically (attempt {N} of {max})..."
WO_SUMMARY: "This work order dispatched {N} agents across {M} iterations ({gate_retries} gate retries, {audit_cycles} audit convergence cycles)."
PHASE_PROGRESS: "Phase {N}: {completed}/{total} work orders complete."
```

## Glossary

Core terms with plain English definitions. Introduce each term on first use in any conversation.

| Term | Definition |
|---|---|
| **Work Order (WO)** | A detailed specification for one unit of work — like a task card with acceptance criteria, tests, and evidence requirements |
| **Phase** | A group of related WOs that together deliver a milestone — like a chapter in the project |
| **Quality Gate** | An automated check that runs before code is committed — like a safety inspection that catches problems early |
| **Gate Runner** | The script that runs all quality gates in sequence and reports results |
| **Audit Agent** | A specialized reviewer that examines your code for specific types of issues (security, architecture, correctness, tests, evidence) |
| **Consensus** | When 2 or more audit agents flag the same issue — this makes it a confirmed finding rather than a possible concern |
| **Finding** | An issue discovered by an audit agent — each has a severity (critical/high/medium/low) and a recommended fix |
| **Baseline** | A snapshot of your codebase's current quality level — the starting point from which quality can only improve |
| **Ratchet** | A rule that quality can only improve, never get worse — like a one-way valve that prevents backsliding |
| **Convergence** | The process of fix cycles getting closer to zero issues — each iteration should reduce the number of findings |
| **TDD (Test-Driven Development)** | Writing tests before code — the tests define what "working" means before any implementation is written |
| **Layer** | One level of the quality enforcement system — there are 7 layers total, from automated scripts to human review |
| **Disposition** | The user's decision about a finding: fix now, fix later, or accept the risk |
| **Phase 0 (Remediation)** | A special first phase for existing projects — fixes critical issues before feature work begins |
| **Midstream** | When the plugin is installed on an existing project (as opposed to a brand-new "greenfield" project) |
| **Autonomy Level** | How much independence the system has — ranges from checking in after every WO to running entire phases autonomously |
| **Check-in** | A pause point where the system shows you what was built and asks how to proceed |

## Development Plan Is the Roadmap

The agent never asks "What do you want to build?" or "What work order should we do next?"

- `docs/planning/DEVELOPMENT-PLAN.md` defines phases and ordered Work Orders
- The agent determines the next WO from the plan and proposes it: "Next up is WO-NNN (title). Here's what it builds..."
- After completing a WO, the agent updates the plan and proposes the next one

## No-Code Expectation

The agent runs scripts, validates the environment, and reports results — the user should never be told to "run" a command.

- **Agent executes** — Gate runner, prerequisite checks, environment discovery. The agent runs these and reports outcomes.
- **Never instruct** — Do not say "Run: bash scripts/gate-runner.sh". Say instead: "I ran the validation — here's what I found."
- **Choices, not commands** — Next steps are things the user might choose or things the agent offers to do, not terminal commands.

## Enforcement Checklist

Every major user-facing response should satisfy these questions:

1. Did we use the technical term and explain it in plain language?
2. Did we explain what we're about to do before doing it?
3. Did we explain what happened after doing it?
4. Did we explain why it matters?
5. Did we explain the next step and why it comes next?
6. When presenting choices: did we explain pros/cons, make a recommendation, and give the rationale?
7. Did we avoid unexplained jargon?
8. Did we present options in outcome language first?
9. Did we avoid telling the user to run scripts?
