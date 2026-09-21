---
name: vibeos-audit
description: VibeOS audit flow for Codex. Use when the user asks for a code audit, quality review, governance review, architecture review, security review, or wants a full audit cycle before or after implementation work.
---

# VibeOS Audit

Use this skill for focused or full audits of the current project state.

## Workflow

1. Read `docs/USER-COMMUNICATION-CONTRACT.md`, `project-definition.json`, and the relevant planning or anchor docs.
2. Decide whether the request is:
   - focused audit of one change area
   - WO-level audit
   - full project audit
3. Refresh runtime capabilities:

```bash
bash ".vibeos/scripts/detect-runtime-capabilities.sh" --project-dir "."
```

4. Run the matching shared gates with `.vibeos/scripts/gate-runner.sh`.
   When the profile activates `claude-companion-audit`, use its installed skill for
   one independent review covering the relevant lenses in step 5; this replaces
   generic auditor fanout for the same change. Add a specialist only for a named
   gap in coverage, retain its findings, and use targeted correction verification.
5. When the companion module is inactive, use available Codex-native agents or `.codex/agent-contracts/*auditor*.md` role contracts according to `.vibeos/runtime-capabilities.json`, then execute the audit phases with severity discipline. Cover flow integrity for user journeys and layer handoffs, system invariants for state/recovery/side effects, dependency intelligence for package and runtime changes, and delivery infrastructure for deployment and operational changes. These are review lenses; in an opted-in companion review they do not each require a separate agent.
6. Report findings in severity order, with business impact first and concrete fixes second.
7. If there are no findings, say that plainly and note residual risk or verification gaps.

## Rules

- Findings come first; summaries come second.
- Do not overstate confidence when the evidence is incomplete.
- Keep accepted risks, deferred work, and blockers explicit.
