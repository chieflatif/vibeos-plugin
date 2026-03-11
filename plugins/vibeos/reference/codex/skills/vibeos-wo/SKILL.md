---
name: vibeos-wo
description: Work Order management for VibeOS in Codex. Use when the user wants to create a WO, inspect WO status, mark a WO complete, audit a WO, or manage an individual unit of work inside the VibeOS plan.
---

# VibeOS Work Orders

Use this skill for Work Order creation, inspection, closeout, and audit.

## Workflow

1. Read:
   - `docs/planning/WO-INDEX.md`
   - `docs/planning/DEVELOPMENT-PLAN.md`
   - `.vibeos/reference/governance/WO-TEMPLATE.md.ref` when creating a new WO
2. Support four common flows:
   - create a new WO
   - show status of a WO
   - validate and close a WO
   - audit a WO before implementation or closeout
3. When closing a WO, run:

```bash
bash ".vibeos/scripts/gate-runner.sh" wo_exit --continue-on-failure
```

4. Keep status truthful. If evidence is partial, use a truthful partial state instead of `Complete`.

## Rules

- No WO without a concrete objective and acceptance criteria.
- No WO closeout without evidence.
- Explain WO status in plain English first, then include identifiers.
