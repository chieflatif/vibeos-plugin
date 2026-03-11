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
3. Run the matching shared gates with `.vibeos/scripts/gate-runner.sh`.
4. Use `.codex/agents/*auditor*.md` as role contracts and execute the audit phases yourself.
5. Report findings in severity order, with business impact first and concrete fixes second.
6. If there are no findings, say that plainly and note residual risk or verification gaps.

## Rules

- Findings come first; summaries come second.
- Do not overstate confidence when the evidence is incomplete.
- Keep accepted risks, deferred work, and blockers explicit.
