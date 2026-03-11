---
name: vibeos-gate
description: Run VibeOS quality gates from Codex. Use when the user says check the code, run quality checks, validate this, are we passing, pre-commit check, or wants gate status before closing a work order.
---

# VibeOS Gate

Use this skill to run the shared gate runner and explain the result in plain English.

## Workflow

1. Determine the requested phase:
   - `session_start`
   - `pre_commit`
   - `wo_exit`
   - `full_audit`
   - `post_deploy`
   - `session_end`
2. Default to `pre_commit` if the user does not specify a phase.
3. Run:

```bash
bash ".vibeos/scripts/gate-runner.sh" <phase> --continue-on-failure
```

4. Explain:
   - what passed
   - what failed
   - what is blocking vs advisory
   - the next recommended move

## Rules

- Lead with the bottom line, not raw terminal output.
- If the user wants gate inventory, read `scripts/quality-gate-manifest.json` and summarize it.
