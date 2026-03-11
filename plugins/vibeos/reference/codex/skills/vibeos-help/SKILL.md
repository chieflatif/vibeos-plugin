---
name: vibeos-help
description: Explain VibeOS concepts and route the user to the right Codex workflow. Use when the user asks what a VibeOS term means, wants the difference between status and project status, needs help choosing a workflow, or wants the system explained in plain English.
---

# VibeOS Help

Use this skill to explain concepts and help the user pick the right workflow.

## Workflow

1. Explain the concept in plain English first.
2. Use the real technical term and define it on first use.
3. If the question clearly maps to a workflow, recommend the matching skill:
   - `vibeos-discover`
   - `vibeos-plan`
   - `vibeos-build`
   - `vibeos-audit`
   - `vibeos-gate`
   - `vibeos-status`
   - `vibeos-project-status`
   - `vibeos-session-audit`
   - `vibeos-checkpoint`
   - `vibeos-wo`
   - `vibeos-autonomous`
4. If the user is asking about a specific file, line, or error, help directly instead of forcing a workflow.

## Rules

- Teach without talking down.
- Favor concrete examples over abstract taxonomy.
- Route the user only when that improves momentum.
